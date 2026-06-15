import json
import os

FILE = os.path.join(os.path.dirname(__file__), "..", "data", "forsakenDate.json")


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


def get_forsaken_date_key():
    return _load().get("dateKey") or None


def set_forsaken_date_key(date_key: str) -> None:
    _save({"dateKey": date_key})
