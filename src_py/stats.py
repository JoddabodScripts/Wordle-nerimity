import json
import os
import re
from datetime import datetime, timezone, timedelta

from game_state_store import load_game_state
from game_scoring import get_effective_guess_count

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
_LB_FILE_RE = re.compile(r"^leaderboard-(\d{4}-\d{2}-\d{2})(?:-([a-z0-9_-]+))?\.json$")

LEVEL_NAMES = [
    "Newcomer","Dabbler","Curious","Learner","Guesser",
    "Thinker","Solver","Speller","Wordsmith","Lexicon",
    "Scholar","Linguist","Scrabbler","Puzzler","Riddler",
    "Sharpie","Ace","Veteran","Expert","Tactician",
    "Strategist","Analyst","Cipher","Codebreaker","Sleuth",
    "Detective","Inspector","Investigator","Profiler","Mastermind",
    "Prodigy","Savant","Genius","Polymath","Sage",
    "Oracle","Seer","Prophet","Mystic","Arcane",
    "Enigma","Phantom","Shadow","Specter","Wraith",
    "Revenant","Legend","Myth","Fable","Icon",
    "Titan","Colossus","Juggernaut","Behemoth","Leviathan",
    "Overlord","Sovereign","Emperor","Supreme","Immortal",
    "Eternal","Infinite","Cosmic","Celestial","Astral",
    "Stellar","Galactic","Universal","Omniscient","Transcendent",
    "Ascendant","Divine","Godlike","Mythic","Ancient",
    "Primordial","Archon","Arbiter","Paragon","Pinnacle",
    "Apex","Zenith","Summit","Absolute","Ultimate",
    "Paramount","Unrivaled","Peerless","Matchless","Flawless",
    "Boundless","Limitless","Endless","Timeless","Ageless",
    "Wordless","Speechless","Breathless","Formless","No Life",
]
MAX_LEVEL = 100


def _norm(event_key: str) -> str:
    if not event_key:
        return ""
    return re.sub(r"[^a-z0-9_-]", "", str(event_key).lower())


def get_mode_title(event_key: str = "") -> str:
    from events import EVENTS
    n = _norm(event_key)
    if not n:
        return "Daily"
    ev = next((e for e in EVENTS if e["key"] == n), None)
    return ev["title"] if ev else n


def _xp_for_level(n: int) -> int:
    return 8 + (n - 1) // 10


def _total_xp_for_level(n: int) -> int:
    return sum(_xp_for_level(i) for i in range(1, n + 1))


def _level_from_xp(xp: int) -> int:
    level = 1
    while level < MAX_LEVEL and xp >= _total_xp_for_level(level + 1):
        level += 1
    return level


