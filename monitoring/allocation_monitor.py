"""
Portfolio Allocation Monitor

Tracks actual portfolio allocation vs recommended allocation
from the portfolio engine. Alerts on drift, rebalancing needs,
and concentration risks.
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import sqlite3

import numpy as np
import requests
from dataclasses import dataclass, asdict
from enum import Enum

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class AllocationSnapshot:
    """Snapshot of portfolio allocation at a point in time"""
    timestamp: datetime
    actual_weights: Dict[str, float]
    recommended_weights: Dict[str, float]
    drift_pcts: Dict[str, float]
    max_drift: float
    concentration_herfindahl: float
    rebalance_needed: bool
    alert_level: AlertLevel
    alert_message: str


class AllocationMonitor:
    """Monitor portfolio allocation vs recommendations"""

    def __init__(self, portfolio_api_url: str = "http://localhost:8001"):
        """
        Initialize allocation monitor.

        Args:
            portfolio_api_url: URL to portfolio engine API
        """
        self.portfolio_api_url = portfolio_api_url
        self.db_path = os.getenv("DATABASE_PATH", "/app/data/allocation_history.db")
        self._initialize_db()

    def _initialize_db(self):
        """Initialize SQLite database for allocation history"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Allocation history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS allocation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    actual_weights JSON NOT NULL,
                    recommended_weights JSON NOT NULL,
                    drift_pcts JSON NOT NULL,
                    max_drift REAL NOT NULL,
                    concentration_herfindahl REAL NOT NULL,
                    rebalance_needed BOOLEAN NOT NULL,
                    alert_level TEXT NOT NULL,
                    alert_message TEXT
                )
            """)

            # Rebalancing events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rebalancing_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    trigger_reason TEXT NOT NULL,
                    old_weights JSON NOT NULL,
                    new_weights JSON NOT NULL,
                    transaction_costs REAL,
                    alert_level TEXT NOT NULL
                )
            """)

            conn.commit()

    def get_current_allocation(self) -> Optional[Dict[str, float]]:
        """
        Get current portfolio allocation from external source.

        This would typically pull from your portfolio management system,
        trading platform, or database.

        Returns:
            Dictionary of {strategy_name: weight}
        """
        try:
            # This is a placeholder - implement based on your system
            # Example: fetch from portfolio DB, trading platform API, etc.
            allocation = {
                "MLB": 0.20,
                "Crypto": 0.15,
                "Earnings": 0.25,
                "AI": 0.20,
                "Econ": 0.20
            }
            return allocation
        except Exception as e:
            logger.error(f"Failed to get current allocation: {str(e)}")
            return None

    def get_recommended_allocation(self) -> Optional[Dict[str, float]]:
        """
        Get recommended allocation from portfolio engine.

        Returns:
            Dictionary of {strategy_name: weight}
        """
        try:
            # Call portfolio engine allocation endpoint
            payload = {
                "strategies": [
                    {"name": "MLB", "expected_return": 15.0, "volatility": 12.0, "sharpe_ratio": 1.25, "max_drawdown": -0.15, "weight": 0.2},
                    {"name": "Crypto", "expected_return": 25.0, "volatility": 40.0, "sharpe_ratio": 0.625, "max_drawdown": -0.50, "weight": 0.2},
                    {"name": "Earnings", "expected_return": 18.0, "volatility": 18.0, "sharpe_ratio": 1.0, "max_drawdown": -0.20, "weight": 0.2},
                    {"name": "AI", "expected_return": 22.0, "volatility": 32.0, "sharpe_ratio": 0.69, "max_drawdown": -0.35, "weight": 0.2},
                    {"name": "Econ", "expected_return": 12.0, "volatility": 8.0, "sharpe_ratio": 1.5, "max_drawdown": -0.10, "weight": 0.2}
                ],
                "optimization_method": "kelly",
                "kelly_fraction": 0.25
            }

            response = requests.post(
                f"{self.portfolio_api_url}/api/portfolio/allocation",
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            return response.json().get("optimal_weights", {})

        except Exception as e:
            logger.error(f"Failed to get recommended allocation: {str(e)}")
            return None

    def calculate_drift(
        self,
        actual: Dict[str, float],
        recommended: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate weight drift (percentage points difference).

        Args:
            actual: Current allocation weights
            recommended: Recommended allocation weights

        Returns:
            Dictionary of {strategy_name: drift_pct}
        """
        drift = {}
        for strategy in actual.keys():
            drift[strategy] = abs(actual.get(strategy, 0) - recommended.get(strategy, 0)) * 100

        return drift

    def calculate_concentration(self, weights: Dict[str, float]) -> float:
        """
        Calculate Herfindahl-Hirschman Index (HHI) concentration.

        HHI = sum(w_i^2)
        Values: 0.2 (equal weight) to 1.0 (single asset)

        Args:
            weights: Portfolio weights

        Returns:
            HHI concentration index
        """
        hhi = sum(w ** 2 for w in weights.values())
        return hhi

    def assess_rebalance_need(
        self,
        drift_pcts: Dict[str, float],
        max_drift_threshold: float = 3.0
    ) -> bool:
        """
        Determine if rebalancing is needed based on drift.

        Args:
            drift_pcts: Drift percentages per strategy
            max_drift_threshold: Maximum acceptable drift in percentage points

        Returns:
            True if rebalancing is recommended
        """
        max_drift = max(drift_pcts.values())
        return max_drift > max_drift_threshold

    def assess_concentration_risk(
        self,
        weights: Dict[str, float],
        hhi_threshold: float = 0.35
    ) -> tuple[bool, str]:
        """
        Assess concentration risk of allocation.

        Args:
            weights: Portfolio weights
            hhi_threshold: Maximum acceptable HHI

        Returns:
            Tuple of (has_concentration_risk, explanation)
        """
        hhi = self.calculate_concentration(weights)

        if hhi > hhi_threshold:
            largest_weight = max(weights.values())
            largest_strategy = max(weights, key=weights.get)
            return True, f"High concentration: {largest_strategy} = {largest_weight:.1%} (HHI={hhi:.2f})"

        return False, f"Concentration acceptable (HHI={hhi:.2f})"

    def generate_snapshot(self) -> Optional[AllocationSnapshot]:
        """
        Generate allocation monitoring snapshot.

        Returns:
            AllocationSnapshot with current state
        """
        # Get allocations
        actual = self.get_current_allocation()
        recommended = self.get_recommended_allocation()

        if actual is None or recommended is None:
            logger.error("Failed to get allocation data")
            return None

        # Calculate metrics
        drift_pcts = self.calculate_drift(actual, recommended)
        max_drift = max(drift_pcts.values())
        hhi = self.calculate_concentration(actual)

        # Assess needs
        rebalance_needed = self.assess_rebalance_need(drift_pcts)
        has_concentration, conc_msg = self.assess_concentration_risk(actual)

        # Determine alert level and message
        alert_level = AlertLevel.INFO
        alert_messages = []

        if has_concentration:
            alert_level = AlertLevel.WARNING
            alert_messages.append(conc_msg)

        if max_drift > 5.0:
            alert_level = AlertLevel.CRITICAL
            alert_messages.append(f"CRITICAL: Max drift {max_drift:.1f}% exceeds 5% threshold")
        elif rebalance_needed:
            if alert_level == AlertLevel.INFO:
                alert_level = AlertLevel.WARNING
            alert_messages.append(f"Rebalancing recommended - max drift {max_drift:.1f}%")

        alert_message = " | ".join(alert_messages) if alert_messages else "Allocation within normal parameters"

        # Drift breakdown
        logger.info(f"Allocation Snapshot ({datetime.now().isoformat()})")
        logger.info(f"  Drift (pct): {drift_pcts}")
        logger.info(f"  Max drift: {max_drift:.2f}%")
        logger.info(f"  Concentration (HHI): {hhi:.3f}")
        logger.info(f"  Alert: {alert_level.value} - {alert_message}")

        return AllocationSnapshot(
            timestamp=datetime.now(),
            actual_weights=actual,
            recommended_weights=recommended,
            drift_pcts=drift_pcts,
            max_drift=max_drift,
            concentration_herfindahl=hhi,
            rebalance_needed=rebalance_needed,
            alert_level=alert_level,
            alert_message=alert_message
        )

    def record_snapshot(self, snapshot: AllocationSnapshot):
        """Record snapshot to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO allocation_history
                    (timestamp, actual_weights, recommended_weights, drift_pcts, max_drift,
                     concentration_herfindahl, rebalance_needed, alert_level, alert_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    snapshot.timestamp.isoformat(),
                    json.dumps(snapshot.actual_weights),
                    json.dumps(snapshot.recommended_weights),
                    json.dumps(snapshot.drift_pcts),
                    snapshot.max_drift,
                    snapshot.concentration_herfindahl,
                    snapshot.rebalance_needed,
                    snapshot.alert_level.value,
                    snapshot.alert_message
                ))
                conn.commit()
                logger.debug("Snapshot recorded to database")
        except Exception as e:
            logger.error(f"Failed to record snapshot: {str(e)}")

    def record_rebalancing_event(
        self,
        old_weights: Dict[str, float],
        new_weights: Dict[str, float],
        trigger_reason: str,
        transaction_costs: Optional[float] = None
    ):
        """Record rebalancing event"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO rebalancing_events
                    (timestamp, trigger_reason, old_weights, new_weights, transaction_costs, alert_level)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    trigger_reason,
                    json.dumps(old_weights),
                    json.dumps(new_weights),
                    transaction_costs,
                    "INFO"
                ))
                conn.commit()
                logger.info(f"Rebalancing event recorded: {trigger_reason}")
        except Exception as e:
            logger.error(f"Failed to record rebalancing event: {str(e)}")

    def get_allocation_history(self, hours: int = 24) -> List[AllocationSnapshot]:
        """
        Get allocation history for the past N hours.

        Args:
            hours: Number of hours to look back

        Returns:
            List of AllocationSnapshot objects
        """
        try:
            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM allocation_history
                    WHERE timestamp > ?
                    ORDER BY timestamp DESC
                """, (cutoff_time,))

                snapshots = []
                for row in cursor.fetchall():
                    snapshots.append(AllocationSnapshot(
                        timestamp=datetime.fromisoformat(row["timestamp"]),
                        actual_weights=json.loads(row["actual_weights"]),
                        recommended_weights=json.loads(row["recommended_weights"]),
                        drift_pcts=json.loads(row["drift_pcts"]),
                        max_drift=row["max_drift"],
                        concentration_herfindahl=row["concentration_herfindahl"],
                        rebalance_needed=bool(row["rebalance_needed"]),
                        alert_level=AlertLevel[row["alert_level"]],
                        alert_message=row["alert_message"]
                    ))

                return snapshots

        except Exception as e:
            logger.error(f"Failed to get allocation history: {str(e)}")
            return []


