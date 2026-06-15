import json
import os

FILE = os.path.join(os.path.dirname(__file__), "..", "data", "debugCommands.json")


def _load() -> set:
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def _save(s: set) -> None:
    os.makedirs(os.path.dirname(FILE), exist_ok=True)
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(list(s), f)


def lock_command(name: str) -> None:
    s = _load()
    s.add(name.lower())
    _save(s)


def unlock_command(name: str) -> None:
    s = _load()
    s.discard(name.lower())
    _save(s)


def is_locked(name: str) -> bool:
    return name.lower() in _load()
