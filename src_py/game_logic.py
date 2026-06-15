import re
from datetime import datetime, timezone

from word_list import get_user_daily_solution, get_user_event_solution
from leaderboard_store import record_result
from events import get_event_for_date_key
from game_state_store import load_game_state, save_game_state
from game_scoring import HINT_PENALTY, get_hint_penalty_count, get_effective_guess_count

MAX_GUESSES = 6
WORD_LENGTH = 5
MIN_GUESSES_BEFORE_HINT = 2

_state = load_game_state()
_games: dict = _state.get("games") or {}
_current_by_user: dict = _state.get("currentStateByUser") or {}


def _persist():
    save_game_state(_games, _current_by_user)


def _get_date_key(dt: datetime = None) -> str:
    if dt is None:
        dt = datetime.now(timezone.utc)
    return f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}"


def normalize_event_key(event_key: str) -> str:
    if not event_key:
        return ""
    return re.sub(r"[^a-z0-9_-]", "", str(event_key).lower())


def _get_or_init_state(user_id: str, date_key: str, event_key: str) -> dict:
    norm = normalize_event_key(event_key)
    existing = _current_by_user.get(user_id)
    if (existing and existing.get("dateKey") == date_key
            and normalize_event_key(existing.get("eventKey", "")) == norm):
        return existing
    nxt = {"dateKey": date_key, "eventKey": norm, "runId": 0}
    _current_by_user[user_id] = nxt
    _persist()
    return nxt


def _game_key(user_id: str, date_key: str, event_key: str, run_id: int) -> str:
    return f"{user_id}:{date_key}:{normalize_event_key(event_key)}:{run_id}"


def _resolve_event_key(date_key: str, requested: str) -> str:
    norm = normalize_event_key(requested)
    if norm:
        return norm
    ev = get_event_for_date_key(date_key)
    return ev["key"] if ev else ""


def get_current_state_for_user(user_id: str):
    return _current_by_user.get(user_id) or None


def start_or_get_game(user_id: str, ctx=None) -> dict:
    if ctx is None:
        ctx = datetime.now(timezone.utc)

    if isinstance(ctx, dict) and "dateKey" in ctx:
        date_key = ctx["dateKey"]
        event_key = _resolve_event_key(date_key, ctx.get("eventKey", ""))
    else:
        date_key = _get_date_key(ctx if isinstance(ctx, datetime) else None)
        event_key = _resolve_event_key(date_key, "")

    state = _get_or_init_state(user_id, date_key, event_key)
    run_id = state["runId"]
    key = _game_key(user_id, date_key, event_key, run_id)
    if key in _games:
        return _games[key]

    solution = (get_user_event_solution(user_id, date_key, run_id, event_key)
                if event_key else get_user_daily_solution(user_id, date_key, run_id))

    game = {
        "dateKey": date_key,
        "runId": run_id,
        "eventKey": event_key,
        "solution": solution,
        "guesses": [],
        "status": "in_progress",
        "hardMode": False,
        "hintUsed": False,
        "hintPenalty": 0,
        "hintPositions": [],
    }
    _games[key] = game
    _persist()
    return game


def start_new_game_run(user_id: str) -> dict:
    current = _current_by_user.get(user_id)
    date_key = current["dateKey"] if current else _get_date_key()
    event_key = current["eventKey"] if current else _resolve_event_key(date_key, "")
    next_run_id = int((current or {}).get("runId", 0)) + 1
    _current_by_user[user_id] = {"dateKey": date_key, "eventKey": event_key, "runId": next_run_id}
    _persist()
    return start_or_get_game(user_id, {"dateKey": date_key, "eventKey": event_key})


def _normalize_guess(raw, event_key: str = ""):
    if not raw:
        return None
    guess = str(raw).strip().upper()
    pattern = re.compile(r"^[A-Z0-9]+$") if event_key == "forsaken" else re.compile(r"^[A-Z]+$")
    if not pattern.match(guess):
        return None
    if len(guess) != WORD_LENGTH:
        return None
    return guess


