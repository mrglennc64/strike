"""
Monte Carlo Portfolio Simulator for Multi-Strategy Backtesting

This module implements:
1. Strategy class: Encapsulates individual trading strategy parameters
2. PortfolioSimulator: Generates correlated monthly returns with market regime shocks
3. MonteCarloBacktest: Runs 1000+ simulations with performance aggregation

Key Features:
- Correlated return generation via Cholesky decomposition
- Market regime factors that amplify correlation during stress
- Transaction costs and slippage modeling
- Strategy attribution analysis
- Correlation drag quantification
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
from scipy.linalg import cholesky
from scipy.stats import norm
import warnings

warnings.filterwarnings('ignore')


@dataclass
class Strategy:
    """
    Represents a single trading strategy with statistical parameters.

    Attributes:
        name: Strategy identifier
        win_rate: Probability of winning trade (0-1)
        avg_win_R: Average win magnitude in risk units
        avg_loss_R: Average loss magnitude in risk units
        trades_per_month: Expected number of trades per month
        volatility: Annualized volatility
        max_drawdown: Historical maximum drawdown
        beta: Systematic risk (market sensitivity)
    """
    name: str
    win_rate: float
    avg_win_R: float
    avg_loss_R: float
    trades_per_month: int
    volatility: float
    max_drawdown: float
    beta: float

    def expected_monthly_return(self) -> float:
        """Calculate expected monthly return from strategy parameters."""
        expectancy_per_trade = (self.win_rate * self.avg_win_R -
                               (1 - self.win_rate) * self.avg_loss_R)
        monthly_expectancy = expectancy_per_trade * self.trades_per_month
        return monthly_expectancy / 100  # Convert to decimal

    def monthly_volatility(self) -> float:
        """Calculate monthly volatility from annualized volatility."""
        return self.volatility / np.sqrt(12)


class PortfolioSimulator:
    """
    Simulates portfolio performance with realistic correlation dynamics.

    This class generates correlated monthly returns for multiple strategies,
    applies market regime shocks, and models transaction costs.
    """

    def __init__(self,
                 strategies: Dict[str, Strategy],
                 weights: Dict[str, float],
                 correlation_matrix: np.ndarray,
                 transaction_cost_bps: float = 3,   # Basis points (commission)
                 slippage_bps: float = 2):
        """
        Initialize portfolio simulator.

        Args:
            strategies: Dictionary of Strategy objects
            weights: Portfolio weights (must sum to ~1.0)
            correlation_matrix: NxN correlation matrix for N strategies
            transaction_cost_bps: Transaction cost in basis points
            slippage_bps: Slippage in basis points
        """
        self.strategies = strategies
        self.weights = weights
        self.correlation_matrix = correlation_matrix
        self.transaction_cost = transaction_cost_bps / 10000
        self.slippage = slippage_bps / 10000
        self.strategy_names = list(strategies.keys())
        self.n_strategies = len(self.strategy_names)
        self.beta_vector = np.array([strategies[name].beta for name in self.strategy_names])

        # Validate correlation matrix
        self._validate_correlation_matrix()

    def _validate_correlation_matrix(self):
        """Ensure correlation matrix is valid and positive definite."""
        if self.correlation_matrix.shape != (self.n_strategies, self.n_strategies):
            raise ValueError(f"Correlation matrix shape {self.correlation_matrix.shape} "
                           f"doesn't match {self.n_strategies} strategies")

        # Check positive definiteness via eigenvalues
        evals = np.linalg.eigvalsh(self.correlation_matrix)
        if np.any(evals < -1e-10):
            # Fix slightly negative eigenvalues from rounding
            evals[evals < 1e-10] = 1e-10
            evecs = np.linalg.eigh(self.correlation_matrix)[1]
            self.correlation_matrix = evecs @ np.diag(evals) @ evecs.T

    def generate_monthly_returns(self,
                                n_months: int,
                                seed: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate monthly returns for all strategies with correlation structure.

        Args:
            n_months: Number of months to simulate
            seed: Random seed for reproducibility

        Returns:
            Tuple of:
            - raw_returns: (n_months, n_strategies) uncorrelated returns
            - correlated_returns: (n_months, n_strategies) correlated returns
            - market_regime: (n_months,) market regime factors
        """
        if seed is not None:
            np.random.seed(seed)

        raw_returns = np.zeros((n_months, self.n_strategies))

        # Generate base returns for each strategy
        for i, strat_name in enumerate(self.strategy_names):
            strategy = self.strategies[strat_name]

            for month in range(n_months):
                # Generate monthly PnL from trade outcomes
                monthly_pnl = self._generate_monthly_pnl(strategy)

                # Add idiosyncratic volatility shock
                monthly_vol = strategy.monthly_volatility()
                vol_shock = np.random.normal(0, monthly_vol)

                raw_returns[month, i] = monthly_pnl + vol_shock

        # Generate market regime factor (stress increases correlations)
        market_regime = self._generate_market_regime(n_months)

        # Apply correlation structure and market regime
        correlated_returns = self._apply_correlation_structure(raw_returns, market_regime)

        return raw_returns, correlated_returns, market_regime

    def _generate_monthly_pnl(self, strategy: Strategy) -> float:
        """
        Generate monthly PnL from individual trade outcomes.

        Uses binomial distribution of wins/losses weighted by R-multiples.
        """
        n_trades = np.random.poisson(strategy.trades_per_month)

        if n_trades == 0:
            return 0.0

        monthly_pnl = 0.0
        for _ in range(n_trades):
            # Generate trade outcome
            if np.random.random() < strategy.win_rate:
                trade_return = strategy.avg_win_R / 100
            else:
                trade_return = -strategy.avg_loss_R / 100

            # Deduct transaction costs and slippage per trade
            trade_return -= (self.transaction_cost + self.slippage)
            monthly_pnl += trade_return

        return monthly_pnl

    def _generate_market_regime(self, n_months: int) -> np.ndarray:
        """
        Generate market regime factors.

        Normal regime: ~1.0 (normal correlations)
        Stress regime: >1.0 (elevated correlations)

        Uses AR(1) process to create persistence in stress periods.
        """
        regime = np.ones(n_months)
        stress_prob = 0.05  # 5% chance of stress each month
        stress_persistence = 0.7  # 70% chance stress continues

        in_stress = False
        for month in range(1, n_months):
            if in_stress:
                # In stress, likely to continue
                if np.random.random() > stress_persistence:
                    in_stress = False
            else:
                # Normal, small chance of entering stress
                if np.random.random() < stress_prob:
                    in_stress = True

            if in_stress:
                # Stress regime: correlations increase by 20-40%
                regime[month] = np.random.uniform(1.2, 1.4)

        return regime

    def _apply_correlation_structure(self,
                                     raw_returns: np.ndarray,
                                     market_regime: np.ndarray) -> np.ndarray:
        """
        Apply correlation structure to independent returns via Cholesky decomposition.

        Preserves mean and variance of raw returns while introducing correlation.
        Then amplify correlations during stress regimes.
        """
        n_months, n_strats = raw_returns.shape

        # Perform Cholesky decomposition
        try:
            L = cholesky(self.correlation_matrix, lower=True)
        except np.linalg.LinAlgError:
            print("Warning: Correlation matrix not positive definite, fixing...")
            evals, evecs = np.linalg.eigh(self.correlation_matrix)
            evals[evals < 1e-10] = 1e-10
            fixed_corr = evecs @ np.diag(evals) @ evecs.T
            L = cholesky(fixed_corr, lower=True)

        # Apply Cholesky transform to all months at once
        # First, standardize each strategy across time
        means = raw_returns.mean(axis=0)
        stds = raw_returns.std(axis=0) + 1e-10
        standardized = (raw_returns - means) / stds

        # Apply Cholesky: this introduces correlation
        correlated_std = standardized @ L.T

        # Restore original scale (mean and volatility)
        correlated_returns = correlated_std * stds + means

        # Apply market regime shock to increase correlation during stress
        for month in range(n_months):
            regime_factor = market_regime[month]
            if regime_factor > 1.0:
                # During stress, pull returns toward portfolio mean
                portfolio_mean = correlated_returns[month].mean()
                stress_magnitude = (regime_factor - 1.0) * 0.25  # Max 25% pull toward mean
                correlated_returns[month] = (
                    correlated_returns[month] * (1 - stress_magnitude) +
                    portfolio_mean * stress_magnitude
                )

        return correlated_returns

    def simulate_portfolio(self,
                          n_months: int = 120,
                          seed: Optional[int] = None) -> Dict:
        """
        Simulate complete portfolio for n_months with all correlations.

        Returns:
            Dictionary containing all simulation outputs
        """
        raw_returns, correlated_returns, market_regime = self.generate_monthly_returns(
            n_months, seed
        )

        # Weight individual strategy returns
        portfolio_returns = np.zeros(n_months)
        strategy_contributions = np.zeros((n_months, self.n_strategies))

        for i, strat_name in enumerate(self.strategy_names):
            weight = self.weights[strat_name]
            strategy_contributions[:, i] = correlated_returns[:, i] * weight
            portfolio_returns += correlated_returns[:, i] * weight

        # Build equity curves
        equity_curve = np.cumprod(1 + portfolio_returns)

        strategy_cumulative = np.zeros((n_months, self.n_strategies))
        for i in range(self.n_strategies):
            strategy_cumulative[:, i] = np.cumprod(1 + correlated_returns[:, i])

        return {
            'portfolio_returns': portfolio_returns,
            'strategy_returns': correlated_returns,
            'raw_returns': raw_returns,
            'equity_curve': equity_curve,
            'strategy_cumulative': strategy_cumulative,
            'strategy_contributions': strategy_contributions,
            'market_regime': market_regime
        }


