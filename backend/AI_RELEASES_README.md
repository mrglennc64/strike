# AI Release Predictor

A comprehensive system for predicting when major AI models (Claude, GPT, xAI) will be released and calculating the trading edge on Polymarket prediction markets.

## Features

### 1. Multi-Source Data Integration
- **GitHub Activity**: Commit frequency, release patterns, repository stars, contributors
- **HuggingFace**: Model upload activity and downloads as signals
- **Polymarket API**: Real-time market prices for release predictions
- **Historical Cadence**: Analysis of past release gaps and patterns
- **News Sentiment**: Temporal proximity to major tech events (WWDC, OpenAI Dev Day, etc.)

### 2. XGBoost Classification Model
- 15-feature prediction model trained on historical release data
- Outputs: P(Release by target_date)
- Confidence scores for each prediction
- Handles temporal, activity, and market features

### 3. Edge Calculation
- Compares model probability to Polymarket price
- Calculates expected value and Kelly-criterion sizing
- Provides trading recommendations (STRONG_BUY/BUY/HOLD/SELL/STRONG_SELL)

### 4. Multi-Provider Support
- **Anthropic** (Claude series)
- **OpenAI** (GPT series)
- **xAI** (Grok series)

## Architecture

### Core Components

#### 1. `GitHubScraper`
Fetches repository activity from GitHub API:
```python
scraper = GitHubScraper(github_token="your_token")
activity = await scraper.fetch_repository_activity(owner, repo, days=90)
```

**Features extracted:**
- Commits in last 7/30 days
- Releases in last 90 days
- Days since last release
- Repository stars & contributors

#### 2. `PolymarketAPI`
Queries Polymarket's prediction markets:
```python
api = PolymarketAPI()
price = await api.fetch_market_price(query, provider, model_name)
markets = await api.search_markets(query)
```

**Returns:**
- YES/NO prices (0-1 scale)
- Market volume and liquidity
- Historical price movements

#### 3. `HuggingFaceScraper`
Monitors model uploads:
```python
scraper = HuggingFaceScraper()
recent_models, downloads = await scraper.fetch_model_uploads(author, days=30)
```

#### 4. `ReleasePredictor`
XGBoost classifier for probability prediction:
```python
predictor = ReleasePredictor(model_path="models/release_predictor.pkl")
prob, confidence = predictor.predict_probability(features)
```

#### 5. `AIReleasesPredictorEngine`
Main orchestration class:
```python
engine = AIReleasesPredictorEngine()

# Single prediction
prediction = await engine.predict(
    provider=ModelProvider.ANTHROPIC,
    model_name="Claude 4",
    target_date=datetime(2026, 12, 31)
)

# Batch predictions
predictions = await engine.predict_batch([
    {"provider": "anthropic", "model_name": "Claude 4", "target_date": "2026-12-31"},
    {"provider": "openai", "model_name": "GPT-5", "target_date": "2027-03-31"},
])
```

## Features (15-dimensional)

### GitHub Metrics (7)
1. `commits_last_7d` - Weekly commit velocity
2. `commits_last_30d` - Monthly commit activity
3. `releases_last_90d` - Quarterly release frequency
4. `days_since_last_release` - Time since last major release
5. `repository_stars` - Repository popularity
6. `contributor_count` - Team size indicator
7. `issue_velocity` - Daily issue resolution rate

### HuggingFace (2)
8. `hf_models_last_30d` - Recent model uploads
9. `hf_model_downloads` - Model adoption/interest

### Market Data (1)
10. `polymarket_price` - Current YES probability

### Temporal (3)
11. `days_until_target` - Time to prediction date
12. `quarter_progress` - Position in current quarter (0-1)
13. `is_major_event` - Within 30 days of WWDC/Dev Day/NeurIPS

### Historical (2)
14. `avg_release_gap_days` - Mean time between releases
15. `last_release_recency_percentile` - How recent was last release

## API Endpoints

### 1. Single Prediction
```
POST /api/verticals/ai-releases/predict

Request:
{
  "provider": "anthropic",
  "model_name": "Claude 4",
  "target_date": "2026-12-31"
}

Response:
{
  "provider": "anthropic",
  "model_name": "Claude 4",
  "prediction_date": "2026-06-28T00:00:00",
  "target_date": "2026-12-31T00:00:00",
  "predicted_probability": 0.62,
  "polymarket_price": 0.40,
  "edge": 0.22,
  "edge_pct": 55.00,
  "recommendation": "STRONG_BUY",
  "confidence": 0.87,
  "features": { ... }
}
```

### 2. Batch Predictions
```
POST /api/verticals/ai-releases/batch-predict

Request:
{
  "predictions": [
    { "provider": "anthropic", "model_name": "Claude 4", "target_date": "2026-12-31" },
    { "provider": "openai", "model_name": "GPT-5", "target_date": "2027-03-31" }
  ]
}

Response:
{
  "predictions": [ ... ],
  "generated_at": "2026-06-28T00:00:00",
  "total_edge_usd": 45.32
}
```

