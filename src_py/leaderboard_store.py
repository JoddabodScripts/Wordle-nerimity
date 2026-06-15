import json
import os
import re
from datetime import datetime, timezone, timedelta

import leaderboard_notifier
from game_state_store import load_game_state
from game_scoring import get_effective_guess_count

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
_LEADERBOARD_FILE_RE = re.compile(r"^leaderboard-(\d{4}-\d{2}-\d{2})(?:-([a-z0-9_-]+))?\.json$")
_RETENTION_DAYS = max(1, int(os.environ.get("LEADERBOARD_RETENTION_DAYS", "14")))
_last_cleanup_date_key = ""


def _mkdirp(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def normalize_event_key(event_key: str) -> str:
    if not event_key:
        return ""
    return re.sub(r"[^a-z0-9_-]", "", str(event_key).lower())


def get_today_key(dt: datetime = None) -> str:
    if dt is None:
        dt = datetime.now(timezone.utc)
    return f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}"


def _leaderboard_path(date_key: str, event_key: str = "") -> str:
    norm = normalize_event_key(event_key)
    if norm:
        return os.path.join(DATA_DIR, f"leaderboard-{date_key}-{norm}.json")
    return os.path.join(DATA_DIR, f"leaderboard-{date_key}.json")


def _create_empty(date_key: str, event_key: str = "") -> dict:
    return {"dateKey": date_key, "eventKey": normalize_event_key(event_key), "results": {}}


def _date_key_days_ago(days: int, base: datetime = None) -> str:
    if base is None:
        base = datetime.now(timezone.utc)
    d = base - timedelta(days=days)
    return f"{d.year:04d}-{d.month:02d}-{d.day:02d}"


def cleanup_old_leaderboard_files(now: datetime = None) -> None:
    global _last_cleanup_date_key
    _mkdirp(DATA_DIR)
    today = get_today_key(now)
    if _last_cleanup_date_key == today:
        return
    _last_cleanup_date_key = today
    cutoff = _date_key_days_ago(_RETENTION_DAYS, now)
    try:
        names = os.listdir(DATA_DIR)
    except OSError:
        return
    for name in names:
        m = _LEADERBOARD_FILE_RE.match(name)
        if not m:
            continue
        if m.group(1) < cutoff:
            try:
                os.unlink(os.path.join(DATA_DIR, name))
            except OSError:
                pass


def _build_from_game_state(date_key: str, event_key: str = "") -> dict:
    norm = normalize_event_key(event_key)
    state = load_game_state()
    data = _create_empty(date_key, norm)
    legacy: dict = {}
    try:
        with open(_leaderboard_path(date_key, ""), "r", encoding="utf-8") as f:
            parsed = json.load(f)
        if isinstance(parsed, dict) and isinstance(parsed.get("results"), dict):
            legacy = parsed["results"]
    except Exception:
        pass

    for game_key, game in (state.get("games") or {}).items():
        if not game or game.get("dateKey") != date_key:
            continue
        if normalize_event_key(game.get("eventKey", "")) != norm:
            continue
        if game.get("status") not in ("won", "lost"):
            continue
        user_id = str(game_key).split(":")[0]
        run_id = int(game.get("runId") or 0)
        result_key = f"{user_id}:{run_id}"
        leg = legacy.get(result_key) or {}
        data["results"][result_key] = {
            "userId": user_id,
            "runId": run_id,
            "displayName": leg.get("displayName") or game.get("displayName") or user_id,
            "status": game["status"],
            "guesses": get_effective_guess_count(game, 6),
            "updatedAt": leg.get("updatedAt") or game.get("updatedAt") or datetime.now(timezone.utc).isoformat(),
        }
    return data


def _load_leaderboard(date_key: str, event_key: str = "") -> dict:
    cleanup_old_leaderboard_files()
    _mkdirp(DATA_DIR)
    norm = normalize_event_key(event_key)
    path = _leaderboard_path(date_key, norm)
    try:
        with open(path, "r", encoding="utf-8") as f:
            parsed = json.load(f)
        if not isinstance(parsed, dict):
            return _create_empty(date_key, norm)
        parsed.setdefault("results", {})
        parsed["dateKey"] = date_key
        parsed["eventKey"] = norm
        return parsed
    except Exception:
        if norm:
            migrated = _build_from_game_state(date_key, norm)
            if migrated["results"]:
                _save_leaderboard(date_key, norm, migrated)
                return migrated
        return _create_empty(date_key, norm)


def _save_leaderboard(date_key: str, event_key: str, data: dict) -> None:
    cleanup_old_leaderboard_files()
    _mkdirp(DATA_DIR)
    with open(_leaderboard_path(date_key, event_key), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def record_result(*, user_id: str, run_id: int = 0, display_name: str = None,
                  date_key: str, event_key: str = "", status: str,
                  guesses: int, hard_mode: bool = False) -> None:
    if not user_id or not date_key:
        return
    if status not in ("won", "lost"):
        return
    if not isinstance(guesses, (int, float)) or guesses < 1:
        return

    norm = normalize_event_key(event_key)
    data = _load_leaderboard(date_key, norm)
    result_key = f"{user_id}:{run_id}"
    prev = data["results"].get(result_key)

    def _is_better(a: dict, b: dict | None) -> bool:
        if b is None:
            return True
        if a["status"] == "won" and b["status"] != "won":
            return True
        if a["status"] != "won" and b["status"] == "won":
            return False
        if a["status"] == "won" and b["status"] == "won":
            return a["guesses"] < b["guesses"]
        return False

    next_entry = {
        "userId": user_id,
        "runId": run_id,
        "displayName": display_name or (prev or {}).get("displayName") or user_id,
        "status": status,
        "guesses": guesses,
        "hardMode": hard_mode,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }

    if _is_better(next_entry, prev):
        data["results"][result_key] = next_entry
    elif prev and next_entry["displayName"] != prev.get("displayName"):
        data["results"][result_key] = {**prev, "displayName": next_entry["displayName"], "updatedAt": next_entry["updatedAt"]}

    _save_leaderboard(date_key, norm, data)
    leaderboard_notifier.emit_updated(date_key, norm)


def get_leaderboard_for_date(date_key: str, event_key: str = "") -> list:
    data = _load_leaderboard(date_key, event_key)
    entries = list(data.get("results", {}).values())

    def _score(r: dict) -> int:
        return r["guesses"] if r["status"] == "won" else 999

    entries.sort(key=lambda r: (_score(r), str(r.get("displayName") or r.get("userId") or ""), int(r.get("runId") or 0)))
    return entries