async def monitor_loop(monitor: AllocationMonitor, check_interval: int = 300):
    """
    Main monitoring loop.

    Args:
        monitor: AllocationMonitor instance
        check_interval: Check interval in seconds (default 5 minutes)
    """
    logger.info(f"Starting allocation monitor (check interval: {check_interval}s)")

    while True:
        try:
            snapshot = monitor.generate_snapshot()
            if snapshot:
                monitor.record_snapshot(snapshot)

                # Alert on critical conditions
                if snapshot.alert_level == AlertLevel.CRITICAL:
                    logger.critical(f"ALLOCATION ALERT: {snapshot.alert_message}")
                    # TODO: Send webhook/email/Slack alert

        except Exception as e:
            logger.error(f"Monitor loop error: {str(e)}")

        await asyncio.sleep(check_interval)


if __name__ == "__main__":
    monitor = AllocationMonitor()

    # Run single snapshot for testing
    snapshot = monitor.generate_snapshot()
    if snapshot:
        monitor.record_snapshot(snapshot)
        print(f"\nSnapshot recorded: {snapshot.timestamp}")
        print(f"  Actual: {snapshot.actual_weights}")
        print(f"  Recommended: {snapshot.recommended_weights}")
        print(f"  Max Drift: {snapshot.max_drift:.2f}%")
        print(f"  HHI: {snapshot.concentration_herfindahl:.3f}")
        print(f"  Alert: {snapshot.alert_level.value} - {snapshot.alert_message}")
