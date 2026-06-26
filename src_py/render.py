"""
Rendering utilities for the Wordle bot. Extracted from bot.py for readability.
All HTML/CSS rendering lives here, separate from command/event handling.
"""
import os
from datetime import datetime, timezone

from leaderboard_store import (
    get_today_key,
    get_leaderboard_for_date,
    normalize_event_key as lb_normalize,
)
from events import EVENTS
from game_scoring import HINT_PENALTY, get_hint_penalty_count
from game_logic import (
    normalize_event_key,
    render_share_grid,
    MAX_GUESSES,
    MIN_GUESSES_BEFORE_HINT,
    _CSS,
)
from genshin_countdown import get_genshin_update_date_key, get_genshin_event_date_key
from stats import (
    get_level,
    get_user_stats,
    get_completed_puzzle_results_for_user,
    get_current_streak,
    get_all_time_leaderboard_entries,
)
from xp_store import check_and_apply_comeback_bonus

# ── constants ─────────────────────────────────────────────────────────────────

OWNER_USER_ID = os.environ.get("OWNER_USER_ID", "")
CREDITS_TAG = "[@:1750075711936438273]"
GENSHIN_ALIAS_HINT = (
    "Use 5-letter Genshin tags like `AYAKA`, `AYATO`, `HUTAO`, `KAZUH`, or `TARTA`."
)
FORSAKEN_ALIAS_HINT = (
    "Use 5-letter Forsaken tags like `NOOBB`, `SLASH`, `JOHND`, `JANEE`, or `NOSFE`."
)
VOCALOID_ALIAS_HINT = (
    "Use 5-letter Vocaloid tags like `MIKUU`, `TETOO`, `LUKAA`, `RINNN`, or `LENNN`."
)

# ── helpers ────────────────────────────────────────────────────────────────────


def _credits(text: str) -> str:
    return f"{text}\n\nCredits: {CREDITS_TAG}"


def _get_display_label(user, fallback: str = "unknown") -> str:
    if not user:
        return fallback
    tag = getattr(user, "tag", None) or getattr(user, "discriminator", None)
    name = getattr(user, "username", None) or fallback
    return f"{name}:{tag}" if tag else name


def _get_level_for_user(user_id: str, xp: int) -> dict:
    if OWNER_USER_ID and str(user_id) == str(OWNER_USER_ID):
        return {
            "level": "inf",
            "tier": "Owner",
            "xp": xp,
            "xpIntoLevel": 0,
            "xpNeeded": 1,
            "isMax": False,
        }
    return get_level(xp)


def _format_avg(value) -> str:
    if value is None or not isinstance(value, (int, float)) or not (value == value):
        return "0.0"
    return f"{value:.1f}"


def _apply_comeback_bonus(user_id: str):
    today = get_today_key()
    results = get_completed_puzzle_results_for_user(user_id)
    if not results:
        return None
    last_played = results[-1]["dateKey"]
    if last_played >= today:
        return None
    fired = check_and_apply_comeback_bonus(user_id, last_played, today)
    return (
        "🎉 **Comeback Bonus!** You were away for a week — your XP this game is **2x**!"
        if fired
        else None
    )


def _get_event_meta(event_key: str):
    norm = normalize_event_key(event_key)
    return next((e for e in EVENTS if e["key"] == norm), None)


def _format_genshin_status() -> str:
    upd = get_genshin_update_date_key()
    evt = get_genshin_event_date_key()
    if not upd or not evt:
        return "Genshin countdown data is unavailable right now."
    return f"The next Genshin update is cached for **{upd}**, so the auto-Genshin day is **{evt}**."


# ── HTML renderers ────────────────────────────────────────────────────────────

