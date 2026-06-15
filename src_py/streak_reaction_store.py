import json
import os

FILE = os.path.join(os.path.dirname(__file__), "..", "data", "streakReactions.json")
_DEFAULT = {"one": 0, "six": 0, "fail": 0, "hard_one": 0, "hard_six": 0, "hard_win": 0, "hard_fail": 0}


def _load() -> dict:
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict) -> None:
    os.makedirs(os.path.dirname(FILE), exist_ok=True)
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def record_reaction_result(user_id: str, guesses: int, max_guesses: int,
                           status: str, hard_mode: bool = False) -> dict:
    data = _load()
    rtype = None
    if hard_mode:
        if status == "lost":
            rtype = "hard_fail"
        elif guesses == 1:
            rtype = "hard_one"
        elif guesses == max_guesses:
            rtype = "hard_six"
        else:
            rtype = "hard_win"
    else:
        if status == "lost":
            rtype = "fail"
        elif guesses == 1:
            rtype = "one"
        elif guesses == max_guesses:
            rtype = "six"

    new_state = {**_DEFAULT}
    if rtype:
        new_state[rtype] = (data.get(user_id) or {}).get(rtype, 0) + 1

    data[user_id] = new_state
    _save(data)
    return {"type": rtype, "streak": new_state.get(rtype, 0) if rtype else 0}