def _evaluate_guess(solution: str, guess: str) -> list:
    feedback = []
    sol_chars = list(solution)
    gue_chars = list(guess)
    sol_used = [False] * WORD_LENGTH

    for i in range(WORD_LENGTH):
        if gue_chars[i] == sol_chars[i]:
            feedback.append({"letter": gue_chars[i], "result": "correct"})
            sol_used[i] = True
        else:
            feedback.append({"letter": gue_chars[i], "result": "absent"})

    for i in range(WORD_LENGTH):
        if feedback[i]["result"] == "correct":
            continue
        letter = gue_chars[i]
        found = -1
        for j in range(WORD_LENGTH):
            if not sol_used[j] and sol_chars[j] == letter:
                found = j
                break
        if found != -1:
            feedback[i]["result"] = "present"
            sol_used[found] = True

    return feedback


def _feedback_to_emoji(feedback: list) -> str:
    return "".join(
        "🟩" if f["result"] == "correct" else "🟨" if f["result"] == "present" else "⬜"
        for f in feedback
    )


def _get_solved_positions(game: dict) -> set:
    solved = set()
    for guess in game["guesses"]:
        for i, f in enumerate(_evaluate_guess(game["solution"], guess)):
            if f["result"] == "correct":
                solved.add(i)
    return solved


def _get_hint_mask(game: dict):
    positions = game.get("hintPositions") or []
    if not positions and isinstance(game.get("hintPosition"), int):
        positions = [game["hintPosition"]]
    if not positions:
        return None
    revealed = set(positions)
    return "".join(
        letter if i in revealed else "_"
        for i, letter in enumerate(game["solution"])
    )


def render_board(game: dict) -> str:
    rows = []
    for guess in game["guesses"]:
        fb = _evaluate_guess(game["solution"], guess)
        rows.append(f"{guess}  {_feedback_to_emoji(fb)}")
    hint_mask = _get_hint_mask(game)
    for _ in range(get_hint_penalty_count(game)):
        rows.append(f"HINT!  {hint_mask or '💡 💡'}")
    for _ in range(get_effective_guess_count(game, MAX_GUESSES), MAX_GUESSES):
        rows.append("_____  ⬛⬛⬛⬛⬛")
    return "\n".join(rows)


_CSS = (
    "<style>"
    ".wb{background:#121213;padding:12px;border-radius:8px;display:inline-block}"
    ".wr{display:flex;gap:5px;margin-bottom:5px}"
    ".wt{display:inline-flex;align-items:center;justify-content:center;"
    "width:46px;height:46px;border-radius:4px;font-size:18px;font-weight:700;"
    "color:#fff;font-family:monospace}"
    ".c{background:#538d4e;border:2px solid #538d4e}"
    ".p{background:#b59f3b;border:2px solid #b59f3b}"
    ".a{background:#3a3a3c;border:2px solid #3a3a3c}"
    ".e{background:#121213;border:2px solid #3a3a3c}"
    ".h{background:#1a6b8a;border:2px solid #1a6b8a}"
    "</style>"
)
_STATE_CLASS = {"correct": "c", "present": "p", "absent": "a", "empty": "e", "hint": "h"}

def _tile(letter: str, state: str) -> str:
    return f'<div class="wt {_STATE_CLASS.get(state, "e")}">{letter}</div>'


def render_board_html(game: dict, title: str = "", footer: str = "", credits: str = "") -> str:
    row_style = 'style="display:flex;gap:5px;margin-bottom:5px"'
    rows_html = []

    for guess in game["guesses"]:
        fb = _evaluate_guess(game["solution"], guess)
        tiles = "".join(_tile(fb[i]["letter"], fb[i]["result"]) for i in range(WORD_LENGTH))
        rows_html.append(f'<div {row_style}>{tiles}</div>')

    hint_mask = _get_hint_mask(game)
    for _ in range(get_hint_penalty_count(game)):
        letters = list(hint_mask) if hint_mask and hint_mask != "💡 💡" else ["?"] * WORD_LENGTH
        tiles = "".join(_tile(letters[i] if i < len(letters) else "?", "hint") for i in range(WORD_LENGTH))
        rows_html.append(f'<div {row_style}>{tiles}</div>')

    for _ in range(get_effective_guess_count(game, MAX_GUESSES), MAX_GUESSES):
        tiles = "".join(_tile("", "empty") for _ in range(WORD_LENGTH))
        rows_html.append(f'<div {row_style}>{tiles}</div>')

    title_html = f'<div style="font-weight:700;font-size:15px;margin-bottom:8px;color:#cdd6f4">{title}</div>' if title else ""
    footer_html = f'<div style="margin-top:10px;font-size:13px;color:#a6adc8">{footer}</div>' if footer else ""
    credits_html = f'<div style="margin-top:6px;font-size:11px;color:#6c7086">Credits: {credits}</div>' if credits else ""
    return (
        f'{_CSS}<div style="display:flex;flex-direction:column;align-items:center">'
        f'<div class="wb">'
        f'{title_html}{"".join(rows_html)}{footer_html}{credits_html}'
        f'</div></div>'
    )


