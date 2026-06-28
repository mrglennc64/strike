"""
Portfolio Allocation Strategies

Implements 3 allocation approaches for 5-vertical portfolio:

A) Equal Weight (baseline) - 20% each vertical
B) Hybrid Kelly + Risk Parity (improved) - Kelly sizing + volatility normalization
C) Regime-Controlled (optimized) - Adaptive weights based on market regime
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np
from .vertical_data_loader import VerticalMetrics


@dataclass
class RegimeIndicators:
    """Market regime detection signals."""
    vix_level: float = 15.0  # VIX level
    vix_trend: str = "normal"  # "rising", "falling", "normal"
    correlation_level: float = 0.35  # Average correlation
    market_momentum: str = "neutral"  # "risk_on", "risk_off", "neutral"
    credit_spreads: str = "tight"  # "tight", "wide", "extreme"

    def get_regime(self) -> str:
        """Infer overall market regime from indicators."""
        # Risk-off: High VIX, wide spreads, rising correlations
        if (self.vix_level > 25 or
            self.credit_spreads == "wide" or
            self.correlation_level > 0.50):
            return "risk_off"

        # Risk-on: Low VIX, tight spreads, low correlations, bullish momentum
        if (self.vix_level < 12 and
            self.credit_spreads == "tight" and
            self.correlation_level < 0.30 and
            self.market_momentum == "risk_on"):
            return "risk_on"

        return "normal"


class AllocationStrategy(ABC):
    """
    Abstract base class for portfolio allocation strategies.

    Each strategy implements calculate_weights() to return a dictionary
    mapping vertical names to portfolio weights.
    """

    @abstractmethod
    def calculate_weights(self,
                         verticals: List[VerticalMetrics],
                         regime: Optional[RegimeIndicators] = None) -> Dict[str, float]:
        """
        Calculate portfolio weights for given verticals.

        Args:
            verticals: List of VerticalMetrics for each vertical
            regime: Optional market regime indicators

        Returns:
            Dictionary mapping vertical name → weight (should sum to ~1.0)
        """
        pass

    def _validate_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Ensure weights sum to 1.0 and are non-negative."""
        total = sum(weights.values())
        if abs(total) < 1e-8:
            raise ValueError("Weights sum to zero")

        # Normalize to 1.0
        normalized = {k: v / total for k, v in weights.items()}

        # Ensure all non-negative
        for v in normalized.values():
            if v < -1e-8:
                raise ValueError(f"Negative weights not allowed: {normalized}")

        return normalized

    def _kelly_fraction(self,
                       win_rate: float,
                       avg_win: float,
                       avg_loss: float,
                       max_kelly: float = 0.25) -> float:
        """
        Calculate Kelly fraction for single strategy.

        Formula: f* = (p*b - q) / b
        Where:
          p = win_rate
          q = 1 - p
          b = avg_win / avg_loss (odds ratio)

        Then apply fractional Kelly (f/4 for safety).
        """
        if avg_loss <= 0 or avg_win <= 0:
            return 0.0

        q = 1 - win_rate
        b = avg_win / avg_loss

        # Avoid division by zero
        if b == 1:
            return 0.0

        kelly = (win_rate * b - q) / b

        # Fractional Kelly for safety (1/4 Kelly by default)
        fractional_kelly = kelly / 4

        # Bound to [0, max_kelly]
        return np.clip(fractional_kelly, 0, max_kelly)


class EqualWeightStrategy(AllocationStrategy):
    """
    Baseline strategy: equal 20% weight to each of 5 verticals.

    Provides simplicity and pure diversification benefit without
    trying to time or optimize allocations.
    """

    def calculate_weights(self,
                         verticals: List[VerticalMetrics],
                         regime: Optional[RegimeIndicators] = None) -> Dict[str, float]:
        """
        Return equal weights to all verticals.

        Args:
            verticals: List of VerticalMetrics (ignored for equal weight)
            regime: Ignored

        Returns:
            Dictionary with 20% weight to each of 5 verticals
        """
        n_verticals = len(verticals)
        equal_weight = 1.0 / n_verticals

        weights = {v.name: equal_weight for v in verticals}

        return self._validate_weights(weights)


class HybridKellyRiskParity(AllocationStrategy):
    """
    Hybrid strategy combining Kelly Criterion sizing with Risk Parity normalization.

    Algorithm:
    1. Calculate Kelly fraction for each vertical (based on win_rate, R-multiples)
    2. Normalize by volatility (risk parity - equal risk contribution)
    3. Rescale weights to sum to 1.0

    Rationale:
    - Kelly sizing captures edge quality
    - Risk parity prevents one volatile strategy from dominating
    - Combined: edge-aware + volatility-controlled allocation
    """

    def calculate_weights(self,
                         verticals: List[VerticalMetrics],
                         regime: Optional[RegimeIndicators] = None) -> Dict[str, float]:
        """
        Calculate weights using hybrid Kelly + risk parity.

        Args:
            verticals: List of VerticalMetrics
            regime: Ignored for this strategy

        Returns:
            Dictionary with Kelly-sized, risk-parity-normalized weights
        """
        weights = {}

        # Step 1: Calculate raw Kelly fractions
        kelly_fractions = {}
        for v in verticals:
            kelly = self._kelly_fraction(
                win_rate=v.win_rate,
                avg_win=v.avg_win_R,
                avg_loss=v.avg_loss_R,
                max_kelly=0.30
            )
            kelly_fractions[v.name] = kelly

        # Step 2: Normalize by volatility (risk parity)
        # Allocate based on inverse volatility (lower vol = higher weight)
        for v in verticals:
            kelly_val = kelly_fractions[v.name]

            # Risk parity: weight inversely proportional to volatility
            if v.volatility > 0:
                risk_parity_factor = 1.0 / v.volatility
            else:
                risk_parity_factor = 1.0

            # Combine: kelly * risk_parity normalization
            weights[v.name] = kelly_val * risk_parity_factor

        # Step 3: Normalize to sum to 1.0
        return self._validate_weights(weights)


