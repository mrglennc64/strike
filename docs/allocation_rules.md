# Portfolio Allocation Rules & Weight Calculations

## Overview

This document explains how portfolio weights are calculated using different optimization methods and how regime-based adjustments work.

---

## Weight Calculation Methods

### 1. Kelly Criterion Allocation (Growth-Optimal)

The Kelly Criterion maximizes expected long-term compounded growth.

#### Theory

For a portfolio, Kelly weights are given by:

```
w = inv(Σ) @ r
```

Where:
- `w` = weight vector
- `Σ` = covariance matrix
- `r` = expected return vector
- `inv(Σ)` = inverse of covariance matrix

#### Interpretation

- Maximizes geometric mean of returns
- Most aggressive allocation method
- Can produce very concentrated positions
- Usually applied with fractional Kelly (0.1-0.5) to reduce leverage

#### Calculation Steps

1. **Build Covariance Matrix from Volatilities and Correlations**
   ```
   σ_i = volatility of strategy i
   ρ_{ij} = correlation between i and j
   
   Σ[i,j] = σ_i × σ_j × ρ_{ij}
   ```

2. **Invert Covariance Matrix**
   ```
   inv(Σ) = inverse via Cholesky decomposition
   ```

3. **Calculate Full Kelly Weights**
   ```
   w_full = inv(Σ) @ r
   ```

4. **Apply Fractional Kelly**
   ```
   w_final = w_full × kelly_fraction (default 0.25)
   ```

5. **Normalize to Sum to 1.0**
   ```
   w_normalized = w / sum(w)
   ```

#### Example Calculation

Given 3 strategies:

```
Returns:  [15%, 25%, 18%]
Vols:     [12%, 40%, 18%]
Corr:     [[1.0,  0.08, 0.15],
           [0.08, 1.0,  0.35],
           [0.15, 0.35, 1.0]]
```

Step 1: Covariance Matrix
```
Σ[0,0] = 0.12 × 0.12 × 1.0  = 0.0144
Σ[0,1] = 0.12 × 0.40 × 0.08 = 0.000384
Σ[0,2] = 0.12 × 0.18 × 0.15 = 0.000324
...
```

Step 2: Inverse Covariance
```
inv(Σ) = [[702.04,  -3.95, -28.25],
          [-3.95,   6.46,  -12.39],
          [-28.25, -12.39,  44.73]]
```

Step 3: Full Kelly
```
w_full = inv(Σ) @ r
       = [702.04 × 0.15 + (-3.95) × 0.25 + (-28.25) × 0.18,
          (-3.95) × 0.15 + 6.46 × 0.25 + (-12.39) × 0.18,
          (-28.25) × 0.15 + (-12.39) × 0.25 + 44.73 × 0.18]
       = [102.3, 0.98, 4.23]
```

Step 4: Apply 0.25 Fractional Kelly
```
w = [102.3 × 0.25, 0.98 × 0.25, 4.23 × 0.25]
  = [25.58, 0.245, 1.058]
```

Step 5: Normalize
```
sum = 25.58 + 0.245 + 1.058 = 26.883
w_final = [25.58/26.883, 0.245/26.883, 1.058/26.883]
        = [0.951, 0.009, 0.040]
```

#### When to Use

- Long-term wealth maximization
- High risk tolerance
- Sufficient capital to absorb large drawdowns
- Highly confident in parameter estimates
- Low transaction costs

#### Advantages
- Theoretically optimal for log utility
- Maximizes expected compounded return
- Accounts for both return and risk

#### Disadvantages
- Can produce extreme concentrations
- Very sensitive to parameter estimation errors
- Requires accurate covariance matrix
- Can produce negative weights (not allowed here)

#### Implementation Notes

- No short selling allowed: weights clipped to [0, 1]
- If correlation matrix is singular: add regularization or fall back to equal-weight
- Fractional Kelly typically 0.25 for risk control

---

### 2. Maximum Sharpe Ratio Allocation (Risk-Adjusted)

Maximizes risk-adjusted return (return per unit of risk).

#### Theory

Solve the convex optimization problem:

