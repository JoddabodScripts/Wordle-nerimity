import json
import os
import re

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
STORE_PATH = os.path.join(DATA_DIR, "leaderboard-messages.json")


def _mkdirp(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _normalize(event_key: str) -> str:
    if not event_key:
        return ""
    return re.sub(r"[^a-z0-9_-]", "", str(event_key).lower())


def _store_key(date_key: str, event_key: str = "") -> str:
    norm = _normalize(event_key)
    return f"{date_key}:{norm}" if norm else date_key


def _load() -> dict:
    _mkdirp(DATA_DIR)
    try:
        with open(STORE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(store: dict) -> None:
    _mkdirp(DATA_DIR)
    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2)


def add_leaderboard_message(*, date_key: str, event_key: str = "", channel_id: str, message_id: str) -> None:
    if not date_key or not channel_id or not message_id:
        return
    store = _load()
    key = _store_key(date_key, event_key)
    arr = [x for x in store.get(key, []) if x and x.get("channelId") and x.get("messageId")]
    if not any(x["channelId"] == channel_id and x["messageId"] == message_id for x in arr):
        arr.append({"channelId": channel_id, "messageId": message_id})
    store[key] = arr
    _save(store)


def list_leaderboard_messages(date_key: str, event_key: str = "") -> list:
    store = _load()
    arr = store.get(_store_key(date_key, event_key), [])
    return [x for x in arr if x and x.get("channelId") and x.get("messageId")]


def prune_leaderboard_messages(date_key: str, event_key: str, predicate) -> None:
    store = _load()
    key = _store_key(date_key, event_key)
    arr = store.get(key, [])
    store[key] = [x for x in arr if not predicate(x)]
    _save(store)
