import os
import sys
import re
import asyncio
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from nerimity_sdk import Bot

from game_logic import (
    start_or_get_game, start_new_game_run, start_hard_mode,
    make_guess, use_hint, render_board, render_board_html,
    give_up_game, MAX_GUESSES, HINT_PENALTY, MIN_GUESSES_BEFORE_HINT,
    get_current_state_for_user, normalize_event_key, _CSS,
)
from duel_store import (
    get_duel_for_user, create_duel, get_duel, end_duel, next_turn, DUEL_TIMEOUT,
)
from word_list import get_user_daily_solution

from game_scoring import get_effective_guess_count

from leaderboard_store import (
    cleanup_old_leaderboard_files, get_today_key,
    get_leaderboard_for_date, normalize_event_key as lb_normalize,
)
from events import EVENTS, get_event_date_key_for_year
from genshin_countdown import (
    ensure_fresh_genshin_countdown,
    get_genshin_event_date_key, get_genshin_update_date_key,
)
import leaderboard_notifier
from leaderboard_message_store import (
    add_leaderboard_message, list_leaderboard_messages, prune_leaderboard_messages,
)
from stats import (
    get_all_time_leaderboard_entries,
    get_user_stats, get_level,
)
from debug_store import lock_command, unlock_command, is_locked
from forsaken_store import set_forsaken_date_key
from max_level_store import has_been_notified, mark_notified
from dm_channel_store import get_dm_channel_id, set_dm_channel_id
from render import (
    CREDITS_TAG, GENSHIN_ALIAS_HINT, FORSAKEN_ALIAS_HINT, VOCALOID_ALIAS_HINT,
    _apply_comeback_bonus, _get_display_label, _get_level_for_user, _format_avg,
    _get_event_meta, _format_genshin_status, _render_error_html, _render_help_html,
    _render_leaderboard_html, _render_all_time_leaderboard_html, _render_my_stats_html,
    _render_compare_html, _render_share_html, _render_server_leaderboard_html,
    _render_duel_board_html, _evaluate_duel_guess,
)

BOT_TOKEN = os.environ.get("NERIMITY_TOKEN") or os.environ.get("NERIMITY_BOT_TOKEN", "")
OWNER_USER_ID = os.environ.get("OWNER_USER_ID", "")
REMINDER_CHANNEL_ID = os.environ.get("REMINDER_CHANNEL_ID", "")
REMINDER_CRON = os.environ.get("REMINDER_CRON", "0 3 * * *")
DEBUG_CODE = "code"
KEEP_ALIVE_CODE = "helloiamtheownercodejj"

if not BOT_TOKEN:
    print("Missing NERIMITY_TOKEN in .env", file=sys.stderr)
    sys.exit(1)

# Patch the gateway to subscribe to the correct button click event name
import nerimity_sdk.transport.gateway as _gw
if "message:button_clicked" not in _gw._GATEWAY_EVENTS:
    _gw._GATEWAY_EVENTS.append("message:button_clicked")

bot = Bot(token=BOT_TOKEN, prefix="/")




async def _refresh_leaderboard_messages(date_key: str, event_key: str = "") -> None:
    norm = lb_normalize(event_key)
    targets = list_leaderboard_messages(date_key, norm)
    if not targets:
        return
    html = _render_leaderboard_html(date_key, norm)
    for t in targets:
        try:
            msg = await bot.rest.fetch_message(t["channelId"], t["messageId"])
            if not msg:
                prune_leaderboard_messages(date_key, norm,
                    lambda x: x["channelId"] == t["channelId"] and x["messageId"] == t["messageId"])
                continue
            await bot.rest.edit_message(t["channelId"], t["messageId"], "", embed={"htmlEmbed": html})
        except Exception as err:
            err_str = str(err).lower()
            if any(w in err_str for w in ("permission", "forbidden", "unauthorized", "missing")):
                prune_leaderboard_messages(date_key, norm,
                    lambda x: x["channelId"] == t["channelId"] and x["messageId"] == t["messageId"])


async def _send_owner_dm(content: str) -> None:
    ch_id = get_dm_channel_id()
    if not ch_id:
        print("[DM]", content)
        return
    try:
        await bot.rest.create_message(ch_id, content)
    except Exception as e:
        print(f"Could not send owner DM: {e}")


def _setup_leaderboard_notifier():
    def _on_updated(date_key: str, event_key: str):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_refresh_leaderboard_messages(date_key, event_key))
        except RuntimeError:
            pass
    leaderboard_notifier.on_updated(_on_updated)


# ── ready ─────────────────────────────────────────────────────────────────────

_RPC_MESSAGES = [
    "Do /wordle to start a game!",
    "Credits to @Kasane:TETO!",
    "21 servers | /whelp",
    "Invite me to your servers!",
]
_rpc_index = 0
_activity_task: asyncio.Task | None = None
_lb_notifier_registered = False


