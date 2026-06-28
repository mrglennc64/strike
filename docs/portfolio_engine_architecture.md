# Portfolio Engine Architecture

## Overview

The Portfolio Engine is a comprehensive system for multi-strategy portfolio optimization, simulation, and regime-based allocation. It combines Monte Carlo simulation, advanced allocation algorithms, and real-time monitoring to manage a diversified portfolio across five distinct trading strategies.

## System Components

### 1. Core Services

#### PortfolioSimulator
Runs Monte Carlo simulations to project portfolio performance under uncertainty.

**Responsibilities:**
- Generate correlated strategy returns using Cholesky decomposition
- Model market regime shocks (stress periods with elevated correlations)
- Simulate transaction costs and slippage
- Calculate equity curves, drawdowns, and risk metrics
- Assess diversification benefits and correlation drag

**Key Algorithms:**
- **Cholesky Decomposition**: Converts independent returns into correlated returns while preserving means and variances
- **Market Regime Shocks**: AR(1) process creates persistent stress periods where correlations increase 20-40%
- **Drawdown Tracking**: Maintains running peak for real-time drawdown calculation
- **Sharpe/Sortino Ratios**: Annualized risk-adjusted return metrics

**Inputs:**
- Strategy parameters (return, volatility, Sharpe, max drawdown)
- Strategy weights
- Correlation matrix
- Number of simulations and time horizon

**Outputs:**
- Equity curve percentiles (5th, 25th, median, 75th, 95th)
- Return distribution statistics
- Risk metrics (Sharpe, Sortino, max drawdown, recovery time)
- Diversification ratio and correlation drag

---

#### PortfolioAllocator
Optimizes portfolio weights using multiple criteria.

**Responsibilities:**
- Calculate optimal weights using specified optimization method
- Compute portfolio metrics (expected return, volatility, Sharpe ratio)
- Assess concentration risk (Herfindahl index)
- Generate Kelly fractions for position sizing

**Optimization Methods:**

1. **Kelly Criterion** (Growth-Optimal)
   - Maximizes long-term compounded growth
   - Formula: f* = inv(Σ) @ r (inverse covariance weighted returns)
   - Applied with fractional Kelly for risk control (default 0.25)
   - Most aggressive, highest leverage

2. **Maximum Sharpe Ratio** (Risk-Adjusted)
   - Maximizes return per unit of risk
   - Uses convex optimization (SLSQP)
   - Balances return and risk exposure
   - Most popular for institutional use

3. **Minimum Variance** (Conservative)
   - Minimizes portfolio volatility
   - Risk-parity approach
   - Suitable for defensive positioning
   - Lowest expected return

4. **Equal Weight** (Baseline)
   - Simple 20% per strategy
   - Provides diversification without optimization
   - Reference point for strategy comparison

**Correlation Matrix:**
```
        MLB    Crypto  Earnings   AI    Econ
MLB     1.00   0.08    0.15      0.12  0.10
Crypto  0.08   1.00    0.35      0.45  0.05
Earnings 0.15  0.35    1.00      0.75  0.20
AI      0.12   0.45    0.75      1.00  0.15
Econ    0.10   0.05    0.20      0.15  1.00
```

**Beta Vector:**
- MLB: 0.1 (very low market sensitivity)
- Crypto: 1.4 (high beta, moves with tech/risk-on)
- Earnings: 1.0 (market beta)
- AI: 1.2 (tech-correlated)
- Econ: 0.6 (defensive, inversely correlated in stress)

---

#### RegimeController
Adjusts portfolio weights based on market regime.

**Responsibilities:**
- Classify market regime (Low Vol, Normal, High Vol, Stress)
- Adjust weights based on VIX, funding rates, and sentiment
- Generate rebalancing recommendations
- Assess portfolio positioning appropriateness

**Regime Classification:**

| Regime | VIX Range | Characteristics | Adjustment |
|--------|-----------|-----------------|------------|
| **Low Vol** | < 12 | Market complacency, risk-on | +20% leverage |
| **Normal** | 12-20 | Balanced risk/reward | Baseline (1.0x) |
| **High Vol** | 20-30 | Elevated uncertainty | -20% deleveraging |
| **Stress** | > 30 | Market crisis, contagion | -40% deleveraging |

