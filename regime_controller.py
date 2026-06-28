"""
Meta-Layer Regime Controller for Multi-Strategy Portfolio Management

Detects market regimes from macro signals and applies dynamic multipliers
to strategy allocations based on regime conditions.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple, Optional
from enum import Enum
import json


class RegimeType(Enum):
    """Market regime classifications."""
    RISK_ON_EXPANSION = "risk_on_expansion"
    RISK_OFF_CONTRACTION = "risk_off_contraction"
    TRANSITION_UNCERTAINTY = "transition_uncertainty"


@dataclass
class MarketConditions:
    """Current market conditions for regime detection."""
    vix: float  # VIX index level (0-100)
    vix_percentile: float  # 20-day percentile (0-100)
    funding_rates_bps: float  # Crypto funding rates in basis points
    usd_strength: float  # DXY Z-score (-3 to +3)
    rate_spread: float  # 10Y-2Y spread basis points
    sentiment_dispersion: float  # St.dev of sentiment scores (0-100)
    earnings_season: bool  # Whether earnings season is active
    earnings_density: Optional[float] = None  # % of S&P 500 reporting (0-100)


@dataclass
class RegimeDetectionResult:
    """Result of regime classification."""
    regime: RegimeType
    confidence: float  # 0-1, higher is more confident
    vix_signal: float  # -1 to +1, contribution to regime
    funding_signal: float  # -1 to +1, crypto carry signal
    liquidity_signal: float  # -1 to +1, macro liquidity tightening
    sentiment_signal: float  # -1 to +1, sentiment dispersion signal
    earnings_signal: float  # -1 to +1, earnings season boost
    raw_score: float  # Unthresholded regime score


class RegimeClassifier:
    """
    Detects market regime from multiple macro and crypto signals.

    Combines:
    - VIX level and percentile (volatility regime)
    - Crypto funding rates (risk appetite)
    - USD strength + rate spreads (macro liquidity)
    - Sentiment dispersion (consensus vs uncertainty)
    - Earnings calendar (equity risk premium)
    """

    # VIX thresholds for regime determination
    VIX_RISK_ON_MAX = 16.0
    VIX_RISK_OFF_MIN = 22.0
    VIX_PERCENTILE_THRESHOLD = 50.0

    # Crypto funding rate thresholds (bps, annualized)
    FUNDING_RATE_RISK_ON_MIN = 5.0
    FUNDING_RATE_RISK_OFF_MAX = -5.0

    # USD strength thresholds (Z-score)
    USD_STRENGTH_RISK_OFF_MIN = 0.5
    USD_STRENGTH_RISK_ON_MAX = -0.5

    # Rate spread thresholds (bps, inverted yield curve is risk-off)
    RATE_SPREAD_RISK_OFF_MAX = -50.0

    # Sentiment dispersion thresholds
    SENTIMENT_DISPERSION_RISK_OFF_MIN = 25.0

    def __init__(self):
        """Initialize regime classifier with default signal weights."""
        self.signal_weights = {
            'vix': 0.30,
            'funding': 0.20,
            'liquidity': 0.25,
            'sentiment': 0.15,
            'earnings': 0.10
        }

    def calculate_vix_signal(self, conditions: MarketConditions) -> Tuple[float, float]:
        """
        Calculate VIX signal (-1 = risk_off, +1 = risk_on).
        Returns: (signal, confidence)
        """
        # Normalize VIX: typical range 10-40, extremes 5-80
        vix_normalized = (conditions.vix - 20.0) / 10.0
        vix_signal = np.clip(-vix_normalized, -1.0, 1.0)  # Negative VIX = risk on

        # Confidence based on VIX percentile extremeness
        percentile_extreme = abs(conditions.vix_percentile - 50.0) / 50.0
        confidence = 0.5 + 0.5 * percentile_extreme

        return vix_signal, confidence

    def calculate_funding_signal(self, conditions: MarketConditions) -> Tuple[float, float]:
        """
        Calculate crypto funding rate signal (-1 = risk_off, +1 = risk_on).
        High positive rates = exuberant longs = risk_on.
        Returns: (signal, confidence)
        """
        if abs(conditions.funding_rates_bps) < 1.0:
            # Near zero: neutral, low confidence
            return 0.0, 0.3

        # Normalize: -50 to +50 bps typical range
        funding_normalized = conditions.funding_rates_bps / 50.0
        funding_signal = np.clip(funding_normalized, -1.0, 1.0)

        # Confidence based on magnitude
        confidence = 0.5 + 0.5 * abs(funding_normalized)

        return funding_signal, confidence

    def calculate_liquidity_signal(self, conditions: MarketConditions) -> Tuple[float, float]:
        """
        Calculate macro liquidity signal (-1 = risk_off, +1 = risk_on).
        Combines USD strength and rate spreads.
        - Strong USD + inverted yield curve = risk_off (liquidity crunch)
        - Weak USD + steep curve = risk_on (abundant liquidity)
        Returns: (signal, confidence)
        """
        # USD signal: strong USD (positive Z-score) = risk-off
        usd_signal = -np.clip(conditions.usd_strength / 2.0, -1.0, 1.0)

        # Spread signal: inverted or flat curve = risk-off
        spread_normalized = conditions.rate_spread / 100.0
        spread_signal = np.clip(spread_normalized, -1.0, 1.0)

        # Combine: equal weight, but spread inverted is more risk-off signal
        liquidity_signal = 0.6 * spread_signal + 0.4 * usd_signal
        liquidity_signal = np.clip(liquidity_signal, -1.0, 1.0)

        # Confidence based on magnitude of both signals
        confidence = 0.5 + 0.5 * max(abs(usd_signal), abs(spread_signal))

        return liquidity_signal, confidence

    def calculate_sentiment_signal(self, conditions: MarketConditions) -> Tuple[float, float]:
        """
        Calculate sentiment dispersion signal (-1 = risk_off, +1 = risk_on).
        High dispersion (disagreement) = market uncertainty = risk-off tilt.
        Low dispersion (consensus) = confidence = risk-on tilt.
        Returns: (signal, confidence)
        """
        # Normalize dispersion: typical range 10-40
        dispersion_normalized = (conditions.sentiment_dispersion - 25.0) / 15.0
        sentiment_signal = np.clip(-dispersion_normalized, -1.0, 1.0)

        # Confidence is inverse: high consensus OR high disagreement both confident
        dispersion_extremeness = abs(dispersion_normalized)
        confidence = 0.5 + 0.5 * min(dispersion_extremeness, 1.0)

        return sentiment_signal, confidence

    def calculate_earnings_signal(self, conditions: MarketConditions) -> Tuple[float, float]:
        """
        Calculate earnings season signal (-1 = risk_off, +1 = risk_on).
        During earnings season, equity risk premium expands, typically risk-on.
        Returns: (signal, confidence)
        """
        if not conditions.earnings_season:
            return 0.0, 0.3

        # During earnings season: baseline risk-on signal
        earnings_signal = 0.5

        # Boost signal if earnings density is high (many companies reporting)
        if conditions.earnings_density is not None:
            density_normalized = (conditions.earnings_density - 50.0) / 50.0
            earnings_signal = 0.3 + 0.7 * np.clip(density_normalized, -1.0, 1.0)

        confidence = 0.7
        return earnings_signal, confidence

    def classify(self, conditions: MarketConditions) -> RegimeDetectionResult:
        """
        Classify market regime and return confidence.

        Combines all signals with learned weights to produce a regime score:
        - Score < -0.3: risk_off_contraction
        - Score -0.3 to +0.3: transition_uncertainty
        - Score > +0.3: risk_on_expansion

        Args:
            conditions: Current market conditions

        Returns:
            RegimeDetectionResult with regime, confidence, and signal breakdown
        """
        # Calculate all signals
        vix_sig, vix_conf = self.calculate_vix_signal(conditions)
        funding_sig, funding_conf = self.calculate_funding_signal(conditions)
        liquidity_sig, liquidity_conf = self.calculate_liquidity_signal(conditions)
        sentiment_sig, sentiment_conf = self.calculate_sentiment_signal(conditions)
        earnings_sig, earnings_conf = self.calculate_earnings_signal(conditions)

        # Weighted regime score
        raw_score = (
            self.signal_weights['vix'] * vix_sig +
            self.signal_weights['funding'] * funding_sig +
            self.signal_weights['liquidity'] * liquidity_sig +
            self.signal_weights['sentiment'] * sentiment_sig +
            self.signal_weights['earnings'] * earnings_sig
        )

        # Classify regime based on score thresholds
        if raw_score > 0.3:
            regime = RegimeType.RISK_ON_EXPANSION
        elif raw_score < -0.3:
            regime = RegimeType.RISK_OFF_CONTRACTION
        else:
            regime = RegimeType.TRANSITION_UNCERTAINTY

        # Calculate overall confidence as weighted average of signal confidences
        overall_confidence = (
            self.signal_weights['vix'] * vix_conf +
            self.signal_weights['funding'] * funding_conf +
            self.signal_weights['liquidity'] * liquidity_conf +
            self.signal_weights['sentiment'] * sentiment_conf +
            self.signal_weights['earnings'] * earnings_conf
        )

        # Adjust confidence based on distance from threshold
        threshold_distance = abs(raw_score)
        if abs(raw_score) < 0.1:
            # Near threshold: lower confidence
            threshold_penalty = 0.7
        elif abs(raw_score) < 0.3:
            threshold_penalty = 0.85
        else:
            threshold_penalty = 1.0

        overall_confidence = np.clip(overall_confidence * threshold_penalty, 0.0, 1.0)

        return RegimeDetectionResult(
            regime=regime,
            confidence=overall_confidence,
            vix_signal=vix_sig,
            funding_signal=funding_sig,
            liquidity_signal=liquidity_sig,
            sentiment_signal=sentiment_sig,
            earnings_signal=earnings_sig,
            raw_score=raw_score
        )


class RegimeMultiplierEngine:
    """
    Applies regime-based multipliers to strategy allocations.

    Each strategy has different sensitivities to market regimes:
    - Crypto: highly cyclical, thrives in risk_on
    - Earnings: moderate cyclicality, benefits from earnings season
    - AI: tech-heavy, risk_on sensitive
    - MLB: idiosyncratic, regime-neutral (stable allocator)
    - Econ: macro hedge, better in risk_off
    """

    REGIME_MULTIPLIERS = {
        'crypto': {
            RegimeType.RISK_ON_EXPANSION: 1.2,
            RegimeType.TRANSITION_UNCERTAINTY: 0.5,
            RegimeType.RISK_OFF_CONTRACTION: 0.2
        },
        'earnings': {
            RegimeType.RISK_ON_EXPANSION: 1.3,
            RegimeType.TRANSITION_UNCERTAINTY: 0.8,
            RegimeType.RISK_OFF_CONTRACTION: 0.6
        },
        'ai': {
            RegimeType.RISK_ON_EXPANSION: 1.2,
            RegimeType.TRANSITION_UNCERTAINTY: 0.7,
            RegimeType.RISK_OFF_CONTRACTION: 0.4
        },
        'mlb': {
            RegimeType.RISK_ON_EXPANSION: 1.0,
            RegimeType.TRANSITION_UNCERTAINTY: 1.0,
            RegimeType.RISK_OFF_CONTRACTION: 1.1
        },
        'econ': {
            RegimeType.RISK_ON_EXPANSION: 0.8,
            RegimeType.TRANSITION_UNCERTAINTY: 1.0,
            RegimeType.RISK_OFF_CONTRACTION: 1.2
        }
    }

    @classmethod
    def apply_multipliers(
        cls,
        base_weights: Dict[str, float],
        regime_result: RegimeDetectionResult,
        normalize: bool = True
    ) -> Dict[str, float]:
        """
        Apply regime multipliers to base weights.

        Formula: adjusted_weight_i = base_weight_i × multiplier_i

        Args:
            base_weights: Dict of strategy -> base allocation (0-1)
            regime_result: Result from RegimeClassifier.classify()
            normalize: Whether to renormalize weights to sum to 1.0

        Returns:
            Dict of strategy -> adjusted allocation
        """
        adjusted_weights = {}

        for strategy, base_weight in base_weights.items():
            if strategy not in cls.REGIME_MULTIPLIERS:
                # Unknown strategy: keep base weight
                adjusted_weights[strategy] = base_weight
                continue

            multiplier = cls.REGIME_MULTIPLIERS[strategy][regime_result.regime]
            adjusted_weights[strategy] = base_weight * multiplier

        # Normalize if requested
        if normalize:
            total = sum(adjusted_weights.values())
            if total > 0:
                adjusted_weights = {
                    s: w / total for s, w in adjusted_weights.items()
                }

        return adjusted_weights

    @classmethod
    def get_multiplier(cls, strategy: str, regime: RegimeType) -> float:
        """Get multiplier for a specific strategy in a regime."""
        if strategy not in cls.REGIME_MULTIPLIERS:
            return 1.0
        return cls.REGIME_MULTIPLIERS[strategy][regime]


@dataclass
class PortfolioRebalanceRequest:
    """Input for portfolio rebalancing with regime adjustment."""
    market_conditions: MarketConditions
    base_weights: Dict[str, float]  # Strategy -> allocation (sums to ~1.0)
    position_sizes: Optional[Dict[str, float]] = None  # Optional: current $ per strategy


@dataclass
class PortfolioRebalanceOutput:
    """Output of regime-adjusted portfolio rebalancing."""
    regime: RegimeType
    regime_confidence: float
    base_weights: Dict[str, float]
    adjusted_weights: Dict[str, float]
    multipliers_applied: Dict[str, float]
    signal_breakdown: Dict[str, float]
    normalized_adjusted_weights: Dict[str, float]
    adjustment_factor: float  # Ratio of (sum of adjusted) / (sum of base)


class RegimeController:
    """
    Master controller: combines RegimeClassifier and RegimeMultiplierEngine
    to rebalance portfolio weights based on market conditions.
    """

    def __init__(self):
        """Initialize controller with classifier and multiplier engine."""
        self.classifier = RegimeClassifier()
        self.multiplier_engine = RegimeMultiplierEngine()

    def rebalance(self, request: PortfolioRebalanceRequest) -> PortfolioRebalanceOutput:
        """
        Rebalance portfolio based on current market conditions.

        Args:
            request: PortfolioRebalanceRequest with conditions and base weights

        Returns:
            PortfolioRebalanceOutput with regime and adjusted weights
        """
        # Classify current regime
        regime_result = self.classifier.classify(request.market_conditions)

        # Apply multipliers
        adjusted_weights = self.multiplier_engine.apply_multipliers(
            request.base_weights,
            regime_result,
            normalize=False
        )

        # Calculate adjustment factor
        base_total = sum(request.base_weights.values())
        adjusted_total = sum(adjusted_weights.values())
        adjustment_factor = adjusted_total / base_total if base_total > 0 else 1.0

        # Normalize adjusted weights
        normalized_adjusted = {
            s: w / adjusted_total for s, w in adjusted_weights.items()
        } if adjusted_total > 0 else adjusted_weights

        # Extract signal breakdown
        signal_breakdown = {
            'vix': regime_result.vix_signal,
            'funding_rates': regime_result.funding_signal,
            'liquidity': regime_result.liquidity_signal,
            'sentiment': regime_result.sentiment_signal,
            'earnings_season': regime_result.earnings_signal,
            'raw_score': regime_result.raw_score
        }

        # Extract multipliers applied
        multipliers_applied = {
            s: self.multiplier_engine.get_multiplier(s, regime_result.regime)
            for s in request.base_weights.keys()
        }

        return PortfolioRebalanceOutput(
            regime=regime_result.regime,
            regime_confidence=regime_result.confidence,
            base_weights=request.base_weights,
            adjusted_weights=adjusted_weights,
            multipliers_applied=multipliers_applied,
            signal_breakdown=signal_breakdown,
            normalized_adjusted_weights=normalized_adjusted,
            adjustment_factor=adjustment_factor
        )

    def format_summary(self, output: PortfolioRebalanceOutput) -> str:
        """Format rebalance output as human-readable summary."""
        lines = [
            "=" * 70,
            "REGIME-ADJUSTED PORTFOLIO REBALANCE",
            "=" * 70,
            f"\nRegime: {output.regime.value.upper()}",
            f"Confidence: {output.regime_confidence:.1%}",
            f"\nSignal Breakdown:",
            f"  VIX Signal:         {output.signal_breakdown['vix']:+.2f}",
            f"  Funding Rates:      {output.signal_breakdown['funding_rates']:+.2f}",
            f"  Liquidity:          {output.signal_breakdown['liquidity']:+.2f}",
            f"  Sentiment:          {output.signal_breakdown['sentiment']:+.2f}",
            f"  Earnings Season:    {output.signal_breakdown['earnings_season']:+.2f}",
            f"  Raw Score:          {output.signal_breakdown['raw_score']:+.2f}",
            f"\nWeight Adjustments:",
            f"  {'Strategy':<12} {'Base':<10} {'Multiplier':<12} {'Adjusted':<10} {'Normalized':<10}",
            "-" * 54
        ]

        for strategy in sorted(output.base_weights.keys()):
            base = output.base_weights[strategy]
            mult = output.multipliers_applied[strategy]
            adj = output.adjusted_weights[strategy]
            norm = output.normalized_adjusted_weights[strategy]
            lines.append(
                f"  {strategy:<12} {base:<10.1%} {mult:<12.2f}x {adj:<10.1%} {norm:<10.1%}"
            )

        lines.extend([
            "-" * 54,
            f"Adjustment Factor: {output.adjustment_factor:.2f}x",
            "=" * 70
        ])

        return "\n".join(lines)


def example_risk_on_earnings_season():
    """
    Example: VIX=25, funding_rates=10bps, earnings_season=true
    Expected: RISK_ON regime, crypto boosted 1.2x, econ dampened 0.8x
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Risk-On Earnings Season Environment")
    print("=" * 70)

    conditions = MarketConditions(
        vix=25.0,
        vix_percentile=60.0,
        funding_rates_bps=10.0,
        usd_strength=-0.5,
        rate_spread=75.0,
        sentiment_dispersion=15.0,
        earnings_season=True,
        earnings_density=45.0
    )

    base_weights = {
        'crypto': 0.15,
        'earnings': 0.25,
        'ai': 0.20,
        'mlb': 0.25,
        'econ': 0.15
    }

    request = PortfolioRebalanceRequest(
        market_conditions=conditions,
        base_weights=base_weights
    )

    controller = RegimeController()
    output = controller.rebalance(request)

    print(controller.format_summary(output))
    return output


