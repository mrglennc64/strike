# AI Release Predictor - Deployment Guide

## Quick Start

### 1. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
cp .env.ai-releases .env.local  # Optional: AI releases-specific config

# Set required tokens
export GITHUB_TOKEN="ghp_..."
export POLYMARKET_API_KEY="pk_..."
```

### 2. Database Setup

```bash
# Initialize database (if using PostgreSQL)
alembic upgrade head

# Or use SQLite for development
sqlite3 data.db < schema.sql
```

### 3. Run API Server

```bash
# Development
python -m uvicorn main:app --reload --port 8000

# Production
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

### 4. Frontend Setup

```bash
cd frontend

npm install
npm run dev  # Development
npm run build  # Production
```

## Docker Deployment

### Backend Container

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build & Run

```bash
# Build
docker build -t stike-backend-ai-releases ./backend

# Run
docker run -p 8000:8000 \
  -e GITHUB_TOKEN=$GITHUB_TOKEN \
  -e POLYMARKET_API_KEY=$POLYMARKET_API_KEY \
  stike-backend-ai-releases
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - POLYMARKET_API_KEY=${POLYMARKET_API_KEY}
      - DATABASE_URL=postgresql://user:pass@db:5432/stike
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=stike
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=stike
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

```bash
docker-compose up
```

## Cloud Deployment

### AWS Lambda (FastAPI)

```python
# handler.py
from mangum import Mangum
from main import app

handler = Mangum(app)
```

```bash
# Deploy
sam build
sam deploy
```

### Google Cloud Run

```bash
# Build container
gcloud builds submit --tag gcr.io/PROJECT/ai-releases-backend

# Deploy
gcloud run deploy ai-releases-backend \
  --image gcr.io/PROJECT/ai-releases-backend \
  --set-env-vars GITHUB_TOKEN=$GITHUB_TOKEN \
  --set-env-vars POLYMARKET_API_KEY=$POLYMARKET_API_KEY
```

### Heroku

```bash
# Create app
heroku create ai-releases-backend

# Set environment variables
heroku config:set GITHUB_TOKEN=$GITHUB_TOKEN
heroku config:set POLYMARKET_API_KEY=$POLYMARKET_API_KEY

# Deploy
git push heroku main
```

## Testing Deployment

### Health Check
```bash
curl http://localhost:8000/api/verticals/ai-releases/health
```

Expected response:
```json
{
  "status": "ok",
  "service": "ai-releases-predictor",
  "models": ["anthropic", "openai", "xai"]
}
```

### Example Prediction
```bash
curl -X POST http://localhost:8000/api/verticals/ai-releases/predict \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "anthropic",
    "model_name": "Claude 4",
    "target_date": "2026-12-31"
  }'
```

### Load Testing
```bash
# Install artillery
npm install -g artillery

# Create load test
cat > load-test.yml << EOF
config:
  target: "http://localhost:8000"
  phases:
    - duration: 60
      arrivalRate: 10
scenarios:
  - name: "AI Releases Predictions"
    flow:
      - post:
          url: "/api/verticals/ai-releases/predict"
          json:
            provider: "anthropic"
            model_name: "Claude 4"
            target_date: "2026-12-31"
EOF

# Run test
artillery run load-test.yml
```

## Monitoring & Logging

### Application Logging

```python
# In main.py
import logging
from pythonjsonlogger import jsonlogger

logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)
```

### Metrics Collection

```python
# prometheus_middleware.py
from prometheus_client import Counter, Histogram, generate_latest
import time

prediction_counter = Counter(
    'ai_releases_predictions_total',
    'Total predictions generated'
)

prediction_duration = Histogram(
    'ai_releases_prediction_duration_seconds',
    'Time to generate prediction'
)