**Adjustment Factors:**
- **Sentiment Adjustment**: Negative sentiment reduces growth assets (AI, Crypto), increases defensive (MLB, Econ)
- **Funding Rate Adjustment**: Crypto funding > 3% triggers -15% weight reduction
- **Dynamic Rebalancing**: Weights adjusted based on multiple factors and normalized to 1.0

**Recommendations:**
- **Hold**: Current positioning is appropriate
- **Increase Risk**: Low volatility environment supports leverage
- **Reduce Risk**: High volatility requires defensive positioning
- **Rebalance**: Significant drift from targets detected
- **Hedge**: Regime shift creates need for tactical hedging

---

### 2. Monitoring Services

#### Allocation Monitor
Tracks actual portfolio allocation vs recommended allocation.

**Metrics Tracked:**
- **Drift**: Absolute deviation between actual and recommended weights (%)
- **Concentration**: Herfindahl-Hirschman Index (HHI = Σw_i²)
  - Range: 0.2 (equal weight) to 1.0 (single asset)
  - Threshold: > 0.35 triggers warning
- **Rebalance Need**: Max drift > 3% or concentration risk

**Alerts:**
- **INFO**: All metrics within normal range
- **WARNING**: Concentration > 0.35 or max drift 3-5%
- **CRITICAL**: Max drift > 5% or major concentration issue

**Database Schema:**
- `allocation_history`: Snapshots of allocation state
- `rebalancing_events`: Log of actual rebalancing transactions

---

#### Correlation Monitor
Monitors correlation structure changes in real-time.

**Metrics Tracked:**
- **Mean Correlation**: Average pairwise correlation
- **Max Correlation**: Highest correlation pair
- **Clustering Strength**: Increase in correlation vs baseline
- **Diversification Ratio**: DR = (sum weighted vols) / portfolio vol
  - DR > 1.5: Good diversification
  - DR < 1.2: Poor diversification

**Correlation Events Detected:**
- **Clustering**: Mean correlation > 0.60
- **Breakdown**: DR < 1.2 (diversification ineffective)
- **Spike**: Single pair correlation change > 10%

**Alerts:**
- **NORMAL**: Structure stable, DR > 1.3
- **ELEVATED**: Mild clustering, DR 1.2-1.3
- **HIGH**: Significant clustering, DR 1.1-1.2
- **CRITICAL**: Severe clustering, DR < 1.1 or spike detected

**Database Schema:**
- `correlation_history`: Historical correlation matrices
- `correlation_events`: Detected correlation changes

---

#### Regime Alerter
Monitors market regime and triggers alerts on shifts.

**Market Indicators Tracked:**
- **VIX**: Volatility index (5-80 typical range)
- **VIX Percentile**: Historical percentile (0-100)
- **Crypto Funding Rate**: Leverage interest rate
- **Market Sentiment**: Aggregate sentiment score (-1 to +1)

**Regime Score Calculation:**
```
RegimeScore = 0.4 * VIX_norm + 0.2 * Funding_norm + 0.2 * Sentiment_norm + 0.2 * Percentile_norm
```

**Shift Detection:**
- Regime classification changed
- Regime score change > 0.15
- Shift magnitude = |current_score - previous_score|

**Alert Actions on Shift:**
- **STRESS regime**: REDUCE_RISK or HEDGE
- **LOW_VOL regime**: INCREASE_RISK
- **Shift magnitude > 0.3**: REBALANCE or tactical hedge

**Database Schema:**
- `regime_history`: Historical regime states
- `regime_shifts`: Detected regime transition events

---

### 3. Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Input Data Sources                        │
│  (Market Data, Strategy Returns, VIX, Sentiment, Funding)   │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴──────────────┐
        │                           │
        ▼                           ▼
   ┌──────────────┐           ┌──────────────┐
   │  Portfolio   │           │   Monitoring │
   │  Simulator   │           │   Services   │
   └──────┬───────┘           └──────┬───────┘
          │                          │
    ┌─────┴──────┐            ┌──────┴──────────┬──────────────┐
    │            │            │                 │              │
    ▼            ▼            ▼                 ▼              ▼