class MonteCarloBacktest:
    """
    Orchestrates multiple Monte Carlo simulations and aggregates results.

    Runs many independent simulations and computes performance statistics,
    risk metrics, correlation drag, and strategy attribution.
    """

    def __init__(self,
                 simulator: PortfolioSimulator,
                 n_simulations: int = 1000,
                 n_months: int = 120,
                 risk_free_rate: float = 0.04):
        """
        Initialize Monte Carlo backtest.

        Args:
            simulator: PortfolioSimulator instance
            n_simulations: Number of Monte Carlo paths
            n_months: Length of each simulation in months
            risk_free_rate: Annual risk-free rate for Sharpe calculation
        """
        self.simulator = simulator
        self.n_simulations = n_simulations
        self.n_months = n_months
        self.risk_free_rate = risk_free_rate
        self.monthly_rf = risk_free_rate / 12

        self.results = {
            'equity_curves': [],
            'cumulative_returns': [],
            'sharpe_ratios': [],
            'max_drawdowns': [],
            'calmar_ratios': [],
            'monthly_returns_list': [],
            'strategy_attributions': [],
            'correlation_costs': [],
            'final_values': []
        }

    def run(self, verbose: bool = True) -> Dict:
        """
        Execute all Monte Carlo simulations.

        Args:
            verbose: Print progress updates

        Returns:
            Aggregated results dictionary
        """
        for sim in range(self.n_simulations):
            if verbose and (sim + 1) % 100 == 0:
                print(f"  Simulation {sim + 1:4d}/{self.n_simulations}")

            # Run single simulation
            result = self.simulator.simulate_portfolio(self.n_months, seed=None)

            # Extract key outputs
            equity_curve = result['equity_curve']
            monthly_returns = result['portfolio_returns']

            # Store for aggregation
            self.results['equity_curves'].append(equity_curve)
            self.results['cumulative_returns'].append(equity_curve[-1] - 1)
            self.results['final_values'].append(equity_curve[-1])
            self.results['monthly_returns_list'].append(monthly_returns)
            self.results['strategy_attributions'].append(result['strategy_contributions'])

            # Calculate risk metrics
            sharpe = self._calculate_sharpe(monthly_returns)
            max_dd = self._calculate_max_drawdown(equity_curve)
            calmar = self._calculate_calmar(monthly_returns, max_dd)

            self.results['sharpe_ratios'].append(sharpe)
            self.results['max_drawdowns'].append(max_dd)
            self.results['calmar_ratios'].append(calmar)

            # Calculate correlation drag
            corr_cost = self._calculate_correlation_cost(
                result['raw_returns'],
                result['strategy_returns']
            )
            self.results['correlation_costs'].append(corr_cost)

        return self._aggregate_results()

    def _calculate_sharpe(self, monthly_returns: np.ndarray) -> float:
        """Calculate annualized Sharpe ratio."""
        excess_returns = monthly_returns - self.monthly_rf
        if np.std(excess_returns) > 1e-8:
            sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(12)
        else:
            sharpe = 0.0
        return sharpe

    def _calculate_max_drawdown(self, equity_curve: np.ndarray) -> float:
        """Calculate maximum drawdown from equity curve."""
        running_max = np.maximum.accumulate(equity_curve)
        drawdown = (equity_curve - running_max) / running_max
        return np.min(drawdown)

    def _calculate_calmar(self, monthly_returns: np.ndarray, max_dd: float) -> float:
        """Calculate Calmar ratio (annual return / abs max drawdown)."""
        annual_return = (1 + np.mean(monthly_returns)) ** 12 - 1
        if abs(max_dd) > 1e-8:
            return annual_return / abs(max_dd)
        else:
            return 0.0

    def _calculate_correlation_cost(self,
                                   raw_returns: np.ndarray,
                                   correlated_returns: np.ndarray) -> float:
        """
        Quantify correlation drag as difference in cumulative returns.

        If strategies were perfectly uncorrelated, returns would be:
        portfolio_return_uncorr = sum(weight_i * raw_return_i)

        With correlation, actual return is lower due to diversification loss.
        """
        weights = np.array([self.simulator.weights[name]
                           for name in self.simulator.strategy_names])

        # Cumulative returns under each scenario
        uncorr_cumulative = np.cumprod(1 + (raw_returns @ weights))
        corr_cumulative = np.cumprod(1 + (correlated_returns @ weights))

        # Cost is difference in final value
        cost = uncorr_cumulative[-1] - corr_cumulative[-1]
        return cost

    def _aggregate_results(self) -> Dict:
        """Aggregate statistics across all simulations."""
        equity_curves = np.array(self.results['equity_curves'])
        cumulative_returns = np.array(self.results['cumulative_returns'])
        final_values = np.array(self.results['final_values'])
        sharpe_ratios = np.array(self.results['sharpe_ratios'])
        max_drawdowns = np.array(self.results['max_drawdowns'])
        calmar_ratios = np.array(self.results['calmar_ratios'])
        correlation_costs = np.array(self.results['correlation_costs'])

        # Strategy attribution
        strategy_attributions = np.array(self.results['strategy_attributions'])
        mean_attribution = strategy_attributions.mean(axis=0).mean(axis=0)

        # Win rate at breaking even (how many sims had positive return)
        win_rate = (cumulative_returns > 0).sum() / len(cumulative_returns)

        results = {
            'n_simulations': self.n_simulations,
            'n_months': self.n_months,

            # Return distribution
            'mean_cumulative_return': cumulative_returns.mean(),
            'median_cumulative_return': np.median(cumulative_returns),
            'std_cumulative_return': cumulative_returns.std(),
            'min_cumulative_return': cumulative_returns.min(),
            'max_cumulative_return': cumulative_returns.max(),
            'percentile_5': np.percentile(cumulative_returns, 5),
            'percentile_25': np.percentile(cumulative_returns, 25),
            'percentile_75': np.percentile(cumulative_returns, 75),
            'percentile_95': np.percentile(cumulative_returns, 95),
            'probability_positive': win_rate,

            # Risk metrics
            'mean_sharpe': sharpe_ratios.mean(),
            'median_sharpe': np.median(sharpe_ratios),
            'std_sharpe': sharpe_ratios.std(),
            'min_sharpe': sharpe_ratios.min(),

            'mean_max_drawdown': max_drawdowns.mean(),
            'median_max_drawdown': np.median(max_drawdowns),
            'worst_max_drawdown': max_drawdowns.min(),
            'best_max_drawdown': max_drawdowns.max(),

            'mean_calmar': calmar_ratios.mean(),
            'median_calmar': np.median(calmar_ratios),

            # Correlation impact analysis
            'mean_correlation_cost': correlation_costs.mean(),
            'std_correlation_cost': correlation_costs.std(),
            'median_correlation_cost': np.median(correlation_costs),
            'total_correlation_cost_bps': correlation_costs.mean() * 10000,
            'correlation_cost_percentile_95': np.percentile(correlation_costs, 95),

            # Strategy attribution (monthly contribution to portfolio return)
            'strategy_attribution': {
                name: contrib for name, contrib in zip(
                    self.simulator.strategy_names, mean_attribution
                )
            },

            # Percentile equity curves for visualization
            'months': np.arange(self.n_months),
            'equity_curves_percentile_5': np.percentile(equity_curves, 5, axis=0),
            'equity_curves_percentile_10': np.percentile(equity_curves, 10, axis=0),
            'equity_curves_percentile_25': np.percentile(equity_curves, 25, axis=0),
            'equity_curves_mean': equity_curves.mean(axis=0),
            'equity_curves_median': np.median(equity_curves, axis=0),
            'equity_curves_percentile_75': np.percentile(equity_curves, 75, axis=0),
            'equity_curves_percentile_90': np.percentile(equity_curves, 90, axis=0),
            'equity_curves_percentile_95': np.percentile(equity_curves, 95, axis=0),

            # Raw data for custom analysis
            'all_cumulative_returns': cumulative_returns,
            'all_sharpe_ratios': sharpe_ratios,
            'all_max_drawdowns': max_drawdowns,
            'all_equity_curves': equity_curves,
        }

        return results