_H = (
    "<style>"
    ".card{background:#1e1e2e;border-radius:10px;padding:20px;color:#cdd6f4;max-width:480px;min-height:400px}"
    ".card-wide{background:#1e1e2e;border-radius:10px;padding:20px;color:#cdd6f4;max-width:600px;min-height:400px}"
    ".title{font-size:18px;font-weight:700;margin-bottom:10px;color:#cba6f7}"
    ".cmd{color:#89b4fa;font-weight:600}"
    ".row{padding:5px 0}"
    ".lbl{color:#a6adc8;font-size:13px}"
    ".val{color:#cdd6f4;font-size:13px;font-weight:600}"
    ".section{margin-top:12px}"
    ".sh{font-size:13px;font-weight:700;color:#f38ba8;margin-bottom:4px}"
    ".tier{color:#fab387;font-size:12px}"
    ".win{color:#a6e3a1}"
    ".lose{color:#f38ba8}"
    ".streak{color:#fab387}"
    ".hard{color:#cba6f7}"
    ".xp{color:#f9e2af}"
    ".dim{color:#6c7086;font-size:12px}"
    "</style>"
)
_S = {
    "card": "card",
    "title": "title",
    "cmd": "cmd",
    "row": "row",
    "lbl": "lbl",
    "val": "val",
    "section": "section",
    "sh": "sh",
    "tier": "tier",
    "win": "win",
    "lose": "lose",
    "streak": "streak",
    "hard": "hard",
    "xp": "xp",
    "dim": "dim",
}


def _h(tag: str, cls: str, content: str) -> str:
    return f'<{tag} class="{cls}">{content}</{tag}>'


def _render_error_html(message: str) -> str:
    """Render an error message as HTML to avoid pinging with credits."""
    return (
        f'{_H}<div class="card">'
        f'<div class="title">❌ Error</div>'
        f'<div class="lbl">{message}</div>'
        f'<div class="dim" style="margin-top:10px">Credits: {CREDITS_TAG}</div></div>'
    )


def _render_help_html() -> str:
    import html as _html

    e = _html.escape
    event_cmds = [
        (f"/{ev['command']}", f"Play the {ev['title']} special Wordle") for ev in EVENTS
    ]
    main_cmds = [
        ("/wordle", "Start or view today's puzzle"),
        ("/answer &lt;word&gt;", "Submit a 5-letter guess"),
        (
            f"/hint",
            f"After {MIN_GUESSES_BEFORE_HINT} guesses, reveal 1 letter (costs {HINT_PENALTY} guesses)",
        ),
        ("/hard", "Hard mode — 2x XP, no hints, must reuse confirmed letters"),
        ("/giveup", "Surrender and reveal the word"),
        ("/share", "Post a spoiler-free emoji grid"),
        ("/challenge @user", "Ping someone to play"),
        ("/versus @user", "1v1 Wordle duel (turn-based, no XP)"),
        ("/duelguess &lt;word&gt;", "Make your guess in an active duel"),
        ("/leaderboard", "Today's leaderboard"),
        ("/alltimeleaderboard", "Hall of fame"),
        ("/mystats", "Your personal stats"),
        *event_cmds,
    ]
    rows = "".join(
        f'<div class="row"><span class="cmd">{c}</span> <span class="lbl">— {d}</span></div>'
        for c, d in main_cmds
    )
    return (
        f'{_H}<div class="card">'
        f'<div class="title">📘 Commands</div>{rows}'
        f'<div class="dim" style="margin-top:10px">Credits: {CREDITS_TAG}</div>'
        f"</div>"
    )


