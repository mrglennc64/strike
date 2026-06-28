# Fed/Economics Predictor - Quick Start Guide

Get the economics predictor running in 5 minutes.

## Prerequisites

- Python 3.9+
- PostgreSQL 12+
- Node.js 16+ (for frontend)
- FRED API Key (free): https://fred.stlouisfed.org/docs/api/api_key.html

## 1. Setup Backend

```bash
# Clone repo and navigate
cd stike/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://user:password@localhost:5432/betting_db
FRED_API_KEY=your_api_key_here
SECRET_KEY=your-secret-key-change-in-production
DEBUG=false
EOF

# Initialize database
alembic upgrade head
```

## 2. Train Models

```bash
# Train CPI and rate cut predictors
python -c "
from services.fed_economics_predictor import FedEconomicsPredictor

predictor = FedEconomicsPredictor(fred_api_key='YOUR_KEY_HERE')
print('Training CPI predictor...')
cpi = predictor.setup_cpi_predictor()
print(f'CPI AUC: {cpi.get(\"auc\", \"N/A\")}')

print('Training rate cut predictor...')
rate = predictor.setup_rate_cut_predictor()
print(f'Rate cut AUC: {rate.get(\"auc\", \"N/A\")}')
"
```

## 3. Start Backend API

```bash
# Start FastAPI server
python -m uvicorn main:app --reload --port 8000

# Test health endpoint
curl http://localhost:8000/health
# Expected: {"status":"ok","app":"Betting Framework API"}
```

## 4. Make Your First Prediction

```bash
# Predict CPI
curl "http://localhost:8000/api/verticals/economics/predict-cpi?threshold=3.5"

# Response:
# {
#   "status": "success",
#   "data": {
#     "metric": "CPI",
#     "threshold": 3.5,
#     "predicted_probability": 0.65,
#     "market_probability": 0.60,
#     "edge": {
#       "edge": 0.05,
#       "edge_pct": 8.33,
#       "kelly_fraction": 0.15,
#       ...
#     }
#   }
# }
```

## 5. Setup Frontend (Optional)

```bash
cd frontend

# Install dependencies
npm install

# Create .env
cat > .env << EOF
VITE_API_URL=http://localhost:8000
EOF

# Start dev server
npm run dev

# Open http://localhost:5173
```

## Common Commands

### Predictions

```bash
# CPI prediction
curl "http://localhost:8000/api/verticals/economics/predict-cpi?threshold=3.5&market_price=0.60"

# Rate cut prediction
curl "http://localhost:8000/api/verticals/economics/predict-rate-cut"

# All edge opportunities
curl "http://localhost:8000/api/verticals/economics/edge-opportunities?min_edge=0.05"

# FOMC schedule
curl "http://localhost:8000/api/verticals/economics/fomc-schedule"

# Economic calendar
curl "http://localhost:8000/api/verticals/economics/calendar"
```

### Model Management

```bash
# Train models
curl -X POST "http://localhost:8000/api/verticals/economics/train-models"

# Get model metrics
curl "http://localhost:8000/api/verticals/economics/model-metrics"

# Get user predictions
curl "http://localhost:8000/api/verticals/economics/user-predictions?user_id=1&limit=10"
```

### Save Predictions

```bash
# Save a prediction
curl -X POST "http://localhost:8000/api/verticals/economics/save-prediction" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "metric": "CPI",
    "threshold": 3.5,
    "prediction_type": "binary",
    "predicted_probability": 0.65,
    "market_probability": 0.60,
    "kelly_fraction": 0.15,
    "expected_value": 0.0833
  }'

# Resolve prediction (when outcome is known)
curl -X POST "http://localhost:8000/api/verticals/economics/resolve-prediction/1" \
  -H "Content-Type: application/json" \
  -d '{"actual_outcome": true}'
```

## Docker (Alternative)