def _get_share_headline(game: dict) -> str:
    used = get_effective_guess_count(game, MAX_GUESSES)
    if game["status"] == "won":
        score = f"{used}/{MAX_GUESSES}"
    elif game["status"] == "lost":
        score = f"X/{MAX_GUESSES}"
    else:
        score = f"{used}/{MAX_GUESSES}*"
    label = f"Wordle {game['dateKey']} ({game['eventKey']})" if game.get("eventKey") else f"Wordle {game['dateKey']}"
    return f"{label} {score}"


def render_share_grid(game: dict) -> str:
    rows = [_feedback_to_emoji(_evaluate_guess(game["solution"], g)) for g in game["guesses"]]
    for _ in range(get_hint_penalty_count(game)):
        rows.append("💡💡💡💡💡")
    if not rows:
        rows.append("⬛⬛⬛⬛⬛")
    return "\n".join([_get_share_headline(game), ""] + rows)


def give_up_game(user_id: str, user_label: str = None) -> dict:
    current = _current_by_user.get(user_id)
    game = (start_or_get_game(user_id, {"dateKey": current["dateKey"], "eventKey": current["eventKey"]})
            if current else start_or_get_game(user_id))

    if game["status"] != "in_progress":
        return {"game": game, "error": f"Your game for {game['dateKey']} is already {game['status']}."}

    game["status"] = "lost"
    game["displayName"] = user_label or game.get("displayName") or user_id
    game["updatedAt"] = datetime.now(timezone.utc).isoformat()

    record_result(user_id=user_id, run_id=game["runId"],
                  display_name=game["displayName"], date_key=game["dateKey"],
                  event_key=game["eventKey"], status="lost",
                  guesses=MAX_GUESSES, hard_mode=game.get("hardMode", False))
    _persist()
    return {"game": game, "error": None}


def make_guess(user_id: str, guess_raw, user_label: str = None) -> dict:
    current = _current_by_user.get(user_id)
    game = (start_or_get_game(user_id, {"dateKey": current["dateKey"], "eventKey": current["eventKey"]})
            if current else start_or_get_game(user_id))

    if game["status"] != "in_progress":
        return {"game": game, "error": f"Your game for {game['dateKey']} is already {game['status']}. Come back tomorrow!"}

    guess = _normalize_guess(guess_raw, game.get("eventKey", ""))
    if not guess:
        example = "/answer 007N7" if game.get("eventKey") == "forsaken" else "/answer CRANE"
        return {"game": game, "error": f"Guesses must be exactly {WORD_LENGTH} characters. Example: {example}"}

    if game.get("hardMode") and game["guesses"]:
        for prev in game["guesses"]:
            fb = _evaluate_guess(game["solution"], prev)
            for i in range(WORD_LENGTH):
                if fb[i]["result"] == "correct" and guess[i] != prev[i]:
                    return {"game": game, "error": f"🔒 Hard mode: position {i+1} must be **{prev[i]}**."}
            for i in range(WORD_LENGTH):
                if fb[i]["result"] == "present" and prev[i] not in guess:
                    return {"game": game, "error": f"🔒 Hard mode: guess must contain **{prev[i]}**."}

    if get_effective_guess_count(game, MAX_GUESSES) >= MAX_GUESSES:
        game["status"] = "lost"
        _persist()
        return {"game": game, "error": f"You've already used all {MAX_GUESSES} guesses. The word was **{game['solution']}**."}

    game["guesses"].append(guess)
    game["displayName"] = user_label or game.get("displayName") or user_id
    game["updatedAt"] = datetime.now(timezone.utc).isoformat()
    feedback = _evaluate_guess(game["solution"], guess)

    if guess == game["solution"]:
        game["status"] = "won"
    elif get_effective_guess_count(game, MAX_GUESSES) >= MAX_GUESSES:
        game["status"] = "lost"

    if game["status"] in ("won", "lost"):
        record_result(user_id=user_id, run_id=game["runId"],
                      display_name=user_label, date_key=game["dateKey"],
                      event_key=game["eventKey"], status=game["status"],
                      guesses=get_effective_guess_count(game, MAX_GUESSES),
                      hard_mode=game.get("hardMode", False))
    _persist()
    return {"game": game, "feedback": feedback, "error": None}


