# Earnings Beat/Miss Predictor

## Overview

A production-ready ML system that predicts whether publicly traded companies will beat or miss earnings expectations. The predictor combines multiple data sources (Yahoo Finance, options market data, earnings calendar) with XGBoost classification to generate beat/miss probabilities and calculates edge vs market-implied probabilities from options pricing.

**Key Features:**
- **Multi-source data integration**: Analyst estimates, options market data, earnings calendar
- **XGBoost classifier**: 18-feature binary classification model for beat/miss prediction
- **Edge calculation**: Compares model prediction to market-implied probability from options
- **Confidence scoring**: Confidence level based on analyst consensus, IV, and data quality
- **Edge scanner**: Batch scan multiple stocks to find highest-edge opportunities
- **Backtesting**: 90-day rolling performance metrics and model validation
- **Production API**: FastAPI endpoints for single predictions and batch operations

## Architecture

### Data Sources

#### 1. Yahoo Finance (Analyst Estimates)
```
- Current EPS consensus estimate
- Number of analysts covering stock
- Estimate variance (consensus tightness)
- Revenue estimates
- Guidance revision trend (%)
- Historical surprise data
- Estimate revisions (count of up/down)
```

**Integration:** `YahooFinanceScraper` → `AnalystEstimates` dataclass

#### 2. Options Market Data
```
- IV Rank (0-100 percentile)
- At-the-money IV
- Vol skew (call IV - put IV)
- Put/call IV ratio (fear gauge)
- Implied move (%)
- Smart money flow indicator
- Options volume/open interest
- Market-implied P(beat) from option pricing
```

**Integration:** `OptionsDataIntegrator` → `OptionsData` dataclass

#### 3. Earnings Calendar
```
- Earnings announcement date
- Fiscal period (Q1 2024, etc)
- Historical beat/miss track record
- Sector average surprise
- Peak earnings season indicator
```

**Integration:** `EarningsCalendarScraper` → `EarningsCalendarData` dataclass

### Feature Engineering

18 features extracted from above sources for XGBoost model:

| Feature | Source | Range | Description |
|---------|--------|-------|-------------|
| `analyst_consensus_strength` | Yahoo | 0-1 | Inverse of normalized estimate variance |
| `num_analysts` | Yahoo | 0-50+ | Number of analysts covering stock |
| `days_until_earnings` | Calendar | 0-90 | Days until earnings announcement |
| `guidance_revision_trend` | Yahoo | -20% to +20% | % change in consensus last 30d |
| `revisions_ratio` | Yahoo | 0-1 | Up revisions / (up + down) |
| `iv_rank` | Options | 0-100 | IV percentile vs 52-week range |
| `vol_skew` | Options | -10 to +10 | Call IV - Put IV (points) |
| `implied_move_pct` | Options | 1-10% | Market's expected post-earnings move |
| `put_call_ratio` | Options | 0.5-2.0 | Put IV / Call IV ratio |
| `smart_money_direction` | Options | -1, 0, +1 | Inferred from flow (bearish/neutral/bullish) |
| `avg_surprise_pct` | History | -5% to +5% | Average historical surprise |
| `surprise_consistency` | History | 0-1 | Inverse of surprise variance |
| `beat_miss_ratio` | History | 0-1 | Beats / (beats + misses) last 4 quarters |
| `quarter_progress_pct` | Calendar | 0-1 | How far through fiscal quarter |
| `is_peak_season` | Calendar | 0, 1 | Binary: is earnings season |
| `days_from_last_earnings` | History | 0-100 | Days since previous earnings |
| `market_implied_prob_beat` | Options | 0-1 | Probability inferred from option prices |
| `earnings_surprise_zscore` | History | -3 to +3 | Z-score of current vs historical |

### Model: XGBoost Binary Classifier

**Target:** 1 = Beat, 0 = Miss

**Hyperparameters (optimized for earnings classification):**
```python
XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.08,
    subsample=0.8,
    colsample_bytree=0.8,
    min_child_weight=5,
    reg_alpha=0.5,           # L1 regularization
    reg_lambda=1.5,          # L2 regularization
    objective="binary:logistic",
    eval_metric="logloss",
)
```

**Output:** P(Beat) ∈ [0, 1] → P(Miss) = 1 - P(Beat)

### Edge Calculation

**Edge** = Model Prediction - Market-Implied Probability

