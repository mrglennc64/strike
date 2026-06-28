"""
Portfolio Regime Shift Alerter

Monitors VIX, funding rates, sentiment, and other market indicators
to detect regime shifts and trigger portfolio rebalancing recommendations.
"""

import os
import logging
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
import asyncio

import requests
import numpy as np

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RegimeType(Enum):
    """Market regime classifications"""
    LOW_VOL = "Low Vol"
    NORMAL = "Normal"
    HIGH_VOL = "High Vol"
    STRESS = "Stress"


class AlertAction(Enum):
    """Recommended actions on regime shift"""
    HOLD = "Hold"
    REDUCE_RISK = "Reduce Risk"
    INCREASE_RISK = "Increase Risk"
    REBALANCE = "Rebalance"
    HEDGE = "Hedge"


@dataclass
class RegimeState:
    """Current market regime state"""
    timestamp: datetime
    vix: float
    vix_percentile_30d: float
    funding_rate: float
    sentiment_score: float
    regime_type: RegimeType
    regime_score: float  # 0-1, higher = more stress
    recommended_action: AlertAction
    explanation: str
    is_regime_shift: bool
    shift_magnitude: float  # 0-1, how big the shift


class RegimeAlerter:
    """Monitor and alert on market regime shifts"""

    def __init__(self, portfolio_api_url: str = "http://localhost:8001"):
        """
        Initialize regime alerter.

        Args:
            portfolio_api_url: URL to portfolio engine API
        """
        self.portfolio_api_url = portfolio_api_url
        self.db_path = os.getenv("DATABASE_PATH", "/app/data/regime_history.db")
        self.alert_webhook_url = os.getenv("ALERT_WEBHOOK_URL")
        self.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        self._initialize_db()
        self.previous_regime = None

    def _initialize_db(self):
        """Initialize SQLite database for regime history"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Regime history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS regime_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    vix REAL NOT NULL,
                    vix_percentile REAL NOT NULL,
                    funding_rate REAL NOT NULL,
                    sentiment_score REAL NOT NULL,
                    regime_type TEXT NOT NULL,
                    regime_score REAL NOT NULL,
                    recommended_action TEXT NOT NULL,
                    is_regime_shift BOOLEAN NOT NULL,
                    shift_magnitude REAL
                )
            """)

            # Regime shift events
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS regime_shifts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    from_regime TEXT NOT NULL,
                    to_regime TEXT NOT NULL,
                    magnitude REAL NOT NULL,
                    trigger_vix REAL,
                    trigger_sentiment REAL,
                    recommended_action TEXT NOT NULL,
                    executed BOOLEAN DEFAULT FALSE
                )
            """)

            conn.commit()

    def get_vix_level(self) -> Optional[float]:
        """
        Get current VIX level.

        Args:
            None

        Returns:
            VIX level (float) or None if fetch fails
        """
        try:
            # In production, fetch from real-time data source
            # For now, return simulated value
            # Example: fetch from Yahoo Finance, CBOE, etc.
            return self._get_simulated_vix()
        except Exception as e:
            logger.error(f"Failed to get VIX level: {str(e)}")
            return None

    def _get_simulated_vix(self) -> float:
        """Get simulated VIX for testing"""
        # In production, fetch real data
        base_vix = 18.0
        noise = np.random.normal(0, 2)
        return max(5.0, base_vix + noise)

    def get_vix_percentile(self, vix: float, days: int = 30) -> float:
        """
        Get VIX percentile over N days.

        Args:
            vix: Current VIX level
            days: Look-back period

        Returns:
            VIX percentile (0-100)
        """
        try:
            cutoff_time = (datetime.now() - timedelta(days=days)).isoformat()

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT vix FROM regime_history
                    WHERE timestamp > ?
                """, (cutoff_time,))

                vix_levels = [row[0] for row in cursor.fetchall()]

                if not vix_levels:
                    return 50.0

                # Calculate percentile
                percentile = 100 * np.mean(np.array(vix_levels) <= vix)
                return float(percentile)

        except Exception as e:
            logger.error(f"Failed to get VIX percentile: {str(e)}")
            return 50.0

    def get_crypto_funding_rate(self) -> Optional[float]:
        """
        Get current crypto funding rate.

        Returns:
            Funding rate (float) or None if fetch fails
        """
        try:
            # In production, fetch from Bybit, Binance Futures, etc.
            # For testing, return simulated value
            return np.random.uniform(-0.01, 0.05)
        except Exception as e:
            logger.error(f"Failed to get funding rate: {str(e)}")
            return 0.0

    def get_market_sentiment(self) -> Optional[float]:
        """
        Get market sentiment score (-1 to +1).

        Returns:
            Sentiment score or None if fetch fails
        """
        try:
            # In production, aggregate from multiple sources:
            # - Fear & Greed Index
            # - Crypto Sentiment
            # - News sentiment
            # - Options put/call ratios
            # For testing, return simulated value
            return np.random.uniform(-1, 1)
        except Exception as e:
            logger.error(f"Failed to get market sentiment: {str(e)}")
            return 0.0

    def classify_regime(self, vix: float, sentiment: float) -> RegimeType:
        """
        Classify market regime based on VIX and sentiment.

        Args:
            vix: Current VIX level
            sentiment: Market sentiment (-1 to +1)

        Returns:
            RegimeType classification
        """
        if vix < 12:
            return RegimeType.LOW_VOL
        elif vix < 20:
            if sentiment < -0.3:
                return RegimeType.HIGH_VOL
            return RegimeType.NORMAL
        elif vix < 30:
            return RegimeType.HIGH_VOL
        else:
            return RegimeType.STRESS

    def calculate_regime_score(
        self,
        vix: float,
        funding: float,
        sentiment: float,
        vix_percentile: float
    ) -> float:
        """
        Calculate overall regime stress score (0-1).

        0 = calm market, 1 = maximum stress

        Args:
            vix: Current VIX level
            funding: Crypto funding rate
            sentiment: Market sentiment (-1 to +1)
            vix_percentile: VIX percentile over lookback

        Returns:
            Regime score (0-1)
        """
        # Normalize VIX (assume range 5-80)
        vix_norm = min(1.0, max(0.0, (vix - 5) / 75))

        # Normalize funding rate (assume range -0.01 to 0.05)
        funding_norm = min(1.0, max(0.0, (funding + 0.01) / 0.06))

        # Sentiment as stress (negative = stress)
        sentiment_norm = (1 - sentiment) / 2  # Convert -1..1 to 0..1

        # VIX percentile (high percentile = high stress)
        percentile_norm = vix_percentile / 100

        # Weighted combination
        score = (
            0.4 * vix_norm +
            0.2 * funding_norm +
            0.2 * sentiment_norm +
            0.2 * percentile_norm
        )

        return float(np.clip(score, 0, 1))

    def detect_regime_shift(
        self,
        current_regime: RegimeType,
        current_score: float,
        previous_state: Optional[RegimeState] = None
    ) -> tuple[bool, float]:
        """
        Detect if a regime shift has occurred.

        Args:
            current_regime: Current regime classification
            current_score: Current regime score
            previous_state: Previous regime state

        Returns:
            Tuple of (is_shift, magnitude) where magnitude is 0-1
        """
        if previous_state is None:
            return False, 0.0

        # Regime changed
        if current_regime != previous_state.regime_type:
            magnitude = abs(current_score - previous_state.regime_score)
            return True, float(magnitude)

        # Score changed significantly
        score_change = abs(current_score - previous_state.regime_score)
        if score_change > 0.15:
            return True, score_change

        return False, 0.0

    def recommend_action(
        self,
        regime: RegimeType,
        is_shift: bool,
        shift_magnitude: float
    ) -> AlertAction:
        """
        Recommend portfolio action based on regime.

        Args:
            regime: Current regime
            is_shift: Whether regime just shifted
            shift_magnitude: Magnitude of shift (0-1)

        Returns:
            Recommended action
        """
        if is_shift and shift_magnitude > 0.3:
            if regime == RegimeType.STRESS:
                return AlertAction.HEDGE
            elif regime == RegimeType.LOW_VOL:
                return AlertAction.INCREASE_RISK
            elif regime == RegimeType.HIGH_VOL:
                return AlertAction.REDUCE_RISK
            else:
                return AlertAction.REBALANCE

        if regime == RegimeType.STRESS:
            return AlertAction.REDUCE_RISK
        elif regime == RegimeType.LOW_VOL:
            return AlertAction.INCREASE_RISK
        elif regime == RegimeType.HIGH_VOL:
            return AlertAction.REDUCE_RISK
        else:
            return AlertAction.HOLD

    def generate_explanation(
        self,
        regime: RegimeType,
        vix: float,
        funding: float,
        sentiment: float,
        is_shift: bool
    ) -> str:
        """
        Generate human-readable explanation of regime.

        Args:
            regime: Current regime
            vix: VIX level
            funding: Funding rate
            sentiment: Sentiment score
            is_shift: Whether regime just shifted

        Returns:
            Explanation string
        """
        parts = []

        if is_shift:
            parts.append("REGIME SHIFT DETECTED")

        parts.append(f"Regime: {regime.value}")
        parts.append(f"VIX: {vix:.1f}")

        if funding > 0.03:
            parts.append(f"Crypto funding elevated ({funding:.3f})")

        if sentiment < -0.5:
            parts.append("Strong negative sentiment")
        elif sentiment > 0.5:
            parts.append("Strong positive sentiment")

        return " | ".join(parts)

    def assess_regime(self) -> Optional[RegimeState]:
        """
        Assess current market regime.

        Returns:
            RegimeState object or None if assessment fails
        """
        try:
            # Get market data
            vix = self.get_vix_level()
            funding = self.get_crypto_funding_rate()
            sentiment = self.get_market_sentiment()

            if vix is None:
                logger.error("Failed to get VIX data")
                return None

            funding = funding or 0.0
            sentiment = sentiment or 0.0

            # Get percentile
            vix_percentile = self.get_vix_percentile(vix)

            # Classify regime
            regime = self.classify_regime(vix, sentiment)

            # Calculate score
            regime_score = self.calculate_regime_score(vix, funding, sentiment, vix_percentile)

            # Detect shift
            is_shift, shift_magnitude = self.detect_regime_shift(
                regime, regime_score, self.previous_regime
            )

            # Recommend action
            action = self.recommend_action(regime, is_shift, shift_magnitude)

            # Generate explanation
            explanation = self.generate_explanation(
                regime, vix, funding, sentiment, is_shift
            )

            state = RegimeState(
                timestamp=datetime.now(),
                vix=vix,
                vix_percentile_30d=vix_percentile,
                funding_rate=funding,
                sentiment_score=sentiment,
                regime_type=regime,
                regime_score=regime_score,
                recommended_action=action,
                explanation=explanation,
                is_regime_shift=is_shift,
                shift_magnitude=shift_magnitude
            )

            logger.info(f"Regime Assessment ({datetime.now().isoformat()})")
            logger.info(f"  Regime: {regime.value}")
            logger.info(f"  VIX: {vix:.1f} (percentile: {vix_percentile:.0f})")
            logger.info(f"  Funding: {funding:.4f}")
            logger.info(f"  Sentiment: {sentiment:.2f}")
            logger.info(f"  Score: {regime_score:.2f}")
            if is_shift:
                logger.warning(f"  REGIME SHIFT: {shift_magnitude:.2f}")
                logger.warning(f"  Recommended: {action.value}")

            # Update previous state
            self.previous_regime = state

            return state

        except Exception as e:
            logger.error(f"Failed to assess regime: {str(e)}")
            return None

    def record_regime_state(self, state: RegimeState):
        """Record regime state to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO regime_history
                    (timestamp, vix, vix_percentile, funding_rate, sentiment_score,
                     regime_type, regime_score, recommended_action, is_regime_shift,
                     shift_magnitude)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    state.timestamp.isoformat(),
                    state.vix,
                    state.vix_percentile_30d,
                    state.funding_rate,
                    state.sentiment_score,
                    state.regime_type.value,
                    state.regime_score,
                    state.recommended_action.value,
                    state.is_regime_shift,
                    state.shift_magnitude if state.is_regime_shift else None
                ))

                # Record shift event if applicable
                if state.is_regime_shift and self.previous_regime:
                    cursor.execute("""
                        INSERT INTO regime_shifts
                        (timestamp, from_regime, to_regime, magnitude, trigger_vix,
                         trigger_sentiment, recommended_action)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        state.timestamp.isoformat(),
                        self.previous_regime.regime_type.value,
                        state.regime_type.value,
                        state.shift_magnitude,
                        state.vix,
                        state.sentiment_score,
                        state.recommended_action.value
                    ))

                conn.commit()
                logger.debug("Regime state recorded to database")

        except Exception as e:
            logger.error(f"Failed to record regime state: {str(e)}")

    def send_alert(self, state: RegimeState):
        """
        Send alert on regime shift.

        Args:
            state: RegimeState to alert on
        """
        if not state.is_regime_shift:
            return

        message = {
            "timestamp": state.timestamp.isoformat(),
            "alert_type": "regime_shift",
            "regime": state.regime_type.value,
            "regime_score": state.regime_score,
            "shift_magnitude": state.shift_magnitude,
            "vix": state.vix,
            "sentiment": state.sentiment_score,
            "recommended_action": state.recommended_action.value,
            "explanation": state.explanation
        }

        logger.critical(f"REGIME SHIFT ALERT: {json.dumps(message)}")

        # Send Slack webhook if configured
        if self.slack_webhook_url:
            try:
                slack_msg = {
                    "text": f"Portfolio Regime Shift Alert",
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": "Portfolio Regime Shift"
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {"type": "mrkdwn", "text": f"*Regime:*\n{state.regime_type.value}"},
                                {"type": "mrkdwn", "text": f"*Score:*\n{state.regime_score:.2f}"},
                                {"type": "mrkdwn", "text": f"*VIX:*\n{state.vix:.1f}"},
                                {"type": "mrkdwn", "text": f"*Sentiment:*\n{state.sentiment_score:.2f}"},
                            ]
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Action:* {state.recommended_action.value}\n{state.explanation}"
                            }
                        }
                    ]
                }

                requests.post(self.slack_webhook_url, json=slack_msg, timeout=10)
                logger.info("Slack alert sent")

            except Exception as e:
                logger.error(f"Failed to send Slack alert: {str(e)}")

        # Send webhook if configured
        if self.alert_webhook_url:
            try:
                requests.post(
                    self.alert_webhook_url,
                    json=message,
                    timeout=10
                )
                logger.info("Webhook alert sent")

            except Exception as e:
                logger.error(f"Failed to send webhook alert: {str(e)}")

    def get_regime_history(self, hours: int = 24) -> List[RegimeState]:
        """
        Get regime history for the past N hours.

        Args:
            hours: Number of hours to look back

        Returns:
            List of RegimeState objects
        """
        try:
            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM regime_history
                    WHERE timestamp > ?
                    ORDER BY timestamp DESC
                """, (cutoff_time,))

                states = []
                for row in cursor.fetchall():
                    states.append(RegimeState(
                        timestamp=datetime.fromisoformat(row["timestamp"]),
                        vix=row["vix"],
                        vix_percentile_30d=row["vix_percentile"],
                        funding_rate=row["funding_rate"],
                        sentiment_score=row["sentiment_score"],
                        regime_type=RegimeType(row["regime_type"]),
                        regime_score=row["regime_score"],
                        recommended_action=AlertAction[row["recommended_action"].replace(" ", "_").upper()],
                        explanation="",
                        is_regime_shift=bool(row["is_regime_shift"]),
                        shift_magnitude=row["shift_magnitude"] or 0.0
                    ))

                return states

        except Exception as e:
            logger.error(f"Failed to get regime history: {str(e)}")
            return []


if __name__ == "__main__":
    alerter = RegimeAlerter()

    # Run single assessment for testing
    state = alerter.assess_regime()
    if state:
        alerter.record_regime_state(state)
        alerter.send_alert(state)
        print(f"\nRegime State ({state.timestamp.isoformat()})")
        print(f"  Regime: {state.regime_type.value}")
        print(f"  VIX: {state.vix:.1f}")
        print(f"  Score: {state.regime_score:.2f}")
        print(f"  Shift: {state.is_regime_shift}")
        print(f"  Recommended: {state.recommended_action.value}")