async def _rotate_activity():
    global _rpc_index
    while True:
        name = _RPC_MESSAGES[_rpc_index % len(_RPC_MESSAGES)]
        _rpc_index += 1
        try:
            await bot._gateway.emit("user:update_activity", {
                "action": "Watching",
                "name": name,
                "startedAt": int(datetime.now(timezone.utc).timestamp() * 1000),
            })
        except Exception as e:
            print(f"[RPC] Failed to set activity: {e}")
        await asyncio.sleep(10)


@bot.on("ready")
async def on_ready(me):
    global _activity_task, _lb_notifier_registered
    print(f"Connected as {me.username}!")

    # Cancel any previous activity task before spawning a new one
    if _activity_task and not _activity_task.done():
        _activity_task.cancel()
    _activity_task = asyncio.get_event_loop().create_task(_rotate_activity())

    cleanup_old_leaderboard_files()
    cache = await ensure_fresh_genshin_countdown()
    if cache.get("updateDateKey"):
        print(f"Genshin countdown cached. Update: {cache['updateDateKey']}; auto-event day: {cache['eventDateKey']}")
    else:
        print("Could not refresh the Genshin countdown cache on startup.")

    # Only register the leaderboard notifier once — re-registering on every
    # reconnect stacks duplicate callbacks and can stall the event loop.
    if not _lb_notifier_registered:
        _setup_leaderboard_notifier()
        _lb_notifier_registered = True

    if REMINDER_CHANNEL_ID:
        print(f"Daily reminder scheduled with cron '{REMINDER_CRON}' for channel {REMINDER_CHANNEL_ID}")
    else:
        print("No REMINDER_CHANNEL_ID set. Daily reminders are disabled.")


# ── cron jobs ─────────────────────────────────────────────────────────────────

if REMINDER_CHANNEL_ID:
    @bot.cron(REMINDER_CRON)
    async def daily_reminder():
        try:
            await bot.rest.create_message(
                REMINDER_CHANNEL_ID,
                "🧩 **Your daily word puzzle is ready!**\nType `/wordle` here to start today's game."
            )
        except Exception as e:
            print(f"Failed to send reminder: {e}")


@bot.cron("17 */6 * * *")
async def refresh_genshin():
    try:
        cache = await ensure_fresh_genshin_countdown()
        if cache.get("updateDateKey"):
            print(f"Genshin countdown refreshed. Update: {cache['updateDateKey']}; auto-event day: {cache['eventDateKey']}")
    except Exception as e:
        print(f"Failed to refresh Genshin countdown: {e}")


# ── commands ──────────────────────────────────────────────────────────────────

DAILY_MODE_COMMANDS = {"wordle", "dailyword", "genshin", "undertale", "deltarune", "vocaloid"}


async def _check_one_mode_per_day(ctx) -> bool:
    """Returns True (and replies) if the user already started a different mode today."""
    user_id = str(ctx.author.id)
    if OWNER_USER_ID and user_id == str(OWNER_USER_ID):
        return False
    cmd = ctx.message.command_name if hasattr(ctx.message, "command_name") else ""
    if cmd not in DAILY_MODE_COMMANDS:
        return False
    today = get_today_key()
    existing = get_current_state_for_user(user_id)
    if existing and existing.get("dateKey") == today:
        requested = "" if cmd in ("wordle", "dailyword") else cmd
        if normalize_event_key(existing.get("eventKey", "")) != normalize_event_key(requested):
            existing_name = f"/{existing['eventKey']}" if existing.get("eventKey") else "/wordle"
            error_html = _render_error_html(f"You already started <b>{existing_name}</b> today. You can only play one mode per day.")
            await ctx.reply_embed({"htmlEmbed": error_html})
            return True
    return False


@bot.command("whelp", description="Show the full slash-command list")
async def cmd_whelp(ctx):
    await ctx.reply_embed({"htmlEmbed": _render_help_html()})


@bot.command("wordle", description="Start or view today's daily word puzzle")
async def cmd_wordle(ctx):
    if await _check_one_mode_per_day(ctx):
        return
    await ensure_fresh_genshin_countdown()
    user_id = str(ctx.author.id)
    game = start_or_get_game(user_id)
    title = f"🧩 Wordle — {game['eventKey']} special" if game.get("eventKey") else "🧩 Wordle"
    used = get_effective_guess_count(game, MAX_GUESSES)
    comeback = _apply_comeback_bonus(user_id) if game["status"] == "in_progress" else None
    if game["status"] == "won":
        footer = f"✅ Already solved in {used} guesses. 🎉"
    elif game["status"] == "lost":
        footer = f"❌ All guesses used. The word was <b>{game['solution']}</b>. Come back tomorrow!"
    else:
        footer = (f"Use <b>/answer CRANE</b> to guess · <b>/hint</b> after {MIN_GUESSES_BEFORE_HINT} guesses (costs {HINT_PENALTY}) · "
                  f"<b>/hard</b> for 2× XP")
    if comeback:
        footer = f"🎉 Comeback Bonus! 2× XP this game!<br />{footer}"
    await ctx.reply_embed({"htmlEmbed": render_board_html(game, title=title, footer=footer, credits=CREDITS_TAG)})