def _render_leaderboard_html(date_key: str, event_key: str = "") -> str:
    norm = lb_normalize(event_key)
    entries = get_leaderboard_for_date(date_key, norm)
    meta = _get_event_meta(norm)
    title = (
        f"{'🏆 ' + meta['title'] + ' Leaderboard' if meta else '🏆 Leaderboard'} — {date_key}"
    )
    play_cmd = f"/{meta['command']}" if meta else "/wordle"
    if not entries:
        return (
            f'{_H}<div class="card">'
            f'<div class="title">{title}</div>'
            f'<div class="lbl">No results yet. Play with <span class="cmd">{play_cmd}</span>.</div>'
            f'<div class="dim" style="margin-top:10px">Credits: {CREDITS_TAG}</div></div>'
        )
    rows = []
    for idx, r in enumerate(entries[:50]):
        score = (
            f"{r['guesses']}/{MAX_GUESSES}"
            if r["status"] == "won"
            else f"X/{MAX_GUESSES}"
        )
        won = r["status"] == "won"
        hard = ' <span class="hard">🔒</span>' if r.get("hardMode") else ""
        label = r.get("displayName") or r.get("userId", "?")
        streak = get_current_streak(r["userId"], norm)
        streak_sfx = f' <span class="streak">🔥{streak}</span>' if streak > 0 else ""
        score_style = "color:#a6e3a1" if won else "color:#f38ba8"
        rows.append(
            f'<div class="row">'
            f'<span class="lbl">{idx + 1}. {label}</span>'
            f'<span><span style="{score_style}">{score}</span>{hard}{streak_sfx}</span>'
            f"</div>"
        )
    return (
        f'{_H}<div class="card">'
        f'<div class="title">{title}</div>'
        + "".join(rows)
        + f'<div class="dim" style="margin-top:10px">Credits: {CREDITS_TAG}</div></div>'
    )


def _render_all_time_leaderboard_html(live_names: dict = None) -> str:
    entries = get_all_time_leaderboard_entries()
    card = "background:#1e1e2e;border-radius:10px;padding:16px;color:#cdd6f4"
    if not entries:
        return (
            f'<div style="{card}">'
            f'<div class="title">🏛️ All-Time Leaderboard</div>'
            f'<div class="lbl">No entries yet. Play with <b>/wordle</b>.</div>'
            f'<div class="dim" style="margin-top:10px">Credits: {CREDITS_TAG}</div></div>'
        )
    rows = []
    for idx, e in enumerate(entries[:20]):
        avg = "-" if e["averageGuesses"] is None else _format_avg(e["averageGuesses"])
        lv = _get_level_for_user(e["userId"], e.get("xp", 0))
        streak = f' 🔥{e["currentStreak"]}' if e["currentStreak"] > 0 else ""
        hard = f' 🔒{e["hardWins"]}' if e["hardWins"] > 0 else ""
        name = (live_names or {}).get(e["userId"]) or e["displayName"]
        rows.append(
            f'<div style="padding:3px 0;font-size:13px">'
            f"<b>{idx + 1}. {name}</b> "
            f'<span class="streak">Lv.{lv["level"]} {lv["tier"]}</span> '
            f'<span class="win">🏆{e["wins"]}W {round(e["winRate"])}%</span> '
            f"avg{avg}{streak}{hard} "
            f'<span class="xp">✨{e.get("xp", 0)}</span>'
            f"</div>"
        )
    return (
        f'<div style="{card}">'
        f'<div class="title">🏛️ All-Time Leaderboard</div>'
        + "".join(rows)
        + f'<div class="dim" style="margin-top:10px">Credits: {CREDITS_TAG}</div></div>'
    )


