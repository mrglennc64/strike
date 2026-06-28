# Portfolio Engine API Reference

## Base URL
```
http://localhost:8001/api/portfolio
```

---

## Endpoints

### 1. Simulate Portfolio

**Endpoint:** `POST /api/portfolio/simulate`

Run Monte Carlo simulation for portfolio paths with multiple strategies.

#### Request Body

```json
{
  "strategies": [
    {
      "name": "MLB",
      "expected_return": 15.0,
      "volatility": 12.0,
      "sharpe_ratio": 1.25,
      "max_drawdown": -0.15,
      "weight": 0.20
    },
    {
      "name": "Crypto",
      "expected_return": 25.0,
      "volatility": 40.0,
      "sharpe_ratio": 0.625,
      "max_drawdown": -0.50,
      "weight": 0.15
    },
    {
      "name": "Earnings",
      "expected_return": 18.0,
      "volatility": 18.0,
      "sharpe_ratio": 1.0,
      "max_drawdown": -0.20,
      "weight": 0.25
    },
    {
      "name": "AI",
      "expected_return": 22.0,
      "volatility": 32.0,
      "sharpe_ratio": 0.69,
      "max_drawdown": -0.35,
      "weight": 0.20
    },
    {
      "name": "Econ",
      "expected_return": 12.0,
      "volatility": 8.0,
      "sharpe_ratio": 1.5,
      "max_drawdown": -0.10,
      "weight": 0.20
    }
  ],
  "num_simulations": 1000,
  "time_horizon_days": 252,
  "initial_capital": 100000,
  "rebalance_frequency": "monthly"
}
```

#### Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `strategies` | array | required | Array of 5 strategy definitions (MLB, Crypto, Earnings, AI, Econ) |
| `num_simulations` | integer | 1000 | Number of Monte Carlo runs (100-10000) |
| `time_horizon_days` | integer | 252 | Trading days to simulate (1-1260) |
| `initial_capital` | number | 100000 | Starting capital in USD |
| `rebalance_frequency` | string | "monthly" | daily/weekly/monthly/quarterly |

#### Strategy Object

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `name` | string | required | Strategy name (MLB, Crypto, Earnings, AI, Econ) |
| `expected_return` | number | > 0 | Annual return as percentage (e.g., 15.0 = 15%) |
| `volatility` | number | > 0 | Annual volatility as percentage (e.g., 12.0 = 12%) |
| `sharpe_ratio` | number | any | Risk-adjusted return (excess return / volatility) |
| `max_drawdown` | number | -1 to 0 | Historical maximum drawdown (e.g., -0.15 = -15%) |
| `weight` | number | 0 to 1 | Portfolio weight (all must sum to ~1.0) |

#### Response (200 OK)

