"""
CLV-Tracker Service

Wraps clv.py logic and provides database integration for capturing, analyzing,
and tracking closing line value (CLV) across player props. CLV is the only
non-overfittable proof of edge: if picks consistently get better odds than close,
you're beating the market regardless of short-run W/L.
"""

import os
import json
import csv
import statistics
from datetime import datetime, timezone
from collections import defaultdict
from typing import List, Dict, Optional, Tuple
from urllib.request import Request, urlopen
from urllib.error import URLError

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from models import CLVBet, LineCapture


class OddsAPIClient:
    """Client for The Odds API."""

    API_BASE = "https://api.the-odds-api.com/v4"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _get(self, url: str):
        """HTTP GET request with User-Agent."""
        try:
            req = Request(url, headers={"User-Agent": "CLV-Tracker"})
            with urlopen(req, timeout=60) as response:
                return json.load(response)
        except URLError as e:
            raise RuntimeError(f"Odds API request failed: {e}")

    def get_events(self, sport: str) -> List[Dict]:
        """Fetch events for a sport."""
        url = f"{self.API_BASE}/sports/{sport}/events?apiKey={self.api_key}"
        return self._get(url).get("events", [])

    def get_odds(self, sport: str, event_id: str, market: str, regions: str = "us") -> Dict:
        """Fetch odds for an event."""
        url = (
            f"{self.API_BASE}/sports/{sport}/events/{event_id}/odds?"
            f"apiKey={self.api_key}&regions={regions}&markets={market}&oddsFormat=american"
        )
        return self._get(url)