@bot.command("dailyword", description="Alias for /wordle")
async def cmd_dailyword(ctx):
    await cmd_wordle(ctx)


@bot.command("hard", description="Start today's Wordle in hard mode (2x XP, no hints)")
async def cmd_hard(ctx):
    user_id = str(ctx.author.id)
    existing = get_current_state_for_user(user_id)
    if existing and existing.get("eventKey"):
        today = get_today_key()
        result = start_hard_mode(user_id, today)
        if result["error"]:
            error_html = (
                f'{_H}<div class="card">'
                f'<div class="title">❌ Error</div>'
                f'<div class="lbl">{result["error"]}</div>'
                f'<div class="dim" style="margin-top:10px">Credits: {CREDITS_TAG}</div></div>'
            )
            await ctx.reply_embed({"htmlEmbed": error_html})
            return
        await ctx.reply_embed({"htmlEmbed": render_board_html(
            result["game"],
            title="🔒 Hard Mode — switched from special mode",
            footer="Every guess must reuse confirmed letters. /hint disabled. Win or lose: 2× XP.<br />Make your first guess with <b>/answer CRANE</b>.",
            credits=CREDITS_TAG,
        )})
        return
    result = start_hard_mode(user_id)
    if result["error"]:
        error_html = (
            f'{_H}<div class="card">'
            f'<div class="title">❌ Error</div>'
            f'<div class="lbl">{result["error"]}</div>'
            f'<div class="dim" style="margin-top:10px">Credits: {CREDITS_TAG}</div></div>'
        )
        await ctx.reply_embed({"htmlEmbed": error_html})
        return
    await ctx.reply_embed({"htmlEmbed": render_board_html(
        result["game"],
        title="🔒 Hard Mode activated!",
        footer="Every guess must reuse confirmed letters. /hint disabled. Win or lose: 2× XP.<br />Make your first guess with <b>/answer CRANE</b>.",
        credits=CREDITS_TAG,
    )})


@bot.command("answer", description="Submit a 5-letter word guess")
async def cmd_answer(ctx):
    user_id = str(ctx.author.id)
    label = _get_display_label(ctx.author, user_id)
    guess_raw = ctx.args[0] if ctx.args else None
    result = make_guess(user_id, guess_raw, label)
    if result["error"]:
        error_html = (
            f'{_H}<div class="card">'
            f'<div class="title">❌ Error</div>'
            f'<div class="lbl">{result["error"]}</div>'
            f'<div class="dim" style="margin-top:10px">Credits: {CREDITS_TAG}</div></div>'
        )
        await ctx.reply_embed({"htmlEmbed": error_html})
        return
    game = result["game"]
    used = get_effective_guess_count(game, MAX_GUESSES)
    has_hint = bool(game.get("hintUsed"))
    title = f"🧩 C00L Wordle — {game['eventKey']}" if game.get("eventKey") else "🧩 Daily Word Puzzle"
    if game["status"] == "won":
        footer = f"✅ Solved in {used}/{MAX_GUESSES} guesses!"
    elif game["status"] == "lost":
        footer = f"❌ No more guesses. The word was <b>{game['solution']}</b>."
    else:
        hint_note = f" (includes {HINT_PENALTY}-guess hint penalty)" if has_hint else ""
        footer = f"Guesses used: {used}/{MAX_GUESSES}{hint_note} · Keep going with <b>/answer WORD</b>"
        if not has_hint and not game.get("hardMode") and len(game["guesses"]) >= MIN_GUESSES_BEFORE_HINT:
            footer += f"<br />💡 Stuck? Use <b>/hint</b> to reveal a letter (costs {HINT_PENALTY} guesses)"
    await ctx.reply_embed({"htmlEmbed": render_board_html(game, title=title, footer=footer, credits=CREDITS_TAG)})

    if game["status"] in ("won", "lost") and not has_been_notified(user_id):
        stats = get_user_stats(user_id, "")
        lv = get_level(stats["xp"])
        if lv["isMax"]:
            mark_notified(user_id)
            notif = f"🏆 **Max Level Reached!** {label} (ID: {user_id}) just hit **Level 100 — No Life**. Go talk to them!"
            print(f"[MAX LEVEL] {label} ({user_id}) reached level 100!")
            await _send_owner_dm(notif)