def example_risk_off_contraction():
    """
    Example: VIX=40, funding_rates=-15bps, USD strength +2.0, inverted curve
    Expected: RISK_OFF regime, crypto dampened 0.2x, econ boosted 1.2x
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Risk-Off Contraction Environment")
    print("=" * 70)

    conditions = MarketConditions(
        vix=40.0,
        vix_percentile=85.0,
        funding_rates_bps=-15.0,
        usd_strength=2.0,
        rate_spread=-75.0,
        sentiment_dispersion=35.0,
        earnings_season=False,
        earnings_density=10.0
    )

    base_weights = {
        'crypto': 0.15,
        'earnings': 0.25,
        'ai': 0.20,
        'mlb': 0.25,
        'econ': 0.15
    }

    request = PortfolioRebalanceRequest(
        market_conditions=conditions,
        base_weights=base_weights
    )

    controller = RegimeController()
    output = controller.rebalance(request)

    print(controller.format_summary(output))
    return output


def example_transition_uncertainty():
    """
    Example: VIX=18, funding_rates=0bps, sentiment dispersion=28
    Expected: TRANSITION regime, most multipliers near 1.0, lower confidence
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Transition Uncertainty Environment")
    print("=" * 70)

    conditions = MarketConditions(
        vix=18.0,
        vix_percentile=45.0,
        funding_rates_bps=0.5,
        usd_strength=0.0,
        rate_spread=50.0,
        sentiment_dispersion=28.0,
        earnings_season=False,
        earnings_density=15.0
    )

    base_weights = {
        'crypto': 0.15,
        'earnings': 0.25,
        'ai': 0.20,
        'mlb': 0.25,
        'econ': 0.15
    }

    request = PortfolioRebalanceRequest(
        market_conditions=conditions,
        base_weights=base_weights
    )

    controller = RegimeController()
    output = controller.rebalance(request)

    print(controller.format_summary(output))
    return output


if __name__ == "__main__":
    # Run all examples
    example_risk_on_earnings_season()
    example_risk_off_contraction()
    example_transition_uncertainty()

    print("\n" + "=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)