class RegimeControlledAllocation(AllocationStrategy):
    """
    Regime-controlled strategy that adapts allocations to market conditions.

    The strategy maintains three playbooks:
    1. Risk-on allocation: Higher weights to growth verticals (Crypto, AI, Earnings)
    2. Risk-off allocation: Higher weights to defensive verticals (MLB, Econ)
    3. Normal allocation: Balanced, forward-looking weights

    Regime Detection:
    - VIX > 25 or credit spreads wide → Risk-off
    - VIX < 12 and bullish momentum → Risk-on
    - Otherwise → Normal

    This allows the portfolio to automatically reduce drawdowns during crises
    by shifting to less correlated, defensive strategies.
    """

    # Risk-on playbook: emphasize growth
    RISK_ON_TEMPLATE = {
        "MLB": 0.10,      # Defensive
        "Econ": 0.10,     # Defensive
        "Earnings": 0.25, # Growth-ish
        "AI": 0.30,       # High-growth
        "Crypto": 0.25    # High-growth
    }

    # Risk-off playbook: defensive
    RISK_OFF_TEMPLATE = {
        "MLB": 0.35,      # Defensive, uncorrelated
        "Econ": 0.30,     # Defensive, macro-hedging
        "Earnings": 0.15, # Less growth-oriented
        "AI": 0.10,       # Risky
        "Crypto": 0.10    # Very risky
    }

    # Normal playbook: balanced
    NORMAL_TEMPLATE = {
        "MLB": 0.20,      # Balanced
        "Econ": 0.20,     # Balanced
        "Earnings": 0.25, # Slight growth tilt
        "AI": 0.20,       # Moderate growth
        "Crypto": 0.15    # Moderate risk
    }

    def calculate_weights(self,
                         verticals: List[VerticalMetrics],
                         regime: Optional[RegimeIndicators] = None) -> Dict[str, float]:
        """
        Calculate weights based on market regime.

        Args:
            verticals: List of VerticalMetrics (used for Kelly overlay)
            regime: Market regime indicators

        Returns:
            Dictionary with regime-adaptive weights
        """
        # Default to normal regime if not provided
        if regime is None:
            regime = RegimeIndicators()

        detected_regime = regime.get_regime()

        # Select template based on regime
        if detected_regime == "risk_on":
            template = self.RISK_ON_TEMPLATE
        elif detected_regime == "risk_off":
            template = self.RISK_OFF_TEMPLATE
        else:  # normal
            template = self.NORMAL_TEMPLATE

        # Convert template to weights dict
        weights = {}
        for v in verticals:
            # Get base weight from template
            base_weight = template.get(v.name, 1.0 / len(verticals))

            # Optional: apply light Kelly overlay (10% of allocation variance)
            kelly_adjustment = 0.0
            if v.win_rate > 0.52:  # Positive edge
                kelly_adjustment = self._kelly_fraction(
                    win_rate=v.win_rate,
                    avg_win=v.avg_win_R,
                    avg_loss=v.avg_loss_R,
                    max_kelly=0.05  # Small Kelly adjustment
                )

            # Blend base weight with Kelly adjustment
            final_weight = base_weight * (1 + kelly_adjustment)
            weights[v.name] = final_weight

        return self._validate_weights(weights)


def create_regime_indicators_from_market_data(
    vix: float = 15.0,
    spread_bps: int = 150,
    correlation: float = 0.35,
    sp500_return_30d: float = 0.01
) -> RegimeIndicators:
    """
    Create RegimeIndicators from live market data.

    Args:
        vix: Current VIX level
        spread_bps: Credit spread (high yield OAS) in basis points
        correlation: Average correlation between major assets
        sp500_return_30d: S&P 500 return over past 30 days

    Returns:
        RegimeIndicators with current market state
    """
    # VIX trend
    if vix > 25:
        vix_trend = "rising"
    elif vix < 12:
        vix_trend = "falling"
    else:
        vix_trend = "normal"

    # Credit spreads
    if spread_bps < 100:
        spreads = "tight"
    elif spread_bps > 250:
        spreads = "wide"
    else:
        spreads = "normal"

    # Market momentum
    if sp500_return_30d > 0.02:
        momentum = "risk_on"
    elif sp500_return_30d < -0.02:
        momentum = "risk_off"
    else:
        momentum = "neutral"

    return RegimeIndicators(
        vix_level=vix,
        vix_trend=vix_trend,
        correlation_level=correlation,
        market_momentum=momentum,
        credit_spreads=spreads
    )