def _render_my_stats_html(user, streak_event_key: str = "") -> str:
    label = _get_display_label(user, getattr(user, "id", "unknown"))
    stats = get_user_stats(str(user.id), streak_event_key)
    lv = _get_level_for_user(str(user.id), stats["xp"])
    is_owner = OWNER_USER_ID and str(user.id) == str(OWNER_USER_ID)
    if not stats["gamesPlayed"]:
        return (
            f'{_H}<div class="card">'
            f'<div class="title">📊 {label}</div>'
            f'<div class="lbl">No completed games yet. Play with <span class="cmd">/wordle</span>!</div>'
            f'<div class="dim" style="margin-top:10px">Credits: {CREDITS_TAG}</div></div>'
        )
    if is_owner:
        xp_str = "MAX"
    elif lv["isMax"]:
        xp_str = f'{stats["xp"]} (MAX)'
    else:
        xp_str = f'{stats["xp"]} ({lv["xpIntoLevel"]}/{lv["xpNeeded"]} to next)'
    best_mode = (
        f'{stats["bestMode"]["title"]} (avg {_format_avg(stats["bestMode"]["avgGuesses"])})'
        if stats.get("bestMode")
        else "No wins yet"
    )
    fields = [
        ("🏅 Level", f'{lv["level"]} — {lv["tier"]}', "tier"),
        ("✨ XP", xp_str, "xp"),
        ("🎮 Played", str(stats["gamesPlayed"]), "val"),
        ("✅ Win Rate", f'{round(stats["winRate"])}%', "win"),
        ("🔒 Hard Wins", str(stats["hardWins"]), "hard"),
        ("📈 Avg Guesses", _format_avg(stats["averageGuesses"]), "val"),
        ("🔥 Streak", str(stats["currentStreak"]), "streak"),
        ("🏆 Best Streak", str(stats["bestStreak"]), "streak"),
        ("💀 Total Fails", str(stats["totalFails"]), "lose"),
        ("⭐ Best Mode", best_mode, "val"),
    ]
    rows = "".join(
        f'<div class="row"><span class="lbl">{k}</span><span class="{cls}">{v}</span></div>'
        for k, v, cls in fields
    )
    return (
        f'{_H}<div class="card">'
        f'<div class="title">📊 {label}</div>'
        + rows
        + f'<div class="dim" style="margin-top:10px">Credits: {CREDITS_TAG}</div></div>'
    )


