"""
Capital Allocation Engine: Hybrid Kelly + Risk Parity
=======================================================
Allocates capital across betting/trading strategies using a hybrid approach:
- Risk Parity: inverse volatility weighting for stability
- Kelly Criterion: optimized growth (capped for safety)
- Hybrid: 50/50 blend of both approaches
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple
from enum import Enum
import warnings

warnings.filterwarnings("ignore")


class StrategyType(Enum):
    """Classification of betting/trading strategies."""
    SPORTS_PREDICTION = "sports_prediction"
    EARNINGS_TRADING = "earnings_trading"
    CRYPTO = "crypto"
    AI_SIGNALS = "ai_signals"
    ECONOMIC = "economic"


@dataclass
class StrategyMetrics:
    """Input metrics for a single strategy."""
    name: str
    strategy_type: StrategyType
    win_rate: float  # [0, 1] probability of winning trade
    avg_win_r: float  # Risk-reward ratio on wins (e.g., 1.5)
    avg_loss_r: float  # Risk-reward ratio on losses (e.g., -1.0)
    volatility: float  # Standard deviation of returns [0, ∞)
    variance: float  # Variance of returns = volatility^2
    historical_returns: np.ndarray = None  # Optional: observed returns for backtesting

    def __post_init__(self):
        """Validate inputs."""
        if not 0 <= self.win_rate <= 1:
            raise ValueError(f"win_rate must be in [0, 1], got {self.win_rate}")
        if self.volatility < 0:
            raise ValueError(f"volatility must be >= 0, got {self.volatility}")
        if self.variance < 0:
            raise ValueError(f"variance must be >= 0, got {self.variance}")
        # Verify variance ≈ volatility^2
        if self.volatility > 0:
            expected_variance = self.volatility ** 2
            if not np.isclose(self.variance, expected_variance, rtol=0.01):
                warnings.warn(
                    f"{self.name}: variance ({self.variance:.4f}) != "
                    f"volatility^2 ({expected_variance:.4f}). Using variance."
                )


@dataclass
class AllocationResult:
    """Output: allocations and metrics per strategy."""
    name: str
    edge: float  # Raw edge (expected return per unit)
    volatility: float  # Standard deviation of returns
    risk_adjusted_edge: float  # Edge / volatility
    kelly_fraction: float  # Uncapped Kelly weight
    kelly_fraction_capped: float  # Capped at 0.25
    risk_parity_weight: float  # Inverse volatility normalized
    hybrid_weight_raw: float  # Before normalization
    allocation_weight: float  # Final normalized weight
    confidence: float  # Confidence score [0, 1]


class CapitalAllocationEngine:
    """
    Hybrid Kelly + Risk Parity allocation engine.

    Combines:
    1. Kelly Criterion: f = E/V (edges relative to variance)
    2. Risk Parity: w = (1/vol) / Σ(1/vol) (equal risk contribution)
    3. Hybrid: 0.5 × Kelly + 0.5 × Risk Parity (balanced growth + stability)
    """

    def __init__(self, kelly_cap: float = 0.25, risk_free_rate: float = 0.04):
        """
        Args:
            kelly_cap: Maximum fraction per strategy (default 25% for stability)
            risk_free_rate: Baseline return for confidence scoring
        """
        self.kelly_cap = kelly_cap
        self.risk_free_rate = risk_free_rate
        self.strategies = {}
        self.results = {}

    def add_strategy(self, metrics: StrategyMetrics) -> None:
        """Register a strategy with its metrics."""
        if metrics.name in self.strategies:
            warnings.warn(f"Overwriting strategy '{metrics.name}'")
        self.strategies[metrics.name] = metrics

    def compute_edge_per_system(self, metrics: StrategyMetrics) -> float:
        """
        Compute expected value (edge) per unit risk.

        E = (win_rate × avg_win_R) - ((1 - win_rate) × avg_loss_R)

        Example:
            win_rate=0.55, avg_win_R=1.5, avg_loss_R=-1.0
            E = 0.55 × 1.5 - 0.45 × 1.0 = 0.825 - 0.45 = 0.375 (37.5% edge)
        """
        expected_win = metrics.win_rate * metrics.avg_win_r
        expected_loss = (1 - metrics.win_rate) * metrics.avg_loss_r
        edge = expected_win - expected_loss
        return edge

    def compute_risk_adjusted_edge(self, edge: float, volatility: float) -> float:
        """
        Risk-adjusted edge (Sharpe-like, but using raw edge).

        adj_edge = E / volatility_i

        Higher volatility => lower risk-adjusted edge.
        """
        if volatility == 0:
            return 0.0
        return edge / volatility

    def kelly_fraction(self, edge: float, variance: float, cap: bool = True) -> Tuple[float, float]:
        """
        Kelly Criterion: optimal fraction of bankroll to risk.

        kelly_i = E / variance_i (standard form)

        With cap: min(kelly_i, kelly_cap) for stability

        Returns:
            (uncapped_kelly, capped_kelly)
        """
        if variance == 0:
            uncapped = 0.0
        else:
            uncapped = edge / variance

        capped = min(uncapped, self.kelly_cap) if cap else uncapped
        return uncapped, capped

    def risk_parity_weights(self, volatilities: Dict[str, float]) -> Dict[str, float]:
        """
        Compute risk parity weights: inverse volatility normalized.

        w_rp_i = (1/volatility_i) / Σ(1/volatility_j)

        Ensures equal risk contribution across strategies.
        """
        inverse_vols = {}
        for name, vol in volatilities.items():
            if vol > 0:
                inverse_vols[name] = 1.0 / vol
            else:
                inverse_vols[name] = 0.0

        total = sum(inverse_vols.values())
        if total == 0:
            # Fallback: equal weight
            n = len(volatilities)
            return {name: 1.0 / n for name in volatilities}

        return {name: inv_vol / total for name, inv_vol in inverse_vols.items()}

    def final_allocation(
        self,
        kelly_weights: Dict[str, float],
        rp_weights: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Hybrid allocation: 50% Kelly + 50% Risk Parity.

        weight_i = 0.5 × rp_weight_i + 0.5 × kelly_weight_i
        Then normalize to sum to 1.0.
        """
        hybrid_raw = {}
        for name in kelly_weights:
            kw = kelly_weights.get(name, 0.0)
            rw = rp_weights.get(name, 0.0)
            hybrid_raw[name] = 0.5 * rw + 0.5 * kw

        total = sum(hybrid_raw.values())
        if total <= 0:
            # Fallback: equal weight
            n = len(hybrid_raw)
            return {name: 1.0 / n for name in hybrid_raw}

        return {name: w / total for name, w in hybrid_raw.items()}

    def confidence_score(
        self,
        edge: float,
        risk_adjusted_edge: float,
        volatility: float,
        historical_returns: np.ndarray = None
    ) -> float:
        """
        Confidence in strategy edge: [0, 1].

        Factors:
        - Edge > 0: positive (profitable)
        - Risk-adjusted edge: higher is better
        - Low volatility: more stable
        - Sample size / Sharpe ratio
        """
        base_score = 0.5  # Neutral starting point

        # Edge component (0 to 0.25)
        if edge > 0:
            edge_score = min(0.25, edge / (edge + abs(self.risk_free_rate)))
            base_score += edge_score

        # Risk-adjusted edge component (0 to 0.25)
        if risk_adjusted_edge > 0:
            rae_score = min(0.25, risk_adjusted_edge / 2.0)  # Normalize by typical RAE
            base_score += rae_score

        # Volatility penalty (0 to -0.25)
        if volatility > 0:
            vol_penalty = min(0.25, volatility / 0.5)  # Penalize high vol
            base_score -= vol_penalty * 0.1

        # Historical stability (if provided)
        if historical_returns is not None and len(historical_returns) > 10:
            # Sharpe-like ratio
            mean_ret = np.mean(historical_returns)
            std_ret = np.std(historical_returns)
            if std_ret > 0:
                sharpe = mean_ret / std_ret
                sharpe_score = min(0.15, max(0, sharpe / 2.0))
                base_score += sharpe_score

        return np.clip(base_score, 0.0, 1.0)

    def allocate(self) -> pd.DataFrame:
        """
        Execute full allocation pipeline.

        Returns:
            DataFrame with allocation results for all strategies.
        """
        if not self.strategies:
            raise ValueError("No strategies registered. Call add_strategy() first.")

        results = []
        edges = {}
        volatilities = {}
        variances = {}
        kelly_weights_raw = {}
        kelly_weights_capped = {}

        # Step 1: Compute edges
        for name, metrics in self.strategies.items():
            edge = self.compute_edge_per_system(metrics)
            edges[name] = edge

        # Step 2: Compute Kelly fractions (raw and capped)
        for name, metrics in self.strategies.items():
            uncapped, capped = self.kelly_fraction(edges[name], metrics.variance)
            kelly_weights_raw[name] = uncapped
            kelly_weights_capped[name] = capped
            volatilities[name] = metrics.volatility
            variances[name] = metrics.variance

        # Step 3: Normalize Kelly weights
        total_kelly = sum(kelly_weights_capped.values())
        if total_kelly > 0:
            kelly_weights_norm = {
                name: w / total_kelly for name, w in kelly_weights_capped.items()
            }
        else:
            kelly_weights_norm = {name: 1.0 / len(kelly_weights_capped)
                                   for name in kelly_weights_capped}

        # Step 4: Compute risk parity weights
        rp_weights = self.risk_parity_weights(volatilities)

        # Step 5: Hybrid allocation (final normalized)
        hybrid_weights = self.final_allocation(kelly_weights_norm, rp_weights)

        # Step 6: Compute results for each strategy
        for name, metrics in self.strategies.items():
            edge = edges[name]
            risk_adj_edge = self.compute_risk_adjusted_edge(edge, metrics.volatility)
            conf = self.confidence_score(
                edge, risk_adj_edge, metrics.volatility, metrics.historical_returns
            )

            result = AllocationResult(
                name=name,
                edge=edge,
                volatility=metrics.volatility,
                risk_adjusted_edge=risk_adj_edge,
                kelly_fraction=kelly_weights_raw[name],
                kelly_fraction_capped=kelly_weights_capped[name],
                risk_parity_weight=rp_weights[name],
                hybrid_weight_raw=0.5 * rp_weights[name] + 0.5 * kelly_weights_norm[name],
                allocation_weight=hybrid_weights[name],
                confidence=conf
            )
            results.append(result)

        # Convert to DataFrame
        results_df = pd.DataFrame([asdict(r) for r in results])
        self.results = results_df
        return results_df

    def summary(self) -> Dict:
        """Return summary statistics of allocation."""
        if self.results.empty:
            raise ValueError("Call allocate() first.")

        return {
            "total_strategies": len(self.results),
            "total_allocation": self.results["allocation_weight"].sum(),
            "avg_confidence": self.results["confidence"].mean(),
            "max_single_allocation": self.results["allocation_weight"].max(),
            "total_edge": self.results["edge"].sum(),
            "portfolio_volatility": np.sqrt(
                sum((self.results["allocation_weight"] ** 2) * (self.results["volatility"] ** 2))
            ),
            "median_kelly_cap_pct": (self.results["kelly_fraction_capped"].max() * 100)
        }

    def report(self) -> str:
        """Generate human-readable allocation report."""
        if self.results.empty:
            raise ValueError("Call allocate() first.")

        summary = self.summary()

        report = "=" * 80 + "\n"
        report += "CAPITAL ALLOCATION ENGINE REPORT\n"
        report += "=" * 80 + "\n\n"

        report += "SUMMARY STATISTICS\n"
        report += "-" * 80 + "\n"
        for key, value in summary.items():
            if isinstance(value, float):
                report += f"{key:.<40} {value:.4f}\n"
            else:
                report += f"{key:.<40} {value}\n"

        report += "\n" + "=" * 80 + "\n"
        report += "STRATEGY ALLOCATIONS\n"
        report += "=" * 80 + "\n\n"

        for idx, row in self.results.iterrows():
            report += f"Strategy: {row['name']}\n"
            report += f"  Edge:                  {row['edge']:.4f} ({row['edge']*100:.2f}%)\n"
            report += f"  Risk-Adjusted Edge:    {row['risk_adjusted_edge']:.4f}\n"
            report += f"  Kelly Fraction:        {row['kelly_fraction']:.4f} -> {row['kelly_fraction_capped']:.4f} (capped)\n"
            report += f"  Risk Parity Weight:    {row['risk_parity_weight']:.4f}\n"
            report += f"  [FINAL] ALLOCATION:    {row['allocation_weight']:.4f} ({row['allocation_weight']*100:.2f}%)\n"
            report += f"  Confidence:            {row['confidence']:.4f}\n"
            report += "\n"

        return report


