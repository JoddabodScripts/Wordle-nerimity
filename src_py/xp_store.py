import json
import os
from datetime import datetime, timezone

FILE = os.path.join(os.path.dirname(__file__), "..", "data", "xpState.json")
COMEBACK_ABSENT_DAYS = 7
COMEBACK_COOLDOWN_DAYS = 30


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


def _days_between(date_key_a: str, date_key_b: str) -> int:
    a = datetime.fromisoformat(date_key_a).replace(tzinfo=timezone.utc)
    b = datetime.fromisoformat(date_key_b).replace(tzinfo=timezone.utc)
    return round((b - a).total_seconds() / 86400)


def check_and_apply_comeback_bonus(user_id: str, last_played: str, today_key: str) -> bool:
    if not last_played or last_played >= today_key:
        return False
    data = _load()
    state = data.get(user_id) or {}
    if _days_between(last_played, today_key) < COMEBACK_ABSENT_DAYS:
        return False
    last_comeback = state.get("lastComebackDateKey")
    if last_comeback and _days_between(last_comeback, today_key) < COMEBACK_COOLDOWN_DAYS:
        return False
    data[user_id] = {**state, "lastComebackDateKey": today_key}
    _save(data)
    return True
