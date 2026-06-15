"""In-memory duel state. Duels are ephemeral — not persisted across restarts."""
import asyncio
import time
from typing import Optional

DUEL_TIMEOUT = 300  # seconds per turn

_duels: dict[str, dict] = {}  # duel_id -> duel


def _duel_id(user1: str, user2: str) -> str:
    return ":".join(sorted([user1, user2]))


def get_duel_for_user(user_id: str) -> Optional[dict]:
    for d in _duels.values():
        if user_id in (d["player1"], d["player2"]) and d["status"] == "active":
            return d
    return None


def create_duel(challenger: str, opponent: str, word: str) -> dict:
    duel_id = _duel_id(challenger, opponent)
    duel = {
        "id": duel_id,
        "player1": challenger,
        "player2": opponent,
        "word": word,
        "turn": challenger,  # challenger goes first
        "boards": {challenger: [], opponent: []},
        "status": "active",
        "created_at": time.time(),
        "turn_started_at": time.time(),
        "timeout_task": None,
    }
    _duels[duel_id] = duel
    return duel


def get_duel(duel_id: str) -> Optional[dict]:
    return _duels.get(duel_id)


def end_duel(duel_id: str):
    d = _duels.pop(duel_id, None)
    if d and d.get("timeout_task"):
        d["timeout_task"].cancel()


def next_turn(duel: dict):
    p1, p2 = duel["player1"], duel["player2"]
    duel["turn"] = p2 if duel["turn"] == p1 else p1
    duel["turn_started_at"] = time.time()
    if duel.get("timeout_task"):
        duel["timeout_task"].cancel()