```
maximize:  (r @ w) / sqrt(w @ Σ @ w)
subject to: sum(w) = 1
           w_i ≥ 0 for all i
```

This is equivalent to:

```
minimize:  w @ Σ @ w
subject to: r @ w = 1  (normalize return)
           sum(w) = 1
           w_i ≥ 0
```

#### Calculation Steps

1. **Build Covariance Matrix** (same as Kelly)

2. **Solve Convex Optimization**
   - Use SLSQP (Sequential Least Squares Programming)
   - Start from equal-weight initial guess
   - Iterate to find optimal weights

3. **Extract Optimal Weights**

#### Example

Given same 3-strategy portfolio:

```
Equal-weight start: w = [1/3, 1/3, 1/3]

Iteration 1:
  Portfolio Return = 0.333 × 15% + 0.333 × 25% + 0.333 × 18% = 19.33%
  Portfolio Vol = sqrt(w @ Σ @ w) = 18.2%
  Sharpe = 19.33% / 18.2% = 1.063

Iteration 2:
  w = [0.28, 0.18, 0.35]
  Portfolio Return = 19.56%
  Portfolio Vol = 17.8%
  Sharpe = 1.099

Iteration 3:
  w = [0.25, 0.15, 0.35]
  Portfolio Return = 19.40%
  Portfolio Vol = 17.5%
  Sharpe = 1.109 ← Converged
```

Final result: w = [0.25, 0.15, 0.35]

#### When to Use

- Risk-adjusted return maximization
- Institutional portfolios (most common)
- Moderate risk tolerance
- Relatively stable market conditions
- When parameter estimates are reasonable

#### Advantages
- Most commonly used in practice
- Balanced risk and return
- Less sensitive to parameter errors than Kelly
- Stable allocations

#### Disadvantages
- May be conservative in bull markets
- Requires solving convex optimization
- Sensitive to volatility estimation

#### Implementation Notes

- Bounds: each weight between 0 and 1
- Constraints: sum(w) = 1
- Solver: SLSQP with maximum 100 iterations
- Convergence tolerance: 1e-9

---

### 3. Minimum Variance Allocation (Risk-Parity)

Minimize portfolio volatility.

#### Theory

Solve the convex optimization problem:

```
minimize: w @ Σ @ w
subject to: sum(w) = 1
           w_i ≥ 0
```

This ignores returns and focuses purely on risk minimization.

#### Calculation Steps

1. **Build Covariance Matrix**

2. **Solve Convex Optimization**
   - Find weights that minimize portfolio variance
   - No constraint on returns

3. **Extract Optimal Weights**

#### Example

Given 3-strategy portfolio:

```
Start from equal-weight: w = [1/3, 1/3, 1/3]

Iteration 1:
  Portfolio Vol = 18.2%

Iteration 2 (reduce high-vol assets):
  w = [0.30, 0.05, 0.65]
  Portfolio Vol = 17.1%

Iteration 3:
  w = [0.35, 0.02, 0.63]
  Portfolio Vol = 16.8% ← Converged
```

Result emphasizes low-volatility strategies (MLB, Econ) and deemphasizes high-vol ones (Crypto).

#### When to Use

- Defensive positioning
- Market downturns/stress regimes
- Conservative risk management
- Capital preservation focus
- When returns are highly uncertain

#### Advantages
- Lowest portfolio volatility
- Most conservative
- Simple optimization
- Stable in all market conditions

#### Disadvantages
- Lowest expected returns
- Ignores return potential
- May concentrate in low-return assets
- Can be boring/under-performing in bull markets

#### Implementation Notes

- Often combined with constraints on minimum weights per strategy
- May need to enforce diversification (max weight limits)
- Useful as baseline for defensive positioning

---

### 4. Equal Weight Allocation (Naive Diversification)

Simple baseline: 20% per strategy.

#### Theory

No optimization - just divide equally.

```
w_i = 1 / n = 1 / 5 = 0.20 for all i
```

#### When to Use

- Baseline/reference allocation
- No strong views on expected returns
- When parameter estimation is uncertain
- Simple benchmark
- Equal-weight index funds

