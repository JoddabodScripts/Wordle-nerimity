import asyncio
import json
import os
import re
from datetime import datetime, timezone, timedelta

import aiohttp

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CACHE_PATH = os.path.join(DATA_DIR, "genshin-countdown.json")
SOURCE_URL = "https://genshin-countdown.gengamer.in/"
REFRESH_INTERVAL_SECS = 6 * 60 * 60

_cache: dict = {}
_inflight = None


def _mkdirp(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _load_cache() -> dict:
    _mkdirp(DATA_DIR)
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            parsed = json.load(f)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _save_cache(data: dict) -> None:
    global _cache
    _cache = data
    _mkdirp(DATA_DIR)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _parse_date_key(dt: datetime) -> str:
    return f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}"


def _subtract_utc_days(date_key: str, days: int) -> str:
    parts = date_key.split("-")
    dt = datetime(int(parts[0]), int(parts[1]), int(parts[2]), tzinfo=timezone.utc)
    dt -= timedelta(days=days)
    return _parse_date_key(dt)


def _parse_release_date_from_html(html: str):
    m = re.search(r"set to release on ([A-Za-z]+ \d{1,2}, \d{4})", html, re.IGNORECASE)
    if not m:
        return None
    try:
        dt = datetime.strptime(m.group(1), "%B %d, %Y").replace(tzinfo=timezone.utc)
        return _parse_date_key(dt)
    except ValueError:
        return None


async def _fetch_html(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url, allow_redirects=True,
                               timeout=aiohttp.ClientTimeout(total=15)) as resp:
            resp.raise_for_status()
            return await resp.text()


async def _do_refresh(now: datetime) -> dict:
    html = await _fetch_html(SOURCE_URL)
    update_date_key = _parse_release_date_from_html(html)
    if not update_date_key:
        raise ValueError("Could not parse the next Genshin update date.")
    next_cache = {
        "sourceUrl": SOURCE_URL,
        "fetchedAt": now.isoformat(),
        "updateDateKey": update_date_key,
        "eventDateKey": _subtract_utc_days(update_date_key, 1),
    }
    _save_cache(next_cache)
    return next_cache


async def refresh_genshin_countdown(now: datetime = None) -> dict:
    global _inflight
    if now is None:
        now = datetime.now(timezone.utc)
    if _inflight is not None:
        return await _inflight
    _inflight = asyncio.ensure_future(_do_refresh(now))
    try:
        return await _inflight
    finally:
        _inflight = None


def _is_stale(now: datetime) -> bool:
    fetched_at = _cache.get("fetchedAt")
    if not fetched_at:
        return True
    try:
        fetched = datetime.fromisoformat(fetched_at)
        return (now - fetched).total_seconds() > REFRESH_INTERVAL_SECS
    except Exception:
        return True


async def ensure_fresh_genshin_countdown(now: datetime = None) -> dict:
    global _cache
    if not _cache:
        _cache = _load_cache()
    if now is None:
        now = datetime.now(timezone.utc)
    if not _is_stale(now) and _cache.get("eventDateKey"):
        return _cache
    try:
        return await refresh_genshin_countdown(now)
    except Exception:
        return _cache


def get_genshin_event_date_key() -> str:
    return _cache.get("eventDateKey", "")


def get_genshin_update_date_key() -> str:
    return _cache.get("updateDateKey", "")


_cache = _load_cache()