def create_default_strategies() -> Dict[str, Strategy]:
    """
    Create 5 realistic trading strategies with parameters.

    Parameters assume:
    - avg_win_R / avg_loss_R are in percentage points (e.g., 0.8 = 0.8% per winning trade)
    - Risk per trade: ~0.5% of portfolio
    - Transaction costs: 10 bps per trade
    - Target: 15-25% annualized return after all costs

    Realistic market segments:
    - MLB: Low volatility, predictable, 2-3% monthly
    - Crypto: High volatility, lower win rate, 1-2% monthly
    - Earnings: Medium volatility, event-driven, 2-3% monthly
    - AI: Tech correlated, moderate, 2-3% monthly
    - Econ: Macro-driven, defensive, 1-2% monthly
    """
    return {
        'MLB': Strategy(
            name='MLB Strikeout Edge',
            win_rate=0.56,
            avg_win_R=0.50,        # 0.5% per win
            avg_loss_R=0.30,       # 0.3% per loss
            trades_per_month=10,   # ~2.5 trades per week
            volatility=0.12,
            max_drawdown=-0.15,
            beta=0.1
        ),
        'Crypto': Strategy(
            name='Crypto Volatility',
            win_rate=0.50,
            avg_win_R=0.60,        # Higher vol trade, bigger wins
            avg_loss_R=0.40,
            trades_per_month=6,    # Lower frequency, higher variance
            volatility=0.35,
            max_drawdown=-0.30,
            beta=1.4
        ),
        'Earnings': Strategy(
            name='Earnings Surprise',
            win_rate=0.57,
            avg_win_R=0.55,        # Event-driven edge
            avg_loss_R=0.32,
            trades_per_month=8,    # Event-driven timing
            volatility=0.18,
            max_drawdown=-0.20,
            beta=1.0
        ),
        'AI': Strategy(
            name='AI Index Pairs',
            win_rate=0.55,
            avg_win_R=0.48,        # Decent R-multiple
            avg_loss_R=0.30,
            trades_per_month=9,    # Moderate frequency
            volatility=0.22,
            max_drawdown=-0.25,
            beta=1.2
        ),
        'Econ': Strategy(
            name='Economic Indicators',
            win_rate=0.53,
            avg_win_R=0.40,        # Conservative
            avg_loss_R=0.30,
            trades_per_month=7,    # Low frequency, macro-based
            volatility=0.14,
            max_drawdown=-0.12,
            beta=0.6
        )
    }