#### Advantages
- Simple to implement
- No parameter estimation needed
- Good diversification
- Useful baseline

#### Disadvantages
- Ignores risk differences
- Ignores expected returns
- Often suboptimal
- Does not adapt to market conditions

#### Implementation Notes

- Useful as sanity check vs optimized allocations
- Should typically underperform optimized methods
- Good for beginners

---

## Regime-Based Adjustments

After computing optimal weights, adjust based on market regime.

### Regime Classification

```
VIX < 12      → Low Vol regime
VIX 12-20     → Normal regime (possibly shifted by sentiment)
VIX 20-30     → High Vol regime
VIX > 30      → Stress regime
```

### Adjustment Factors

#### VIX-Based Adjustment

```
Low Vol (VIX < 12):
  vol_multiplier = 1.2 (increase risk exposure)
  
Normal (VIX 12-20):
  vol_multiplier = 1.0 (hold baseline)
  
High Vol (VIX 20-30):
  vol_multiplier = 0.8 (reduce risk)
  
Stress (VIX > 30):
  vol_multiplier = 0.6 (significant reduction)
```

#### Sentiment-Based Adjustment

```
Negative Sentiment (score < -0.5):
  Risky assets (AI, Crypto): × 0.8 (reduce)
  Defensive assets (MLB, Econ): × 1.1 (increase)
  
Neutral Sentiment (-0.5 to 0.5):
  No adjustment
  
Positive Sentiment (score > 0.5):
  Risky assets (AI, Crypto): × 1.2 (increase)
  Defensive assets: no change
```

#### Funding Rate Adjustment (Crypto-Specific)

```
Normal funding (< 0.02%):
  Crypto weight: no adjustment
  
Elevated funding (0.02-0.03%):
  Crypto weight: × 0.85
  
Extreme funding (> 0.03%):
  Crypto weight: × 0.70
```

### Adjustment Algorithm

```
adjusted_weight[i] = base_weight[i] × vol_multiplier × sentiment_factor[i] × funding_factor[i]

# Normalize to sum to 1.0
adjusted_weight[i] = adjusted_weight[i] / sum(adjusted_weight)
```

### Example Adjustment

Base allocation:
```
MLB: 0.20, Crypto: 0.15, Earnings: 0.25, AI: 0.20, Econ: 0.20
```

Market Conditions:
```
VIX: 25 (High Vol regime) → vol_multiplier = 0.8
Sentiment: -0.6 (negative) → Crypto ×0.8, AI ×0.8, MLB ×1.1, Econ ×1.1
Funding: 0.025 (elevated) → Crypto ×0.85
```

Calculation:
```
MLB:      0.20 × 0.8 × 1.1 = 0.176
Crypto:   0.15 × 0.8 × 0.8 × 0.85 = 0.0816
Earnings: 0.25 × 0.8 = 0.20
AI:       0.20 × 0.8 × 0.8 = 0.128
Econ:     0.20 × 0.8 × 1.1 = 0.176

Sum = 0.761

Normalized:
MLB:      0.176 / 0.761 = 0.231
Crypto:   0.0816 / 0.761 = 0.107
Earnings: 0.20 / 0.761 = 0.263
AI:       0.128 / 0.761 = 0.168
Econ:     0.176 / 0.761 = 0.231
```

Result: Crypto reduced due to stress regime + negative sentiment + elevated funding

---

## Portfolio Metrics Calculated

### Portfolio Expected Return

```
E[R_p] = sum(w_i × E[r_i])

Example:
E[R_p] = 0.20 × 15% + 0.15 × 25% + 0.25 × 18% + 0.20 × 22% + 0.20 × 12%
       = 3% + 3.75% + 4.5% + 4.4% + 2.4%
       = 18.05%
```

### Portfolio Volatility

```
σ_p = sqrt(w @ Σ @ w)

Where Σ is the covariance matrix.
```

### Sharpe Ratio

```
Sharpe = (E[R_p] - r_f) / σ_p

Assuming r_f (risk-free rate) = 4%:
Sharpe = (18.05% - 4%) / σ_p
```

