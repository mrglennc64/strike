"""The MLB "game day" clock.

Every default-date path must agree on what "today" means. The server runs on
UTC, where ``date.today()`` rolls over at 8pm ET — mid-evening-slate — so a
naive default silently serves tomorrow's (empty) slate while tonight's games
are still live. MLB's slate day is anchored to US Eastern time.
"""
from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

_EASTERN = ZoneInfo("America/New_York")


def mlb_today() -> date:
    """Today's MLB slate date (US Eastern), regardless of server timezone."""
    return datetime.now(tz=_EASTERN).date()


def mlb_today_iso() -> str:
    return mlb_today().isoformat()
