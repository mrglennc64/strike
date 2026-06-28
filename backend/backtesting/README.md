# Multi-Vertical Portfolio Backtesting Engine

Complete framework for backtesting a 5-vertical sports/crypto/macro trading portfolio with 3 distinct allocation strategies.

## Quick Start

```python
from backend.backtesting import BacktestOrchestrator

# Run full backtest
orchestrator = BacktestOrchestrator(
    n_simulations=1000,
    n_months_simulation=120,
    output_dir="./backtest_results"
)

results = orchestrator.run_full_backtest()
```

## Architecture

### 4-Layer Pipeline

```
1. DATA EXTRACTION LAYER
   ├─ MLB strikeout trades (Statcast)
   ├─ Earnings surprise events
   ├─ Crypto volatility trades
   ├─ AI release impact trades
   └─ Economics (CPI/Fed) trades

2. METRICS AGGREGATION LAYER
   ├─ Monthly return computation
   ├─ Win rate calculation
   ├─ Volatility & Sharpe ratios
   ├─ Max drawdown analysis
   └─ Correlation matrix building

3. ALLOCATION STRATEGY LAYER
   ├─ Equal Weight (baseline)
   ├─ Hybrid Kelly + Risk Parity (improved)
   └─ Regime-Controlled (optimized)

4. MONTE CARLO + REPORTING LAYER
   ├─ 1000 simulations per strategy
   ├─ Equity curve generation
   ├─ Performance metrics aggregation
   └─ Visualization & report generation
```

## Components

### 1. Data Loaders (`vertical_data_loader.py`)

Each loader implements the `VerticalDataLoader` interface:

```python
class MLBDataLoader(VerticalDataLoader):
    def get_vertical_name(self) -> str:
        return "MLB"
    
    def load_trades(self) -> List[VerticalTradeRecord]:
        # Load historical trades
        pass
    
    def aggregate_metrics(self) -> VerticalMetrics:
        # Returns VerticalMetrics with all risk/return stats
        pass
```

**Available Loaders**:
- `MLBDataLoader` - Strikeout edge trades
- `EarningsDataLoader` - Event surprise trades
- `CryptoDataLoader` - BTC/ETH volatility trades
- `AIReleasesDataLoader` - Claude/GPT impact trades
- `EconomicsDataLoader` - CPI/Fed trades

**VerticalMetrics Output**:
```python
@dataclass
class VerticalMetrics:
    name: str
    monthly_returns: np.ndarray          # (n_months,)
    win_rate: float                      # P(trade > 0)
    avg_win_R: float                     # % per win
    avg_loss_R: float                    # % per loss
    trades_per_month: float              # Volume
    volatility: float                    # Annualized
    max_drawdown: float                  # Worst peak-to-trough
    sharpe_ratio: float                  # Risk-adjusted return
    calmar_ratio: float                  # Return / max_dd
```

### 2. Allocation Strategies (`allocation_strategies.py`)

#### Strategy A: Equal Weight
```python
strategy = EqualWeightStrategy()
weights = strategy.calculate_weights(verticals)
# Returns: {MLB: 0.20, Earnings: 0.20, Crypto: 0.20, AI: 0.20, Econ: 0.20}
```

#### Strategy B: Hybrid Kelly + Risk Parity
```python
strategy = HybridKellyRiskParity()
weights = strategy.calculate_weights(verticals)
# Returns: {MLB: 0.247, Earnings: 0.272, Crypto: 0.139, AI: 0.178, Econ: 0.164}
```

Algorithm:
1. Calculate Kelly fraction for each vertical: `f* = (p*b - q) / b / 4`
2. Normalize by inverse volatility (risk parity)
3. Rescale to sum to 1.0

#### Strategy C: Regime-Controlled
```python
regime = RegimeIndicators(vix_level=15, credit_spreads="tight", ...)
strategy = RegimeControlledAllocation()
weights = strategy.calculate_weights(verticals, regime)
```

Dynamic allocation based on:
- **Risk-on**: Increase growth (Crypto 25%, AI 30%)
- **Risk-off**: Increase defensive (MLB 35%, Econ 30%)
- **Normal**: Balanced (shown in Strategy B)

### 3. Portfolio Simulator (existing `portfolio_simulator.py`)

Extends existing framework to:
- Generate correlated monthly returns via Cholesky decomposition
- Apply market regime shocks (elevated correlation during stress)
- Model transaction costs and slippage
- Compute strategy attribution

### 4. Backtest Orchestrator (`backtest_orchestrator.py`)

Main entry point that coordinates full pipeline:

```python
orchestrator = BacktestOrchestrator(
    start_date=datetime(2023, 6, 29),
    end_date=datetime(2026, 6, 28),
    n_simulations=1000,
    n_months_simulation=120,
    risk_free_rate=0.04,
    output_dir="./backtest_results"
)

results = orchestrator.run_full_backtest()
```

**Output Files**:
1. `01_SUMMARY_REPORT.txt` - Detailed metrics
2. `02_EQUITY_CURVES_OVERLAY.png` - All 3 strategies
3. `03_SHARPE_COMPARISON.csv` - Sharpe metrics table
4. `03_SHARPE_COMPARISON.png` - Sharpe bar chart
5. `04_MAX_DRAWDOWN_COMPARISON.png` - DD distributions
6. `05_STRATEGY_METRICS_SUMMARY.csv` - Summary metrics
7. `06_CORRELATION_IMPACT.txt` - Drag analysis in $

