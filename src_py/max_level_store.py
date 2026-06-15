import json
import os

FILE = os.path.join(os.path.dirname(__file__), "..", "data", "maxLevelNotified.json")


def _load() -> set:
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def has_been_notified(user_id: str) -> bool:
    return str(user_id) in _load()


def mark_notified(user_id: str) -> None:
    s = _load()
    s.add(str(user_id))
    os.makedirs(os.path.dirname(FILE), exist_ok=True)
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(list(s), f)