@app.middleware("http")
async def track_metrics(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    
    if "/predict" in request.url.path:
        prediction_counter.inc()
        prediction_duration.observe(duration)
    
    return response

@app.get("/metrics")
async def metrics():
    return generate_latest()
```

### Error Tracking (Sentry)

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="https://...@sentry.io/...",
    integrations=[FastApiIntegration()],
)
```

## Performance Tuning

### Caching Layer

```python
# routes/ai_releases.py
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
async def cached_predict(provider_str, model_name, target_date_str):
    # Prediction logic
    pass
```

### Database Indexing

```sql
CREATE INDEX idx_predictions_provider ON predictions(provider);
CREATE INDEX idx_predictions_model ON predictions(model_name);
CREATE INDEX idx_predictions_target_date ON predictions(target_date);
CREATE INDEX idx_predictions_created ON predictions(created_at DESC);
```

### Connection Pooling

```python
# config.py
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
)
```

## Scaling Strategy

### Horizontal Scaling

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-releases-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-releases-backend
  template:
    metadata:
      labels:
        app: ai-releases-backend
    spec:
      containers:
      - name: backend
        image: stike/ai-releases-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: GITHUB_TOKEN
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: github-token
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
```

### Load Balancer Setup

```yaml
apiVersion: v1
kind: Service
metadata:
  name: ai-releases-backend-lb
spec:
  type: LoadBalancer
  selector:
    app: ai-releases-backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
```

## API Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@router.post("/predict")
@limiter.limit("100/minute")
async def predict(request: ReleasePredictionRequest):
    # Prediction logic
    pass
```

## Security Checklist

- [ ] Set `HTTPS` in production
- [ ] Use environment variables for secrets
- [ ] Implement request signing for Polymarket API calls
- [ ] Add rate limiting per IP/user
- [ ] Enable CORS only for trusted origins
- [ ] Use JWT authentication for protected endpoints
- [ ] Rotate API keys regularly
- [ ] Enable request logging for audit trail
- [ ] Add input validation on all endpoints
- [ ] Use parameterized queries to prevent SQL injection

## Backup & Recovery

### Database Backup

```bash
# PostgreSQL
pg_dump stike > backup_$(date +%Y%m%d).sql

# Automated backup (cron)
0 2 * * * pg_dump stike | gzip > /backups/stike_$(date +\%Y\%m\%d).sql.gz
```

### Model Checkpoint Backup

```bash
# Backup trained model
cp models/release_predictor.pkl backups/release_predictor_$(date +%Y%m%d).pkl
```

## Troubleshooting

### Common Issues

**Issue**: GitHub API rate limit
```
Solution: Use GitHub token, check rate limits:
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/rate_limit
```

**Issue**: Polymarket API timeout
```
Solution: Increase timeout, implement retry logic:
timeout=30
max_retries=3
```

**Issue**: High memory usage
```
Solution: Reduce model cache size, implement pagination:
lru_cache(maxsize=100)  # Reduce from 1000
```

## Monitoring Dashboard

### Key Metrics to Track

1. **Prediction Latency** (p50, p95, p99)
2. **API Error Rate** (%)
3. **GitHub API Calls/Day**
4. **Polymarket API Calls/Day**
5. **Cache Hit Rate** (%)
6. **Database Query Time** (ms)
7. **Active Predictions** (batch size)

### Grafana Dashboard Template

```json
{
  "dashboard": {
    "title": "AI Release Predictor",
    "panels": [
      {
        "title": "Predictions/Hour",
        "targets": [
          {"expr": "rate(ai_releases_predictions_total[1h])"}
        ]
      },
      {
        "title": "Avg Prediction Duration",
        "targets": [
          {"expr": "histogram_quantile(0.5, ai_releases_prediction_duration_seconds)"}
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {"expr": "rate(ai_releases_errors_total[5m])"}
        ]
      }
    ]
  }
}
```

## Maintenance

### Weekly Tasks
- Review error logs
- Check API quota usage
- Validate predictions against actual releases

### Monthly Tasks
- Retrain XGBoost model with new data
- Update historical release data
- Review and optimize slow queries

### Quarterly Tasks
- Major version updates
- Security audit
- Capacity planning review

## Support & Documentation

- **API Docs**: http://localhost:8000/docs
- **Code Examples**: `backend/examples_ai_releases.py`
- **Tests**: `backend/tests/test_ai_releases.py`
- **README**: `AI_RELEASES_README.md`
