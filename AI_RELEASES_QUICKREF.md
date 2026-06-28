# AI Release Predictor - Quick Reference

## Setup (5 minutes)

```bash
# Backend
cd backend
pip install -r requirements.txt
export GITHUB_TOKEN="ghp_xxxx"
export POLYMARKET_API_KEY="pk_xxxx"
python -m uvicorn main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

## API Endpoints

### Single Prediction
```bash
curl -X POST http://localhost:8000/api/verticals/ai-releases/predict \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "anthropic",
    "model_name": "Claude 4",
    "target_date": "2026-12-31"
  }'
```

**Response**:
```json
{
  "provider": "anthropic",
  "model_name": "Claude 4",
  "predicted_probability": 0.62,
  "polymarket_price": 0.40,
  "edge": 0.22,
  "edge_pct": 55.0,
  "recommendation": "STRONG_BUY",
  "confidence": 0.87
}
```

### Batch Predictions
```bash
curl -X POST http://localhost:8000/api/verticals/ai-releases/batch-predict \
  -H "Content-Type: application/json" \
  -d '{
    "predictions": [
      {"provider": "anthropic", "model_name": "Claude 4", "target_date": "2026-12-31"},
      {"provider": "openai", "model_name": "GPT-5", "target_date": "2027-03-31"}
    ]
  }'
```

### Examples
```bash
curl http://localhost:8000/api/verticals/ai-releases/examples
```

### Leaderboard
```bash
curl "http://localhost:8000/api/verticals/ai-releases/leaderboard?min_edge=0.05"
```

### Health
```bash
curl http://localhost:8000/api/verticals/ai-releases/health
```

## Providers

- `anthropic` - Claude models
- `openai` - GPT models
- `xai` - Grok models

## Python Usage

```python
import asyncio
from datetime import datetime, timedelta
from services.ai_releases_predictor import AIReleasesPredictorEngine, ModelProvider

async def main():
    engine = AIReleasesPredictorEngine()
    
    # Single prediction
    pred = await engine.predict(
        provider=ModelProvider.ANTHROPIC,
        model_name="Claude 4",
        target_date=datetime.utcnow() + timedelta(days=180)
    )
    
    print(f"Prob: {pred.predicted_probability:.1%}")
    print(f"Price: {pred.polymarket_price:.1%}")
    print(f"Edge: {pred.edge:.1%}")
    print(f"Rec: {pred.recommendation}")

asyncio.run(main())
```

## Features (15-dim)

1. `commits_last_7d` - Weekly commits
2. `commits_last_30d` - Monthly commits
3. `releases_last_90d` - Quarterly releases
4. `days_since_last_release` - Time since last
5. `repository_stars` - GitHub stars
6. `contributor_count` - Team size
7. `issue_velocity` - Issues/day
8. `hf_models_last_30d` - HF uploads/month
9. `hf_model_downloads` - Total HF downloads
10. `polymarket_price` - Market price
11. `days_until_target` - Time to target
12. `quarter_progress` - Q progress (0-1)
13. `is_major_event` - Near WWDC/Dev Day
14. `avg_release_gap_days` - Avg gap (historical)
15. `last_release_recency_percentile` - Recency %ile

## Recommendations

| Edge | Signal |
|------|--------|
| > 10% | STRONG_BUY |
| 5-10% | BUY |
| -5 to 5% | HOLD |
| -10 to -5% | SELL |
| < -10% | STRONG_SELL |

## Kelly Sizing

```
Kelly % = Edge / (1 - P(model))
Bet size = Kelly % × Bankroll
```

Example:
- Edge: 20% (0.20)
- Model prob: 60% (0.60)
- Kelly % = 0.20 / 0.40 = 50%
- For $1000: Bet $500

## Files Reference

| File | Purpose | Lines |
|------|---------|-------|
| `services/ai_releases_predictor.py` | Core engine | 640 |
| `routes/ai_releases.py` | FastAPI routes | 280 |
| `schemas/ai_releases.py` | Pydantic schemas | 120 |
| `tests/test_ai_releases.py` | Test suite | 300 |
| `examples_ai_releases.py` | Examples | 400 |
| `pages/AIReleasesPage.tsx` | React UI | 500 |

## Testing

```bash
# Run tests
pytest backend/tests/test_ai_releases.py -v

# Run examples
python backend/examples_ai_releases.py

# Run specific test
pytest backend/tests/test_ai_releases.py::test_prediction_edge_calculation -v
```

## Debugging

```python
# Print features
features = await engine.build_features(provider, model_name, target_date)
print(features)

# Print model confidence
prob, confidence = engine.predictor.predict_probability(features)
print(f"Confidence: {confidence:.1%}")