class CLVTracker:
    """CLV analysis and tracking service."""

    def __init__(self, db: Session, api_key: Optional[str] = None):
        self.db = db
        self.api_key = api_key or os.getenv("ODDS_API_KEY")
        self.odds_client = OddsAPIClient(self.api_key) if self.api_key else None

    # ========== Odds Conversion ==========

    @staticmethod
    def american_to_decimal(american: float) -> float:
        """Convert American odds to decimal."""
        american = float(american)
        return 1 + american / 100.0 if american > 0 else 1 + 100.0 / abs(american)

    @staticmethod
    def decimal_to_american(decimal: float) -> float:
        """Convert decimal odds to American."""
        decimal = float(decimal)
        if decimal >= 2:
            return round(100 * (decimal - 1))
        else:
            return round(-100 / (decimal - 1))

    @staticmethod
    def fair_over(over_am: float, under_am: float) -> Optional[float]:
        """De-vigged P(over) from two-sided American prices."""
        try:
            io = 1.0 / CLVTracker.american_to_decimal(over_am)
            iu = 1.0 / CLVTracker.american_to_decimal(under_am)
        except (TypeError, ValueError, ZeroDivisionError):
            return None
        total = io + iu
        return io / total if total else None

    # ========== CLV Calculation ==========

    def clv_of_pick(
        self,
        side: str,
        your_american: float,
        close_over_am: float,
        close_under_am: float,
    ) -> Optional[float]:
        """
        Calculate CLV of a pick.

        CLV = de-vigged CLOSE prob of your side - your price's break-even prob.
        Positive => you beat the close.
        """
        close_fair = self.fair_over(close_over_am, close_under_am)
        if close_fair is None:
            return None

        close_side_prob = close_fair if side == "over" else 1 - close_fair
        your_break_even = 1.0 / self.american_to_decimal(your_american)

        return close_side_prob - your_break_even

    # ========== Line Capture ==========

    def capture_from_odds_api(
        self,
        tag: str,
        sport: str = "baseball_mlb",
        market: str = "pitcher_strikeouts",
        regions: str = "us",
    ) -> int:
        """
        Capture player prop lines from Odds API.

        Args:
            tag: 'open' or 'close'
            sport: sport slug (e.g., 'baseball_mlb')
            market: market slug (e.g., 'pitcher_strikeouts')
            regions: comma-separated regions (e.g., 'us,us2,eu')

        Returns:
            Number of lines captured
        """
        if not self.odds_client:
            raise RuntimeError("ODDS_API_KEY not configured")

        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")

        try:
            events = self.odds_client.get_events(sport)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch events: {e}")

        rows_created = 0
        for event in events:
            event_id = event.get("id")
            event_label = f"{event.get('away_team', '')} @ {event.get('home_team', '')}"

            try:
                odds_data = self.odds_client.get_odds(
                    sport, event_id, market, regions
                )
            except Exception:
                continue  # Skip bad events

            seen = {}  # player -> (line, over, under, book)
            for bookmaker in odds_data.get("bookmakers", []):
                book_key = bookmaker.get("key", "")
                for market_data in bookmaker.get("markets", []):
                    if market_data.get("key") != market:
                        continue

                    over, under = {}, {}
                    for outcome in market_data.get("outcomes", []):
                        player_name = outcome.get("description")
                        side = (outcome.get("name") or "").lower()
                        point = outcome.get("point")
                        price = outcome.get("price")

                        if None in (player_name, point, price):
                            continue

                        (over if side == "over" else under)[player_name] = (point, price)

                    for pl, (pt, pr) in over.items():
                        if pl not in seen and pl in under and under[pl][0] == pt:
                            seen[pl] = (pt, pr, under[pl][1], book_key)

            # Save to database
            for player, (line, over_odds, under_odds, book) in seen.items():
                line_capture = LineCapture(
                    date=date_str,
                    captured_at=now,
                    tag=tag,
                    event=event_label,
                    player=player,
                    line=float(line),
                    over_odds=float(over_odds),
                    under_odds=float(under_odds),
                    bookmaker=book,
                    sport=sport,
                    market=market,
                )
                self.db.add(line_capture)
                rows_created += 1

        self.db.commit()
        return rows_created

    def record_line_capture(
        self,
        date: str,
        tag: str,
        event: str,
        player: str,
        line: float,
        over_odds: float,
        under_odds: float,
        bookmaker: str,
        sport: str = "baseball_mlb",
        market: str = "pitcher_strikeouts",
    ) -> LineCapture:
        """Manually record a line capture."""
        capture = LineCapture(
            date=date,
            captured_at=datetime.now(timezone.utc),
            tag=tag,
            event=event,
            player=player,
            line=float(line),
            over_odds=float(over_odds),
            under_odds=float(under_odds),
            bookmaker=bookmaker,
            sport=sport,
            market=market,
        )
        self.db.add(capture)
        self.db.commit()
        return capture

    # ========== CLV Bet Recording ==========

    def record_bet(
        self,
        date: str,
        player: str,
        your_side: str,
        your_american: float,
        close_over_american: Optional[float] = None,
        close_under_american: Optional[float] = None,
        bookmaker: Optional[str] = None,
        sport: str = "baseball_mlb",
        market: str = "pitcher_strikeouts",
        notes: Optional[str] = None,
    ) -> CLVBet:
        """
        Record a CLV bet.

        If close odds provided, CLV is calculated immediately.
        Otherwise, bet is marked PENDING until closed.
        """
        your_decimal = self.american_to_decimal(your_american)
        your_break_even = 1.0 / your_decimal

        clv_value = None
        close_fair_prob = None

        if close_over_american is not None and close_under_american is not None:
            clv_value = self.clv_of_pick(
                your_side,
                your_american,
                close_over_american,
                close_under_american,
            )
            close_fair_prob = self.fair_over(close_over_american, close_under_american)

        bet = CLVBet(
            date=date,
            player=player,
            your_side=your_side,
            your_american=your_american,
            your_decimal=your_decimal,
            close_over_american=close_over_american,
            close_under_american=close_under_american,
            close_fair_prob=close_fair_prob,
            your_break_even=your_break_even,
            clv_value=clv_value,
            status="CLOSED" if clv_value is not None else "RECORDED",
            sport=sport,
            market=market,
            bookmaker=bookmaker,
            notes=notes,
            recorded_at=datetime.now(timezone.utc),
            closed_at=datetime.now(timezone.utc) if clv_value is not None else None,
        )
        self.db.add(bet)
        self.db.commit()
        return bet

    def close_bet(
        self,
        bet_id: int,
        close_over_american: float,
        close_under_american: float,
    ) -> CLVBet:
        """Close an open bet with closing odds."""
        bet = self.db.query(CLVBet).filter(CLVBet.id == bet_id).first()
        if not bet:
            raise ValueError(f"Bet {bet_id} not found")

        bet.close_over_american = close_over_american
        bet.close_under_american = close_under_american
        bet.close_fair_prob = self.fair_over(close_over_american, close_under_american)
        bet.clv_value = self.clv_of_pick(
            bet.your_side,
            bet.your_american,
            close_over_american,
            close_under_american,
        )
        bet.status = "CLOSED"
        bet.closed_at = datetime.now(timezone.utc)

        self.db.commit()
        return bet

    # ========== Line Movement Analysis ==========

    def analyze_line_movement(
        self,
        sport: str = "baseball_mlb",
        market: str = "pitcher_strikeouts",
        limit: int = 10,
    ) -> Dict:
        """
        Analyze line movement open->close.

        Returns line changes, fair prob moves, and biggest movers.
        """
        # Group captures by (date, player)
        captures = self.db.query(LineCapture).filter(
            and_(
                LineCapture.sport == sport,
                LineCapture.market == market,
            )
        ).all()

        g = defaultdict(list)
        for capture in captures:
            g[(capture.date, capture.player)].append(capture)

        moves = []
        for (date, player), caps in g.items():
            caps.sort(key=lambda c: c.captured_at)
            if len(caps) < 2:
                continue

            open_cap = caps[0]
            close_cap = caps[-1]

            if open_cap.captured_at == close_cap.captured_at:
                continue

            open_fair = self.fair_over(open_cap.over_odds, open_cap.under_odds)
            close_fair = self.fair_over(close_cap.over_odds, close_cap.under_odds)

            if open_fair is None or close_fair is None:
                continue

            moves.append(
                {
                    "date": date,
                    "player": player,
                    "open_line": float(open_cap.line),
                    "close_line": float(close_cap.line),
                    "open_fair_prob": open_fair,
                    "close_fair_prob": close_fair,
                    "fair_prob_move": abs(close_fair - open_fair),
                    "direction": "OVER" if close_fair > open_fair else "UNDER",
                }
            )

        if not moves:
            return {
                "analysis_date": datetime.now(timezone.utc),
                "captures_count": len(captures),
                "pairs_analyzed": 0,
                "line_changed_count": 0,
                "fair_moves": [],
                "mean_fair_move": 0,
                "median_fair_move": 0,
                "max_fair_move": 0,
                "avg_available_clv": 0,
                "biggest_movers": [],
            }

        fair_moves = [m["fair_prob_move"] for m in moves]
        line_changed = sum(1 for m in moves if m["open_line"] != m["close_line"])

        return {
            "analysis_date": datetime.now(timezone.utc),
            "captures_count": len(captures),
            "pairs_analyzed": len(moves),
            "line_changed_count": line_changed,
            "fair_moves": fair_moves,
            "mean_fair_move": statistics.mean(fair_moves) if fair_moves else 0,
            "median_fair_move": statistics.median(fair_moves) if fair_moves else 0,
            "max_fair_move": max(fair_moves) if fair_moves else 0,
            "avg_available_clv": statistics.mean(fair_moves) * 100 if fair_moves else 0,
            "biggest_movers": sorted(moves, key=lambda m: -m["fair_prob_move"])[:limit],
        }

    # ========== CLV Leaderboard ==========

    def get_leaderboard(
        self,
        sport: str = "baseball_mlb",
        market: str = "pitcher_strikeouts",
        limit: int = 100,
        min_status: str = "CLOSED",
    ) -> Dict:
        """
        Get CLV leaderboard sorted by CLV value.

        Returns bets with CLV calculations, sorted descending.
        """
        query = self.db.query(CLVBet).filter(
            and_(
                CLVBet.sport == sport,
                CLVBet.market == market,
                CLVBet.status.in_(["CLOSED", "ANALYZED"]),
                CLVBet.clv_value.isnot(None),
            )
        )

        total_bets = query.count()
        bets = query.order_by(desc(CLVBet.clv_value)).limit(limit).all()

        if not bets:
            return {
                "total_bets": 0,
                "analyzed_bets": 0,
                "mean_clv": None,
                "median_clv": None,
                "max_clv": None,
                "min_clv": None,
                "positive_clv_count": 0,
                "entries": [],
            }

        clv_values = [b.clv_value for b in bets if b.clv_value is not None]
        positive_count = sum(1 for v in clv_values if v > 0)

        entries = [
            {
                "rank": idx + 1,
                "player": b.player,
                "date": b.date,
                "side": b.your_side,
                "your_odds": b.your_american,
                "close_odds_over": b.close_over_american,
                "close_odds_under": b.close_under_american,
                "clv_value": b.clv_value,
                "status": b.status,
            }
            for idx, b in enumerate(bets)
        ]

        return {
            "total_bets": total_bets,
            "analyzed_bets": len(bets),
            "mean_clv": statistics.mean(clv_values) if clv_values else None,
            "median_clv": statistics.median(clv_values) if clv_values else None,
            "max_clv": max(clv_values) if clv_values else None,
            "min_clv": min(clv_values) if clv_values else None,
            "positive_clv_count": positive_count,
            "entries": entries,
        }

    def get_player_history(self, player: str) -> List[CLVBet]:
        """Get all CLV bets for a player."""
        return (
            self.db.query(CLVBet)
            .filter(CLVBet.player == player)
            .order_by(desc(CLVBet.date))
            .all()
        )

    def get_bets_by_date_range(self, start_date: str, end_date: str) -> List[CLVBet]:
        """Get CLV bets in date range (YYYY-MM-DD format)."""
        return (
            self.db.query(CLVBet)
            .filter(
                and_(
                    CLVBet.date >= start_date,
                    CLVBet.date <= end_date,
                )
            )
            .order_by(desc(CLVBet.date))
            .all()
        )