def create_correlation_matrix() -> np.ndarray:
    """
    Create realistic correlation matrix for 5 strategies.

    Correlations reflect market structure:
    - MLB uncorrelated to most (low market beta)
    - Crypto & AI highly correlated (tech/risk-on)
    - Earnings & AI moderately correlated (systematic equity exposure)
    - Econ defensive (negative correlation to risk assets during stress)

    Returns:
        5x5 symmetric positive definite correlation matrix
    """
    corr = np.array([
        [1.00, 0.08, 0.15, 0.12, 0.10],   # MLB: low correlation to all
        [0.08, 1.00, 0.35, 0.45, 0.05],   # Crypto: correlated with AI, uncorr with Econ
        [0.15, 0.35, 1.00, 0.75, 0.20],   # Earnings: high correlation with AI
        [0.12, 0.45, 0.75, 1.00, 0.15],   # AI: high correlation with Earnings/Crypto
        [0.10, 0.05, 0.20, 0.15, 1.00]    # Econ: low correlation, defensive
    ])

    return corr


def plot_results(results: Dict, output_file: str = 'portfolio_equity_curve.png'):
    """
    Plot equity curves with percentile bands.

    Args:
        results: Output from MonteCarloBacktest.run()
        output_file: Path to save figure
    """
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))

    months = results['months']

    # Equity curves
    ax = axes[0, 0]
    ax.fill_between(months, results['equity_curves_percentile_5'],
                    results['equity_curves_percentile_95'], alpha=0.15, label='5-95%')
    ax.fill_between(months, results['equity_curves_percentile_25'],
                    results['equity_curves_percentile_75'], alpha=0.25, label='25-75%')
    ax.plot(months, results['equity_curves_mean'], label='Mean', linewidth=2, color='darkgreen')
    ax.plot(months, results['equity_curves_median'], label='Median', linewidth=1.5,
            color='darkblue', linestyle='--')
    ax.set_xlabel('Months', fontsize=10)
    ax.set_ylabel('Equity Multiple', fontsize=10)
    ax.set_title('Portfolio Equity Curves (1000 Simulations)', fontsize=11, fontweight='bold')
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)

    # Return distribution
    ax = axes[0, 1]
    ax.hist(results['all_cumulative_returns'] * 100, bins=50, edgecolor='black', alpha=0.7, color='steelblue')
    ax.axvline(results['mean_cumulative_return'] * 100, color='red', linestyle='--',
               linewidth=2, label=f"Mean: {results['mean_cumulative_return']:.1%}")
    ax.axvline(0, color='black', linestyle='-', linewidth=1, alpha=0.5)
    ax.set_xlabel('Cumulative Return (%)', fontsize=10)
    ax.set_ylabel('Frequency', fontsize=10)
    ax.set_title('10-Year Return Distribution', fontsize=11, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')

    # Sharpe ratio distribution
    ax = axes[1, 0]
    ax.hist(results['all_sharpe_ratios'], bins=50, edgecolor='black', alpha=0.7, color='coral')
    ax.axvline(results['mean_sharpe'], color='red', linestyle='--',
               linewidth=2, label=f"Mean: {results['mean_sharpe']:.2f}")
    ax.set_xlabel('Sharpe Ratio', fontsize=10)
    ax.set_ylabel('Frequency', fontsize=10)
    ax.set_title('Sharpe Ratio Distribution', fontsize=11, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')

    # Max drawdown distribution
    ax = axes[1, 1]
    ax.hist(results['all_max_drawdowns'] * 100, bins=50, edgecolor='black', alpha=0.7, color='lightcoral')
    ax.axvline(results['mean_max_drawdown'] * 100, color='red', linestyle='--',
               linewidth=2, label=f"Mean: {results['mean_max_drawdown']:.1%}")
    ax.set_xlabel('Maximum Drawdown (%)', fontsize=10)
    ax.set_ylabel('Frequency', fontsize=10)
    ax.set_title('Maximum Drawdown Distribution', fontsize=11, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\nPlot saved to: {output_file}")
    plt.close()


def print_results(results: Dict):
    """Pretty-print Monte Carlo backtest results."""
    print("\n" + "="*70)
    print("MONTE CARLO PORTFOLIO BACKTEST RESULTS".center(70))
    print("="*70)
    print(f"Simulations: {results['n_simulations']} | Period: {results['n_months']} months ({results['n_months']/12:.1f} years)")
    print("="*70)

    print("\nRETURN STATISTICS:")
    print(f"  Mean Cumulative Return:     {results['mean_cumulative_return']:>10.2%}")
    print(f"  Median Cumulative Return:   {results['median_cumulative_return']:>10.2%}")
    print(f"  Std Dev:                    {results['std_cumulative_return']:>10.2%}")
    print(f"  Probability of Profit:      {results['probability_positive']:>10.1%}")
    print(f"\n  Return Percentiles:")
    print(f"    5th:                      {results['percentile_5']:>10.2%}")
    print(f"    25th:                     {results['percentile_25']:>10.2%}")
    print(f"    75th:                     {results['percentile_75']:>10.2%}")
    print(f"    95th:                     {results['percentile_95']:>10.2%}")

    print("\nRISK METRICS:")
    print(f"  Mean Sharpe Ratio:          {results['mean_sharpe']:>10.2f}")
    print(f"  Median Sharpe Ratio:        {results['median_sharpe']:>10.2f}")
    print(f"  Min Sharpe Ratio:           {results['min_sharpe']:>10.2f}")
    print(f"\n  Mean Max Drawdown:          {results['mean_max_drawdown']:>10.2%}")
    print(f"  Worst Max Drawdown:         {results['worst_max_drawdown']:>10.2%}")
    print(f"\n  Mean Calmar Ratio:          {results['mean_calmar']:>10.2f}")
    print(f"  Median Calmar Ratio:        {results['median_calmar']:>10.2f}")

    print("\nCORRELATION IMPACT ANALYSIS:")
    print(f"  Mean Correlation Drag:      {results['mean_correlation_cost']:>10.4f}")
    print(f"  Correlation Drag (bps):     {results['total_correlation_cost_bps']:>10.1f} bps")
    print(f"  95th Percentile Drag:       {results['correlation_cost_percentile_95']:>10.4f}")
    print(f"  Drag % of Mean Return:      {(results['mean_correlation_cost'] / max(results['mean_cumulative_return'], 0.01) * 100):>9.1f}%")

    print("\nSTRATEGY ATTRIBUTION (Avg Monthly Contribution):")
    for strategy, contrib in results['strategy_attribution'].items():
        print(f"  {strategy:<15}          {contrib:>10.6f} ({contrib*100:>6.2f}%)")

    print("\n" + "="*70)


# ============================================================================
# EXAMPLE USAGE: MLB + Earnings + Crypto Portfolio
# ============================================================================

if __name__ == "__main__":
    print("\nBuilding Portfolio Simulator...")

    # Create strategies
    all_strategies = create_default_strategies()
    all_correlation_matrix = create_correlation_matrix()

    # Select subset: MLB, Earnings, Crypto (3-strategy diversified portfolio)
    selected_strategies = {
        'MLB': all_strategies['MLB'],
        'Earnings': all_strategies['Earnings'],
        'Crypto': all_strategies['Crypto']
    }

    # 3x3 correlation matrix for subset
    selected_correlation = np.array([
        [1.00, 0.15, 0.08],    # MLB
        [0.15, 1.00, 0.35],    # Earnings
        [0.08, 0.35, 1.00]     # Crypto
    ])

    # Allocate weights (MLB conservative, Earnings core, Crypto tactical)
    weights = {
        'MLB': 0.35,
        'Earnings': 0.45,
        'Crypto': 0.20
    }

    # Create simulator
    simulator = PortfolioSimulator(
        strategies=selected_strategies,
        weights=weights,
        correlation_matrix=selected_correlation,
        transaction_cost_bps=3,    # 3 bps commission
        slippage_bps=2              # 2 bps slippage (institutional)
    )

    # Run 1000 Monte Carlo simulations
    print("\nRunning 1000 Monte Carlo simulations over 10 years...")
    backtest = MonteCarloBacktest(
        simulator=simulator,
        n_simulations=1000,
        n_months=120,
        risk_free_rate=0.04
    )

    results = backtest.run(verbose=True)

    # Print results
    print_results(results)

    # Plot equity curves and distributions
    plot_results(results, 'portfolio_mc_backtest.png')

    # Detailed correlation impact analysis
    print("\n" + "="*70)
    print("CORRELATION DRAG DEEP DIVE".center(70))
    print("="*70)
    print(f"\nTotal correlation drag over {results['n_months']} months:")
    print(f"  Average: ${results['mean_correlation_cost']*1000:>8.2f}k per ${1000}k portfolio")
    print(f"  95th percentile: ${results['correlation_cost_percentile_95']*1000:>8.2f}k per ${1000}k")
    print(f"\nDrag in basis points: {results['total_correlation_cost_bps']:.1f} bps")
    print(f"This is the cost of diversification imperfection.")

    print(f"\nImplication:")
    print(f"  - Without correlation: Expected return would be {(results['mean_cumulative_return'] + results['mean_correlation_cost']):.2%}")
    print(f"  - With correlation: Actual expected return is {results['mean_cumulative_return']:.2%}")
    print(f"  - Correlation cost: {results['mean_correlation_cost']:.2%}")

    print("\n" + "="*70)
