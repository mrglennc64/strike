"""Portfolio engine schemas - request/response models."""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class StrategyInput(BaseModel):
    """Input for a single strategy in simulation."""
    name: str = Field(..., description="Strategy name (MLB, Crypto, Earnings, AI, Econ)")
    expected_return: float = Field(..., gt=0, description="Expected annual return (%)")
    volatility: float = Field(..., gt=0, description="Annual volatility (%)")
    sharpe_ratio: float = Field(..., description="Sharpe ratio of the strategy")
    max_drawdown: float = Field(..., ge=-1, le=0, description="Max drawdown (-1 to 0)")
    weight: float = Field(default=0.2, ge=0, le=1, description="Initial weight in portfolio")


class PortfolioSimulationRequest(BaseModel):
    """Request for Monte Carlo portfolio simulation."""
    strategies: List[StrategyInput] = Field(..., description="5 strategies to simulate")
    num_simulations: int = Field(default=1000, ge=100, le=10000, description="Number of Monte Carlo runs")
    time_horizon_days: int = Field(default=252, ge=1, le=1260, description="Trading days to simulate")
    initial_capital: float = Field(default=100000, gt=0, description="Starting capital")
    rebalance_frequency: Optional[str] = Field(default="monthly", description="Rebalance frequency: daily, weekly, monthly, quarterly")


class EquityCurvePoint(BaseModel):
    """Single point on equity curve."""
    day: int
    percentile_5: float
    percentile_25: float
    median: float
    percentile_75: float
    percentile_95: float


class DrawdownPoint(BaseModel):
    """Single point in drawdown distribution."""
    drawdown: float = Field(..., description="Drawdown percentage (0 to 1)")
    frequency: int = Field(..., description="How many paths hit this drawdown")


class PortfolioSimulationResult(BaseModel):
    """Result of Monte Carlo simulation."""
    num_simulations: int
    time_horizon_days: int
    initial_capital: float
    strategies: List[StrategyInput]

    # Overall statistics
    final_capital_mean: float
    final_capital_median: float
    final_capital_std: float
    final_capital_min: float
    final_capital_max: float

    # Return statistics
    total_return_mean: float = Field(..., description="Mean total return (%)")
    total_return_median: float
    total_return_std: float

    # Risk statistics
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_mean: float
    max_drawdown_worst: float
    max_drawdown_percentile_95: float
    recovery_time_mean: int = Field(..., description="Mean days to recovery from max drawdown")

    # Win metrics
    probability_profitable: float = Field(..., description="% of simulations with positive return")
    probability_double: float = Field(..., description="% of simulations with 2x return")

    # Equity curve (path statistics)
    equity_curve: List[EquityCurvePoint]

    # Drawdown distribution
    drawdown_distribution: List[DrawdownPoint]

    # Correlation effects
    correlation_drag: float = Field(..., description="% return reduction from correlation vs optimal")
    diversification_ratio: float = Field(..., description="Ratio of weighted avg vol to portfolio vol")


class AllocationRequest(BaseModel):
    """Request for optimal portfolio allocation."""
    strategies: List[StrategyInput] = Field(..., description="Strategy metrics")
    optimization_method: str = Field(default="kelly", description="kelly, sharpe, min_variance, equal_weight")
    kelly_fraction: float = Field(default=0.25, ge=0.01, le=1.0, description="Kelly fraction to use if kelly method")


class AllocationResult(BaseModel):
    """Optimal portfolio weights and allocation metrics."""
    optimization_method: str
    optimal_weights: Dict[str, float] = Field(..., description="Strategy name -> weight (0-1)")
    kelly_fractions: Dict[str, float] = Field(..., description="Kelly fractions per strategy")

    # Portfolio metrics from allocation
    portfolio_expected_return: float
    portfolio_volatility: float
    portfolio_sharpe_ratio: float

    # Risk metrics
    largest_weight: float
    concentration_herfindahl: float = Field(..., description="HHI concentration index (0.2-1.0)")

    # Validation
    weights_sum: float = Field(..., ge=0.99, le=1.01, description="Sum of weights (should be ~1.0)")
    is_valid: bool = Field(..., description="Are weights valid and normalized")


class RegimeState(BaseModel):
    """Current market regime for weight adjustment."""
    regime_name: str = Field(..., description="Low Vol, Normal, High Vol, Stress")
    vix_level: float = Field(..., ge=0, description="Current VIX level")
    vix_percentile: float = Field(..., ge=0, le=100, description="VIX historical percentile")

    funding_rate: float = Field(..., description="Crypto funding rate (%)")
    funding_regime: str = Field(..., description="normal, elevated, extreme")

    sentiment_score: float = Field(..., ge=-1, le=1, description="Market sentiment -1 to +1")

    # Regime-adjusted weights
    regime_adjusted_weights: Dict[str, float] = Field(..., description="Weights adjusted for current regime")
    regime_adjustment_factor: Dict[str, float] = Field(..., description="Multiplier applied to base weights")

    # Recommendations
    recommended_action: str = Field(..., description="Hold, Reduce Risk, Increase Risk, Rebalance")
    explanation: str = Field(..., description="Why we recommend this action")


class RegimeRequest(BaseModel):
    """Request regime assessment and adjustment."""
    current_vix: float = Field(..., ge=0, description="Current VIX level")
    vix_percentile_30d: float = Field(..., ge=0, le=100, description="VIX percentile over 30 days")

    crypto_funding_rate: float = Field(..., description="Current crypto funding rate (%)")

    market_sentiment: float = Field(..., ge=-1, le=1, description="Market sentiment score")

    base_weights: Dict[str, float] = Field(..., description="Current allocation weights")
    strategies: List[StrategyInput] = Field(..., description="Strategy info for context")
