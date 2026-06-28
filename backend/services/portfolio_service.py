"""Portfolio engine service - Monte Carlo simulator, allocator, and regime controller."""

import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import timedelta
import logging
from scipy.optimize import minimize
from scipy.stats import norm

from schemas.portfolio import (
    StrategyInput,
    PortfolioSimulationRequest,
    PortfolioSimulationResult,
    EquityCurvePoint,
    DrawdownPoint,
    AllocationRequest,
    AllocationResult,
    RegimeRequest,
    RegimeState,
)

logger = logging.getLogger(__name__)


# Correlation matrix: MLB 0.1, Crypto 1.4, Earnings 1.0, AI 1.2, Econ 0.6 betas
# MLB-All 0.05-0.20, AI-Earnings 0.65-0.85, etc
CORRELATION_MATRIX = {
    "MLB": {"MLB": 1.0, "Crypto": 0.08, "Earnings": 0.12, "AI": 0.10, "Econ": 0.15},
    "Crypto": {"MLB": 0.08, "Crypto": 1.0, "Earnings": 0.35, "AI": 0.45, "Econ": 0.22},
    "Earnings": {"MLB": 0.12, "Crypto": 0.35, "Earnings": 1.0, "AI": 0.75, "Econ": 0.30},
    "AI": {"MLB": 0.10, "Crypto": 0.45, "Earnings": 0.75, "AI": 1.0, "Econ": 0.28},
    "Econ": {"MLB": 0.15, "Crypto": 0.22, "Earnings": 0.30, "AI": 0.28, "Econ": 1.0},
}

BETAS = {
    "MLB": 0.1,
    "Crypto": 1.4,
    "Earnings": 1.0,
    "AI": 1.2,
    "Econ": 0.6,
}


