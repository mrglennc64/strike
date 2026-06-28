"""
Multi-Vertical Portfolio Backtesting Engine

This module orchestrates comprehensive portfolio backtesting across 5 trading verticals:
1. MLB Strikeout Edge
2. Earnings Surprise Events
3. Crypto (BTC/ETH)
4. AI Releases
5. Economics (CPI/Fed)

Features:
- Data loading from each vertical with historical trade records
- Metric extraction (win rate, Sharpe, max drawdown, etc)
- 3 allocation strategies (equal weight, hybrid Kelly, regime-controlled)
- 1000 Monte Carlo simulations per strategy
- Comprehensive reporting and visualization
- Regime controller validation
"""

from .vertical_data_loader import (
    VerticalDataLoader,
    MLBDataLoader,
    EarningsDataLoader,
    CryptoDataLoader,
    AIReleasesDataLoader,
    EconomicsDataLoader,
    VerticalTradeRecord,
    VerticalMetrics,
)

from .allocation_strategies import (
    AllocationStrategy,
    EqualWeightStrategy,
    HybridKellyRiskParity,
    RegimeControlledAllocation,
)

from .backtest_orchestrator import BacktestOrchestrator

__all__ = [
    "VerticalDataLoader",
    "MLBDataLoader",
    "EarningsDataLoader",
    "CryptoDataLoader",
    "AIReleasesDataLoader",
    "EconomicsDataLoader",
    "VerticalTradeRecord",
    "VerticalMetrics",
    "AllocationStrategy",
    "EqualWeightStrategy",
    "HybridKellyRiskParity",
    "RegimeControlledAllocation",
    "BacktestOrchestrator",
]