### Concentration (Herfindahl Index)

```
HHI = sum(w_i²)

Range: 0.2 (equal weight) to 1.0 (single asset)
Threshold: > 0.35 triggers concentration warning
```

### Kelly Fractions

```
f_i = (E[r_i] / σ_i²) × kelly_fraction

Example for MLB (15%, 12%):
f_MLB = (0.15 / 0.0144) × 0.25 = 2.604

Interpretation: Allocate at most 2.6% of capital per unit of risk
```

---

## Rebalancing Rules

### When to Rebalance

1. **Drift Threshold**: Max weight drift > 3%
   ```
   |actual_weight - target_weight| > 0.03
   ```

2. **Concentration Alert**: HHI > 0.35
   ```
   sum(w_i²) > 0.35
   ```

3. **Regime Shift**: Regime changes and recommended action != "Hold"

4. **Periodic**: At fixed intervals (monthly, quarterly)

### Rebalancing Costs

Transaction costs:
```
cost = trade_size × (commission + slippage)
     = |w_new - w_old| × portfolio_value × 0.05%

Example: 10% rebalance in $1M portfolio with 5bps cost
cost = 0.10 × $1M × 0.05% = $500
```

---

## Constraints & Limits

### Position Limits

```
Minimum weight per strategy: 0% (can be zero)
Maximum weight per strategy: 100% (unlikely)

Practical constraints:
- Single position max: 35% (concentration limit)
- Minimum for meaningful allocation: 5%
```

### Leverage

```
Sum of absolute weights: sum(|w_i|) ≤ 1.5

Current implementation: all long, no shorts
sum(w) = 1.0 (no leverage)
```

### Diversification Requirements

```
At least 3 strategies with > 5% weight
No single strategy > 40% of portfolio
```

---

## Parameter Estimation

### Expected Returns

```
Sources:
- Historical backtests (3-5 years)
- Forward expectations from analysts
- Risk-adjusted equilibrium models

Considerations:
- Regime-dependence (higher in bull markets)
- Survivorship bias (overstates historical returns)
- Look-ahead bias (use realized forward returns)
```

### Volatility

```
Annualized vol = sqrt(252) × daily vol

Historical window: 1-2 years of data
GARCH model: dynamic volatility estimate
Implied vol: from option prices
```

### Correlation

```
Pearson correlation: standard pairwise correlation
Rolling window: 1-2 years to capture regime changes
Tail dependence: higher correlation in downturns (not captured by Pearson)
```

---

## Sensitivity Analysis

### Parameter Sensitivity

Kelly criterion is **most sensitive** to:
1. Correlation matrix (especially negative correlations)
2. Expected returns (linear sensitivity)
3. Volatility (quadratic sensitivity)

Maximum Sharpe is **more robust** to:
- Parameter estimation errors
- Correlation changes

### Robustness Testing

```
1. Vary expected returns ±20%
2. Vary volatilities ±20%
3. Vary correlations ±0.1

Check if allocation is stable:
- Weight changes < 5 pct points
- Relative weights rank unchanged
```

---

## Implementation Checklist

- [ ] Implement Kelly criterion optimization
- [ ] Implement Sharpe optimization
- [ ] Implement minimum variance optimization
- [ ] Build correlation matrix from data
- [ ] Add regime classification logic
- [ ] Implement adjustment factor calculations
- [ ] Add rebalancing trigger detection
- [ ] Calculate all portfolio metrics
- [ ] Add concentration monitoring
- [ ] Build monitoring/alerting
- [ ] Set up database logging
- [ ] Create admin dashboard
- [ ] Backtest allocation rules
- [ ] Validate against historical data
- [ ] Document assumptions and limitations

---

## References

- **Kelly Criterion**: MacLean et al. "The Kelly Capital Growth Investment Criterion"
- **Portfolio Optimization**: Markowitz "Portfolio Selection"
- **Sharpe Ratio**: Sharpe "Mutual Fund Performance"
- **Covariance Estimation**: Ledoit-Wolf Shrinkage
- **Regime Detection**: Hamilton "Regime-Switching Models"