## Key Metrics Explained

### Sharpe Ratio
```
Sharpe = (Annual Return - Risk-Free Rate) / Annual Volatility

Higher = Better (more return per unit of risk)
Typical: 0.5-2.0 is good, >2.0 is excellent
```

### Maximum Drawdown
```
Max DD = (Lowest Point - Peak) / Peak

Typical: -15% to -30% for equity portfolios
Better strategies have shallower drawdowns
```

### Calmar Ratio
```
Calmar = Annual Return / |Max Drawdown|

Higher = Better (more return per unit of drawdown)
Typical: 0.5-2.0 is good
```

### Correlation Impact
```
Correlation Drag = $X per $1M portfolio

Caused by strategies moving together instead of independently
Negative correlations reduce drag
Example: -$3.6M drag on $1B portfolio (36 bps annually)
```

## Customization

### Add New Vertical

1. Create new loader class:

```python
from backend.backtesting import VerticalDataLoader, VerticalTradeRecord

class MyVerticalLoader(VerticalDataLoader):
    def get_vertical_name(self) -> str:
        return "MyVertical"
    
    def load_trades(self) -> List[VerticalTradeRecord]:
        # Load from your data source
        trades = []
        # ... populate trades
        return trades
```

2. Register in orchestrator:

```python
loaders = [
    # ... existing loaders
    MyVerticalLoader(start_date, end_date),
]
```

3. Update correlation matrix in allocation strategies

### Modify Allocation Strategy

Create new strategy class:

```python
from backend.backtesting import AllocationStrategy

class MyStrategy(AllocationStrategy):
    def calculate_weights(self, verticals, regime=None):
        # Your custom weighting logic
        weights = {...}
        return self._validate_weights(weights)
```

### Adjust Simulator Parameters

```python
# Transaction costs
simulator = PortfolioSimulator(
    strategies=...,
    weights=...,
    correlation_matrix=...,
    transaction_cost_bps=10,  # Change this
    slippage_bps=5            # And this
)
```

## Interpretation Guide

### What Do Negative Returns Mean?

The synthetic model uses small per-trade returns (0.4-0.6%) and monthly rebalancing. Over 120 months with 10 bps transaction costs, cumulative drag becomes significant.

**For real implementation**: Use actual trading data instead of synthetic data.

### When Is Hybrid Kelly Better?

- When verticals have different Sharpe ratios
- When correlation structure is favorable (negative correlations)
- When volatility varies significantly across verticals

Hybrid Kelly doesn't help if all verticals have:
- Similar volatility
- Similar win rates
- High positive correlations

### When To Use Regime Control?

Use regime controller if:
1. You have real-time VIX, credit spread data
2. Your system can rebalance within days
3. Regime shifts are predictable (>75% accuracy)

Don't use if:
- Data latency >1 day
- Rebalancing costs are high
- Regime signals are noisy

## Testing

Run unit tests:

```bash
pytest backend/backtesting/tests/
```

Test individual components:

```python
from backend.backtesting import MLBDataLoader

loader = MLBDataLoader()
metrics = loader.aggregate_metrics()
print(f"Win Rate: {metrics.win_rate:.1%}")
print(f"Sharpe: {metrics.sharpe_ratio:.2f}")
```

## Performance Metrics

**Execution Time** (1000 simulations):
- Data loading: ~5 seconds
- Metrics aggregation: <1 second
- Correlation building: <1 second
- MC simulations: ~45 seconds (5 seconds each strategy)
- Report generation: ~10 seconds
- **Total: ~60 seconds**

**Memory Usage**:
- Strategies: <10 MB
- 1000 MC paths: ~50 MB
- Reports: <5 MB
- **Total: ~65 MB**

## Production Checklist

- [ ] Load real vertical data (not synthetic)
- [ ] Validate correlation matrix with live data
- [ ] Backtest on held-out period (2024-2025)
- [ ] Compare predicted vs actual Sharpe
- [ ] Set up real-time monitoring
- [ ] Configure alerts for drawdowns >20%
- [ ] Establish rebalancing schedule (quarterly recommended)
- [ ] Document allocation methodology
- [ ] Train team on Kelly calculation
- [ ] Set up audit logging

## Troubleshooting

### Issue: Negative Correlation Matrix

**Solution**: Check input data for NaNs or outliers

```python
df.describe()  # Check for extremes
df.isnull().sum()  # Check for NaNs
```

### Issue: One Strategy Dominates

**Solution**: Verify weights sum to 1.0

```python
print(sum(weights.values()))  # Should be ~1.0
```

### Issue: Sharpe Ratio Unstable

**Solution**: Increase simulation count or check data quality

```python
# Run 2000 instead of 1000
backtest = MonteCarloBacktest(simulator, n_simulations=2000)
```

## References

### Kelly Criterion
- Paper: "A New Interpretation of Information Rate" (Kelly, 1956)
- Formula: `f* = (p*b - q) / b`
- Fractional Kelly: `f/4` for safety

### Risk Parity
- Allocate by inverse volatility
- Equal risk contribution from each asset
- Reduces concentration in high-vol strategies

### Regime Detection
- VIX >25 + Credit spreads >250 bps = Risk-off
- VIX <12 + Tight spreads + Bullish momentum = Risk-on

## License

Internal use only - do not distribute

## Support

For questions about implementation, contact: mrglenncarter@yahoo.com
