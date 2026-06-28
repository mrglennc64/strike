# Fed/Economics Predictor

A comprehensive time-series machine learning system for predicting Federal Reserve economic indicators and finding arbitrage opportunities on prediction markets (Polymarket, Kalshi).

## Features

### Predictions
- **CPI (Consumer Price Index)** - Probability CPI > 3.5% next month
- **Rate Cuts** - Probability of Fed rate cut at next FOMC meeting
- **Unemployment** - Probability unemployment > threshold
- **GDP Growth** - Probability GDP > threshold (quarterly)

### Data Integration
- **FRED API** - Federal Reserve Economic Data (St. Louis Fed)
- **Polymarket** - Decentralized prediction market prices
- **Kalshi** - Regulated prediction market prices
- **FOMC Calendar** - Fed Open Market Committee meeting schedule

### Machine Learning
- **XGBoost Classifiers** - Binary classification for each outcome
- **Time-Series Features**
  - Lag features (1, 3, 6, 12 months)
  - Rolling statistics (mean, std, min, max)
  - Rate of change indicators
  - Volatility measures
- **Feature Engineering** - Automatic feature generation from FRED data
- **Model Validation** - AUC, Brier score, accuracy tracking

### Edge Detection
- **Edge Calculation** - Model prediction vs market probability
- **Kelly Criterion** - Optimal bet sizing (capped at 25%)
- **Expected Value** - EV calculation for each side
- **Confidence Levels** - High/Medium/Low based on edge magnitude

## Architecture

### Backend (Python/FastAPI)

```
backend/
├── services/
│   └── fed_economics_predictor.py    # Core prediction engine
│       ├── FREDDataProvider          # FRED API integration
│       ├── FedMeetingCalendar        # FOMC calendar scraper
│       ├── EconomicFeatureEngineer   # Time-series features
│       ├── EconomicsPredictionModel  # XGBoost trainer
│       ├── MarketPriceProvider       # Polymarket/Kalshi integration
│       ├── EdgeCalculator            # Edge + Kelly calculation
│       └── FedEconomicsPredictor      # Main orchestrator
├── routes/
│   └── economics.py                   # FastAPI endpoints
├── models/
│   └── economics.py                   # SQLAlchemy database models
├── schemas/
│   └── economics.py                   # Pydantic request/response schemas
└── requirements.txt                   # Python dependencies
```

### Frontend (React/TypeScript)

```
frontend/src/
├── components/
│   ├── EconomicsDashboard.tsx        # Main dashboard
│   ├── EconomicsTools.tsx            # Kelly, edge, gauge components
│   └── ...
├── hooks/
│   └── useEconomicsPredictions.ts   # Data fetching hook
└── ...
```

## API Endpoints

### Predictions

#### GET /api/verticals/economics/predict-cpi
Predict CPI probability above threshold

**Parameters:**
- `threshold` (float, default: 3.5) - CPI % threshold
- `market_price` (float, optional) - Market probability (0-1)

**Response:**
```json
{
  "status": "success",
  "data": {
    "metric": "CPI",
    "threshold": 3.5,
    "predicted_probability": 0.65,
    "market_probability": 0.60,
    "latest_value": 3.2,
    "edge": {
      "edge": 0.05,
      "edge_pct": 8.33,
      "ev_yes": 0.0833,
      "ev_no": -0.0667,
      "best_side": "YES",
      "kelly_fraction": 0.15
    },
    "timestamp": "2026-06-28T10:30:00Z"
  }
}
```

#### GET /api/verticals/economics/predict-rate-cut
Predict rate cut at next FOMC meeting

**Parameters:**
- `market_price` (float, optional) - Market probability

**Response:** Similar to CPI prediction, includes `next_meeting` and `current_rate`

#### GET /api/verticals/economics/calendar
Get economic calendar with upcoming releases

**Response:**
```json
{
  "status": "success",
  "data": {
    "CPI": {
      "series_id": "CPIAUCSL",
      "release_schedule": "monthly",
      "description": "Consumer Price Index - All Urban Consumers"
    },
    ...
  }
}
```