class PortfolioSimulator:
    """Monte Carlo simulator for portfolio paths."""

    @staticmethod
    def simulate_paths(
        request: PortfolioSimulationRequest,
    ) -> PortfolioSimulationResult:
        """
        Run Monte Carlo simulation for portfolio paths.

        Args:
            request: Simulation parameters

        Returns:
            Simulation results with equity curves and statistics
        """
        strategies = request.strategies
        num_sims = request.num_simulations
        days = request.time_horizon_days
        initial_capital = request.initial_capital

        # Extract returns and vols (convert from % to decimals)
        returns = np.array([s.expected_return / 100 / 252 for s in strategies])  # Daily return
        vols = np.array([s.volatility / 100 / np.sqrt(252) for s in strategies])  # Daily vol
        weights = np.array([s.weight for s in strategies])

        # Build correlation matrix from strategy names
        strategy_names = [s.name for s in strategies]
        corr_matrix = np.zeros((len(strategies), len(strategies)))
        for i, name_i in enumerate(strategy_names):
            for j, name_j in enumerate(strategy_names):
                corr_matrix[i, j] = CORRELATION_MATRIX.get(name_i, {}).get(name_j, 0.5)

        # Convert correlation to covariance matrix
        cov_matrix = np.outer(vols, vols) * corr_matrix

        # Generate correlated random returns
        cholesky = np.linalg.cholesky(cov_matrix)

        # Simulate all paths
        paths = np.zeros((num_sims, days + 1))
        paths[:, 0] = initial_capital

        max_drawdowns = np.zeros(num_sims)
        peak_values = np.full(num_sims, initial_capital)

        for day in range(days):
            # Generate correlated innovations
            z = np.random.standard_normal(len(strategies))
            daily_returns = returns + cholesky @ z

            # Apply rebalancing if needed
            portfolio_return = weights @ daily_returns
            paths[:, day + 1] = paths[:, day] * (1 + portfolio_return)

            # Track drawdown
            peak_values = np.maximum(peak_values, paths[:, day + 1])
            drawdown = (peak_values - paths[:, day + 1]) / peak_values
            max_drawdowns = np.maximum(max_drawdowns, drawdown)

        # Calculate statistics
        final_values = paths[:, -1]
        total_returns = (final_values - initial_capital) / initial_capital

        # Equity curve percentiles
        equity_curve = []
        for day in range(0, days + 1, max(1, days // 50)):  # 50 points
            equity_curve.append(
                EquityCurvePoint(
                    day=day,
                    percentile_5=np.percentile(paths[:, day], 5),
                    percentile_25=np.percentile(paths[:, day], 25),
                    median=np.percentile(paths[:, day], 50),
                    percentile_75=np.percentile(paths[:, day], 75),
                    percentile_95=np.percentile(paths[:, day], 95),
                )
            )

        # Drawdown distribution
        drawdown_distribution = []
        for pct in np.linspace(0, max_drawdowns.max(), 20):
            count = np.sum(max_drawdowns >= pct)
            if count > 0:
                drawdown_distribution.append(DrawdownPoint(drawdown=pct, frequency=count))

        # Calculate Sharpe and Sortino
        daily_returns_array = np.diff(paths, axis=1) / paths[:, :-1]
        mean_daily_ret = np.mean(np.mean(daily_returns_array, axis=1))
        std_daily_ret = np.std(np.mean(daily_returns_array, axis=1))
        sharpe = (mean_daily_ret * 252) / (std_daily_ret * np.sqrt(252)) if std_daily_ret > 0 else 0

        # Sortino (only downside variance)
        downside_returns = np.minimum(daily_returns_array, 0)
        downside_var = np.mean(downside_returns ** 2)
        sortino = (mean_daily_ret * 252) / np.sqrt(downside_var * 252) if downside_var > 0 else 0

        # Recovery time (mean days to recover from max drawdown)
        recovery_times = []
        for path_idx in range(num_sims):
            max_dd_val = peak_values[path_idx] * (1 - max_drawdowns[path_idx])
            for recovery_day in range(days, 0, -1):
                if paths[path_idx, recovery_day] >= peak_values[path_idx] * 0.95:
                    recovery_times.append(days - recovery_day)
                    break
        recovery_time_mean = int(np.mean(recovery_times)) if recovery_times else 0

        # Correlation drag: compare to equal-weight uncorrelated portfolio
        uncorr_vol = np.sqrt(np.sum((weights * vols) ** 2))
        actual_vol = np.sqrt(weights @ cov_matrix @ weights)
        correlation_drag = (1 - actual_vol / uncorr_vol) * 100 if uncorr_vol > 0 else 0

        # Diversification ratio
        weighted_vol = np.sum(weights * vols)
        diversification_ratio = weighted_vol / actual_vol if actual_vol > 0 else 1.0

        return PortfolioSimulationResult(
            num_simulations=num_sims,
            time_horizon_days=days,
            initial_capital=initial_capital,
            strategies=strategies,
            final_capital_mean=float(np.mean(final_values)),
            final_capital_median=float(np.median(final_values)),
            final_capital_std=float(np.std(final_values)),
            final_capital_min=float(np.min(final_values)),
            final_capital_max=float(np.max(final_values)),
            total_return_mean=float(np.mean(total_returns) * 100),
            total_return_median=float(np.median(total_returns) * 100),
            total_return_std=float(np.std(total_returns) * 100),
            sharpe_ratio=float(sharpe),
            sortino_ratio=float(sortino),
            max_drawdown_mean=float(np.mean(max_drawdowns) * 100),
            max_drawdown_worst=float(np.max(max_drawdowns) * 100),
            max_drawdown_percentile_95=float(np.percentile(max_drawdowns, 95) * 100),
            recovery_time_mean=recovery_time_mean,
            probability_profitable=float(np.mean(total_returns > 0) * 100),
            probability_double=float(np.mean(total_returns > 1.0) * 100),
            equity_curve=equity_curve,
            drawdown_distribution=drawdown_distribution,
            correlation_drag=float(correlation_drag),
            diversification_ratio=float(diversification_ratio),
        )


class PortfolioAllocator:
    """Optimize portfolio allocation given strategy metrics."""

    @staticmethod
    def allocate(request: AllocationRequest) -> AllocationResult:
        """
        Calculate optimal portfolio weights using specified method.

        Args:
            request: Strategies and optimization method

        Returns:
            Optimal weights and allocation metrics
        """
        strategies = request.strategies
        method = request.optimization_method.lower()

        # Convert to numpy arrays
        returns = np.array([s.expected_return / 100 for s in strategies])
        vols = np.array([s.volatility / 100 for s in strategies])
        strategy_names = [s.name for s in strategies]

        # Build correlation matrix
        corr_matrix = np.zeros((len(strategies), len(strategies)))
        for i, name_i in enumerate(strategy_names):
            for j, name_j in enumerate(strategy_names):
                corr_matrix[i, j] = CORRELATION_MATRIX.get(name_i, {}).get(name_j, 0.5)

        cov_matrix = np.outer(vols, vols) * corr_matrix

        # Select optimization method
        if method == "kelly":
            weights = PortfolioAllocator._kelly_allocation(
                returns, vols, cov_matrix, strategy_names, request.kelly_fraction
            )
        elif method == "sharpe":
            weights = PortfolioAllocator._sharpe_allocation(returns, cov_matrix)
        elif method == "min_variance":
            weights = PortfolioAllocator._min_variance_allocation(cov_matrix)
        elif method == "equal_weight":
            weights = np.ones(len(strategies)) / len(strategies)
        else:
            weights = np.ones(len(strategies)) / len(strategies)

        # Normalize weights
        weights = weights / np.sum(weights)

        # Calculate Kelly fractions
        kelly_fractions = {}
        for i, name in enumerate(strategy_names):
            # Simple Kelly: f* = (p * b - q) / b where p=win%, b=odds, q=loss%
            # Simplified for continuous returns
            s = strategies[i]
            if s.volatility > 0:
                kelly_f = (s.expected_return / 100) / ((s.volatility / 100) ** 2)
                kelly_f = min(kelly_f, 1.0)  # Cap at 1.0
                kelly_fractions[name] = max(kelly_f * request.kelly_fraction, 0)
            else:
                kelly_fractions[name] = 0

        # Portfolio metrics
        portfolio_return = weights @ returns
        portfolio_vol = np.sqrt(weights @ cov_matrix @ weights)
        portfolio_sharpe = portfolio_return / portfolio_vol if portfolio_vol > 0 else 0

        # Concentration metrics
        largest_weight = np.max(weights)
        herfindahl = np.sum(weights ** 2)

        return AllocationResult(
            optimization_method=method,
            optimal_weights={name: float(w) for name, w in zip(strategy_names, weights)},
            kelly_fractions={name: float(f) for name, f in kelly_fractions.items()},
            portfolio_expected_return=float(portfolio_return * 100),
            portfolio_volatility=float(portfolio_vol * 100),
            portfolio_sharpe_ratio=float(portfolio_sharpe),
            largest_weight=float(largest_weight),
            concentration_herfindahl=float(herfindahl),
            weights_sum=float(np.sum(weights)),
            is_valid=True,
        )

    @staticmethod
    def _kelly_allocation(
        returns: np.ndarray,
        vols: np.ndarray,
        cov_matrix: np.ndarray,
        names: List[str],
        kelly_frac: float,
    ) -> np.ndarray:
        """Kelly criterion allocation - growth-optimal."""
        # Inverse covariance weighted allocation
        try:
            inv_cov = np.linalg.inv(cov_matrix)
            weights = inv_cov @ returns
            weights = np.maximum(weights, 0)  # No short selling
            return weights * kelly_frac
        except np.linalg.LinAlgError:
            return np.ones(len(returns)) / len(returns)

    @staticmethod
    def _sharpe_allocation(returns: np.ndarray, cov_matrix: np.ndarray) -> np.ndarray:
        """Maximum Sharpe ratio allocation."""

        def neg_sharpe(w):
            port_ret = w @ returns
            port_vol = np.sqrt(w @ cov_matrix @ w)
            return -port_ret / port_vol if port_vol > 0 else 0

        n = len(returns)
        x0 = np.ones(n) / n
        bounds = tuple((0, 1) for _ in range(n))
        constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}

        result = minimize(
            neg_sharpe,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )

        return result.x if result.success else x0

    @staticmethod
    def _min_variance_allocation(cov_matrix: np.ndarray) -> np.ndarray:
        """Minimum variance (risk parity)."""

        def variance(w):
            return w @ cov_matrix @ w

        n = len(cov_matrix)
        x0 = np.ones(n) / n
        bounds = tuple((0, 1) for _ in range(n))
        constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}

        result = minimize(
            variance,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )

        return result.x if result.success else x0