def _render_compare_html(
    my_id: str,
    my_label: str,
    my_stats: dict,
    their_id: str,
    their_label: str,
    their_stats: dict,
) -> str:
    """Render a side-by-side stats comparison."""
    my_lv = _get_level_for_user(my_id, my_stats["xp"])
    their_lv = _get_level_for_user(their_id, their_stats["xp"])

    def _winner(my_val, their_val, higher_is_better=True):
        if my_val == their_val:
            return "tie", "tie"
        try:
            my_cmp = (
                float("inf")
                if my_val in ("inf", "inf")
                else float(my_val) if my_val is not None else -float("inf")
            )
            their_cmp = (
                float("inf")
                if their_val in ("inf", "inf")
                else float(their_val) if their_val is not None else -float("inf")
            )
        except (ValueError, TypeError):
            return "tie", "tie"
        if my_cmp == their_cmp:
            return "tie", "tie"
        if higher_is_better:
            return ("win", "lose") if my_cmp > their_cmp else ("lose", "win")
        return ("win", "lose") if my_cmp < their_cmp else ("lose", "win")

    my_wr = round(my_stats["winRate"])
    their_wr = round(their_stats["winRate"])
    wr_result = _winner(my_wr, their_wr, True)
    my_avg = my_stats["averageGuesses"] if my_stats["averageGuesses"] else 999
    their_avg = their_stats["averageGuesses"] if their_stats["averageGuesses"] else 999
    avg_result = _winner(my_avg, their_avg, False)
    streak_result = _winner(
        my_stats["currentStreak"], their_stats["currentStreak"], True
    )
    best_streak_result = _winner(
        my_stats["bestStreak"], their_stats["bestStreak"], True
    )
    level_result = _winner(my_lv["level"], their_lv["level"], True)

    def _stat_row(label, my_value, their_value, my_class, their_class):
        return (
            f'<div class="row" style="display:flex;justify-content:space-between;padding:8px 0">'
            f'<span class="{my_class}" style="flex:1;text-align:left">{my_value}</span>'
            f'<span class="lbl" style="flex:1;text-align:center;font-weight:600">{label}</span>'
            f'<span class="{their_class}" style="flex:1;text-align:right">{their_value}</span>'
            f"</div>"
        )

    rows = [
        _stat_row(
            "🏅 Level",
            f'{my_lv["level"]} {my_lv["tier"]}',
            f'{their_lv["level"]} {their_lv["tier"]}',
            level_result[0],
            level_result[1],
        ),
        _stat_row("✨ XP", str(my_stats["xp"]), str(their_stats["xp"]), "xp", "xp"),
        _stat_row(
            "✅ Win Rate",
            f"{my_wr}%",
            f"{their_wr}%",
            wr_result[0],
            wr_result[1],
        ),
        _stat_row(
            "📈 Avg Guesses",
            _format_avg(my_stats["averageGuesses"]),
            _format_avg(their_stats["averageGuesses"]),
            avg_result[0],
            avg_result[1],
        ),
        _stat_row(
            "🔥 Streak",
            str(my_stats["currentStreak"]),
            str(their_stats["currentStreak"]),
            streak_result[0],
            streak_result[1],
        ),
        _stat_row(
            "🏆 Best Streak",
            str(my_stats["bestStreak"]),
            str(their_stats["bestStreak"]),
            best_streak_result[0],
            best_streak_result[1],
        ),
        _stat_row(
            "🎮 Games Played",
            str(my_stats["gamesPlayed"]),
            str(their_stats["gamesPlayed"]),
            "val",
            "val",
        ),
        _stat_row(
            "🔒 Hard Wins",
            str(my_stats["hardWins"]),
            str(their_stats["hardWins"]),
            "hard",
            "hard",
        ),
    ]

    return (
        f'{_H}<div style="display:flex;font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,sans-serif;">'
        f'<div style="width:4px;background:#cba6f7;flex-shrink:0;border-radius:5px 0px 0px 5px;"></div>'
        f'<div style="padding:16px;background:#1e1e2e;flex:1;border-radius:0px 5px 5px 0px;min-width:400px;">'
        f'<div class="title">⚔️ Stats Comparison</div>'
        f'<div style="display:flex;justify-content:space-between;margin:10px 0;padding:10px;background:#181825;border-radius:5px">'
        f'<span class="lbl" style="font-weight:700;color:#89b4fa">{my_label}</span>'
        f'<span class="lbl" style="font-weight:700;color:#f38ba8">{their_label}</span>'
        f"</div>"
        + "".join(rows)
        + f'<div class="dim" style="margin-top:10px">Credits: {CREDITS_TAG}</div>'
        f"</div></div>"
    )


def _render_share_html(game: dict) -> str:
    """Render a spoiler-free emoji grid. Uses render_share_grid from game_logic."""
    grid_text = render_share_grid(game)
    lines = grid_text.split("\n")
    headline = lines[0]
    emoji_rows = lines[2:]
    grid_html = "".join(
        f'<div style="font-size:22px">{r}</div>' for r in emoji_rows if r
    )
    return (
        f'{_H}<div class="card">'
        f'<div class="title">{headline}</div>'
        f"{grid_html}"
        f'<div class="dim" style="margin-top:10px">Credits: {CREDITS_TAG}</div></div>'
    )