def get_level(xp: int) -> dict:
    level = _level_from_xp(xp)
    is_max = level >= MAX_LEVEL
    tier = "No Life" if is_max else LEVEL_NAMES[(level // 5) * 5]
    base_xp = _total_xp_for_level(level)
    xp_into = 0 if is_max else xp - base_xp
    xp_needed = 0 if is_max else _total_xp_for_level(level + 1) - base_xp
    return {"level": level, "tier": tier, "xp": xp,
            "xpIntoLevel": xp_into, "xpNeeded": xp_needed, "isMax": is_max}


def compute_xp(results: list, comeback_bonus_active: bool = False) -> int:
    if not results:
        return 0
    running = 0
    prev_date = None
    total = 0.0
    for i, r in enumerate(results):
        base = 10 if r["status"] == "won" else 5
        hard = 2 if r.get("hardMode") else 1
        if r["status"] == "won":
            running = running + 1 if prev_date else 1
        else:
            running = 0
        prev_date = r["dateKey"]
        mult = 1 + max(0, running - 1) * 0.1
        cb = 2 if (i == len(results) - 1 and comeback_bonus_active) else 1
        total += base * hard * mult * cb
    return int(total)


def _load_backfill(user_id: str) -> list:
    results = []
    try:
        names = os.listdir(DATA_DIR)
    except OSError:
        return results
    for name in names:
        m = _LB_FILE_RE.match(name)
        if not m:
            continue
        date_key = m.group(1)
        event_key = _norm(m.group(2) or "")
        try:
            with open(os.path.join(DATA_DIR, name), "r", encoding="utf-8") as f:
                parsed = json.load(f)
            for entry in (parsed.get("results") or {}).values():
                if not entry or str(entry.get("userId")) != str(user_id):
                    continue
                if entry.get("status") not in ("won", "lost"):
                    continue
                results.append({
                    "userId": str(user_id),
                    "dateKey": parsed.get("dateKey") or date_key,
                    "eventKey": _norm(parsed.get("eventKey") or event_key),
                    "runId": int(entry.get("runId") or 0),
                    "status": entry["status"],
                    "guesses": int(entry.get("guesses") or 0) if entry["status"] == "won" else 6,
                    "hardMode": bool(entry.get("hardMode")),
                    "displayName": entry.get("displayName") or str(user_id),
                })
        except Exception:
            pass
    return results


def get_completed_puzzle_results_for_user(user_id: str) -> list:
    state = load_game_state()
    by_puzzle: dict = {}
    all_results = []

    for game_key, game in (state.get("games") or {}).items():
        if not game or game.get("status") not in ("won", "lost"):
            continue
        if str(game_key).split(":")[0] != str(user_id):
            continue
        ek = _norm(game.get("eventKey", ""))
        run_id = int(game.get("runId") or 0)
        all_results.append({
            "userId": str(user_id),
            "dateKey": game["dateKey"],
            "eventKey": ek,
            "runId": run_id,
            "status": game["status"],
            "guesses": get_effective_guess_count(game, 6) if game["status"] == "won" else 6,
            "hardMode": bool(game.get("hardMode")),
            "displayName": game.get("displayName") or str(user_id),
        })

    all_results.extend(_load_backfill(user_id))

    for r in all_results:
        pk = f"{r['dateKey']}:{r['eventKey']}"
        prev = by_puzzle.get(pk)
        if prev is None:
            by_puzzle[pk] = r
            continue
        # prefer won over lost, then fewer guesses, then lower runId
        def _better(a, b):
            if a["status"] == "won" and b["status"] != "won":
                return True
            if a["status"] != "won" and b["status"] == "won":
                return False
            if a["status"] == "won" and a["guesses"] != b["guesses"]:
                return a["guesses"] < b["guesses"]
            return int(a.get("runId", 0)) < int(b.get("runId", 0))
        if _better(r, prev):
            by_puzzle[pk] = r

    return sorted(by_puzzle.values(),
                  key=lambda r: (r["dateKey"], r["eventKey"], r["runId"]))


def _expected_prev_date_key(date_key: str, event_key: str = ""):
    from events import EVENTS
    n = _norm(event_key)
    if n:
        ev = next((e for e in EVENTS if e["key"] == n), None)
        if not ev or not ev.get("fixed"):
            return None
        year = int(date_key[:4])
        return f"{year-1:04d}-{ev['fixed']['month']:02d}-{ev['fixed']['day']:02d}"
    parts = date_key.split("-")
    dt = datetime(int(parts[0]), int(parts[1]), int(parts[2]), tzinfo=timezone.utc)
    prev = dt - timedelta(days=1)
    return f"{prev.year:04d}-{prev.month:02d}-{prev.day:02d}"


def _streak_stats(user_id: str, event_key: str = "") -> dict:
    n = _norm(event_key)
    results = [r for r in get_completed_puzzle_results_for_user(user_id) if r["eventKey"] == n]
    if not results:
        return {"currentStreak": 0, "bestStreak": 0}

    by_date = {r["dateKey"]: r for r in results}
    best = running = 0
    prev = None

    for r in results:
        if r["status"] != "won":
            running = 0
            prev = r
            continue
        exp = _expected_prev_date_key(r["dateKey"], r["eventKey"])
        running = (running + 1) if (prev and prev["status"] == "won" and prev["dateKey"] == exp) else 1
        best = max(best, running)
        prev = r

    latest = results[-1]
    current = 0
    if latest["status"] == "won":
        current = 1
        pk = _expected_prev_date_key(latest["dateKey"], latest["eventKey"])
        while pk:
            p = by_date.get(pk)
            if not p or p["status"] != "won":
                break
            current += 1
            pk = _expected_prev_date_key(p["dateKey"], p["eventKey"])

    return {"currentStreak": current, "bestStreak": best}


def get_current_streak(user_id: str, event_key: str = "") -> int:
    return _streak_stats(user_id, event_key)["currentStreak"]


def _best_mode(results: list):
    grouped: dict = {}
    for r in results:
        k = r["eventKey"]
        e = grouped.setdefault(k, {"eventKey": k, "title": get_mode_title(k), "wins": 0, "total": 0})
        if r["status"] == "won":
            e["wins"] += 1
            e["total"] += r["guesses"]
    best = None
    for e in grouped.values():
        if not e["wins"]:
            continue
        avg = e["total"] / e["wins"]
        c = {"eventKey": e["eventKey"], "title": e["title"], "avgGuesses": avg, "wins": e["wins"]}
        if best is None or avg < best["avgGuesses"] or (avg == best["avgGuesses"] and c["wins"] > best["wins"]):
            best = c
    return best


def get_user_stats(user_id: str, streak_event_key: str = "",
                   comeback_bonus_active: bool = False) -> dict:
    results = get_completed_puzzle_results_for_user(user_id)
    wins = [r for r in results if r["status"] == "won"]
    hard_wins = sum(1 for r in wins if r.get("hardMode"))
    total_fails = sum(1 for r in results if r["status"] == "lost")
    avg = sum(r["guesses"] for r in wins) / len(wins) if wins else None
    streaks = _streak_stats(user_id, streak_event_key)
    xp = compute_xp(results, comeback_bonus_active)
    return {
        "gamesPlayed": len(results),
        "wins": len(wins),
        "hardWins": hard_wins,
        "winRate": (len(wins) / len(results) * 100) if results else 0,
        "averageGuesses": avg,
        "currentStreak": streaks["currentStreak"],
        "bestStreak": streaks["bestStreak"],
        "totalFails": total_fails,
        "bestMode": _best_mode(results),
        "streakModeTitle": get_mode_title(streak_event_key),
        "xp": xp,
    }


def _known_users() -> list:
    users: dict = {}
    state = load_game_state()
    for gk, game in (state.get("games") or {}).items():
        if not game:
            continue
        uid = str(gk).split(":")[0]
        if uid:
            prev = users.get(uid, {})
            users[uid] = {"userId": uid, "displayName": game.get("displayName") or prev.get("displayName") or uid}
    try:
        for name in os.listdir(DATA_DIR):
            if not _LB_FILE_RE.match(name):
                continue
            with open(os.path.join(DATA_DIR, name), "r", encoding="utf-8") as f:
                parsed = json.load(f)
            for entry in (parsed.get("results") or {}).values():
                if not entry or not entry.get("userId"):
                    continue
                uid = str(entry["userId"])
                prev = users.get(uid, {})
                users[uid] = {"userId": uid, "displayName": entry.get("displayName") or prev.get("displayName") or uid}
    except Exception:
        pass
    return list(users.values())


def get_all_time_leaderboard_entries() -> list:
    entries = []
    for user in _known_users():
        stats = get_user_stats(user["userId"], "")
        if not stats["gamesPlayed"]:
            continue
        avg = stats["averageGuesses"]
        entries.append({
            "userId": user["userId"],
            "displayName": user.get("displayName") or user["userId"],
            "gamesPlayed": stats["gamesPlayed"],
            "wins": stats["wins"],
            "hardWins": stats["hardWins"],
            "winRate": stats["winRate"],
            "averageGuesses": avg,
            "currentStreak": stats["currentStreak"],
            "bestStreak": stats["bestStreak"],
            "totalFails": stats["totalFails"],
            "xp": stats["xp"],
        })
    entries.sort(key=lambda e: (
        -e["wins"], -e["bestStreak"],
        e["averageGuesses"] if e["averageGuesses"] is not None else float("inf"),
        -e["winRate"], e["displayName"]
    ))
    return entries
