import json
import os

FILE = os.path.join(os.path.dirname(__file__), "..", "data", "dmChannel.json")


def get_dm_channel_id():
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("channelId") or None
    except Exception:
        return None


def set_dm_channel_id(channel_id: str) -> None:
    os.makedirs(os.path.dirname(FILE), exist_ok=True)
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump({"channelId": channel_id}, f)