### 3. Market Data
```
GET /api/verticals/ai-releases/markets?provider=anthropic&model_name=Claude%204&query=release%20before%20Dec%202026

Response:
{
  "provider": "anthropic",
  "model_name": "Claude 4",
  "markets": [ ... ],
  "top_market": { ... },
  "current_price": 0.40
}
```

### 4. Examples
```
GET /api/verticals/ai-releases/examples

Returns example predictions for quick testing.
```

### 5. Leaderboard
```
GET /api/verticals/ai-releases/leaderboard?min_edge=0.05

Returns predictions sorted by edge, filtered by minimum edge.
```

### 6. Health Check
```
GET /api/verticals/ai-releases/health

Response:
{
  "status": "ok",
  "service": "ai-releases-predictor",
  "models": ["anthropic", "openai", "xai"]
}
```

## Usage Examples

### Python (Async)

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
    
    print(f"Probability: {pred.predicted_probability:.1%}")
    print(f"Market price: {pred.polymarket_price:.1%}")
    print(f"Edge: {pred.edge:.1%}")
    print(f"Recommendation: {pred.recommendation}")

asyncio.run(main())
```

### FastAPI Client

```python
import httpx
from datetime import datetime, timedelta

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/verticals/ai-releases/predict",
        json={
            "provider": "openai",
            "model_name": "GPT-5",
            "target_date": (datetime.utcnow() + timedelta(days=240)).isoformat()
        }
    )
    
    prediction = response.json()
    print(f"Edge: {prediction['edge']:.1%}")
```

### React Component

```tsx
import AIReleasesPage from './pages/AIReleasesPage';

function App() {
  return <AIReleasesPage />;
}
```

The React component provides:
- Single prediction form
- Batch prediction results
- Leaderboard visualization
- Detailed prediction inspection
- Real-time edge calculations

## Historical Release Data

### Anthropic (Claude)
- Claude 3 (Opus) - March 4, 2024
- Claude 3.5 (Sonnet) - May 22, 2024
- Claude 3 (Haiku) - June 20, 2024

### OpenAI (GPT)
- GPT-4 - March 14, 2023
- GPT-4 Turbo - November 6, 2023
- GPT-4 Vision - April 9, 2024

### xAI (Grok)
- Grok-1 - November 4, 2023
- Grok-1.5 (Vision) - March 17, 2024

## Trading Strategy

### Edge Definition
```
Edge = P(model prediction) - P(market price)
```

### Position Sizing (Kelly Criterion)
```
Kelly fraction = Edge / (1 - P(model))
Bet size = Kelly fraction × Bankroll
```

### Thresholds
- **STRONG_BUY**: Edge > 10%
- **BUY**: Edge > 5%
- **HOLD**: -5% < Edge < 5%
- **SELL**: Edge < -5%
- **STRONG_SELL**: Edge < -10%

## Model Training

The XGBoost model is trained on:
- 15 historical release events
- Synthetic data augmentation
- Cross-validation on held-out test set

### Feature Importance (by SHAP)
1. Days until target (temporal priority)
2. Polymarket price (market consensus)
3. Commits last 30d (development activity)
4. Days since last release (cadence)
5. Major event flag (event-driven)

## Installation & Setup

### Backend Setup
```bash
cd backend
pip install -r requirements.txt

# Set environment variables
export GITHUB_TOKEN="your_github_token"
export POLYMARKET_API_KEY="your_polymarket_key"

# Run API
python -m uvicorn main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Configuration
Update `.env` with:
```
GITHUB_TOKEN=your_token
POLYMARKET_API_KEY=your_key
DEBUG=true
```

## Dependencies

```
fastapi==0.104.1
httpx==0.25.2
xgboost==2.0.0
scikit-learn==1.3.2
pandas==2.1.3
numpy==1.24.3
pydantic==2.5.0
```

## Testing

```bash
# Run all tests
pytest backend/tests/test_ai_releases.py -v

# Run examples
python backend/examples_ai_releases.py

# Run specific test
pytest backend/tests/test_ai_releases.py::test_prediction_edge_calculation -v
```

## Performance

- Single prediction: ~500ms (includes API calls)
- Batch prediction (10 models): ~2.5s
- Leaderboard generation: ~50ms
- Memory footprint: ~150MB

## Limitations & Future Work

### Current Limitations
- Polymarket API occasionally has rate limits
- Historical data limited to ~2 years per provider
- Market prices sometimes unavailable for niche models
- Sentiment analysis not yet integrated

### Future Enhancements
1. **News Sentiment**: NLP analysis of tech news
2. **Leak Detection**: Social media signals
3. **Keynote Predictions**: Conference-specific probabilities
4. **Model Ensembling**: Combine with other predictive signals
5. **Real-time Updates**: Websocket integration for market prices

## Contributing

To add support for new providers:

1. Add to `ModelProvider` enum
2. Add GitHub repo config to `REPO_CONFIGS`
3. Add historical releases to `HISTORICAL_RELEASES`
4. Add tests in `test_ai_releases.py`

## License

Proprietary - for internal betting framework use only.