def _render_server_leaderboard_html(
    date_key: str, event_key: str, member_ids: set
) -> str:
    """Render a server-specific leaderboard filtered to a set of member user IDs."""
    norm = lb_normalize(event_key)
    entries = get_leaderboard_for_date(date_key, norm)
    filtered = [e for e in entries if e["userId"] in member_ids]
    meta = _get_event_meta(norm)
    title = f"{'🏆 ' + meta['title'] + ' Leaderboard' if meta else '🏆 Leaderboard'} — {date_key}"
    play_cmd = f"/{meta['command']}" if meta else "/wordle"
    if not filtered:
        return (
            f'{_H}<div class="card-wide">'
            f'<div class="title">{title}</div>'
            f'<div class="lbl">No one in this server has played yet. '
            f'Play with <span class="cmd">{play_cmd}</span>.</div>'
            f'<div class="dim" style="margin-top:10px">Credits: {CREDITS_TAG}</div></div>'
        )
    rows = []
    for idx, r in enumerate(filtered[:50]):
        score = (
            f"{r['guesses']}/{MAX_GUESSES}"
            if r["status"] == "won"
            else f"X/{MAX_GUESSES}"
        )
        won = r["status"] == "won"
        hard = ' <span class="hard">🔒</span>' if r.get("hardMode") else ""
        label = r.get("displayName") or r.get("userId", "?")
        streak_entry = get_current_streak(r["userId"], norm)
        streak_sfx = (
            f' <span class="streak">🔥{streak_entry}</span>'
            if streak_entry > 0
            else ""
        )
        score_style = "color:#a6e3a1" if won else "color:#f38ba8"
        rows.append(
            f'<div class="row">'
            f'<span class="lbl">{idx + 1}. {label}</span>'
            f'<span><span style="{score_style}">{score}</span>{hard}{streak_sfx}</span>'
            f"</div>"
        )
    return (
        f'{_H}<div class="card-wide">'
        f'<div class="title">{title}</div>'
        + "".join(rows)
        + f'<div class="dim" style="margin-top:10px">Credits: {CREDITS_TAG}</div></div>'
    )


# ── duel helpers ───────────────────────────────────────────────────────────────

_DUEL_CLS = {"correct": "c", "present": "p", "absent": "a"}


def _evaluate_duel_guess(word: str, guess: str) -> list:
    """Same feedback logic as make_guess but returns list of result dicts.
    Used for duel rendering without modifying any game state."""
    result = [{"letter": guess[i], "result": "absent"} for i in range(len(guess))]
    remaining = list(word)
    for i in range(min(len(guess), len(word))):
        if guess[i] == word[i]:
            result[i]["result"] = "correct"
            remaining[i] = None
    for i in range(len(guess)):
        if result[i]["result"] == "correct":
            continue
        if i < len(remaining) and remaining[i] and guess[i] == remaining[i]:
            result[i]["result"] = "present"
            remaining[i] = None
        elif guess[i] in remaining:
            try:
                idx = remaining.index(guess[i])
                result[i]["result"] = "present"
                remaining[idx] = None
            except ValueError:
                pass
    return result


def _render_duel_board_html(duel: dict, pov_user: str) -> str:
    """Render a duel board from the perspective of a given user."""
    my_guesses = duel.get("boards", {}).get(pov_user, [])
    rows = []
    for guess in my_guesses:
        fb = _evaluate_duel_guess(duel["word"], guess)
        cells = "".join(
            f'<span style="display:inline-block;width:32px;height:32px;'
            f'line-height:32px;text-align:center;font-weight:700;'
            f'border-radius:4px;margin:1px;color:#fff;font-size:16px;'
            f'background:{"#538d4e" if r["result"]=="correct" else "#b59f3b" if r["result"]=="present" else "#3a3a3c" if r["result"]=="absent" else "#1e1e2e"}">'
            f'{_DUEL_CLS.get(r["result"], "?")}</span>'
            for r in fb
        )
        rows.append(f'<div style="margin:2px 0">{cells}</div>')
    board = "".join(rows) if rows else '<div class="lbl">No guesses yet.</div>'
    blanks = MAX_GUESSES - len(my_guesses)
    for _ in range(blanks):
        cells = "".join(
            '<span style="display:inline-block;width:32px;height:32px;'
            'line-height:32px;text-align:center;font-weight:700;'
            'border-radius:4px;margin:1px;background:#1e1e2e;border:1px solid #3a3a3c"></span>'
            for _ in range(5)
        )
        board += f'<div style="margin:2px 0">{cells}</div>'
    return f'{_CSS}<div style="display:flex;flex-direction:column;align-items:center">{board}</div>'