@bot.command("guess", description="Use /answer instead")
async def cmd_guess(ctx):
    error_html = (
        f'{_H}<div class="card">'
        f'<div class="title">❌ Error</div>'
        f'<div class="lbl">/guess isn\'t the right command. Use <span class="cmd">/answer</span> instead.</div>'
        f'<div class="lbl" style="margin-top:6px">Example: <span class="cmd">/answer CRANE</span></div>'
        f'<div class="dim" style="margin-top:10px">Credits: {CREDITS_TAG}</div></div>'
    )
    await ctx.reply_embed({"htmlEmbed": error_html})


@bot.command("hint", description=f"After {MIN_GUESSES_BEFORE_HINT} guesses, reveal 1 letter")
async def cmd_hint(ctx):
    user_id = str(ctx.author.id)
    label = _get_display_label(ctx.author, user_id)
    result = use_hint(user_id, label)
    if result["error"]:
        error_html = (
            f'{_H}<div class="card">'
            f'<div class="title">❌ Error</div>'
            f'<div class="lbl">{result["error"]}</div>'
            f'<div class="dim" style="margin-top:10px">Credits: {CREDITS_TAG}</div></div>'
        )
        await ctx.reply_embed({"htmlEmbed": error_html})
        return
    game = result["game"]
    hint = result["hint"]
    title = f"🧩 Special Wordle — {game['eventKey']}" if game.get("eventKey") else "🧩 Daily Word Puzzle"
    parts = [
        f"<b>{hint['letters'][i]}</b> at position <b>{hint['positions'][i] + 1}</b>"
        for i in range(len(hint["letters"]))
    ]
    footer = (
        f"💡 The word has {' and '.join(parts)}.<br />"
        f"Spent {HINT_PENALTY} guesses — {hint['remainingGuesses']} remaining."
    )
    await ctx.reply_embed({"htmlEmbed": render_board_html(game, title=title, footer=footer, credits=CREDITS_TAG)})


@bot.command("giveup", description="Surrender, reveal the word, and score X/6")
async def cmd_giveup(ctx):
    user_id = str(ctx.author.id)
    label = _get_display_label(ctx.author, user_id)

    # Check duel first
    duel = get_duel_for_user(user_id)
    if duel:
        opp_id = duel["player2"] if user_id == duel["player1"] else duel["player1"]
        word = duel["word"]
        duel["status"] = "done"
        end_duel(duel["id"])
        await ctx.reply(f"🏳️ [@:{user_id}] forfeited the duel! [@:{opp_id}] wins! The word was **{word}**.")
        return

    result = give_up_game(user_id, label)
    if result["error"]:
        error_html = (
            f'{_H}<div class="card">'
            f'<div class="title">❌ Error</div>'
            f'<div class="lbl">{result["error"]}</div>'
            f'<div class="dim" style="margin-top:10px">Credits: {CREDITS_TAG}</div></div>'
        )
        await ctx.reply_embed({"htmlEmbed": error_html})
        return
    game = result["game"]
    title = f"🧩 Special Wordle — {game['eventKey']}" if game.get("eventKey") else "🧩 Daily Word Puzzle"
    footer = f"You gave up. The word was <b>{game['solution']}</b>. Recorded as X/{MAX_GUESSES}."
    await ctx.reply_embed({"htmlEmbed": render_board_html(game, title=title, footer=footer, credits=CREDITS_TAG)})


@bot.command("share", description="Share a spoiler-free emoji grid of your run")
async def cmd_share(ctx):
    user_id = str(ctx.author.id)
    current = get_current_state_for_user(user_id)
    game = (start_or_get_game(user_id, {"dateKey": current["dateKey"], "eventKey": current["eventKey"]})
            if current else start_or_get_game(user_id))
    await ctx.reply_embed({"htmlEmbed": _render_share_html(game)})


@bot.command("challenge", description="Ping someone to play today's Wordle")
async def cmd_challenge(ctx):
    user_id = str(ctx.author.id)
    target = ctx.mentions[0] if ctx.mentions else None
    if not target and ctx.args:
        import re as _re
        m = _re.search(r'\[@:(\d+)\]', " ".join(str(a) for a in ctx.args))
        if m:
            from nerimity_sdk.models import User as _User
            target = type("U", (), {"id": m.group(1)})()
    if not target:
        error_html = _render_error_html('Mention one user. Example: <span class="cmd">/challenge [@:123456789]</span>')
        await ctx.reply_embed({"htmlEmbed": error_html})
        return
    if str(target.id) == user_id:
        error_html = _render_error_html("Challenge someone else, not yourself.")
        await ctx.reply_embed({"htmlEmbed": error_html})
        return
    await ctx.reply_embed({"htmlEmbed": (
        f'<div style="background:#1e1e2e;border-radius:10px;padding:16px;color:#cdd6f4;display:inline-block">'
        f'<div style="font-size:16px;font-weight:700;color:#cba6f7;margin-bottom:6px">⚔️ Wordle Challenge!</div>'
        f'<div style="font-size:13px;color:#a6adc8">[@:{user_id}] challenged [@:{target.id}] to today\'s Wordle!</div>'
        f'<div style="font-size:13px;color:#a6adc8;margin-top:4px">Use <span style="color:#89b4fa;font-weight:600">/wordle</span> to start your run.</div>'
        f'<div style="color:#6c7086;font-size:12px;margin-top:8px">Credits: {CREDITS_TAG}</div>'
        f'</div>'
    )})