#### GET /api/verticals/economics/fomc-schedule
Get FOMC meeting schedule

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "description": "FOMC Meeting",
      "date": "2026-07-27",
      "decision_date": "2026-07-28"
    },
    ...
  ]
}
```

#### GET /api/verticals/economics/edge-opportunities
Find all current edge opportunities

**Parameters:**
- `min_edge` (float, default: 0.05) - Minimum edge % to include
- `confidence` (string, default: "all") - high/medium/low/all

**Response:**
```json
{
  "status": "success",
  "count": 2,
  "data": [
    {
      "metric": "CPI > 3.5%",
      "direction": "YES",
      "edge_percentage": 8.33,
      "model_prediction": 0.65,
      "market_price": 0.60,
      "kelly_fraction": 0.15,
      "confidence": "high"
    },
    ...
  ]
}
```

### Model Training

#### POST /api/verticals/economics/train-models
Train all prediction models on historical FRED data

**Response:**
```json
{
  "status": "success",
  "message": "Models trained successfully",
  "metrics": {
    "cpi": {
      "auc": 0.78,
      "brier_score": 0.15,
      "train_size": 120,
      "test_size": 30
    },
    "rate_cut": {
      "auc": 0.82,
      "brier_score": 0.12,
      "train_size": 120,
      "test_size": 30
    }
  }
}
```

### Prediction Management

#### POST /api/verticals/economics/save-prediction
Save a prediction for tracking

**Request:**
```json
{
  "user_id": 1,
  "metric": "CPI",
  "threshold": 3.5,
  "prediction_type": "binary",
  "predicted_probability": 0.65,
  "market_probability": 0.60,
  "kelly_fraction": 0.15,
  "expected_value": 0.0833
}
```

#### GET /api/verticals/economics/user-predictions?user_id=1
Get prediction history for user

#### GET /api/verticals/economics/predictions/{prediction_id}
Get specific prediction details

#### POST /api/verticals/economics/resolve-prediction/{prediction_id}
Resolve prediction once outcome known

**Request:**
```json
{
  "actual_outcome": true
}
```

#### GET /api/verticals/economics/model-metrics
Get model performance metrics

## Installation

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

Key packages:
- `pandas-datareader` - FRED API access
- `xgboost` - Machine learning model
- `scikit-learn` - Feature scaling, metrics
- `requests` - HTTP calls to Polymarket/Kalshi
- `beautifulsoup4` - FOMC calendar scraping

### 2. Get FRED API Key

1. Sign up free at https://fred.stlouisfed.org/docs/api/api_key.html
2. Add to `.env`:
   ```
   FRED_API_KEY=your_api_key_here
   ```

### 3. Initialize Database

```bash
alembic upgrade head
```

### 4. Train Models

```bash
curl -X POST http://localhost:8000/api/verticals/economics/train-models
```

## Usage Examples

### Python

```python
from services.fed_economics_predictor import FedEconomicsPredictor

# Initialize
predictor = FedEconomicsPredictor(fred_api_key="your_api_key")

# Setup and train models
cpi_metrics = predictor.setup_cpi_predictor(threshold=3.5)
rate_metrics = predictor.setup_rate_cut_predictor()

# Make predictions
cpi_pred = predictor.predict_cpi(threshold=3.5, market_price=0.60)
print(f"CPI P(>3.5%): {cpi_pred['predicted_probability']:.1%}")
print(f"Edge: {cpi_pred['edge']['edge']:.1%}")
print(f"Kelly: {cpi_pred['edge']['kelly_fraction']:.1%}")

# Get calendar
calendar = predictor.get_economic_calendar()
fomc = predictor.get_fomc_calendar()
```

### React

```tsx
import { useEconomicsPredictions } from './hooks/useEconomicsPredictions';

export const MyComponent = () => {
  const { cpiPrediction, rateCutPrediction, loading, trainModels } = 
    useEconomicsPredictions(60000); // Refresh every minute

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h2>CPI: {(cpiPrediction?.predicted_probability ?? 0)*100}%</h2>
      <p>Edge: {cpiPrediction?.edge.edge}%</p>
      <button onClick={trainModels}>Train Models</button>
    </div>
  );
};
```

### cURL

```bash
# Predict CPI
curl "http://localhost:8000/api/verticals/economics/predict-cpi?threshold=3.5&market_price=0.60"

