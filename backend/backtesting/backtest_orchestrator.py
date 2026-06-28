"""
Portfolio Backtest Orchestrator

Main entry point that coordinates:
1. Loading vertical data
2. Computing metrics
3. Building correlation matrix
4. Running 3 allocation strategies
5. Executing 1000 MC simulations each
6. Generating all reports and visualizations
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from portfolio_simulator import (
    Strategy, PortfolioSimulator, MonteCarloBacktest,
    print_results, plot_results
)

from .vertical_data_loader import (
    VerticalDataLoader,
    MLBDataLoader,
    EarningsDataLoader,
    CryptoDataLoader,
    AIReleasesDataLoader,
    EconomicsDataLoader,
    VerticalMetrics,
)

from .allocation_strategies import (
    AllocationStrategy,
    EqualWeightStrategy,
    HybridKellyRiskParity,
    RegimeControlledAllocation,
    RegimeIndicators,
)


class BacktestOrchestrator:
    """
    Orchestrates complete multi-vertical portfolio backtesting.

    High-level flow:
    1. Load trades from all 5 verticals
    2. Compute metrics (win_rate, volatility, etc)
    3. Build correlation matrix from historical returns
    4. Define 3 allocation strategies
    5. Run 1000 MC simulations for each strategy
    6. Generate comprehensive reports
    7. Validate regime controller effectiveness
    """

    def __init__(self,
                 start_date: datetime = None,
                 end_date: datetime = None,
                 n_simulations: int = 1000,
                 n_months_simulation: int = 120,
                 risk_free_rate: float = 0.04,
                 output_dir: str = "./backtest_results"):
        """
        Initialize orchestrator.

        Args:
            start_date: Backtest start date (default: 3 years ago)
            end_date: Backtest end date (default: today)
            n_simulations: Number of MC simulations per strategy
            n_months_simulation: Length of each simulation (months)
            risk_free_rate: Annual risk-free rate for Sharpe
            output_dir: Directory for output files
        """
        self.end_date = end_date or datetime.now()
        self.start_date = start_date or (self.end_date - timedelta(days=1095))
        self.n_simulations = n_simulations
        self.n_months_simulation = n_months_simulation
        self.risk_free_rate = risk_free_rate
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Will be populated during run
        self.vertical_metrics: Dict[str, VerticalMetrics] = {}
        self.correlation_matrix: np.ndarray = None
        self.strategies: Dict[str, Strategy] = {}
        self.results: Dict = {}

    def run_full_backtest(self) -> Dict:
        """
        Execute complete backtesting pipeline.

        Returns:
            Dictionary with results from all 3 strategies
        """
        print("\n" + "="*80)
        print("MULTI-VERTICAL PORTFOLIO BACKTEST ORCHESTRATOR".center(80))
        print("="*80)

        # Phase 1: Load and aggregate vertical data
        print("\n[PHASE 1] Loading and aggregating vertical data...")
        self._load_vertical_data()

        # Phase 2: Build correlation matrix
        print("\n[PHASE 2] Building correlation matrix...")
        self._build_correlation_matrix()

        # Phase 3: Create allocation strategies
        print("\n[PHASE 3] Creating allocation strategies...")
        strategies_dict = self._create_allocation_strategies()

        # Phase 4: Run 3 parallel backtests
        print("\n[PHASE 4] Running 1000 Monte Carlo simulations per strategy...")
        self.results = self._run_all_strategies(strategies_dict)

        # Phase 5: Generate reports
        print("\n[PHASE 5] Generating reports and visualizations...")
        self._generate_reports()

        # Phase 6: Validate regime controller
        print("\n[PHASE 6] Validating regime controller effectiveness...")
        validation = self._validate_regime_controller()

        return {
            'vertical_metrics': self.vertical_metrics,
            'correlation_matrix': self.correlation_matrix,
            'backtest_results': self.results,
            'regime_validation': validation,
            'output_dir': str(self.output_dir),
        }

    def _load_vertical_data(self):
        """Load trade data from all 5 verticals and compute metrics."""
        loaders = [
            MLBDataLoader(self.start_date, self.end_date),
            EarningsDataLoader(self.start_date, self.end_date),
            CryptoDataLoader(self.start_date, self.end_date),
            AIReleasesDataLoader(self.start_date, self.end_date),
            EconomicsDataLoader(self.start_date, self.end_date),
        ]

        print(f"\n  Date range: {self.start_date.date()} to {self.end_date.date()}")

        for loader in loaders:
            print(f"\n  Loading {loader.get_vertical_name()}...")
            metrics = loader.aggregate_metrics()
            self.vertical_metrics[metrics.name] = metrics

            print(f"    Win Rate: {metrics.win_rate:.1%}")
            print(f"    Avg Win R: {metrics.avg_win_R:.2f}%")
            print(f"    Avg Loss R: {metrics.avg_loss_R:.2f}%")
            print(f"    Trades/Month: {metrics.trades_per_month:.1f}")
            print(f"    Volatility: {metrics.volatility:.1%}")
            print(f"    Max Drawdown: {metrics.max_drawdown:.1%}")
            print(f"    Sharpe Ratio: {metrics.sharpe_ratio:.2f}")

    def _build_correlation_matrix(self):
        """Build correlation matrix from historical monthly returns."""
        # Get all monthly returns
        monthly_returns_dict = {}
        n_months = None

        for name, metrics in self.vertical_metrics.items():
            monthly_returns_dict[name] = metrics.monthly_returns
            if n_months is None:
                n_months = len(metrics.monthly_returns)

        # Align all to same length (pad if needed)
        min_length = min(len(r) for r in monthly_returns_dict.values())

        # Create dataframe
        df = pd.DataFrame({
            name: monthly_returns[:min_length]
            for name, monthly_returns in monthly_returns_dict.items()
        })

        # Compute correlation
        correlation_matrix = df.corr().values

        # Ensure positive definiteness
        try:
            np.linalg.cholesky(correlation_matrix)
        except np.linalg.LinAlgError:
            # Fix eigenvalues
            evals, evecs = np.linalg.eigh(correlation_matrix)
            evals[evals < 1e-10] = 1e-10
            correlation_matrix = evecs @ np.diag(evals) @ evecs.T

        self.correlation_matrix = correlation_matrix

        print(f"\n  Correlation Matrix ({len(self.vertical_metrics)} x {len(self.vertical_metrics)}):")
        print("  " + "\t".join([f"{v.name:8}" for v in self.vertical_metrics.values()]))
        for i, row in enumerate(correlation_matrix):
            print(f"  {list(self.vertical_metrics.keys())[i]:8}" + "\t".join([f"{v:8.2f}" for v in row]))

        # Average correlation
        triu_indices = np.triu_indices(len(correlation_matrix), k=1)
        avg_corr = correlation_matrix[triu_indices].mean()
        print(f"\n  Average Correlation: {avg_corr:.3f}")

    def _create_allocation_strategies(self) -> Dict[str, AllocationStrategy]:
        """Create the 3 allocation strategies."""
        strategies = {
            'Equal Weight': EqualWeightStrategy(),
            'Hybrid Kelly + Risk Parity': HybridKellyRiskParity(),
            'Regime-Controlled': RegimeControlledAllocation(),
        }

        # Print strategy weights
        verticals_list = list(self.vertical_metrics.values())

        for strategy_name, strategy in strategies.items():
            weights = strategy.calculate_weights(verticals_list)
            print(f"\n  {strategy_name}:")
            for vertical_name, weight in weights.items():
                print(f"    {vertical_name:15} {weight:6.1%}")

        return strategies

    def _run_all_strategies(self, strategies: Dict[str, AllocationStrategy]) -> Dict:
        """Run 1000 MC simulations for each of 3 strategies."""
        results = {}
        verticals_list = list(self.vertical_metrics.values())

        for strategy_name, strategy in strategies.items():
            print(f"\n  Running {strategy_name}...")

            # Get weights
            weights = strategy.calculate_weights(verticals_list)

            # Convert VerticalMetrics to Strategy objects for simulator
            strategy_objects = {}
            weight_dict = {}

            for v in verticals_list:
                strategy_objects[v.name] = Strategy(
                    name=v.name,
                    win_rate=v.win_rate,
                    avg_win_R=v.avg_win_R,
                    avg_loss_R=v.avg_loss_R,
                    trades_per_month=int(np.ceil(v.trades_per_month)),
                    volatility=v.volatility,
                    max_drawdown=v.max_drawdown,
                    beta=v.correlation_to_spy
                )
                weight_dict[v.name] = weights[v.name]

            # Create simulator
            simulator = PortfolioSimulator(
                strategies=strategy_objects,
                weights=weight_dict,
                correlation_matrix=self.correlation_matrix,
                transaction_cost_bps=10,
                slippage_bps=5
            )

            # Run MC backtest
            backtest = MonteCarloBacktest(
                simulator=simulator,
                n_simulations=self.n_simulations,
                n_months=self.n_months_simulation,
                risk_free_rate=self.risk_free_rate
            )

            mc_results = backtest.run(verbose=False)
            results[strategy_name] = {
                'backtest': mc_results,
                'weights': weights,
            }

        return results

    def _generate_reports(self):
        """Generate all reports and visualizations."""
        # Summary report
        self._generate_summary_report()

        # Equity curves overlay
        self._generate_equity_curves_overlay()

        # Sharpe comparison table
        self._generate_sharpe_comparison_table()

        # Max drawdown comparison
        self._generate_max_drawdown_comparison()

        # Monthly performance grid
        self._generate_monthly_performance_grid()

        # Correlation impact
        self._generate_correlation_impact_report()

    def _generate_summary_report(self):
        """Generate text summary report."""
        output_file = self.output_dir / "01_SUMMARY_REPORT.txt"

        with open(output_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("PORTFOLIO BACKTEST SUMMARY REPORT\n")
            f.write("="*80 + "\n\n")

            f.write(f"Test Period: {self.start_date.date()} to {self.end_date.date()}\n")
            f.write(f"Simulations: {self.n_simulations} per strategy\n")
            f.write(f"Simulation Period: {self.n_months_simulation} months ({self.n_months_simulation/12:.1f} years)\n")
            f.write(f"Risk-Free Rate: {self.risk_free_rate:.1%}\n\n")

            f.write("="*80 + "\n")
            f.write("VERTICAL METRICS\n")
            f.write("="*80 + "\n\n")

            for name, metrics in self.vertical_metrics.items():
                f.write(f"\n{name}:\n")
                f.write(f"  Win Rate:          {metrics.win_rate:.1%}\n")
                f.write(f"  Avg Win R:         {metrics.avg_win_R:.2f}%\n")
                f.write(f"  Avg Loss R:        {metrics.avg_loss_R:.2f}%\n")
                f.write(f"  Trades/Month:      {metrics.trades_per_month:.1f}\n")
                f.write(f"  Volatility:        {metrics.volatility:.1%}\n")
                f.write(f"  Max Drawdown:      {metrics.max_drawdown:.1%}\n")
                f.write(f"  Sharpe:            {metrics.sharpe_ratio:.2f}\n")
                f.write(f"  Calmar:            {metrics.calmar_ratio:.2f}\n")

            f.write("\n" + "="*80 + "\n")
            f.write("STRATEGY RESULTS\n")
            f.write("="*80 + "\n\n")

            # Extract and display key metrics for each strategy
            for strategy_name, result in self.results.items():
                mc_results = result['backtest']
                weights = result['weights']

                f.write(f"\n{strategy_name}:\n")
                f.write(f"\n  Allocation:\n")
                for vertical, weight in weights.items():
                    f.write(f"    {vertical:15} {weight:6.1%}\n")

                f.write(f"\n  Return Statistics:\n")
                f.write(f"    Mean Return:       {mc_results['mean_cumulative_return']:>10.2%}\n")
                f.write(f"    Median Return:     {mc_results['median_cumulative_return']:>10.2%}\n")
                f.write(f"    Std Dev:           {mc_results['std_cumulative_return']:>10.2%}\n")
                f.write(f"    Prob of Profit:    {mc_results['probability_positive']:>10.1%}\n")
                f.write(f"    5th Percentile:    {mc_results['percentile_5']:>10.2%}\n")
                f.write(f"    95th Percentile:   {mc_results['percentile_95']:>10.2%}\n")

                f.write(f"\n  Risk Metrics:\n")
                f.write(f"    Mean Sharpe:       {mc_results['mean_sharpe']:>10.2f}\n")
                f.write(f"    Median Sharpe:     {mc_results['median_sharpe']:>10.2f}\n")
                f.write(f"    Std Sharpe:        {mc_results['std_sharpe']:>10.2f}\n")
                f.write(f"    Mean Max DD:       {mc_results['mean_max_drawdown']:>10.2%}\n")
                f.write(f"    Worst Max DD:      {mc_results['worst_max_drawdown']:>10.2%}\n")

                f.write(f"\n  Correlation Impact:\n")
                f.write(f"    Avg Drag:          ${mc_results['mean_correlation_cost']*1000:>9.2f}k\n")
                f.write(f"    Drag (bps):        {mc_results['total_correlation_cost_bps']:>10.1f}\n")

        print(f"    -> Summary report saved: {output_file}")

    def _generate_equity_curves_overlay(self):
        """Plot equity curves for all 3 strategies overlaid."""
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(14, 8))

        colors = ['steelblue', 'darkgreen', 'coral']
        strategy_names = list(self.results.keys())

        for idx, strategy_name in enumerate(strategy_names):
            result = self.results[strategy_name]['backtest']
            months = result['months']

            ax.fill_between(months,
                           result['equity_curves_percentile_5'],
                           result['equity_curves_percentile_95'],
                           alpha=0.08,
                           color=colors[idx])

            ax.plot(months,
                   result['equity_curves_mean'],
                   label=f'{strategy_name} (mean)',
                   linewidth=2.5,
                   color=colors[idx])

            ax.plot(months,
                   result['equity_curves_median'],
                   linestyle='--',
                   color=colors[idx],
                   alpha=0.6,
                   linewidth=1.5)

        ax.set_xlabel('Months', fontsize=11)
        ax.set_ylabel('Equity Multiple', fontsize=11)
        ax.set_title(f'Portfolio Equity Curves: All 3 Strategies ({self.n_simulations} simulations)',
                    fontsize=12, fontweight='bold')
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)

        output_file = self.output_dir / "02_EQUITY_CURVES_OVERLAY.png"
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"    -> Equity curves saved: {output_file}")

    def _generate_sharpe_comparison_table(self):
        """Generate Sharpe ratio comparison across strategies."""
        import matplotlib.pyplot as plt

        # Extract Sharpe metrics
        data = []
        for strategy_name, result in self.results.items():
            mc = result['backtest']
            data.append({
                'Strategy': strategy_name,
                'Mean Sharpe': mc['mean_sharpe'],
                'Median Sharpe': mc['median_sharpe'],
                'Std Dev': mc['std_sharpe'],
                'Min Sharpe': mc['min_sharpe'],
                '5th %ile': np.percentile(mc['all_sharpe_ratios'], 5),
                '95th %ile': np.percentile(mc['all_sharpe_ratios'], 95),
            })

        df = pd.DataFrame(data)

        # Calculate improvement over baseline (equal weight)
        baseline_sharpe = df[df['Strategy'] == 'Equal Weight']['Mean Sharpe'].values[0]
        df['Improvement (bps)'] = (df['Mean Sharpe'] - baseline_sharpe) * 100

        # Print and save
        print("\n  Sharpe Ratio Comparison:")
        print("\n" + df.to_string(index=False))

        output_file = self.output_dir / "03_SHARPE_COMPARISON.csv"
        df.to_csv(output_file, index=False)
        print(f"    -> Sharpe table saved: {output_file}")

        # Visualization
        fig, ax = plt.subplots(figsize=(10, 6))

        strategies = df['Strategy'].values
        means = df['Mean Sharpe'].values
        stds = df['Std Dev'].values

        x = np.arange(len(strategies))
        ax.bar(x, means, yerr=stds, capsize=5, alpha=0.7, edgecolor='black')

        ax.set_ylabel('Sharpe Ratio', fontsize=11)
        ax.set_title('Mean Sharpe Ratio Comparison (Error bars = 1 Std Dev)', fontsize=12, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(strategies, rotation=15, ha='right')
        ax.grid(True, alpha=0.3, axis='y')

        for i, (mean, std) in enumerate(zip(means, stds)):
            ax.text(i, mean + std + 0.1, f'{mean:.2f}', ha='center', fontsize=10, fontweight='bold')

        output_file_plot = self.output_dir / "03_SHARPE_COMPARISON.png"
        plt.savefig(output_file_plot, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"    -> Sharpe chart saved: {output_file_plot}")

    def _generate_max_drawdown_comparison(self):
        """Compare max drawdown distributions."""
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        strategy_names = list(self.results.keys())

        for idx, strategy_name in enumerate(strategy_names):
            result = self.results[strategy_name]['backtest']
            max_dds = result['all_max_drawdowns'] * 100

            ax = axes[idx]
            ax.hist(max_dds, bins=40, edgecolor='black', alpha=0.7, color='lightcoral')
            ax.axvline(np.mean(max_dds), color='red', linestyle='--', linewidth=2,
                      label=f"Mean: {np.mean(max_dds):.1f}%")
            ax.axvline(np.percentile(max_dds, 95), color='darkred', linestyle='--', linewidth=2,
                      label=f"95th: {np.percentile(max_dds, 95):.1f}%")
            ax.set_xlabel('Max Drawdown (%)', fontsize=10)
            ax.set_ylabel('Frequency', fontsize=10)
            ax.set_title(f'{strategy_name}', fontsize=11, fontweight='bold')
            ax.legend(fontsize=9)
            ax.grid(True, alpha=0.3, axis='y')

        fig.suptitle('Max Drawdown Distribution by Strategy', fontsize=13, fontweight='bold')
        plt.tight_layout()

        output_file = self.output_dir / "04_MAX_DRAWDOWN_COMPARISON.png"
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"    -> Max DD chart saved: {output_file}")

    def _generate_monthly_performance_grid(self):
        """Generate heatmap showing which allocation won each month."""
        # This requires re-running simulations to track monthly performance
        # For now, create a summary table
        output_file = self.output_dir / "05_STRATEGY_METRICS_SUMMARY.csv"

        data = []
        for strategy_name, result in self.results.items():
            mc = result['backtest']
            data.append({
                'Strategy': strategy_name,
                'Mean Return': f"{mc['mean_cumulative_return']:.2%}",
                'Mean Sharpe': f"{mc['mean_sharpe']:.2f}",
                'Mean Max DD': f"{mc['mean_max_drawdown']:.2%}",
                'Prob Positive': f"{mc['probability_positive']:.1%}",
                'Calmar Ratio': f"{mc['mean_calmar']:.2f}",
            })

        df = pd.DataFrame(data)
        df.to_csv(output_file, index=False)

        print(f"\n  Monthly/Aggregate Performance Grid:")
        print("\n" + df.to_string(index=False))
        print(f"\n    -> Summary metrics saved: {output_file}")

    def _generate_correlation_impact_report(self):
        """Quantify correlation drag in dollar terms."""
        output_file = self.output_dir / "06_CORRELATION_IMPACT.txt"

        with open(output_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("CORRELATION IMPACT ANALYSIS\n")
            f.write("="*80 + "\n\n")

            f.write("Correlation Drag: Cost of imperfect diversification\n")
            f.write("(What returns would be if all strategies were 100% uncorrelated)\n\n")

            for strategy_name, result in self.results.items():
                mc = result['backtest']

                f.write(f"\n{strategy_name}:\n")
                f.write(f"  Mean Correlation Drag:  ${mc['mean_correlation_cost']*1000:>8.2f}k per $1M portfolio\n")
                f.write(f"  Median Drag:            ${mc['median_correlation_cost']*1000:>8.2f}k\n")
                f.write(f"  95th Percentile:        ${mc['correlation_cost_percentile_95']*1000:>8.2f}k\n")
                f.write(f"  Total Drag (bps):       {mc['total_correlation_cost_bps']:>8.1f} bps\n")

                # Calculate drag as % of return
                if mc['mean_cumulative_return'] > 0:
                    drag_pct = (mc['mean_correlation_cost'] / mc['mean_cumulative_return']) * 100
                    f.write(f"  Drag % of Mean Return:  {drag_pct:>8.1f}%\n")

        print(f"    -> Correlation impact saved: {output_file}")

    def _validate_regime_controller(self) -> Dict:
        """Validate that regime-controlled allocation actually helps."""
        validation = {}

        # Get equal weight (baseline) and regime (optimized) results
        ew_result = self.results['Equal Weight']['backtest']
        regime_result = self.results['Regime-Controlled']['backtest']

        validation['baseline_sharpe'] = ew_result['mean_sharpe']
        validation['regime_sharpe'] = regime_result['mean_sharpe']
        validation['sharpe_improvement'] = regime_result['mean_sharpe'] - ew_result['mean_sharpe']
        validation['sharpe_improvement_bps'] = validation['sharpe_improvement'] * 100

        validation['baseline_max_dd'] = ew_result['mean_max_drawdown']
        validation['regime_max_dd'] = regime_result['mean_max_drawdown']
        validation['dd_improvement'] = ew_result['mean_max_drawdown'] - regime_result['mean_max_drawdown']
        validation['dd_improvement_bps'] = validation['dd_improvement'] * 100 * 100

        validation['baseline_return'] = ew_result['mean_cumulative_return']
        validation['regime_return'] = regime_result['mean_cumulative_return']
        validation['return_improvement'] = regime_result['mean_cumulative_return'] - ew_result['mean_cumulative_return']

        # Print validation summary
        print("\n  Regime-Controlled vs Equal Weight:")
        print(f"    Sharpe: {validation['baseline_sharpe']:.2f} -> {validation['regime_sharpe']:.2f} " +
              f"({validation['sharpe_improvement_bps']:+.0f} bps)")
        print(f"    Max DD: {validation['baseline_max_dd']:.1%} -> {validation['regime_max_dd']:.1%} " +
              f"({validation['dd_improvement_bps']:+.0f} bps)")
        print(f"    Return: {validation['baseline_return']:.2%} -> {validation['regime_return']:.2%} " +
              f"({validation['return_improvement']:+.2%})")

        return validation


def main():
    """Run complete backtest."""
    orchestrator = BacktestOrchestrator(
        n_simulations=1000,
        n_months_simulation=120,
        output_dir="/c/Users/carin/OneDrive/Dokument/stike/backtest_results"
    )

    results = orchestrator.run_full_backtest()

    print("\n" + "="*80)
    print("BACKTEST COMPLETE".center(80))
    print("="*80)
    print(f"\nOutput directory: {results['output_dir']}")
    print("\nGenerated files:")
    print("  1. 01_SUMMARY_REPORT.txt - Detailed text report")
    print("  2. 02_EQUITY_CURVES_OVERLAY.png - Equity curves for all strategies")
    print("  3. 03_SHARPE_COMPARISON.csv - Sharpe metrics table")
    print("  4. 03_SHARPE_COMPARISON.png - Sharpe bar chart")
    print("  5. 04_MAX_DRAWDOWN_COMPARISON.png - Drawdown distributions")
    print("  6. 05_STRATEGY_METRICS_SUMMARY.csv - Summary metrics")
    print("  7. 06_CORRELATION_IMPACT.txt - Correlation drag analysis")

    return results


if __name__ == "__main__":
    main()