# Check Polymarket price
markets = await engine.polymarket.search_markets(query)
print(markets[0]['outcomes'])
```

## Common Issues

**Issue**: `GITHUB_TOKEN not found`
```
Fix: export GITHUB_TOKEN="ghp_xxxx"
```

**Issue**: Polymarket API timeout
```
Fix: Increase timeout in PolymarketAPI.__init__()
timeout=30  # Default is 10
```

**Issue**: Port 8000 already in use
```
Fix: python -m uvicorn main:app --port 8001
```

**Issue**: No module named 'xgboost'
```
Fix: pip install xgboost scikit-learn pandas numpy
```

## Performance Tips

1. **Cache predictions**: Predictions are deterministic
2. **Batch requests**: Process multiple at once
3. **Reduce feature calls**: Cache GitHub/HF data
4. **Use SQLite locally**: PostgreSQL for production
5. **Enable compression**: HTTP gzip for responses

## Deployment Checklist

- [ ] Set HTTPS in production
- [ ] Store secrets in env vars
- [ ] Enable rate limiting
- [ ] Set up monitoring/logging
- [ ] Configure CORS properly
- [ ] Add request authentication
- [ ] Enable request signing
- [ ] Set up error tracking (Sentry)
- [ ] Configure backups
- [ ] Test load handling

## Documentation Links

- Full docs: `AI_RELEASES_README.md`
- Deployment: `AI_RELEASES_DEPLOYMENT.md`
- Summary: `AI_RELEASES_SUMMARY.md`
- Examples: `backend/examples_ai_releases.py`

## Key Data

### Historical Releases

**Claude (Anthropic)**
- Claude 3.0 (Opus) - 2024-03-04
- Claude 3.5 (Sonnet) - 2024-05-22
- Claude 3.0 (Haiku) - 2024-06-20

**GPT (OpenAI)**
- GPT-4 - 2023-03-14
- GPT-4 Turbo - 2023-11-06
- GPT-4 Vision - 2024-04-09

**Grok (xAI)**
- Grok-1 - 2023-11-04
- Grok-1.5 (Vision) - 2024-03-17

### Major Tech Events (triggering `is_major_event`)

| Month | Event |
|-------|-------|
| June | WWDC |
| September | Google I/O |
| November | OpenAI Dev Day |
| December | NeurIPS |

## Response Schema

```json
{
  "provider": "string",
  "model_name": "string",
  "prediction_date": "2026-06-28T00:00:00",
  "target_date": "2026-12-31T00:00:00",
  "predicted_probability": 0.0,
  "polymarket_price": 0.0,
  "edge": 0.0,
  "edge_pct": 0.0,
  "recommendation": "STRONG_BUY|BUY|HOLD|SELL|STRONG_SELL",
  "confidence": 0.0,
  "features": {
    "commits_last_7d": 0,
    "commits_last_30d": 0,
    ...
  }
}
```

## Environment Variables

```
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
POLYMARKET_API_KEY=pk_xxxxxxxx
POLYMARKET_BASE_URL=https://gamma-api.polymarket.com
MODEL_CHECKPOINT_PATH=./models/release_predictor.pkl
SCALER_CHECKPOINT_PATH=./models/scaler.pkl
PREDICTION_CACHE_TTL=30
LOG_LEVEL=INFO
```

## Running Examples

```bash
# All examples with formatted output
python backend/examples_ai_releases.py

# Outputs 5 demonstrations:
# 1. Single Prediction - Claude 4 (6-month forecast)
# 2. Batch Predictions - Leaderboard of 3 models
# 3. Feature Analysis - All 15 features explained
# 4. Trading Strategy - Position sizing & signals
# 5. Sensitivity - Same model at 3 time horizons
```

## Quick Test

```bash
# Check server is running
curl http://localhost:8000/health

# Get AI releases health
curl http://localhost:8000/api/verticals/ai-releases/health

# Try prediction
curl -X POST http://localhost:8000/api/verticals/ai-releases/predict \
  -H "Content-Type: application/json" \
  -d '{"provider":"anthropic","model_name":"Claude 4","target_date":"2026-12-31"}' \
  | python -m json.tool
```

## Browser URLs

- **API Docs (interactive)**: http://localhost:8000/docs
- **OpenAPI JSON**: http://localhost:8000/openapi.json
- **Frontend**: http://localhost:3000
- **Health check**: http://localhost:8000/health

## Need Help?

1. Check `AI_RELEASES_README.md` for architecture
2. Review `backend/examples_ai_releases.py` for usage
3. Run `pytest backend/tests/test_ai_releases.py -v` for test examples
4. Check API docs at `/docs` for live playground
5. View deployment guide for production setup
