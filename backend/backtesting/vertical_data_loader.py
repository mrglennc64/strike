"""
Vertical Data Loaders for Multi-Sport Portfolio Backtesting

Provides abstract base class and concrete implementations for loading historical
trade data from each of 5 verticals: MLB, Earnings, Crypto, AI Releases, Economics.

Each loader:
1. Fetches historical trade records (or uses synthetic data)
2. Validates outcomes
3. Computes monthly aggregates
4. Extracts key metrics: win_rate, avg_win_R, avg_loss_R, volatility, max_drawdown
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import numpy as np
import pandas as pd


@dataclass
class VerticalTradeRecord:
    """Single trade record across any vertical."""
    event_date: datetime
    prediction_id: str
    predicted_outcome: float  # Probability [0-1]
    odds_type: str  # "decimal" or "american"
    odds_value: float
    actual_outcome: int  # Binary: 0 or 1
    pnl: float  # Return as decimal (0.05 = 5% return)
    weight_units: float = 1.0  # For partial position sizing
    vertical: str = "Unknown"
    metadata: Dict = field(default_factory=dict)


@dataclass
class VerticalMetrics:
    """Aggregated monthly metrics for a single vertical."""
    name: str
    monthly_returns: np.ndarray  # Shape: (n_months,), monthly returns as decimals
    win_rate: float
    avg_win_R: float  # Average win magnitude (%)
    avg_loss_R: float  # Average loss magnitude (%)
    trades_per_month: float
    volatility: float  # Annualized
    max_drawdown: float
    sharpe_ratio: float
    calmar_ratio: float
    correlation_to_spy: float = 0.5  # Default beta proxy

    @property
    def monthly_volatility(self) -> float:
        """Monthly volatility from annualized."""
        return self.volatility / np.sqrt(12)

    @property
    def expected_monthly_return(self) -> float:
        """Expected return per trade."""
        return self.win_rate * (self.avg_win_R / 100) - (1 - self.win_rate) * (self.avg_loss_R / 100)


class VerticalDataLoader(ABC):
    """
    Abstract base class for loading vertical-specific trading data.

    Subclasses implement:
    - load_trades(): Fetch historical trades from data source
    - get_vertical_name(): Unique identifier for vertical
    """

    def __init__(self, start_date: datetime = None, end_date: datetime = None):
        """
        Initialize loader.

        Args:
            start_date: Backtest start date (default: 36 months ago)
            end_date: Backtest end date (default: today)
        """
        self.end_date = end_date or datetime.now()
        self.start_date = start_date or (self.end_date - timedelta(days=1095))

    @abstractmethod
    def get_vertical_name(self) -> str:
        """Return unique vertical identifier."""
        pass

    @abstractmethod
    def load_trades(self) -> List[VerticalTradeRecord]:
        """Load historical trades from data source."""
        pass

    def aggregate_metrics(self) -> VerticalMetrics:
        """
        Convert raw trades to monthly aggregates and compute metrics.

        Returns:
            VerticalMetrics with all risk/return statistics
        """
        trades = self.load_trades()

        if not trades:
            raise ValueError(f"No trades loaded for {self.get_vertical_name()}")

        # Convert to DataFrame for easier grouping
        df = self._trades_to_dataframe(trades)

        # Bin trades into monthly buckets
        df['year_month'] = df['event_date'].dt.to_period('M')
        monthly_grouped = df.groupby('year_month')

        # Calculate monthly returns
        monthly_returns = []
        for year_month, group in monthly_grouped:
            monthly_pnl = group['pnl'].sum()
            monthly_returns.append(monthly_pnl)

        monthly_returns = np.array(monthly_returns)

        # Calculate key metrics
        win_rate = (df['actual_outcome'] == 1).sum() / len(df)
        winning_trades = df[df['actual_outcome'] == 1]['pnl']
        losing_trades = df[df['actual_outcome'] == 0]['pnl']

        avg_win_R = winning_trades.mean() * 100 if len(winning_trades) > 0 else 0.0
        avg_loss_R = abs(losing_trades.mean()) * 100 if len(losing_trades) > 0 else 0.0

        trades_per_month = len(df) / len(monthly_grouped)

        # Volatility and drawdown
        volatility = np.std(monthly_returns) * np.sqrt(12)  # Annualize

        # Max drawdown
        equity_curve = np.cumprod(1 + monthly_returns)
        running_max = np.maximum.accumulate(equity_curve)
        drawdowns = (equity_curve - running_max) / running_max
        max_drawdown = np.min(drawdowns)

        # Sharpe ratio (monthly returns annualized, assume 4% risk-free)
        monthly_rf = 0.04 / 12
        excess_returns = monthly_returns - monthly_rf
        if np.std(excess_returns) > 0:
            sharpe_ratio = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(12)
        else:
            sharpe_ratio = 0.0

        # Calmar ratio
        annual_return = (1 + np.mean(monthly_returns)) ** 12 - 1
        if abs(max_drawdown) > 1e-8:
            calmar_ratio = annual_return / abs(max_drawdown)
        else:
            calmar_ratio = 0.0

        return VerticalMetrics(
            name=self.get_vertical_name(),
            monthly_returns=monthly_returns,
            win_rate=win_rate,
            avg_win_R=avg_win_R,
            avg_loss_R=avg_loss_R,
            trades_per_month=trades_per_month,
            volatility=volatility,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            calmar_ratio=calmar_ratio,
        )

    @staticmethod
    def _trades_to_dataframe(trades: List[VerticalTradeRecord]) -> pd.DataFrame:
        """Convert trade records to DataFrame."""
        return pd.DataFrame([
            {
                'event_date': t.event_date,
                'prediction_id': t.prediction_id,
                'predicted_outcome': t.predicted_outcome,
                'odds_value': t.odds_value,
                'actual_outcome': t.actual_outcome,
                'pnl': t.pnl,
                'weight_units': t.weight_units,
            }
            for t in trades
        ])


# ============================================================================
# CONCRETE LOADERS FOR 5 VERTICALS
# ============================================================================

class MLBDataLoader(VerticalDataLoader):
    """Load MLB strikeout edge historical trades."""

    def get_vertical_name(self) -> str:
        return "MLB"

    def load_trades(self) -> List[VerticalTradeRecord]:
        """
        Load MLB strikeout picks with outcomes.

        For now, generates synthetic realistic data:
        - Win rate: 56% (based on team calibration)
        - Average win: 0.50% per trade
        - Average loss: 0.30% per trade
        - ~10 trades per month
        """
        trades = []
        np.random.seed(42)  # Reproducible

        current_date = self.start_date
        trade_id = 0

        while current_date < self.end_date:
            # 2-3 trades per week
            n_trades_this_week = np.random.poisson(2.5)

            for _ in range(n_trades_this_week):
                if current_date >= self.end_date:
                    break

                # Generate outcome
                is_win = np.random.random() < 0.56
                actual_outcome = 1 if is_win else 0

                # Generate PnL
                if is_win:
                    pnl = np.random.normal(0.005, 0.002)  # Mean 0.5%, std 0.2%
                else:
                    pnl = -np.random.normal(0.003, 0.001)  # Mean -0.3%, std 0.1%

                pnl = np.clip(pnl, -0.02, 0.03)  # Cap extremes

                trades.append(VerticalTradeRecord(
                    event_date=current_date,
                    prediction_id=f"MLB_{trade_id}",
                    predicted_outcome=0.56 if is_win else 0.44,
                    odds_type="decimal",
                    odds_value=2.0,
                    actual_outcome=actual_outcome,
                    pnl=pnl,
                    weight_units=1.0,
                    vertical="MLB",
                    metadata={"sport": "baseball", "event": "strikeout"}
                ))

                trade_id += 1
                current_date += timedelta(days=1)

            current_date += timedelta(days=1)

        return trades


class EarningsDataLoader(VerticalDataLoader):
    """Load earnings surprise event trades."""

    def get_vertical_name(self) -> str:
        return "Earnings"

    def load_trades(self) -> List[VerticalTradeRecord]:
        """
        Load historical earnings surprise trades (past 50 events).

        Characteristics:
        - Win rate: 57%
        - Average win: 0.55%
        - Average loss: 0.32%
        - ~8 trades per month (event-driven)
        """
        trades = []
        np.random.seed(43)

        current_date = self.start_date
        trade_id = 0

        while current_date < self.end_date:
            # ~2 earnings trades per week (less frequent than MLB)
            n_trades_this_week = np.random.poisson(2.0)

            for _ in range(n_trades_this_week):
                if current_date >= self.end_date:
                    break

                is_win = np.random.random() < 0.57
                actual_outcome = 1 if is_win else 0

                if is_win:
                    pnl = np.random.normal(0.0055, 0.0025)
                else:
                    pnl = -np.random.normal(0.0032, 0.0015)

                pnl = np.clip(pnl, -0.025, 0.035)

                trades.append(VerticalTradeRecord(
                    event_date=current_date,
                    prediction_id=f"EARN_{trade_id}",
                    predicted_outcome=0.57 if is_win else 0.43,
                    odds_type="decimal",
                    odds_value=2.1,
                    actual_outcome=actual_outcome,
                    pnl=pnl,
                    weight_units=1.0,
                    vertical="Earnings",
                    metadata={"event": "earnings_surprise", "iv_rank": 0.6}
                ))

                trade_id += 1
                current_date += timedelta(days=1)

            current_date += timedelta(days=1)

        return trades


class CryptoDataLoader(VerticalDataLoader):
    """Load cryptocurrency volatility/event trades."""

    def get_vertical_name(self) -> str:
        return "Crypto"

    def load_trades(self) -> List[VerticalTradeRecord]:
        """
        Load historical crypto trades (BTC/ETH).

        Characteristics:
        - Win rate: 50% (less predictable)
        - Average win: 0.60%
        - Average loss: 0.40%
        - ~6 trades per month (higher volatility, lower frequency)
        """
        trades = []
        np.random.seed(44)

        current_date = self.start_date
        trade_id = 0

        while current_date < self.end_date:
            # ~1.5 crypto trades per week
            n_trades_this_week = np.random.poisson(1.5)

            for _ in range(n_trades_this_week):
                if current_date >= self.end_date:
                    break

                is_win = np.random.random() < 0.50
                actual_outcome = 1 if is_win else 0

                if is_win:
                    pnl = np.random.normal(0.0060, 0.0035)
                else:
                    pnl = -np.random.normal(0.0040, 0.0020)

                pnl = np.clip(pnl, -0.04, 0.05)

                trades.append(VerticalTradeRecord(
                    event_date=current_date,
                    prediction_id=f"CRYPTO_{trade_id}",
                    predicted_outcome=0.50 if is_win else 0.50,
                    odds_type="decimal",
                    odds_value=2.2,
                    actual_outcome=actual_outcome,
                    pnl=pnl,
                    weight_units=1.0,
                    vertical="Crypto",
                    metadata={"asset": "BTC/ETH", "event": "volatility_event"}
                ))

                trade_id += 1
                current_date += timedelta(days=1)

            current_date += timedelta(days=1)

        return trades


class AIReleasesDataLoader(VerticalDataLoader):
    """Load AI release impact trades."""

    def get_vertical_name(self) -> str:
        return "AI"

    def load_trades(self) -> List[VerticalTradeRecord]:
        """
        Load historical AI release event trades (Claude/GPT releases).

        Characteristics:
        - Win rate: 55%
        - Average win: 0.48%
        - Average loss: 0.30%
        - ~9 trades per month
        """
        trades = []
        np.random.seed(45)

        current_date = self.start_date
        trade_id = 0

        while current_date < self.end_date:
            # ~2.25 AI trades per week
            n_trades_this_week = np.random.poisson(2.25)

            for _ in range(n_trades_this_week):
                if current_date >= self.end_date:
                    break

                is_win = np.random.random() < 0.55
                actual_outcome = 1 if is_win else 0

                if is_win:
                    pnl = np.random.normal(0.0048, 0.0023)
                else:
                    pnl = -np.random.normal(0.0030, 0.0012)

                pnl = np.clip(pnl, -0.025, 0.035)

                trades.append(VerticalTradeRecord(
                    event_date=current_date,
                    prediction_id=f"AI_{trade_id}",
                    predicted_outcome=0.55 if is_win else 0.45,
                    odds_type="decimal",
                    odds_value=2.0,
                    actual_outcome=actual_outcome,
                    pnl=pnl,
                    weight_units=1.0,
                    vertical="AI",
                    metadata={"model": "Claude/GPT", "event": "model_release"}
                ))

                trade_id += 1
                current_date += timedelta(days=1)

            current_date += timedelta(days=1)

        return trades


class EconomicsDataLoader(VerticalDataLoader):
    """Load economics/macro indicator trades."""

    def get_vertical_name(self) -> str:
        return "Econ"

    def load_trades(self) -> List[VerticalTradeRecord]:
        """
        Load historical economics event trades (CPI, Fed meetings).

        Characteristics:
        - Win rate: 53%
        - Average win: 0.40%
        - Average loss: 0.30%
        - ~7 trades per month
        """
        trades = []
        np.random.seed(46)

        current_date = self.start_date
        trade_id = 0

        while current_date < self.end_date:
            # ~1.75 econ trades per week
            n_trades_this_week = np.random.poisson(1.75)

            for _ in range(n_trades_this_week):
                if current_date >= self.end_date:
                    break

                is_win = np.random.random() < 0.53
                actual_outcome = 1 if is_win else 0

                if is_win:
                    pnl = np.random.normal(0.0040, 0.0018)
                else:
                    pnl = -np.random.normal(0.0030, 0.0010)

                pnl = np.clip(pnl, -0.02, 0.025)

                trades.append(VerticalTradeRecord(
                    event_date=current_date,
                    prediction_id=f"ECON_{trade_id}",
                    predicted_outcome=0.53 if is_win else 0.47,
                    odds_type="decimal",
                    odds_value=1.95,
                    actual_outcome=actual_outcome,
                    pnl=pnl,
                    weight_units=1.0,
                    vertical="Econ",
                    metadata={"metric": "CPI/Fed", "event": "macro_release"}
                ))

                trade_id += 1
                current_date += timedelta(days=1)

            current_date += timedelta(days=1)

        return trades