def use_hint(user_id: str, user_label: str = None) -> dict:
    current = _current_by_user.get(user_id)
    game = (start_or_get_game(user_id, {"dateKey": current["dateKey"], "eventKey": current["eventKey"]})
            if current else start_or_get_game(user_id))

    if game["status"] != "in_progress":
        return {"game": game, "error": f"Your game for {game['dateKey']} is already {game['status']}."}
    if game.get("hardMode"):
        return {"game": game, "error": "🔒 Hard mode: `/hint` is not available."}
    if game.get("hintUsed"):
        return {"game": game, "error": "You already used your hint for this run."}
    if len(game["guesses"]) < MIN_GUESSES_BEFORE_HINT:
        return {"game": game, "error": f"You need at least {MIN_GUESSES_BEFORE_HINT} guesses before using /hint."}

    remaining = MAX_GUESSES - get_effective_guess_count(game, MAX_GUESSES)
    if remaining <= HINT_PENALTY:
        return {"game": game, "error": f"You need more than {HINT_PENALTY} guesses left to use /hint."}

    solved = _get_solved_positions(game)
    hinted_letters = []
    hinted_positions = []
    used_letters: set = set()

    for i in range(WORD_LENGTH):
        if len(hinted_letters) >= 2:
            break
        if i in solved:
            continue
        letter = game["solution"][i]
        if letter in used_letters:
            continue
        hinted_letters.append(letter)
        hinted_positions.append(i)
        used_letters.add(letter)

    for i in range(WORD_LENGTH):
        if len(hinted_letters) >= 2:
            break
        letter = game["solution"][i]
        if letter not in used_letters:
            hinted_letters.append(letter)
            hinted_positions.append(i)
            used_letters.add(letter)

    game["hintUsed"] = True
    game["hintPenalty"] = HINT_PENALTY
    game["hintLetters"] = hinted_letters[:2]
    game["hintPositions"] = hinted_positions[:2]
    game["hintPosition"] = hinted_positions[0] if hinted_positions else 0
    game["displayName"] = user_label or game.get("displayName") or user_id
    game["updatedAt"] = datetime.now(timezone.utc).isoformat()
    _persist()

    return {
        "game": game,
        "hint": {
            "letters": game["hintLetters"],
            "positions": game["hintPositions"],
            "remainingGuesses": MAX_GUESSES - get_effective_guess_count(game, MAX_GUESSES),
        },
        "error": None,
    }


def start_hard_mode(user_id: str, force_date_key: str = None) -> dict:
    if force_date_key:
        _current_by_user[user_id] = {"dateKey": force_date_key, "eventKey": "", "runId": 0}
        _persist()
        game = start_or_get_game(user_id, {"dateKey": force_date_key, "eventKey": ""})
    else:
        game = start_or_get_game(user_id)

    if game["guesses"]:
        return {"game": game, "error": "🔒 You can only enable hard mode before making any guesses."}
    if game.get("hardMode"):
        return {"game": game, "error": "You're already in hard mode!"}
    game["hardMode"] = True
    _persist()
    return {"game": game, "error": None}