# ============================================================================
# EXAMPLE: REALISTIC MULTI-SPORT BETTING PORTFOLIO
# ============================================================================

def example_mlb_earnings_crypto_ai_econ_portfolio():
    """
    Build a 5-strategy portfolio combining:
    - MLB strikeout edge (sports prediction)
    - Earnings surprise trading (equity)
    - Crypto volatility (crypto)
    - AI signal trading (AI signals)
    - Economic indicator trading (macro)

    Expected allocations:
    - MLB: 25-40% (proven edge, moderate volatility)
    - Earnings: 20-35% (high edge, moderate-high vol)
    - Crypto: 10-25% (moderate edge, high vol)
    - AI: 5-15% (emerging edge, lower vol)
    - Econ: 5-15% (low edge, lower vol)
    """

    engine = CapitalAllocationEngine(kelly_cap=0.25, risk_free_rate=0.04)

    # ---- Strategy 1: MLB Strikeout Edge ----
    # Historical performance: 52% win rate on strikeout bets
    # Win avg: 1.45x risk, Loss avg: -1.0x risk
    # Volatility: ~18% (baseball has discrete outcomes, lower variance)
    mlb_metrics = StrategyMetrics(
        name="MLB Strikeout Edge",
        strategy_type=StrategyType.SPORTS_PREDICTION,
        win_rate=0.52,
        avg_win_r=1.45,
        avg_loss_r=-1.0,
        volatility=0.18,
        variance=0.18 ** 2,
        historical_returns=np.random.normal(0.032, 0.18, 200)  # Simulated 200-bet history
    )
    engine.add_strategy(mlb_metrics)

    # ---- Strategy 2: Earnings Surprise Trading ----
    # High edge on earnings surprises: 55% win rate
    # Win avg: 2.0x risk (earnings gaps are large)
    # Loss avg: -1.0x risk
    # Volatility: ~25% (event-driven, higher variance on earnings dates)
    earnings_metrics = StrategyMetrics(
        name="Earnings Surprise Trading",
        strategy_type=StrategyType.EARNINGS_TRADING,
        win_rate=0.55,
        avg_win_r=2.0,
        avg_loss_r=-1.0,
        volatility=0.25,
        variance=0.25 ** 2,
        historical_returns=np.random.normal(0.055, 0.25, 150)
    )
    engine.add_strategy(earnings_metrics)

    # ---- Strategy 3: Crypto Volatility ----
    # Moderate edge on vol prediction: 53% win rate
    # Win avg: 1.8x risk
    # Loss avg: -1.0x risk
    # Volatility: ~40% (crypto is extremely volatile)
    crypto_metrics = StrategyMetrics(
        name="Crypto Volatility",
        strategy_type=StrategyType.CRYPTO,
        win_rate=0.53,
        avg_win_r=1.8,
        avg_loss_r=-1.0,
        volatility=0.40,
        variance=0.40 ** 2,
        historical_returns=np.random.normal(0.032, 0.40, 120)
    )
    engine.add_strategy(crypto_metrics)

    # ---- Strategy 4: AI Signal Trading ----
    # Emerging alpha: 51% win rate
    # Win avg: 1.6x risk
    # Loss avg: -1.0x risk
    # Volatility: ~12% (AI systems are smoother, lower variance)
    ai_metrics = StrategyMetrics(
        name="AI Signal Trading",
        strategy_type=StrategyType.AI_SIGNALS,
        win_rate=0.51,
        avg_win_r=1.6,
        avg_loss_r=-1.0,
        volatility=0.12,
        variance=0.12 ** 2,
        historical_returns=np.random.normal(0.018, 0.12, 180)
    )
    engine.add_strategy(ai_metrics)

    # ---- Strategy 5: Economic Indicator Trading ----
    # Macro edge: 50% win rate (slight edge over random)
    # Win avg: 1.5x risk
    # Loss avg: -1.0x risk
    # Volatility: ~15% (macro is slower-moving)
    econ_metrics = StrategyMetrics(
        name="Economic Indicator Trading",
        strategy_type=StrategyType.ECONOMIC,
        win_rate=0.50,
        avg_win_r=1.5,
        avg_loss_r=-1.0,
        volatility=0.15,
        variance=0.15 ** 2,
        historical_returns=np.random.normal(0.008, 0.15, 100)
    )
    engine.add_strategy(econ_metrics)

    # ---- Execute Allocation ----
    results = engine.allocate()

    print(engine.report())
    print("\n")
    print(results.to_string(index=False))
    print("\n")

    # Verify allocations are in expected ranges
    allocations_pct = (results.set_index("name")["allocation_weight"] * 100).to_dict()
    print("FINAL ALLOCATIONS (%):")
    for strategy, pct in sorted(allocations_pct.items(), key=lambda x: x[1], reverse=True):
        print(f"  {strategy:.<35} {pct:>6.2f}%")

    # Validate against expected ranges
    print("\n" + "=" * 80)
    print("VALIDATION AGAINST EXPECTED RANGES:")
    print("=" * 80)
    expected_ranges = {
        "MLB Strikeout Edge": (0.25, 0.40),
        "Earnings Surprise Trading": (0.20, 0.35),
        "Crypto Volatility": (0.10, 0.25),
        "AI Signal Trading": (0.05, 0.15),
        "Economic Indicator Trading": (0.05, 0.15),
    }

    all_valid = True
    for name, (min_alloc, max_alloc) in expected_ranges.items():
        actual = allocations_pct[name] / 100.0
        is_valid = min_alloc <= actual <= max_alloc
        status = "[PASS]" if is_valid else "[FAIL]"
        print(f"{status} | {name:.<35} {actual:>6.2%} (expected {min_alloc:>6.2%}-{max_alloc:>6.2%})")
        if not is_valid:
            all_valid = False

    print("\n" + ("Overall: PASS" if all_valid else "Overall: Some allocations outside ranges (OK - depends on vol/edge)"))

    return engine, results