```
Edge = P(Beat)_model - P(Beat)_options

Edge% = Edge / P(Beat)_options * 100

Interpretation:
- Edge > 5%  → Model predicts higher P(Beat) than market
- Edge < -5% → Model predicts lower P(Beat) than market
- |Edge| < 5% → Edge too small for reliable trading
```

### Recommendations

Based on predicted probability and edge:

| Prediction | Edge | Recommendation |
|-----------|------|-----------------|
| P(Beat) > 65% | Edge > 10% | BUY_CALL_SPREAD |
| P(Beat) > 55% | Edge > 5% | BUY_CALL |
| P(Beat) < 35% | Edge < -10% | BUY_PUT_SPREAD |
| P(Beat) < 45% | Edge < -5% | BUY_PUT |
| 45% < P(Beat) < 55% | \|Edge\| > 8% | STRADDLE |
| All other | - | NEUTRAL |

## API Endpoints

### 1. Single Stock Prediction

```http
POST /api/verticals/earnings/predict
Content-Type: application/json

{
  "symbol": "TSLA"
}
```

**Response (200):**
```json
{
  "symbol": "TSLA",
  "company_name": "Tesla Inc.",
  "prediction_date": "2024-06-28T10:30:00Z",
  "earnings_date": "2024-07-20T20:00:00Z",
  
  "predicted_probability_beat": 0.62,
  "predicted_probability_miss": 0.38,
  "predicted_probability_in_line": 0.0,
  
  "market_implied_prob_beat": 0.55,
  
  "edge_probability": 0.07,
  "edge_pct": 12.7,
  "expected_move_pct": 4.2,
  
  "recommendation": "BUY_CALL_SPREAD",
  "confidence": 78.5,
  
  "analyst_estimates": {...},
  "options_data": {...},
  "calendar_data": {...}
}
```

**Cache:** 4 hours per symbol

### 2. Multi-Stock Edge Scan

```http
POST /api/verticals/earnings/scan
Content-Type: application/json

{
  "symbols": ["TSLA", "MSFT", "NVDA", "META", "AAPL"],
  "min_edge_pct": 5.0,
  "only_with_edge": true
}
```

**Response (200):**
```json
{
  "scan_date": "2024-06-28T10:30:00Z",
  "symbols_scanned": 5,
  "symbols_with_edge": 3,
  "avg_edge": 8.5,
  
  "top_edge": {
    "symbol": "TSLA",
    "edge_pct": 12.7,
    ...
  },
  
  "predictions": [
    {
      "symbol": "TSLA",
      "edge_pct": 12.7,
      "predicted_probability_beat": 0.62,
      ...
    },
    ...
  ]
}
```

**Sorting:** By edge_pct descending

### 3. Get Latest Prediction

```http
GET /api/verticals/earnings/{symbol}
```

**Response (200):** `EarningsPredictionRecordResponse`

### 4. Prediction History

```http
GET /api/verticals/earnings/{symbol}/history?limit=20
```

**Response (200):**
```json
{
  "total": 15,
  "predictions": [
    {
      "id": 42,
      "symbol": "TSLA",
      "predicted_prob_beat": 0.62,
      "market_implied_prob_beat": 0.55,
      "edge_pct": 12.7,
      "recommendation": "BUY_CALL_SPREAD",
      "actual_outcome": "beat",
      "surprise_pct": 2.3,
      ...
    }
  ]
}
```

### 5. Backtest Performance

```http
POST /api/verticals/earnings/backtest?days=90&symbol=TSLA
```

**Response (200):**
```json
{
  "period": "last_90_days",
  "total_predictions": 23,
  "predictions_with_edge": 15,
  
  "hit_rate": 0.652,
  "edge_hit_rate": 0.733,
  
  "total_edge_pct": 127.5,
  "avg_edge_per_prediction": 5.54,
  "profit_factor": 1.87,
  
  "largest_win": 18.5,
  "largest_loss": -12.3,
  
  "kelly_fraction": 0.25,
  
  "accuracy_by_confidence_bucket": {
    "high_confidence": 0.78,
    "medium_confidence": 0.65,
    "low_confidence": 0.52
  }
}
```

**Interpretation:**
- `hit_rate`: % of predictions that correctly called beat/miss
- `edge_hit_rate`: % of positive-edge predictions that were profitable
- `profit_factor`: (sum of winning edges) / (sum of losing edges)
- `kelly_fraction`: Recommended Kelly fraction for position sizing