@bot.command("leaderboard", description="Show today's leaderboard")
async def cmd_leaderboard(ctx):
    user_id = str(ctx.author.id)
    current = get_current_state_for_user(user_id)
    date_key = current["dateKey"] if current else get_today_key()
    event_key = lb_normalize(current.get("eventKey", "") if current else "")
    keep_alive = ctx.args and str(ctx.args[0]).strip() == KEEP_ALIVE_CODE
    html = _render_leaderboard_html(date_key, event_key)
    msg = await bot.rest.request(
        "POST",
        f"/channels/{ctx.channel_id}/messages",
        json={"content": "\u200b", "htmlEmbed": html, "buttons": _lb_buttons(date_key, event_key)},
    )
    if msg and keep_alive:
        add_leaderboard_message(date_key=date_key, event_key=event_key,
                                channel_id=str(ctx.channel_id), message_id=str(msg.get("id", "")))


@bot.on("message:button_clicked")
async def _on_button_clicked_raw(event):
    data = event if isinstance(event, dict) else (event.__dict__ if hasattr(event, "__dict__") else {})
    button_id = data.get("buttonId", "")
    if not button_id.startswith("lb_"):
        return
    from nerimity_sdk.commands.buttons import ButtonContext
    bctx = ButtonContext(data, bot.rest, bot.cache)
    await on_lb_button(bctx)


@bot.button("lb_*")
async def on_lb_button(bctx):
    print(f"[BUTTON] id={bctx.button_id}")
    # id format: lb_{view}_{YYYYMMDD}_{eventkey}
    parts = bctx.button_id.split("_", 3)  # ["lb", view, date, event]
    if len(parts) < 3:
        return
    view = parts[1]
    raw_date = parts[2]
    event_key = parts[3] if len(parts) > 3 else ""
    date_key = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}"

    if view == "a":
        entries = get_all_time_leaderboard_entries()
        live_names = {}
        for e in entries[:20]:
            live_names[e["userId"]] = await _get_live_display_name(e["userId"])
        html = _render_all_time_leaderboard_html(live_names)
    elif view == "s":
        member_ids = set()
        if bctx.server_id:
            try:
                members = await bot.rest.fetch_server_members(bctx.server_id)
                member_ids = {str(m.id) for m in members}
            except Exception:
                pass
        html = _render_server_leaderboard_html(date_key, event_key, member_ids)
    else:
        html = _render_leaderboard_html(date_key, event_key)

    await bot.rest.request(
        "PATCH",
        f"/channels/{bctx.channel_id}/messages/{bctx.message_id}",
        json={"content": "\u200b", "htmlEmbed": html, "buttons": _lb_buttons(date_key, event_key)},
    )


@bot.command("alltimeleaderboard", description="Show the Wordle hall of fame")
async def cmd_alltimeleaderboard(ctx):
    entries = get_all_time_leaderboard_entries()
    # Resolve live display names
    live_names = {}
    for e in entries[:20]:
        live_names[e["userId"]] = await _get_live_display_name(e["userId"])
    await ctx.reply_embed({"htmlEmbed": _render_all_time_leaderboard_html(live_names)})


@bot.command("mystats", description="Show your personal Wordle stats")
async def cmd_mystats(ctx):
    user_id = str(ctx.author.id)
    current = get_current_state_for_user(user_id)
    event_key = lb_normalize(current.get("eventKey", "") if current else "")
    await ctx.reply_embed({"htmlEmbed": _render_my_stats_html(ctx.author, event_key)})


@bot.command("compare", description="Compare your stats with another player")
async def cmd_compare(ctx):
    user_id = str(ctx.author.id)
    target = ctx.mentions[0] if ctx.mentions else None
    if not target and ctx.args:
        import re as _re
        m = _re.search(r'\[@:(\d+)\]', " ".join(str(a) for a in ctx.args))
        if m:
            target = type("U", (), {"id": m.group(1)})()
    if not target:
        error_html = _render_error_html('Mention a user to compare with. Example: <span class="cmd">/compare [@:123456789]</span>')
        await ctx.reply_embed({"htmlEmbed": error_html})
        return
    if str(target.id) == user_id:
        error_html = _render_error_html("Compare with someone else, not yourself!")
        await ctx.reply_embed({"htmlEmbed": error_html})
        return

    # Get stats for both users
    my_stats = get_user_stats(user_id, "")
    their_stats = get_user_stats(str(target.id), "")
    my_label = _get_display_label(ctx.author, user_id)
    their_label = await _get_live_display_name(str(target.id))

    # Render comparison HTML
    html = _render_compare_html(user_id, my_label, my_stats, str(target.id), their_label, their_stats)
    await ctx.reply_embed({"htmlEmbed": html})


