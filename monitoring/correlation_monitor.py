"""
Portfolio Correlation Monitor

Monitors correlation structure between strategies in real-time.
Detects changes in correlation, clustering, and diversification breakdown.
"""

import os
import logging
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

import numpy as np
import requests
from scipy.stats import spearmanr, pearsonr

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CorrelationAlertLevel(Enum):
    """Alert levels for correlation changes"""
    NORMAL = "NORMAL"
    ELEVATED = "ELEVATED"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class CorrelationSnapshot:
    """Snapshot of correlation matrix and diversification metrics"""
    timestamp: datetime
    correlation_matrix: np.ndarray
    strategy_names: List[str]
    mean_correlation: float
    max_correlation: float
    min_correlation: float
    diversification_ratio: float
    clustering_strength: float
    alert_level: CorrelationAlertLevel
    alert_message: str


class CorrelationMonitor:
    """Monitor portfolio correlation structure"""

    # Reference correlation matrix (from portfolio service)
    REFERENCE_CORRELATION = {
        "MLB": {"MLB": 1.0, "Crypto": 0.08, "Earnings": 0.15, "AI": 0.12, "Econ": 0.10},
        "Crypto": {"MLB": 0.08, "Crypto": 1.0, "Earnings": 0.35, "AI": 0.45, "Econ": 0.05},
        "Earnings": {"MLB": 0.15, "Crypto": 0.35, "Earnings": 1.0, "AI": 0.75, "Econ": 0.20},
        "AI": {"MLB": 0.12, "Crypto": 0.45, "Earnings": 0.75, "AI": 1.0, "Econ": 0.15},
        "Econ": {"MLB": 0.10, "Crypto": 0.05, "Earnings": 0.20, "AI": 0.15, "Econ": 1.0},
    }

    def __init__(self, portfolio_api_url: str = "http://localhost:8001"):
        """
        Initialize correlation monitor.

        Args:
            portfolio_api_url: URL to portfolio engine API
        """
        self.portfolio_api_url = portfolio_api_url
        self.db_path = os.getenv("DATABASE_PATH", "/app/data/correlation_history.db")
        self.price_data_path = os.getenv("PRICE_DATA_PATH", "/app/data/strategy_returns.json")
        self._initialize_db()

    def _initialize_db(self):
        """Initialize SQLite database for correlation history"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Correlation history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS correlation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    strategy_names JSON NOT NULL,
                    correlation_matrix JSON NOT NULL,
                    mean_correlation REAL NOT NULL,
                    max_correlation REAL NOT NULL,
                    min_correlation REAL NOT NULL,
                    diversification_ratio REAL NOT NULL,
                    clustering_strength REAL NOT NULL,
                    alert_level TEXT NOT NULL,
                    alert_message TEXT
                )
            """)

            # Correlation breakdown events
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS correlation_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    event_type TEXT NOT NULL,
                    correlation_pair TEXT NOT NULL,
                    old_correlation REAL,
                    new_correlation REAL,
                    change_pct REAL NOT NULL,
                    alert_level TEXT NOT NULL
                )
            """)

            conn.commit()

    def get_strategy_returns(self, days: int = 252) -> Optional[Dict[str, List[float]]]:
        """
        Get historical strategy returns for correlation calculation.

        This would typically pull from your data warehouse, trading platform, or
        historical data service.

        Args:
            days: Number of days of historical data

        Returns:
            Dictionary of {strategy_name: [returns]}
        """
        try:
            # Placeholder implementation
            # In production, pull from database, data warehouse, or API
            if os.path.exists(self.price_data_path):
                with open(self.price_data_path) as f:
                    return json.load(f)

            # Generate sample data for testing
            np.random.seed(42)
            strategies = ["MLB", "Crypto", "Earnings", "AI", "Econ"]
            returns = {}

            for strategy in strategies:
                # Generate correlated returns
                drift = 0.0001 * days / 252
                vol = np.random.uniform(0.08, 0.40) / np.sqrt(252)
                returns[strategy] = np.random.normal(drift, vol, days).tolist()

            return returns

        except Exception as e:
            logger.error(f"Failed to get strategy returns: {str(e)}")
            return None

    def calculate_correlation_matrix(
        self,
        returns: Dict[str, List[float]]
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Calculate correlation matrix from returns data.

        Args:
            returns: Dictionary of {strategy_name: [returns]}

        Returns:
            Tuple of (correlation_matrix, strategy_names)
        """
        strategy_names = list(returns.keys())
        n = len(strategy_names)

        corr_matrix = np.zeros((n, n))

        for i, strat_i in enumerate(strategy_names):
            for j, strat_j in enumerate(strategy_names):
                if i == j:
                    corr_matrix[i, j] = 1.0
                elif i < j:
                    # Calculate Pearson correlation
                    corr, _ = pearsonr(returns[strat_i], returns[strat_j])
                    corr_matrix[i, j] = corr
                    corr_matrix[j, i] = corr

        return corr_matrix, strategy_names

    def calculate_mean_correlation(self, corr_matrix: np.ndarray) -> float:
        """
        Calculate mean correlation (excluding diagonal).

        Args:
            corr_matrix: Correlation matrix

        Returns:
            Mean correlation coefficient
        """
        n = corr_matrix.shape[0]
        # Extract upper triangle excluding diagonal
        upper_triangle = corr_matrix[np.triu_indices(n, k=1)]
        return np.mean(upper_triangle)

    def calculate_diversification_ratio(
        self,
        weights: np.ndarray,
        vols: np.ndarray,
        corr_matrix: np.ndarray
    ) -> float:
        """
        Calculate diversification ratio.

        DR = (sum of weighted vols) / (portfolio vol)

        Higher is better (more diversified).

        Args:
            weights: Portfolio weights
            vols: Asset volatilities
            corr_matrix: Correlation matrix

        Returns:
            Diversification ratio
        """
        weighted_vol = np.sum(weights * vols)

        # Covariance matrix
        cov_matrix = np.outer(vols, vols) * corr_matrix
        portfolio_vol = np.sqrt(weights @ cov_matrix @ weights)

        if portfolio_vol > 1e-8:
            return weighted_vol / portfolio_vol
        else:
            return 1.0

    def calculate_clustering_strength(
        self,
        corr_matrix: np.ndarray,
        reference_corr: np.ndarray
    ) -> float:
        """
        Calculate how much correlations have increased (clustering).

        Measures deviation from reference correlation structure.

        Args:
            corr_matrix: Current correlation matrix
            reference_corr: Reference/expected correlation matrix

        Returns:
            Clustering strength (0 = no clustering, 1 = full clustering)
        """
        n = corr_matrix.shape[0]

        # Extract upper triangles
        current = corr_matrix[np.triu_indices(n, k=1)]
        reference = reference_corr[np.triu_indices(n, k=1)]

        # Calculate increase in correlation
        correlation_increases = np.maximum(current - reference, 0)
        clustering = np.mean(correlation_increases)

        return float(clustering)

    def detect_correlation_spikes(
        self,
        current_corr: np.ndarray,
        previous_corr: Optional[np.ndarray] = None,
        threshold: float = 0.10
    ) -> List[Tuple[str, str, float, float]]:
        """
        Detect significant correlation changes.

        Args:
            current_corr: Current correlation matrix
            previous_corr: Previous correlation matrix
            threshold: Change threshold to trigger alert

        Returns:
            List of (strategy1, strategy2, old_corr, new_corr) tuples
        """
        if previous_corr is None:
            previous_corr = self._reference_to_array()

        spikes = []
        n = current_corr.shape[0]

        for i in range(n):
            for j in range(i + 1, n):
                change = abs(current_corr[i, j] - previous_corr[i, j])
                if change > threshold:
                    spikes.append((
                        f"Strategy {i}",
                        f"Strategy {j}",
                        float(previous_corr[i, j]),
                        float(current_corr[i, j])
                    ))

        return spikes

    def _reference_to_array(self) -> np.ndarray:
        """Convert reference correlation dict to numpy array"""
        strategies = ["MLB", "Crypto", "Earnings", "AI", "Econ"]
        n = len(strategies)
        corr = np.zeros((n, n))

        for i, strat_i in enumerate(strategies):
            for j, strat_j in enumerate(strategies):
                corr[i, j] = self.REFERENCE_CORRELATION[strat_i][strat_j]

        return corr

    def assess_correlation_health(
        self,
        mean_corr: float,
        clustering: float,
        diversification_ratio: float
    ) -> Tuple[CorrelationAlertLevel, str]:
        """
        Assess overall correlation health.

        Args:
            mean_corr: Mean correlation
            clustering: Clustering strength (correlation increase)
            diversification_ratio: Diversification ratio

        Returns:
            Tuple of (alert_level, message)
        """
        messages = []
        alert_level = CorrelationAlertLevel.NORMAL

        # Check clustering
        if clustering > 0.20:
            alert_level = CorrelationAlertLevel.CRITICAL
            messages.append(f"CRITICAL: Severe correlation clustering (+{clustering:.1%})")
        elif clustering > 0.10:
            alert_level = CorrelationAlertLevel.HIGH
            messages.append(f"High correlation clustering (+{clustering:.1%})")
        elif clustering > 0.05:
            alert_level = CorrelationAlertLevel.ELEVATED
            messages.append(f"Moderate correlation clustering (+{clustering:.1%})")

        # Check mean correlation
        if mean_corr > 0.60:
            if alert_level == CorrelationAlertLevel.NORMAL:
                alert_level = CorrelationAlertLevel.ELEVATED
            messages.append(f"High mean correlation ({mean_corr:.2f})")

        # Check diversification ratio
        if diversification_ratio < 1.2:
            if alert_level in [CorrelationAlertLevel.NORMAL, CorrelationAlertLevel.ELEVATED]:
                alert_level = CorrelationAlertLevel.HIGH
            messages.append(f"Low diversification ratio ({diversification_ratio:.2f})")

        message = " | ".join(messages) if messages else "Correlation structure healthy"

        return alert_level, message

    def generate_snapshot(self) -> Optional[CorrelationSnapshot]:
        """
        Generate correlation monitoring snapshot.

        Returns:
            CorrelationSnapshot with current state
        """
        try:
            # Get returns data
            returns = self.get_strategy_returns()
            if returns is None:
                logger.error("Failed to get strategy returns")
                return None

            # Calculate correlation
            corr_matrix, strategy_names = self.calculate_correlation_matrix(returns)

            # Calculate metrics
            mean_corr = self.calculate_mean_correlation(corr_matrix)
            max_corr = np.max(corr_matrix[np.triu_indices(len(strategy_names), k=1)])
            min_corr = np.min(corr_matrix[np.triu_indices(len(strategy_names), k=1)])

            # Diversification (assume equal weights)
            weights = np.ones(len(strategy_names)) / len(strategy_names)
            vols = np.array([0.15, 0.35, 0.18, 0.25, 0.12])  # Example vols
            div_ratio = self.calculate_diversification_ratio(weights, vols, corr_matrix)

            # Clustering
            ref_corr = self._reference_to_array()
            clustering = self.calculate_clustering_strength(corr_matrix, ref_corr)

            # Health assessment
            alert_level, alert_msg = self.assess_correlation_health(
                mean_corr, clustering, div_ratio
            )

            logger.info(f"Correlation Snapshot ({datetime.now().isoformat()})")
            logger.info(f"  Mean Correlation: {mean_corr:.3f}")
            logger.info(f"  Max Correlation: {max_corr:.3f}")
            logger.info(f"  Clustering: {clustering:.3f}")
            logger.info(f"  Diversification Ratio: {div_ratio:.3f}")
            logger.info(f"  Alert: {alert_level.value} - {alert_msg}")

            return CorrelationSnapshot(
                timestamp=datetime.now(),
                correlation_matrix=corr_matrix,
                strategy_names=strategy_names,
                mean_correlation=float(mean_corr),
                max_correlation=float(max_corr),
                min_correlation=float(min_corr),
                diversification_ratio=float(div_ratio),
                clustering_strength=float(clustering),
                alert_level=alert_level,
                alert_message=alert_msg
            )

        except Exception as e:
            logger.error(f"Failed to generate snapshot: {str(e)}")
            return None

    def record_snapshot(self, snapshot: CorrelationSnapshot):
        """Record snapshot to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Convert matrix to JSON
                matrix_json = json.dumps(snapshot.correlation_matrix.tolist())

                cursor.execute("""
                    INSERT INTO correlation_history
                    (timestamp, strategy_names, correlation_matrix, mean_correlation,
                     max_correlation, min_correlation, diversification_ratio,
                     clustering_strength, alert_level, alert_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    snapshot.timestamp.isoformat(),
                    json.dumps(snapshot.strategy_names),
                    matrix_json,
                    snapshot.mean_correlation,
                    snapshot.max_correlation,
                    snapshot.min_correlation,
                    snapshot.diversification_ratio,
                    snapshot.clustering_strength,
                    snapshot.alert_level.value,
                    snapshot.alert_message
                ))
                conn.commit()
                logger.debug("Snapshot recorded to database")

        except Exception as e:
            logger.error(f"Failed to record snapshot: {str(e)}")

    def get_correlation_history(self, hours: int = 24) -> List[CorrelationSnapshot]:
        """
        Get correlation history for the past N hours.

        Args:
            hours: Number of hours to look back

        Returns:
            List of CorrelationSnapshot objects
        """
        try:
            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM correlation_history
                    WHERE timestamp > ?
                    ORDER BY timestamp DESC
                """, (cutoff_time,))

                snapshots = []
                for row in cursor.fetchall():
                    snapshots.append(CorrelationSnapshot(
                        timestamp=datetime.fromisoformat(row["timestamp"]),
                        correlation_matrix=np.array(json.loads(row["correlation_matrix"])),
                        strategy_names=json.loads(row["strategy_names"]),
                        mean_correlation=row["mean_correlation"],
                        max_correlation=row["max_correlation"],
                        min_correlation=row["min_correlation"],
                        diversification_ratio=row["diversification_ratio"],
                        clustering_strength=row["clustering_strength"],
                        alert_level=CorrelationAlertLevel[row["alert_level"]],
                        alert_message=row["alert_message"]
                    ))

                return snapshots

        except Exception as e:
            logger.error(f"Failed to get correlation history: {str(e)}")
            return []


if __name__ == "__main__":
    monitor = CorrelationMonitor()

    # Run single snapshot for testing
    snapshot = monitor.generate_snapshot()
    if snapshot:
        monitor.record_snapshot(snapshot)
        print(f"\nSnapshot recorded: {snapshot.timestamp}")
        print(f"  Mean Correlation: {snapshot.mean_correlation:.3f}")
        print(f"  Max Correlation: {snapshot.max_correlation:.3f}")
        print(f"  Clustering: {snapshot.clustering_strength:.3f}")
        print(f"  Diversification Ratio: {snapshot.diversification_ratio:.3f}")
        print(f"  Alert: {snapshot.alert_level.value} - {snapshot.alert_message}")