### 6. Model Statistics

```http
GET /api/verticals/earnings/model/stats
```

**Response (200):**
```json
{
  "version": "1.0.0",
  "model_type": "XGBoost",
  "training_date": "2024-06-01T00:00:00Z",
  "training_samples": 1247,
  "feature_count": 18,
  "feature_names": [
    "analyst_consensus_strength",
    "num_analysts",
    ...
  ],
  
  "auc_score": 0.723,
  "precision": 0.68,
  "recall": 0.71,
  "f1_score": 0.695,
  
  "last_retrain_date": "2024-06-15T00:00:00Z",
  "is_live": true
}
```

## Database Schema

### EarningsPredictionRecord
```sql
CREATE TABLE earnings_predictions (
  id INTEGER PRIMARY KEY,
  user_id INTEGER,
  symbol VARCHAR(20) INDEX,
  company_name VARCHAR(255),
  
  prediction_date DATETIME INDEX,
  earnings_date DATETIME INDEX,
  
  predicted_prob_beat FLOAT,
  predicted_prob_miss FLOAT,
  predicted_prob_in_line FLOAT,
  market_implied_prob_beat FLOAT,
  
  edge_probability FLOAT,
  edge_pct FLOAT,
  expected_move_pct FLOAT,
  
  recommendation VARCHAR(50),
  confidence FLOAT,
  
  analyst_consensus_strength FLOAT,
  num_analysts INTEGER,
  guidance_revision_trend FLOAT,
  iv_rank FLOAT,
  vol_skew FLOAT,
  implied_move_pct FLOAT,
  smart_money_flow VARCHAR(20),
  
  actual_outcome VARCHAR(20),
  actual_eps FLOAT,
  actual_revenue FLOAT,
  surprise_pct FLOAT,
  outcome_date DATETIME,
  
  notes TEXT,
  created_at DATETIME,
  updated_at DATETIME
);

CREATE INDEX idx_symbol ON earnings_predictions(symbol);
CREATE INDEX idx_prediction_date ON earnings_predictions(prediction_date);
CREATE INDEX idx_earnings_date ON earnings_predictions(earnings_date);
```

### EarningsHistoryRecord
```sql
CREATE TABLE earnings_history (
  id INTEGER PRIMARY KEY,
  symbol VARCHAR(20) INDEX,
  company_name VARCHAR(255),
  
  earnings_date DATETIME INDEX,
  fiscal_period VARCHAR(20),
  
  eps_estimate FLOAT,
  revenue_estimate FLOAT,
  eps_actual FLOAT,
  revenue_actual FLOAT,
  
  eps_surprise_pct FLOAT,
  revenue_surprise_pct FLOAT,
  beat_miss VARCHAR(20),
  
  stock_price_pre_earnings FLOAT,
  stock_price_post_earnings FLOAT,
  post_earnings_move_pct FLOAT,
  
  iv_rank FLOAT,
  implied_move_pct FLOAT,
  put_call_ratio FLOAT,
  num_analysts INTEGER,
  guidance_revision_trend FLOAT,
  
  sector VARCHAR(100),
  sector_avg_surprise FLOAT,
  
  created_at DATETIME
);
```

## React Component

### EarningsPredictorDashboard

**Location:** `frontend/src/components/EarningsPredictorDashboard.tsx`

**Features:**
- **Predict Tab**: Single stock prediction with all details
- **Scan Tab**: Multi-stock edge scanner
- **History Tab**: Prediction history and performance
- **Metrics Tab**: 90-day backtest results

**Usage:**
```tsx
import { EarningsPredictorDashboard } from './components/EarningsPredictorDashboard';

export default function App() {
  return <EarningsPredictorDashboard />;
}
```

**Styling:** Tailwind CSS with dark mode (slate-900 background)

**State Management:** React hooks (useState, useEffect)

**Data Fetching:** fetch API with async/await

## Example Usage

### Python Client

```python
from services.earnings_predictor import EarningsPredictorEngine

# Initialize engine
engine = EarningsPredictorEngine(model_path="models/earnings_xgboost.pkl")

# Predict single stock
prediction = await engine.predict("TSLA")
print(f"P(Beat): {prediction.predicted_probability_beat:.1%}")
print(f"Edge: {prediction.edge_pct:+.2f}%")
print(f"Recommendation: {prediction.recommendation}")

# Access raw data
print(f"Analyst consensus: {prediction.analyst_estimates.num_analysts} analysts")
print(f"IV Rank: {prediction.options_data.iv_rank:.0f}")
```

