import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
STATE_PATH = os.path.join(DATA_DIR, "game-state.json")


def _mkdirp(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def load_game_state() -> dict:
    _mkdirp(DATA_DIR)
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            parsed = json.load(f)
        if not isinstance(parsed, dict):
            return {"games": {}, "currentStateByUser": {}}
        parsed.setdefault("games", {})
        parsed.setdefault("currentStateByUser", {})
        return parsed
    except Exception:
        return {"games": {}, "currentStateByUser": {}}


def save_game_state(games: dict, current_state_by_user: dict) -> None:
    _mkdirp(DATA_DIR)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump({"games": games or {}, "currentStateByUser": current_state_by_user or {}}, f, indent=2)
