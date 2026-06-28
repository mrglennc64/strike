"""
CLV-Tracker Cron Utilities

Scheduled tasks for:
  - capture_open() @ 1pm
  - capture_close() @ 10pm
  - calculate_clv() @ 11pm

These can be called by an external scheduler (e.g., cron, APScheduler, cloud functions).
"""

import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from database import SessionLocal
from services import CLVTracker

logger = logging.getLogger(__name__)


def capture_open(
    sport: str = "baseball_mlb",
    market: str = "pitcher_strikeouts",
    regions: str = "us",
) -> dict:
    """
    Capture OPEN lines at 1pm.

    Runs once per day early in the day before sharp money moves.

    Args:
        sport: sport slug (default: baseball_mlb)
        market: market slug (default: pitcher_strikeouts)
        regions: regions to capture (default: us)

    Returns:
        Summary of capture
    """
    db = SessionLocal()
    try:
        logger.info(f"[{datetime.now(timezone.utc)}] Starting capture_open")

        tracker = CLVTracker(db)
        rows_captured = tracker.capture_from_odds_api(
            tag="open",
            sport=sport,
            market=market,
            regions=regions,
        )

        result = {
            "timestamp": datetime.now(timezone.utc),
            "tag": "open",
            "rows_captured": rows_captured,
            "sport": sport,
            "market": market,
            "status": "success",
        }

        logger.info(f"[{datetime.now(timezone.utc)}] capture_open completed: {rows_captured} rows")
        return result

    except Exception as e:
        logger.error(f"[{datetime.now(timezone.utc)}] capture_open failed: {e}")
        return {
            "timestamp": datetime.now(timezone.utc),
            "tag": "open",
            "status": "error",
            "error": str(e),
        }

    finally:
        db.close()


def capture_close(
    sport: str = "baseball_mlb",
    market: str = "pitcher_strikeouts",
    regions: str = "us",
) -> dict:
    """
    Capture CLOSE lines at 10pm.

    Runs once per day near game time or end of market activity.

    Args:
        sport: sport slug (default: baseball_mlb)
        market: market slug (default: pitcher_strikeouts)
        regions: regions to capture (default: us)

    Returns:
        Summary of capture
    """
    db = SessionLocal()
    try:
        logger.info(f"[{datetime.now(timezone.utc)}] Starting capture_close")

        tracker = CLVTracker(db)
        rows_captured = tracker.capture_from_odds_api(
            tag="close",
            sport=sport,
            market=market,
            regions=regions,
        )

        result = {
            "timestamp": datetime.now(timezone.utc),
            "tag": "close",
            "rows_captured": rows_captured,
            "sport": sport,
            "market": market,
            "status": "success",
        }

        logger.info(f"[{datetime.now(timezone.utc)}] capture_close completed: {rows_captured} rows")
        return result

    except Exception as e:
        logger.error(f"[{datetime.now(timezone.utc)}] capture_close failed: {e}")
        return {
            "timestamp": datetime.now(timezone.utc),
            "tag": "close",
            "status": "error",
            "error": str(e),
        }

    finally:
        db.close()


def calculate_clv(
    sport: str = "baseball_mlb",
    market: str = "pitcher_strikeouts",
) -> dict:
    """
    Calculate and analyze CLV at 11pm.

    Runs after close capture to analyze line movement and update
    CLV calculations for all bets with both open and close odds.

    Args:
        sport: sport slug (default: baseball_mlb)
        market: market slug (default: pitcher_strikeouts)

    Returns:
        Summary of analysis
    """
    db = SessionLocal()
    try:
        logger.info(f"[{datetime.now(timezone.utc)}] Starting calculate_clv")

        tracker = CLVTracker(db)
        analysis = tracker.analyze_line_movement(sport, market, limit=100)

        result = {
            "timestamp": datetime.now(timezone.utc),
            "sport": sport,
            "market": market,
            "captures_count": analysis["captures_count"],
            "pairs_analyzed": analysis["pairs_analyzed"],
            "line_changed_count": analysis["line_changed_count"],
            "mean_fair_move": analysis["mean_fair_move"],
            "median_fair_move": analysis["median_fair_move"],
            "max_fair_move": analysis["max_fair_move"],
            "avg_available_clv": analysis["avg_available_clv"],
            "status": "success",
        }

        logger.info(f"[{datetime.now(timezone.utc)}] calculate_clv completed: {analysis['pairs_analyzed']} pairs analyzed")
        return result

    except Exception as e:
        logger.error(f"[{datetime.now(timezone.utc)}] calculate_clv failed: {e}")
        return {
            "timestamp": datetime.now(timezone.utc),
            "sport": sport,
            "market": market,
            "status": "error",
            "error": str(e),
        }

    finally:
        db.close()


def full_daily_cycle(
    sport: str = "baseball_mlb",
    market: str = "pitcher_strikeouts",
) -> dict:
    """
    Execute full daily cycle: open -> close -> analyze.

    Useful for testing or manual execution.

    Args:
        sport: sport slug (default: baseball_mlb)
        market: market slug (default: pitcher_strikeouts)

    Returns:
        Summary of all three tasks
    """
    logger.info(f"[{datetime.now(timezone.utc)}] Starting full_daily_cycle")

    open_result = capture_open(sport=sport, market=market)
    close_result = capture_close(sport=sport, market=market)
    clv_result = calculate_clv(sport=sport, market=market)

    return {
        "timestamp": datetime.now(timezone.utc),
        "open": open_result,
        "close": close_result,
        "analysis": clv_result,
        "overall_status": "success" if all(
            r.get("status") == "success"
            for r in [open_result, close_result, clv_result]
        ) else "partial_failure",
    }


if __name__ == "__main__":
    """Quick test of cron utilities."""
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "open":
            result = capture_open()
        elif cmd == "close":
            result = capture_close()
        elif cmd == "clv":
            result = calculate_clv()
        elif cmd == "full":
            result = full_daily_cycle()
        else:
            print(f"Unknown command: {cmd}")
            print("Valid commands: open, close, clv, full")
            sys.exit(1)

        import json
        print(json.dumps(result, indent=2, default=str))
    else:
        print("Usage: python cron_utils.py [open|close|clv|full]")
        sys.exit(1)