```json
{
  "num_simulations": 1000,
  "time_horizon_days": 252,
  "initial_capital": 100000,
  "strategies": [...],
  
  "final_capital_mean": 152340.50,
  "final_capital_median": 148920.30,
  "final_capital_std": 28450.20,
  "final_capital_min": 89450.10,
  "final_capital_max": 245670.80,
  
  "total_return_mean": 52.34,
  "total_return_median": 48.92,
  "total_return_std": 28.45,
  
  "sharpe_ratio": 1.42,
  "sortino_ratio": 2.15,
  
  "max_drawdown_mean": -12.5,
  "max_drawdown_worst": -28.3,
  "max_drawdown_percentile_95": -21.2,
  
  "recovery_time_mean": 42,
  "probability_profitable": 87.5,
  "probability_double": 32.1,
  
  "equity_curve": [
    {
      "day": 0,
      "percentile_5": 100000.0,
      "percentile_25": 100000.0,
      "median": 100000.0,
      "percentile_75": 100000.0,
      "percentile_95": 100000.0
    },
    {
      "day": 5,
      "percentile_5": 99250.5,
      "percentile_25": 100125.3,
      "median": 101340.2,
      "percentile_75": 102850.1,
      "percentile_95": 104670.3
    }
  ],
  
  "drawdown_distribution": [
    {"drawdown": 0.0, "frequency": 1000},
    {"drawdown": 0.05, "frequency": 950},
    {"drawdown": 0.10, "frequency": 850}
  ],
  
  "correlation_drag": 0.35,
  "diversification_ratio": 1.48
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `final_capital_*` | number | Terminal capital statistics across simulations |
| `total_return_*` | number | Total return percentage distribution |
| `sharpe_ratio` | number | Annualized Sharpe ratio (mean simulation) |
| `sortino_ratio` | number | Annualized Sortino ratio (downside volatility) |
| `max_drawdown_*` | number | Maximum drawdown statistics (%) |
| `recovery_time_mean` | integer | Mean days to recover from max drawdown |
| `probability_profitable` | number | % of simulations with positive return |
| `probability_double` | number | % of simulations that doubled capital |
| `equity_curve` | array | Path statistics at key time points |
| `drawdown_distribution` | array | Histogram of drawdown levels |
| `correlation_drag` | number | % return reduction from correlation |
| `diversification_ratio` | number | Benefit of diversification (1.0 = no benefit) |

#### Example cURL

```bash
curl -X POST http://localhost:8001/api/portfolio/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "strategies": [
      {"name": "MLB", "expected_return": 15, "volatility": 12, "sharpe_ratio": 1.25, "max_drawdown": -0.15, "weight": 0.2},
      {"name": "Crypto", "expected_return": 25, "volatility": 40, "sharpe_ratio": 0.625, "max_drawdown": -0.5, "weight": 0.2},
      {"name": "Earnings", "expected_return": 18, "volatility": 18, "sharpe_ratio": 1.0, "max_drawdown": -0.2, "weight": 0.2},
      {"name": "AI", "expected_return": 22, "volatility": 32, "sharpe_ratio": 0.69, "max_drawdown": -0.35, "weight": 0.2},
      {"name": "Econ", "expected_return": 12, "volatility": 8, "sharpe_ratio": 1.5, "max_drawdown": -0.1, "weight": 0.2}
    ],
    "num_simulations": 500,
    "time_horizon_days": 252,
    "initial_capital": 100000
  }'