# ── event-mode commands (genshin, undertale, deltarune, forsaken) ─────────────

for _ev in EVENTS:
    def _make_event_cmd(ev):
        @bot.command(ev["command"], description=f"Play the {ev['title']} special Wordle")
        async def _event_cmd(ctx, _ev=ev):
            if await _check_one_mode_per_day(ctx):
                return
            await ensure_fresh_genshin_countdown()
            user_id = str(ctx.author.id)
            year = datetime.now(timezone.utc).year
            date_key = get_event_date_key_for_year(_ev["key"], year) or get_today_key()
            game = start_or_get_game(user_id, {"dateKey": date_key, "eventKey": _ev["key"]})
            if game["status"] != "in_progress":
                game = start_new_game_run(user_id)
            extra = ""
            if _ev["key"] == "genshin":
                extra = f"<br />{_format_genshin_status()}<br />{GENSHIN_ALIAS_HINT}"
            elif _ev["key"] == "forsaken":
                extra = f"<br />{FORSAKEN_ALIAS_HINT}"
            elif _ev["key"] == "vocaloid":
                extra = f"<br />{VOCALOID_ALIAS_HINT}"
            footer = (
                f"Use <b>/answer CRANE</b> to guess · <b>/hint</b> after {MIN_GUESSES_BEFORE_HINT} guesses "
                f"(costs {HINT_PENALTY}) · <b>/wordle</b> to return to daily{extra}"
            )
            await ctx.reply_embed({"htmlEmbed": render_board_html(
                game,
                title=f"🧩 Special Wordle — {_ev['title']}",
                footer=footer,
                credits=CREDITS_TAG,
            )})
    _make_event_cmd(_ev)


# ── duel helpers ─────────────────────────────────────────────────────────────

async def _duel_timeout(duel: dict, channel_id: str, loser_id: str):
    await asyncio.sleep(DUEL_TIMEOUT)
    if duel["status"] != "active":
        return
    winner_id = duel["player2"] if loser_id == duel["player1"] else duel["player1"]
    duel["status"] = "done"
    end_duel(duel["id"])
    await bot.rest.create_message(
        channel_id,
        f"⏰ [@:{loser_id}] ran out of time! [@:{winner_id}] wins the duel! 🎉"
    )


@bot.command("versus", description="Challenge someone to a 1v1 Wordle duel")
async def cmd_versus(ctx):
    user_id = str(ctx.author.id)
    if get_duel_for_user(user_id):
        error_html = _render_error_html("You're already in a duel! Finish it first or <span class=\"cmd\">/giveup</span>.")
        await ctx.reply_embed({"htmlEmbed": error_html})
        return
    target = ctx.mentions[0] if ctx.mentions else None
    if not target and ctx.args:
        import re as _re
        m = _re.search(r'\[@:(\d+)\]', " ".join(str(a) for a in ctx.args))
        if m:
            target = type("U", (), {"id": m.group(1)})()
    if not target:
        error_html = _render_error_html('Mention someone to duel. Example: <span class="cmd">/versus [@:123456789]</span>')
        await ctx.reply_embed({"htmlEmbed": error_html})
        return
    opp_id = str(target.id)
    if opp_id == user_id:
        error_html = _render_error_html("You can't duel yourself.")
        await ctx.reply_embed({"htmlEmbed": error_html})
        return
    if get_duel_for_user(opp_id):
        error_html = _render_error_html(f"[@:{opp_id}] is already in a duel.")
        await ctx.reply_embed({"htmlEmbed": error_html})
        return

    # Pick a shared word based on today's date + both user IDs
    word = get_user_daily_solution(f"{user_id}:{opp_id}", get_today_key())
    duel = create_duel(user_id, opp_id, word)

    html = _render_duel_board_html(duel, user_id)
    await ctx.reply_embed({"htmlEmbed": html})
    await ctx.reply(f"⚔️ [@:{user_id}] challenged [@:{opp_id}] to a Wordle duel!\n[@:{user_id}] goes first — use `/duelguess WORD` to play.")

    task = asyncio.get_event_loop().create_task(
        _duel_timeout(duel, str(ctx.channel_id), user_id)
    )
    duel["timeout_task"] = task
    duel["channel_id"] = str(ctx.channel_id)