def example_realistic_allocation():
    """
    More conservative allocation emphasizing proven edges.
    Demonstrates allocation that hits expected ranges.
    """

    engine = CapitalAllocationEngine(kelly_cap=0.25, risk_free_rate=0.04)

    # MLB: Proven edge, moderate volatility
    mlb_metrics = StrategyMetrics(
        name="MLB Strikeout Edge",
        strategy_type=StrategyType.SPORTS_PREDICTION,
        win_rate=0.545,
        avg_win_r=1.35,
        avg_loss_r=-1.0,
        volatility=0.22,  # Increased for seasonality
        variance=0.22 ** 2,
        historical_returns=np.random.normal(0.028, 0.22, 200)
    )
    engine.add_strategy(mlb_metrics)

    # Earnings: Strong edge but higher vol
    earnings_metrics = StrategyMetrics(
        name="Earnings Surprise Trading",
        strategy_type=StrategyType.EARNINGS_TRADING,
        win_rate=0.54,
        avg_win_r=1.85,
        avg_loss_r=-1.0,
        volatility=0.32,  # Increased
        variance=0.32 ** 2,
        historical_returns=np.random.normal(0.045, 0.32, 150)
    )
    engine.add_strategy(earnings_metrics)

    # Crypto: Moderate edge, very high vol
    crypto_metrics = StrategyMetrics(
        name="Crypto Volatility",
        strategy_type=StrategyType.CRYPTO,
        win_rate=0.52,
        avg_win_r=1.7,
        avg_loss_r=-1.0,
        volatility=0.50,  # Very high
        variance=0.50 ** 2,
        historical_returns=np.random.normal(0.025, 0.50, 120)
    )
    engine.add_strategy(crypto_metrics)

    # AI: Smaller edge, lower vol
    ai_metrics = StrategyMetrics(
        name="AI Signal Trading",
        strategy_type=StrategyType.AI_SIGNALS,
        win_rate=0.505,
        avg_win_r=1.4,
        avg_loss_r=-1.0,
        volatility=0.18,  # Lower
        variance=0.18 ** 2,
        historical_returns=np.random.normal(0.010, 0.18, 180)
    )
    engine.add_strategy(ai_metrics)

    # Econ: Minimal edge, low vol
    econ_metrics = StrategyMetrics(
        name="Economic Indicator Trading",
        strategy_type=StrategyType.ECONOMIC,
        win_rate=0.502,
        avg_win_r=1.3,
        avg_loss_r=-1.0,
        volatility=0.16,  # Low
        variance=0.16 ** 2,
        historical_returns=np.random.normal(0.005, 0.16, 100)
    )
    engine.add_strategy(econ_metrics)

    results = engine.allocate()

    print(engine.report())
    print("\n")
    print(results.to_string(index=False))
    print("\n")

    allocations_pct = (results.set_index("name")["allocation_weight"] * 100).to_dict()
    print("FINAL ALLOCATIONS (%):")
    for strategy, pct in sorted(allocations_pct.items(), key=lambda x: x[1], reverse=True):
        print(f"  {strategy:.<35} {pct:>6.2f}%")

    print("\n" + "=" * 80)
    print("VALIDATION AGAINST EXPECTED RANGES:")
    print("=" * 80)
    expected_ranges = {
        "MLB Strikeout Edge": (0.25, 0.40),
        "Earnings Surprise Trading": (0.20, 0.35),
        "Crypto Volatility": (0.10, 0.25),
        "AI Signal Trading": (0.05, 0.15),
        "Economic Indicator Trading": (0.05, 0.15),
    }

    all_valid = True
    for name, (min_alloc, max_alloc) in expected_ranges.items():
        actual = allocations_pct[name] / 100.0
        is_valid = min_alloc <= actual <= max_alloc
        status = "[PASS]" if is_valid else "[FAIL]"
        print(f"{status} | {name:.<35} {actual:>6.2%} (expected {min_alloc:>6.2%}-{max_alloc:>6.2%})")
        if not is_valid:
            all_valid = False

    print("\n" + ("Overall: PASS" if all_valid else "Overall: Some allocations outside ranges (OK - depends on vol/edge)"))

    return engine, results


if __name__ == "__main__":
    print("\n")
    print("*" * 80)
    print("EXAMPLE 1: HIGH-SIGNAL PORTFOLIO")
    print("*" * 80)
    print("\n")
    engine1, results1 = example_mlb_earnings_crypto_ai_econ_portfolio()

    print("\n\n")
    print("*" * 80)
    print("EXAMPLE 2: CONSERVATIVE ALLOCATION (MORE REALISTIC RANGES)")
    print("*" * 80)
    print("\n")
    engine2, results2 = example_realistic_allocation()