```bash
# Build and run with Docker Compose
docker-compose -f docker-compose.economics.yml up

# Train models in running container
docker-compose -f docker-compose.economics.yml exec economics-api \
  python -m pytest tests/test_economics_predictor.py -v
```

## Verify Installation

```bash
# 1. Check FRED API connection
python -c "
from services.fed_economics_predictor import FREDDataProvider
fred = FREDDataProvider('YOUR_API_KEY')
cpi = fred.fetch_series('CPIAUCSL', '2024-01-01', '2026-06-28')
print(f'Fetched {len(cpi)} CPI records')
"

# 2. Check models can be trained
python -c "
from services.fed_economics_predictor import FedEconomicsPredictor
p = FedEconomicsPredictor('YOUR_API_KEY')
metrics = p.setup_cpi_predictor()
print(f'CPI Model AUC: {metrics.get(\"auc\")}')
"

# 3. Check API endpoints
curl -s http://localhost:8000/health | python -m json.tool
```

## Common Issues

### 1. "FRED_API_KEY not set"
```bash
# Make sure .env file exists and contains:
FRED_API_KEY=your_actual_api_key
```

### 2. "Database connection failed"
```bash
# Check PostgreSQL is running and credentials are correct
psql -U user -d betting_db -h localhost
```

### 3. "No such module pandas_datareader"
```bash
# Reinstall requirements
pip install --upgrade pandas-datareader
```

### 4. Models not trained
```bash
# Train manually
python -c "
from services.fed_economics_predictor import FedEconomicsPredictor
p = FedEconomicsPredictor('YOUR_API_KEY')
p.setup_cpi_predictor()
p.setup_rate_cut_predictor()
"
```

## Next Steps

1. **Real-time Predictions**
   - Connect to Polymarket API for live market prices
   - Set up scheduled retraining (daily/weekly)

2. **Extend Models**
   - Add unemployment predictor
   - Add GDP predictor
   - Add inflation expectations

3. **Integration**
   - Connect to bankroll management
   - Integrate with Kelly criterion for bet sizing
   - Track prediction accuracy over time

4. **Deployment**
   - Deploy backend to cloud (AWS/GCP/Azure)
   - Set up CI/CD pipeline
   - Configure monitoring and alerts

## Documentation

- Full docs: [FED_ECONOMICS_PREDICTOR.md](./FED_ECONOMICS_PREDICTOR.md)
- API reference: `http://localhost:8000/docs` (Swagger UI)
- Architecture: [ARCHITECTURE.md](./ARCHITECTURE.md)

## Support

For issues:
1. Check FRED API status: https://fred.stlouisfed.org
2. Verify API key: https://fred.stlouisfed.org/docs/api/api_key.html
3. Check database connection
4. Review logs: `tail -f logs/economics_predictor.log`

## Example: Full Workflow

```python
from services.fed_economics_predictor import FedEconomicsPredictor

# 1. Initialize
predictor = FedEconomicsPredictor(fred_api_key="YOUR_KEY")

# 2. Train models
cpi_metrics = predictor.setup_cpi_predictor(threshold=3.5)
rate_metrics = predictor.setup_rate_cut_predictor()

# 3. Make predictions
cpi_pred = predictor.predict_cpi(threshold=3.5, market_price=0.60)
rate_pred = predictor.predict_rate_cut(market_price=0.55)

# 4. Check edge
print(f"CPI Edge: {cpi_pred['edge']['edge']:.1%}")
print(f"CPI Kelly: {cpi_pred['edge']['kelly_fraction']:.1%}")
print(f"Rate Cut Edge: {rate_pred['edge']['edge']:.1%}")

# 5. Identify opportunities
if cpi_pred['edge']['edge'] > 0.05:
    print("✓ CPI has positive edge - BET YES")
else:
    print("✗ CPI has negative edge")

# 6. Get calendar
calendar = predictor.get_economic_calendar()
fomc = predictor.get_fomc_calendar()
print(f"Next {len(fomc)} FOMC meetings scheduled")
```

Ready to trade! 🚀