@bot.command("duelguess", description="Make a guess in your active duel")
async def cmd_duelguess(ctx):
    user_id = str(ctx.author.id)
    duel = get_duel_for_user(user_id)
    if not duel:
        error_html = _render_error_html('You\'re not in a duel. Start one with <span class="cmd">/versus @user</span>.')
        await ctx.reply_embed({"htmlEmbed": error_html})
        return
    if duel["turn"] != user_id:
        other = duel["player2"] if user_id == duel["player1"] else duel["player1"]
        error_html = _render_error_html(f"It's [@:{other}]'s turn, not yours!")
        await ctx.reply_embed({"htmlEmbed": error_html})
        return

    guess_raw = str(ctx.args[0]).upper().strip() if ctx.args else ""
    if len(guess_raw) != 5 or not guess_raw.isalpha():
        error_html = _render_error_html("Guess must be exactly 5 letters.")
        await ctx.reply_embed({"htmlEmbed": error_html})
        return

    duel["boards"][user_id].append(guess_raw)
    fb = _evaluate_duel_guess(duel["word"], guess_raw)
    won = all(f["result"] == "correct" for f in fb)
    out_of_guesses = len(duel["boards"][user_id]) >= MAX_GUESSES

    opp_id = duel["player2"] if user_id == duel["player1"] else duel["player1"]
    channel_id = duel.get("channel_id", str(ctx.channel_id))

    if won:
        duel["status"] = "done"
        end_duel(duel["id"])
        html = _render_duel_board_html(duel, user_id)
        await ctx.reply_embed({"htmlEmbed": html})
        await ctx.reply(f"🎉 [@:{user_id}] solved it in {len(duel['boards'][user_id])} guesses and wins the duel!")
        return

    if out_of_guesses:
        duel["status"] = "done"
        end_duel(duel["id"])
        html = _render_duel_board_html(duel, user_id)
        await ctx.reply_embed({"htmlEmbed": html})
        await ctx.reply(f"💀 [@:{user_id}] used all guesses! [@:{opp_id}] wins the duel! The word was **{duel['word']}**.")
        return

    next_turn(duel)
    html = _render_duel_board_html(duel, opp_id)
    await ctx.reply_embed({"htmlEmbed": html})
    await ctx.reply(f"[@:{opp_id}] — your turn! Use `/duelguess WORD`.")

    task = asyncio.get_event_loop().create_task(
        _duel_timeout(duel, channel_id, opp_id)
    )
    duel["timeout_task"] = task


# ── owner-only commands ───────────────────────────────────────────────────────

@bot.command_private("setdm")
async def cmd_setdm(ctx):
    if str(ctx.author.id) != str(OWNER_USER_ID):
        return
    if not ctx.args or str(ctx.args[0]).strip() != DEBUG_CODE:
        error_html = _render_error_html("🔐 Wrong code.")
        await ctx.reply_embed({"htmlEmbed": error_html})
        return
    set_dm_channel_id(str(ctx.channel_id))
    success_html = (
        f'{_H}<div class="card">'
        f'<div class="title">✅ Success</div>'
        f'<div class="lbl">This channel is now set as the owner DM channel for notifications.</div>'
        f'<div class="dim" style="margin-top:10px">Credits: {CREDITS_TAG}</div></div>'
    )
    await ctx.reply_embed({"htmlEmbed": success_html})


@bot.command_private("testnotif")
async def cmd_testnotif(ctx):
    if str(ctx.author.id) != str(OWNER_USER_ID):
        return
    if not ctx.args or str(ctx.args[0]).strip() != DEBUG_CODE:
        error_html = _render_error_html("🔐 Wrong code.")
        await ctx.reply_embed({"htmlEmbed": error_html})
        return
    fake_label = str(ctx.args[1]).strip() if len(ctx.args) > 1 else "TestUser:0000"
    await _send_owner_dm(f"🏆 **Max Level Reached!** {fake_label} just hit **Level 100 — No Life**. Go talk to them!")
    success_html = (
        f'{_H}<div class="card">'
        f'<div class="title">✅ Success</div>'
        f'<div class="lbl">Test notification sent.</div>'
        f'<div class="dim" style="margin-top:10px">Credits: {CREDITS_TAG}</div></div>'
    )
    await ctx.reply_embed({"htmlEmbed": success_html})


@bot.command_private("itsforsakenupdate")
async def cmd_forsaken_update(ctx):
    if str(ctx.author.id) != str(OWNER_USER_ID):
        return
    if not ctx.args or str(ctx.args[0]).strip() != DEBUG_CODE:
        error_html = _render_error_html("🔐 Wrong code.")
        await ctx.reply_embed({"htmlEmbed": error_html})
        return
    date_key = get_today_key()
    set_forsaken_date_key(date_key)
    success_html = (
        f'{_H}<div class="card">'
        f'<div class="title">✅ Success</div>'
        f'<div class="lbl">Forsaken update day set to <b>{date_key}</b>. Today\'s <span class="cmd">/forsaken</span> puzzle is now active.</div>'
        f'<div class="dim" style="margin-top:10px">Credits: {CREDITS_TAG}</div></div>'
    )
    await ctx.reply_embed({"htmlEmbed": success_html})