```

#### Error Responses

**400 Bad Request** - Invalid input
```json
{
  "detail": "Must provide exactly 5 strategies (MLB, Crypto, Earnings, AI, Econ)"
}
```

**400 Bad Request** - Weights don't sum to 1.0
```json
{
  "detail": "Weights must sum to 1.0 (got 0.95)"
}
```

**500 Internal Server Error** - Simulation failed
```json
{
  "detail": "Simulation failed: [error message]"
}
```

---

### 2. Calculate Optimal Allocation

**Endpoint:** `POST /api/portfolio/allocation`

Calculate optimal portfolio weights using specified optimization method.

#### Request Body

```json
{
  "strategies": [
    {
      "name": "MLB",
      "expected_return": 15.0,
      "volatility": 12.0,
      "sharpe_ratio": 1.25,
      "max_drawdown": -0.15,
      "weight": 0.20
    },
    ...
  ],
  "optimization_method": "kelly",
  "kelly_fraction": 0.25
}
```

#### Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `strategies` | array | required | Array of 5 strategy definitions |
| `optimization_method` | string | "kelly" | kelly, sharpe, min_variance, or equal_weight |
| `kelly_fraction` | number | 0.25 | Fraction of full Kelly to apply (0.01-1.0) |

#### Response (200 OK)

```json
{
  "optimization_method": "kelly",
  "optimal_weights": {
    "MLB": 0.25,
    "Crypto": 0.18,
    "Earnings": 0.28,
    "AI": 0.15,
    "Econ": 0.14
  },
  "kelly_fractions": {
    "MLB": 0.25,
    "Crypto": 0.18,
    "Earnings": 0.28,
    "AI": 0.15,
    "Econ": 0.14
  },
  "portfolio_expected_return": 16.8,
  "portfolio_volatility": 14.2,
  "portfolio_sharpe_ratio": 1.18,
  "largest_weight": 0.28,
  "concentration_herfindahl": 0.189,
  "weights_sum": 1.0,
  "is_valid": true
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `optimal_weights` | object | Strategy name → weight (0-1) |
| `kelly_fractions` | object | Recommended bet sizing per strategy |
| `portfolio_expected_return` | number | Portfolio expected annual return (%) |
| `portfolio_volatility` | number | Portfolio annual volatility (%) |
| `portfolio_sharpe_ratio` | number | Portfolio Sharpe ratio |
| `largest_weight` | number | Concentration in largest position |
| `concentration_herfindahl` | number | HHI (0.2-1.0, lower = more diversified) |
| `weights_sum` | number | Sum of weights (should be ~1.0) |
| `is_valid` | boolean | Are weights valid and normalized? |

#### Optimization Methods

**Kelly Criterion** (`kelly`)
- Growth-optimal allocation
- Most aggressive, highest leverage
- Best for: Long-term wealth maximization
- Formula: w = inv(Σ) @ r × kelly_fraction
- Applied kelly_fraction: reduces risk (0.25 = quarter-Kelly)

**Maximum Sharpe Ratio** (`sharpe`)
- Risk-adjusted return maximization
- Balanced risk and return
- Best for: Institutional portfolios
- Uses convex optimization (SLSQP)

**Minimum Variance** (`min_variance`)
- Volatility minimization (risk-parity)
- Conservative, lower return
- Best for: Defensive positioning
- Uses convex optimization

**Equal Weight** (`equal_weight`)
- Simple baseline (20% each)
- No optimization
- Best for: Diversification without optimization

#### Example cURL

```bash
curl -X POST http://localhost:8001/api/portfolio/allocation \
  -H "Content-Type: application/json" \
  -d '{
    "strategies": [...],
    "optimization_method": "sharpe",
    "kelly_fraction": 0.25
  }'
```

---

### 3. Assess Market Regime

**Endpoint:** `POST /api/portfolio/regime`

Assess current market regime and get weight adjustment recommendations.

#### Request Body

```json
{
  "current_vix": 18.5,
  "vix_percentile_30d": 60,
  "crypto_funding_rate": 0.015,
  "market_sentiment": 0.3,
  "base_weights": {
    "MLB": 0.20,
    "Crypto": 0.15,
    "Earnings": 0.25,
    "AI": 0.20,
    "Econ": 0.20
  },
  "strategies": [...]
}
```

#### Request Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `current_vix` | number | Current VIX level (0-80 typical) |
| `vix_percentile_30d` | number | VIX percentile over 30 days (0-100) |
| `crypto_funding_rate` | number | Crypto annualized funding rate (-0.01 to 0.05) |
| `market_sentiment` | number | Market sentiment score (-1 to +1) |
| `base_weights` | object | Current/baseline allocation |
| `strategies` | array | Strategy definitions for context |

#### Response (200 OK)

```json
{
  "regime_name": "Normal",
  "vix_level": 18.5,
  "vix_percentile": 60,
  "funding_rate": 0.015,
  "funding_regime": "elevated",
  "sentiment_score": 0.3,
  "regime_adjusted_weights": {
    "MLB": 0.18,
    "Crypto": 0.12,
    "Earnings": 0.28,
    "AI": 0.24,
    "Econ": 0.18
  },
  "regime_adjustment_factor": {
    "MLB": 0.90,
    "Crypto": 0.80,
    "Earnings": 1.12,
    "AI": 1.20,
    "Econ": 0.90
  },
  "recommended_action": "Rebalance",
  "explanation": "Elevated funding rate and positive sentiment warrant tactical positioning. Consider rebalancing to recommended weights."
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `regime_name` | string | Low Vol, Normal, High Vol, or Stress |
| `vix_level` | number | Current VIX level |
| `vix_percentile` | number | Historical percentile (0-100) |
| `funding_rate` | number | Crypto funding rate |
| `funding_regime` | string | normal, elevated, or extreme |
| `sentiment_score` | number | Market sentiment (-1 to +1) |
| `regime_adjusted_weights` | object | Recommended weights for current regime |
| `regime_adjustment_factor` | object | Multiplier applied to base weights per strategy |
| `recommended_action` | string | Hold, Reduce Risk, Increase Risk, or Rebalance |
| `explanation` | string | Human-readable reasoning |

#### Regime Classification

| VIX Range | Regime | Vol Multiplier | Characteristics |
|-----------|--------|----------------|-----------------|
| < 12 | Low Vol | 1.2x | Market complacency, risk-on |
| 12-20 | Normal | 1.0x | Balanced risk/reward |
| 20-30 | High Vol | 0.8x | Elevated uncertainty |
| > 30 | Stress | 0.6x | Market crisis, contagion |

#### Sentiment Impact

- **Negative (< -0.5)**: Reduce risky assets (AI, Crypto), increase defensive (MLB, Econ)
- **Positive (> 0.5)**: Increase growth assets (AI, Crypto)

#### Funding Rate Impact

- **Normal (< 0.02)**: No adjustment
- **Elevated (0.02-0.03)**: -15% Crypto weight
- **Extreme (> 0.03)**: -25% Crypto weight

#### Example cURL

```bash
curl -X POST http://localhost:8001/api/portfolio/regime \
  -H "Content-Type: application/json" \
  -d '{
    "current_vix": 18.5,
    "vix_percentile_30d": 60,
    "crypto_funding_rate": 0.015,
    "market_sentiment": 0.3,
    "base_weights": {
      "MLB": 0.2, "Crypto": 0.15, "Earnings": 0.25, "AI": 0.2, "Econ": 0.2
    },
    "strategies": [...]
  }'