class RegimeController:
    """Adjust portfolio for market regime."""

    @staticmethod
    def assess_regime(request: RegimeRequest) -> RegimeState:
        """
        Assess current market regime and adjust weights.

        Args:
            request: Current market conditions

        Returns:
            Regime state with adjusted weights
        """
        vix = request.current_vix
        vix_pctl = request.vix_percentile_30d
        funding = request.crypto_funding_rate
        sentiment = request.market_sentiment

        # Determine regime based on VIX
        if vix < 12:
            regime_name = "Low Vol"
            vol_multiplier = 1.2  # Can take more risk
        elif vix < 20:
            regime_name = "Normal"
            vol_multiplier = 1.0
        elif vix < 30:
            regime_name = "High Vol"
            vol_multiplier = 0.8  # Reduce risk
        else:
            regime_name = "Stress"
            vol_multiplier = 0.6  # Significant risk reduction

        # Funding rate regime
        if funding > 0.05:
            funding_regime = "extreme"
        elif funding > 0.02:
            funding_regime = "elevated"
        else:
            funding_regime = "normal"

        # Adjust weights based on regime
        base_weights = request.base_weights
        adjusted_weights = {}
        adjustment_factors = {}

        for strategy_name, base_weight in base_weights.items():
            factor = vol_multiplier

            # Sentiment adjustment
            if sentiment < -0.5:
                # Negative sentiment - reduce risky assets
                if strategy_name in ["AI", "Crypto"]:
                    factor *= 0.8
                elif strategy_name in ["MLB", "Econ"]:
                    factor *= 1.1
            elif sentiment > 0.5:
                # Positive sentiment - increase growth assets
                if strategy_name in ["AI", "Crypto"]:
                    factor *= 1.2

            # Funding rate adjustment (mainly for Crypto)
            if strategy_name == "Crypto" and funding > 0.03:
                factor *= 0.85

            adjusted_weights[strategy_name] = base_weight * factor
            adjustment_factors[strategy_name] = factor

        # Normalize weights
        total = sum(adjusted_weights.values())
        if total > 0:
            adjusted_weights = {k: v / total for k, v in adjusted_weights.items()}

        # Recommendation logic
        if vix > 30 or sentiment < -0.5:
            recommended_action = "Reduce Risk"
            explanation = f"High volatility ({vix:.1f}) and/or negative sentiment require defensive positioning"
        elif vol_multiplier > 1.0:
            recommended_action = "Increase Risk"
            explanation = "Low volatility environment supports increased risk exposure"
        elif abs(sum(adjusted_weights.values()) - 1.0) > 0.02:
            recommended_action = "Rebalance"
            explanation = "Significant drift detected from target weights"
        else:
            recommended_action = "Hold"
            explanation = "Current positioning is appropriate for regime"

        return RegimeState(
            regime_name=regime_name,
            vix_level=vix,
            vix_percentile=vix_pctl,
            funding_rate=funding,
            funding_regime=funding_regime,
            sentiment_score=sentiment,
            regime_adjusted_weights=adjusted_weights,
            regime_adjustment_factor=adjustment_factors,
            recommended_action=recommended_action,
            explanation=explanation,
        )