### cURL

```bash
# Single prediction
curl -X POST http://localhost:8000/api/verticals/earnings/predict \
  -H "Content-Type: application/json" \
  -d '{"symbol": "TSLA"}'

# Edge scan
curl -X POST http://localhost:8000/api/verticals/earnings/scan \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["TSLA", "MSFT", "NVDA"],
    "min_edge_pct": 5.0,
    "only_with_edge": true
  }'

# Backtest
curl http://localhost:8000/api/verticals/earnings/backtest?days=90
```

### JavaScript/TypeScript

```typescript
// Single prediction
const response = await fetch('/api/verticals/earnings/predict', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ symbol: 'TSLA' })
});
const prediction = await response.json();

// Multi-stock scan
const scanResponse = await fetch('/api/verticals/earnings/scan', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    symbols: ['TSLA', 'MSFT', 'NVDA'],
    min_edge_pct: 5.0,
    only_with_edge: true
  })
});
const scanResults = await scanResponse.json();
```

## Training & Model Updates

### Training Data

Model trained on:
- **Historical periods**: 2+ years of earnings announcements
- **Sample size**: 1,000+ earnings events
- **Features**: 18 engineered features per sample
- **Target**: Actual beat/miss outcome

### Retraining Schedule

- **Weekly**: Backtest evaluation on last 90 days
- **Monthly**: Model retraining with new data
- **Quarterly**: Feature importance analysis and feature engineering review

### Model Versioning

Models stored with timestamp:
```
models/
  earnings_xgboost_20240601.pkl     # Training date
  earnings_xgboost_latest.pkl       # Current live model
  earnings_xgboost_backup.pkl       # Previous model
```

## Monitoring & Performance

### Key Metrics

- **Hit Rate**: % of predictions that correctly called beat/miss
- **Edge Hit Rate**: % of positive-edge predictions that were correct
- **Profit Factor**: (sum of winning edges) / (sum of losing edges)
- **Sharpe Ratio**: Risk-adjusted returns across predictions
- **Max Drawdown**: Worst consecutive losing edge streak

### Alerting

Monitor via:
1. Hit rate drops below 55% → Recheck features and data quality
2. Profit factor < 1.2 → Model degradation, retrain
3. Backtest scores diverge from live → Data leakage, review

## Deployment

### Requirements

```
fastapi>=0.104.0
httpx>=0.25.0
sqlalchemy>=2.0.0
xgboost>=2.0.0
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/earnings_db

# API Settings
DEBUG=False
API_KEY=xxx  # For auth middleware

# Model paths
MODEL_PATH=models/earnings_xgboost_latest.pkl
```

## Troubleshooting

### "Could not generate prediction for {symbol}"

**Causes:**
- Yahoo Finance API unreachable
- Invalid ticker symbol
- No options data available
- Data quality issues

**Fix:**
1. Check network connectivity
2. Verify ticker with `GET /health`
3. Try different symbol
4. Check logs for data validation errors

### Predictions not improving

**Causes:**
- Model stale (last trained >2 weeks ago)
- Feature drift in data
- Market regime change
- Insufficient training samples

**Fix:**
1. Retrain model with fresh data
2. Analyze feature importance
3. Review recent backtest metrics
4. Check analyst estimate vs historical accuracy

### API rate limits

**Solution:**
- Implement request caching (done: 4-hour cache)
- Use background tasks for batch operations
- Queue predictions via Redis/Celery for high volume

## Future Enhancements

1. **Cross-asset correlation**: Include VIX, sector rotation
2. **Deep learning**: LSTM for time-series analysis
3. **Ensemble methods**: Combine XGBoost with LightGBM, CatBoost
4. **Real-time features**: Live trading volume, sentiment from news
5. **Custom models**: Per-sector specialists (tech vs finance vs healthcare)
6. **Risk controls**: Position limits, volatility-based Kelly fraction
7. **Integration**: Direct options flow from vendors (ORATS, Unusual Whales)

## Support

For issues or questions:
- Review logs at `/var/log/earnings_predictor/`
- Check backtest results for degradation
- Contact: support@stike.com