```

---

### 4. Health Check

**Endpoint:** `GET /api/portfolio/health`

Check portfolio service health and available endpoints.

#### Response (200 OK)

```json
{
  "status": "ok",
  "service": "portfolio_engine",
  "endpoints": [
    "POST /api/portfolio/simulate - Monte Carlo simulation",
    "POST /api/portfolio/allocation - Optimal allocation",
    "POST /api/portfolio/regime - Regime assessment"
  ]
}
```

#### Example cURL

```bash
curl http://localhost:8001/api/portfolio/health
```

---

## Common Use Cases

### Use Case 1: Portfolio Backtesting
```bash
# Simulate portfolio with current allocation
curl -X POST http://localhost:8001/api/portfolio/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "strategies": [...],
    "num_simulations": 1000,
    "time_horizon_days": 252
  }' > backtest_results.json

# Parse results for decision-making
jq '.sharpe_ratio, .probability_profitable' backtest_results.json
```

### Use Case 2: Optimal Reallocation
```bash
# Get optimal allocation
curl -X POST http://localhost:8001/api/portfolio/allocation \
  -H "Content-Type: application/json" \
  -d '{
    "strategies": [...],
    "optimization_method": "sharpe"
  }' > optimal_weights.json

# Extract weights for execution
jq '.optimal_weights' optimal_weights.json
```

### Use Case 3: Regime-Based Adjustment
```bash
# Check current regime and get adjustment
curl -X POST http://localhost:8001/api/portfolio/regime \
  -H "Content-Type: application/json" \
  -d '{
    "current_vix": 20.5,
    "vix_percentile_30d": 75,
    "crypto_funding_rate": 0.025,
    "market_sentiment": -0.4,
    "base_weights": {...},
    "strategies": [...]
  }' > regime_adjustment.json

# Execute rebalancing if recommended
jq -r '.recommended_action' regime_adjustment.json
```

### Use Case 4: Monitoring Pipeline
```bash
# Run hourly regime checks
# Run every 5 minutes: allocation vs recommended
# Run daily: correlation structure analysis
# Log alerts to database
# Send webhooks on regime shifts
```

---

## Error Handling

### Common Errors

**400 - Invalid Request**
- Weights don't sum to 1.0
- Missing required fields
- Invalid strategy names
- Out-of-range parameter values

**500 - Server Error**
- Singular/non-positive definite correlation matrix
- Optimization convergence failure
- Database connection issues
- External API failures

### Retry Logic

For transient failures (500 errors), use exponential backoff:
```python
import requests
from time import sleep

max_retries = 3
for attempt in range(max_retries):
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        break
    except requests.exceptions.RequestException as e:
        if attempt < max_retries - 1:
            sleep(2 ** attempt)
        else:
            raise
```

---

## Rate Limiting

No official rate limiting is implemented, but recommended:
- Simulate: 1 request per minute (computationally expensive)
- Allocate: 10 requests per minute
- Regime: 10 requests per minute
- Health: Unlimited

---

## Authentication

Currently no authentication. In production, add:
- API key in `Authorization: Bearer <token>` header
- JWT tokens with short expiration
- CORS restrictions

---

## Versioning

Current API version: **v1**

Future versions may include:
- Advanced analytics
- Machine learning integration
- Real-time streaming
- GraphQL endpoint
