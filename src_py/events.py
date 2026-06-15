"""Game event definitions (Undertale, Deltarune, Genshin, Forsaken)."""
from datetime import datetime, timezone


def _pad2(n: int) -> str:
    return str(n).zfill(2)


EVENTS = [
    {"key": "undertale", "command": "undertale", "title": "Undertale Anniversary", "fixed": {"month": 9, "day": 15}},
    {"key": "deltarune", "command": "deltarune", "title": "Deltarune Anniversary", "fixed": {"month": 10, "day": 31}},
    {"key": "genshin",   "command": "genshin",   "title": "Genshin Update Countdown"},
    {"key": "forsaken",  "command": "forsaken",  "title": "Forsaken Update"},
    {"key": "vocaloid",  "command": "vocaloid",  "title": "Vocaloid Night"},
]


def get_event_date_key_for_year(event_key: str, year: int) -> str | None:
    ev = next((e for e in EVENTS if e["key"] == event_key), None)
    if not ev:
        return None
    fixed = ev.get("fixed")
    if fixed:
        return f"{year:04d}-{_pad2(fixed['month'])}-{_pad2(fixed['day'])}"
    return None


def get_event_for_date_key(date_key: str) -> dict | None:
    from genshin_countdown import get_genshin_event_date_key
    from forsaken_store import get_forsaken_date_key

    for ev in EVENTS:
        if ev["key"] == "genshin":
            if get_genshin_event_date_key() == date_key:
                return ev
            continue
        if ev["key"] == "forsaken":
            if get_forsaken_date_key() == date_key:
                return ev
            continue
        year = int(str(date_key)[:4])
        if get_event_date_key_for_year(ev["key"], year) == date_key:
            return ev
    return None


def get_event_for_date(dt: datetime = None) -> dict | None:
    if dt is None:
        dt = datetime.now(timezone.utc)
    date_key = f"{dt.year:04d}-{_pad2(dt.month)}-{_pad2(dt.day)}"
    return get_event_for_date_key(date_key)