┌─────────┐ ┌─────────┐ ┌──────────────┐ ┌───────────┐ ┌──────────────┐
│Allocation│ │ Regime  │ │  Allocation  │ │Correlation│ │   Regime     │
│Optimizer │ │Controller│ │  Monitor     │ │ Monitor   │ │  Alerter     │
└────┬────┘ └────┬────┘ └──────┬───────┘ └─────┬─────┘ └──────┬───────┘
     │           │              │               │              │
     └───────────┴──────────────┴───────────────┴──────────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
            ┌──────────────┐         ┌────────────┐
            │  SQLite DBs  │         │   Alerts   │
            │   (History)  │         │  (Webhook) │
            └──────────────┘         └────────────┘
```

---

### 4. Strategy Profiles

#### MLB (Strikeout Edge)
- **Expected Return**: 15%
- **Volatility**: 12%
- **Sharpe Ratio**: 1.25
- **Beta**: 0.1 (very low market sensitivity)
- **Correlation**: Low to all others (0.08-0.15)
- **Role**: Defensive alpha, market-neutral
- **Allocation**: 20-35% (core holding)

#### Crypto (Volatility)
- **Expected Return**: 25%
- **Volatility**: 40%
- **Sharpe Ratio**: 0.625
- **Beta**: 1.4 (high risk-on beta)
- **Correlation**: High with AI (0.45), Earnings (0.35)
- **Role**: Growth driver in risk-on environments
- **Allocation**: 10-20% (tactical position)

#### Earnings (Surprise)
- **Expected Return**: 18%
- **Volatility**: 18%
- **Sharpe Ratio**: 1.0
- **Beta**: 1.0 (market beta)
- **Correlation**: High with AI (0.75), moderate with Crypto (0.35)
- **Role**: Core growth, fundamental alpha
- **Allocation**: 20-30% (core holding)

#### AI (Index Pairs)
- **Expected Return**: 22%
- **Volatility**: 32%
- **Sharpe Ratio**: 0.69
- **Beta**: 1.2 (tech-correlated growth)
- **Correlation**: High with Earnings (0.75), Crypto (0.45)
- **Role**: Tech/growth exposure
- **Allocation**: 15-25% (core holding)

#### Econ (Economic Indicators)
- **Expected Return**: 12%
- **Volatility**: 8%
- **Sharpe Ratio**: 1.5 (highest risk-adjusted return)
- **Beta**: 0.6 (defensive, inversely correlated in stress)
- **Correlation**: Low to all others (0.05-0.20)
- **Role**: Defensive anchor, macro alpha
- **Allocation**: 15-25% (core holding)

---

## API Integration

### REST Endpoints

**Portfolio Simulation:**
```
POST /api/portfolio/simulate
Input: Strategies, num_simulations, time_horizon, initial_capital
Output: Equity curves, risk metrics, diversification analysis
```

**Allocation Optimization:**
```
POST /api/portfolio/allocation
Input: Strategies, optimization_method (kelly/sharpe/min_variance/equal_weight)
Output: Optimal weights, portfolio metrics, concentration indices
```

**Regime Assessment:**
```
POST /api/portfolio/regime
Input: VIX, funding_rate, sentiment, base_weights
Output: Regime classification, adjusted weights, recommended actions
```

**Health Check:**
```
GET /api/portfolio/health
Output: Service status, available endpoints
```

---

## Database Schema

### allocation_history
```sql
- id INTEGER PRIMARY KEY
- timestamp DATETIME
- actual_weights JSON (strategy name -> weight)
- recommended_weights JSON
- drift_pcts JSON (per-strategy drift %)
- max_drift REAL
- concentration_herfindahl REAL
- rebalance_needed BOOLEAN
- alert_level TEXT (INFO/WARNING/CRITICAL)
- alert_message TEXT
```

### correlation_history
```sql
- id INTEGER PRIMARY KEY
- timestamp DATETIME
- strategy_names JSON
- correlation_matrix JSON (NxN array)
- mean_correlation REAL
- max_correlation REAL
- min_correlation REAL
- diversification_ratio REAL
- clustering_strength REAL
- alert_level TEXT
- alert_message TEXT
```

### regime_history
```sql
- id INTEGER PRIMARY KEY
- timestamp DATETIME
- vix REAL
- vix_percentile REAL (0-100)
- funding_rate REAL
- sentiment_score REAL (-1 to +1)
- regime_type TEXT (Low Vol/Normal/High Vol/Stress)
- regime_score REAL (0-1, higher = more stress)
- recommended_action TEXT (Hold/Reduce Risk/Increase Risk/Rebalance)
- is_regime_shift BOOLEAN
- shift_magnitude REAL (0-1)
```

### regime_shifts
```sql
- id INTEGER PRIMARY KEY
- timestamp DATETIME
- from_regime TEXT
- to_regime TEXT
- magnitude REAL
- trigger_vix REAL
- trigger_sentiment REAL
- recommended_action TEXT
- executed BOOLEAN (was action taken?)
```

---

## Configuration

### Environment Variables

**Portfolio Engine:**
```bash
PORTFOLIO_ENABLE_MONITORING=true
PORTFOLIO_REBALANCE_FREQUENCY=monthly
PORTFOLIO_MAX_CORRELATION_THRESHOLD=0.85
PORTFOLIO_REGIME_SHOCK_THRESHOLD=0.3
```

**Monitoring:**
```bash
MONITOR_ENABLED=true
ALLOCATION_CHECK_INTERVAL=300  # 5 minutes
CORRELATION_CHECK_INTERVAL=3600  # 1 hour
REGIME_CHECK_INTERVAL=300  # 5 minutes
```

**Alerts:**
```bash
ALERT_WEBHOOK_URL=https://...
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
ALERT_EMAIL=alerts@example.com
```

---

## Performance Characteristics

### Simulation Performance
- **500 simulations, 252 days**: ~2-5 seconds (depending on strategies)
- **1000 simulations, 252 days**: ~4-10 seconds
- **Scaling**: Linear with number of simulations

### Allocation Optimization
- **Kelly criterion**: ~0.5 seconds (matrix inversion)
- **Sharpe optimization**: ~1-2 seconds (convex optimization)
- **Min-variance**: ~1-2 seconds (convex optimization)

### Monitoring Overhead
- **Allocation monitor**: ~100ms per check
- **Correlation monitor**: ~500ms per check (requires historical data)
- **Regime alerter**: ~200ms per check (VIX, sentiment fetch)

---

## Failure Modes & Recovery

### Common Issues

1. **Non-positive Definite Correlation Matrix**
   - **Cause**: Rounding errors or invalid user input
   - **Fix**: Auto-repair via eigenvalue adjustment (set negative eigenvalues to 1e-10)
   - **Recovery**: 100% success rate, transparent to user

2. **Singular Covariance Matrix**
   - **Cause**: Degenerate assets or zero variance
   - **Fix**: Add small regularization term to diagonal
   - **Recovery**: Falls back to equal-weight allocation

3. **Optimization Non-Convergence**
   - **Cause**: Ill-conditioned optimization problem
   - **Fix**: Return equal-weight or best attempt
   - **Recovery**: Non-fatal, still produces valid weights

4. **Market Data Unavailable**
   - **Cause**: VIX, funding rate, or sentiment API down
   - **Fix**: Use last known values + time decay
   - **Recovery**: Alert but continue operation

---

## Future Enhancements

1. **Dynamic Correlations**: Model time-varying correlations using multivariate GARCH
2. **Tail Risk Hedging**: Add VaR/CVaR optimization alongside Sharpe
3. **Leverage Control**: Implement dynamic leverage based on drawdown limits
4. **Real-Time Rebalancing**: Trigger rebalancing on drift OR regime shift, not just periodic
5. **Machine Learning**: Use LSTM to predict regime shifts before they occur
6. **Multi-Period Optimization**: Solve path-dependent optimization over multiple periods
7. **Transaction Cost Optimization**: Solve for optimal rebalancing frequency vs cost tradeoff

---

## References

- **Kelly Criterion**: MacLean et al. "The Kelly Capital Growth Investment Criterion"
- **Cholesky Decomposition**: Higham "Computing the nearest correlation matrix"
- **Diversification Ratio**: Choueifaty & Coignard "Toward Maximum Diversification"
- **Regime Detection**: Hamilton "A New Approach to the Economic Analysis of Nonstationary Time Series"
