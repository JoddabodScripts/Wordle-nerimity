"""Simple in-process event emitter for leaderboard update notifications."""
from typing import Callable

_listeners: list[Callable] = []


def on_updated(fn: Callable) -> None:
    _listeners.append(fn)


def emit_updated(date_key: str, event_key: str) -> None:
    for fn in _listeners:
        try:
            fn(date_key, event_key)
        except Exception:
            pass