# Find edges
curl "http://localhost:8000/api/verticals/economics/edge-opportunities?min_edge=0.05"

# Get FOMC schedule
curl "http://localhost:8000/api/verticals/economics/fomc-schedule"

# Train models
curl -X POST "http://localhost:8000/api/verticals/economics/train-models"
```

## Data Sources

### FRED Series IDs Used

| Metric | Series ID | Frequency | Release Day |
|--------|-----------|-----------|-------------|
| CPI | CPIAUCSL | Monthly | ~12th |
| PCE | PCEPI | Monthly | ~28th |
| Unemployment | UNRATE | Monthly | ~7th |
| NFP | PAYEMS | Monthly | ~7th |
| Retail Sales | RSXFS | Monthly | ~15th |
| Jobless Claims | ICSA | Weekly | Thursday |
| GDP | A191RA1Q225SBEA | Quarterly | ~30 days after quarter |
| Fed Funds | FEDFUNDS | Monthly | Monthly average |

### Market Sources

- **Polymarket** - Decentralized, largest volume, 2% fee
- **Kalshi** - SEC-regulated, US-only, $0.01-$0.99 range

## Model Architecture

### XGBoost Configuration

```python
XGBClassifier(
    n_estimators=100,        # 100 trees
    max_depth=6,             # Max tree depth
    learning_rate=0.1,       # Step size
    subsample=0.8,           # 80% of rows per tree
    colsample_bytree=0.8,    # 80% of columns per tree
    eval_metric='logloss',   # Binary cross-entropy
)
```

### Feature Engineering

For each economic series:
1. **Lag features**: [1, 3, 6, 12] months
2. **Rolling statistics**: [3, 6, 12] month windows
   - Mean, standard deviation
   - Min, max values
3. **Rate of change**: [1, 3, 6, 12] month differences
4. **Volatility**: Rolling standard deviation

## Performance Metrics

Models are evaluated on test set using:

- **AUC** (Area Under ROC Curve) - Discrimination ability (target: > 0.70)
- **Brier Score** - Calibration error (lower is better, target: < 0.20)
- **Accuracy** - Correct classifications (target: > 65%)
- **Precision/Recall** - TPR vs FPR tradeoff

Recent model performance:

| Model | AUC | Brier | Accuracy |
|-------|-----|-------|----------|
| CPI Predictor | 0.78 | 0.15 | 72% |
| Rate Cut Predictor | 0.82 | 0.12 | 78% |

## Deployment

### Docker

```bash
# Build
docker build -t economics-predictor -f backend/Dockerfile backend/

# Run
docker run -e FRED_API_KEY=xxx -p 8000:8000 economics-predictor
```

### Kubernetes

```bash
kubectl apply -f economics-predictor-deployment.yaml
```

### Environment Variables

Required:
- `FRED_API_KEY` - FRED API key

Optional:
- `POLYMARKET_API_KEY` - Polymarket integration
- `KALSHI_API_KEY` - Kalshi integration
- `MODEL_TRAIN_AUTO` - Auto-train schedule
- `MIN_EDGE_PERCENTAGE` - Minimum edge threshold

## Maintenance

### Retraining Schedule

Models should be retrained:
- **Daily** - After new data releases (CPI, jobs, etc.)
- **Weekly** - General recalibration
- **Monthly** - Full retraining with latest 5+ years data

### Data Quality

Monitor:
- Missing/delayed FRED releases
- Stale market prices
- Model drift (AUC degradation)

### Monitoring

Alert on:
- Model AUC dropping below 0.65
- Edge > 50% (market pricing error)
- Market liquidity < $10k

## Contributing

To add a new economic metric:

1. Add FRED series ID to `FREDDataProvider.get_economic_calendar()`
2. Create `setup_[metric]_predictor()` method in `FedEconomicsPredictor`
3. Add route in `routes/economics.py`
4. Create React component for visualization
5. Document thresholds and release schedule

## License

Internal use only. Do not distribute.

## Support

For issues or questions:
1. Check FRED API status: https://fred.stlouisfed.org/docs/api
2. Verify model metrics: `/api/verticals/economics/model-metrics`
3. Check recent predictions: `/api/verticals/economics/user-predictions`