@bot.command_private("printservers")
async def cmd_printservers(ctx):
    if not ctx.args or str(ctx.args[0]).strip() != DEBUG_CODE:
        error_html = _render_error_html("Invalid code.")
        await ctx.reply_embed({"htmlEmbed": error_html})
        return
    servers = list((bot.cache.servers or {}).values()) if hasattr(bot, "cache") else []
    lines = [f"• {getattr(s, 'name', '?')} — `{getattr(s, 'id', '?')}`" for s in servers]
    await ctx.reply(f"**Servers ({len(lines)}):**\n" + "\n".join(lines))


@bot.command_private("debug")
async def cmd_debug(ctx):
    if str(ctx.author.id) != str(OWNER_USER_ID):
        error_html = _render_error_html("You don't have permission to use this command.")
        await ctx.reply_embed({"htmlEmbed": error_html})
        return
    if len(ctx.args) < 2:
        error_html = _render_error_html('Usage: <span class="cmd">/debug [command] [code]</span>')
        await ctx.reply_embed({"htmlEmbed": error_html})
        return
    target = str(ctx.args[0]).lower()
    code = str(ctx.args[1]).strip()
    if code != DEBUG_CODE:
        error_html = _render_error_html("🔐 Wrong code. Command not locked.")
        await ctx.reply_embed({"htmlEmbed": error_html})
        return
    lock_command(target)
    success_html = (
        f'{_H}<div class="card">'
        f'<div class="title">🔒 Debug Mode</div>'
        f'<div class="lbl"><span class="cmd">/{target}</span> is now in debug mode. Only you can use it.</div>'
        f'<div class="dim" style="margin-top:10px">Credits: {CREDITS_TAG}</div></div>'
    )
    await ctx.reply_embed({"htmlEmbed": success_html})


@bot.command_private("undebug")
async def cmd_undebug(ctx):
    if str(ctx.author.id) != str(OWNER_USER_ID):
        error_html = _render_error_html("You don't have permission to use this command.")
        await ctx.reply_embed({"htmlEmbed": error_html})
        return
    if not ctx.args:
        error_html = _render_error_html('Usage: <span class="cmd">/undebug [command]</span>')
        await ctx.reply_embed({"htmlEmbed": error_html})
        return
    target = str(ctx.args[0]).lower()
    unlock_command(target)
    success_html = (
        f'{_H}<div class="card">'
        f'<div class="title">🔓 Debug Mode Disabled</div>'
        f'<div class="lbl"><span class="cmd">/{target}</span> is no longer in debug mode.</div>'
        f'<div class="dim" style="margin-top:10px">Credits: {CREDITS_TAG}</div></div>'
    )
    await ctx.reply_embed({"htmlEmbed": success_html})


# ── global middleware: debug lock ─────────────────────────────────────────────

@bot.on("message:created")
async def _debug_lock_guard(event):
    """Block debug-locked commands for non-owners before the router sees them."""
    msg = event.message
    content = (getattr(msg, "content", "") or "").strip()
    if not content.startswith("/"):
        return
    first_word = content.split()[0]
    cmd_name = re.sub(r"^/([^:\s]+).*", r"\1", first_word).lower()
    if cmd_name in ("debug", "undebug"):
        return
    user_id = str(getattr(msg, "author_id", "") or getattr(msg, "user_id", ""))
    if is_locked(cmd_name) and user_id != str(OWNER_USER_ID):
        channel_id = str(getattr(msg, "channel_id", ""))
        if channel_id:
            try:
                error_html = (
                    f'{_H}<div class="card">'
                    f'<div class="title">🚧 Command Locked</div>'
                    f'<div class="lbl"><span class="cmd">/{cmd_name}</span> is currently in debug mode and unavailable.</div>'
                    f'<div class="dim" style="margin-top:10px">Credits: {CREDITS_TAG}</div></div>'
                )
                await bot.rest.request(
                    "POST",
                    f"/channels/{channel_id}/messages",
                    json={"content": "​", "htmlEmbed": error_html}
                )
            except Exception:
                pass


# ── error handler ─────────────────────────────────────────────────────────────

@bot.on_command_error
async def on_error(ctx, error):
    print(f"Command error: {error}")
    try:
        error_html = (
            f'{_H}<div class="card">'
            f'<div class="title">❌ Error</div>'
            f'<div class="lbl">Something went wrong: {error}</div>'
            f'<div class="dim" style="margin-top:10px">Credits: {CREDITS_TAG}</div></div>'
        )
        await ctx.reply_embed({"htmlEmbed": error_html})
    except Exception:
        pass


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    bot.run()
