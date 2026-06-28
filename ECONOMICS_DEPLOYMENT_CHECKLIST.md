# Fed/Economics Predictor - Deployment Checklist

Quick checklist to get the economics predictor live.

## Pre-Deployment (5 min)

- [ ] Clone/pull latest code
- [ ] Review files created:
  - [ ] `backend/services/fed_economics_predictor.py` (core engine)
  - [ ] `backend/routes/economics.py` (FastAPI routes)
  - [ ] `backend/models/economics.py` (database models)
  - [ ] `backend/schemas/economics.py` (request/response schemas)
  - [ ] `frontend/src/components/EconomicsDashboard.tsx` (main UI)
  - [ ] `frontend/src/components/EconomicsTools.tsx` (components)
  - [ ] `backend/requirements.txt` (updated dependencies)
  - [ ] `backend/tests/test_economics_predictor.py` (tests)

## Backend Setup (10 min)

- [ ] **Install dependencies**
  ```bash
  cd backend
  pip install -r requirements.txt
  ```

- [ ] **Get FRED API key** (2 min)
  - Visit: https://fred.stlouisfed.org/docs/api/api_key.html
  - Sign up (free)
  - Copy API key

- [ ] **Configure environment** (2 min)
  ```bash
  # Create/update .env
  echo "FRED_API_KEY=your_api_key_here" >> .env
  ```

- [ ] **Initialize database**
  ```bash
  alembic upgrade head
  ```

- [ ] **Verify installation**
  ```bash
  python -c "from services.fed_economics_predictor import FedEconomicsPredictor; print('✓ Import successful')"
  ```

## Backend Testing (5 min)

- [ ] **Run unit tests**
  ```bash
  pytest tests/test_economics_predictor.py -v
  ```
  Expected: All tests pass or warnings only

- [ ] **Train models** (2-5 min, first time only)
  ```bash
  python -c "
  from services.fed_economics_predictor import FedEconomicsPredictor
  p = FedEconomicsPredictor(fred_api_key='YOUR_KEY')
  cpi = p.setup_cpi_predictor()
  rate = p.setup_rate_cut_predictor()
  print(f'CPI AUC: {cpi.get(\"auc\")}')
  print(f'Rate AUC: {rate.get(\"auc\")}')
  "
  ```
  Expected: AUC > 0.65 for both models

## Backend Launch (2 min)

- [ ] **Start FastAPI server**
  ```bash
  python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
  ```

- [ ] **Test health endpoint**
  ```bash
  curl http://localhost:8000/health
  # Expected: {"status":"ok","app":"..."}
  ```

- [ ] **Test economics endpoint**
  ```bash
  curl "http://localhost:8000/api/verticals/economics/predict-cpi?threshold=3.5"
  # Expected: JSON with prediction data
  ```

## Frontend Setup (5 min)

- [ ] **Install Node dependencies**
  ```bash
  cd frontend
  npm install
  ```

- [ ] **Configure environment**
  ```bash
  echo "VITE_API_URL=http://localhost:8000" > .env
  ```

- [ ] **Start dev server**
  ```bash
  npm run dev
  ```

- [ ] **Verify in browser**
  - Open http://localhost:5173
  - Check if EconomicsDashboard loads
  - Check if data appears

## Integration Testing (5 min)

- [ ] **Test CPI prediction**
  ```bash
  curl "http://localhost:8000/api/verticals/economics/predict-cpi"
  ```
  Check: Has `predicted_probability`, `market_probability`, `edge`

- [ ] **Test rate cut prediction**
  ```bash
  curl "http://localhost:8000/api/verticals/economics/predict-rate-cut"
  ```
  Check: Has probability and next meeting info

- [ ] **Test edge opportunities**
  ```bash
  curl "http://localhost:8000/api/verticals/economics/edge-opportunities"
  ```
  Check: Returns list of opportunities with edge > 0

- [ ] **Test calendar**
  ```bash
  curl "http://localhost:8000/api/verticals/economics/calendar"
  ```
  Check: Returns economic events

- [ ] **Test FOMC schedule**
  ```bash
  curl "http://localhost:8000/api/verticals/economics/fomc-schedule"
  ```
  Check: Returns upcoming meetings

## Database Setup (Optional, for production)

- [ ] **Create migrations** (if needed)
  ```bash
  alembic revision --autogenerate -m "add economics tables"
  ```

- [ ] **Apply migrations**
  ```bash
  alembic upgrade head
  ```

- [ ] **Verify tables created**
  ```bash
  psql $DATABASE_URL -c "\dt"
  # Should see: economics_predictions, economics_model_metrics, etc.
  ```

## Docker Deployment (Optional)

- [ ] **Start services**
  ```bash
  docker-compose -f docker-compose.economics.yml up
  ```

- [ ] **Verify all services running**
  ```bash
  docker-compose -f docker-compose.economics.yml ps
  # All services should have status "running"
  ```

- [ ] **Test via Docker**
  ```bash
  curl http://localhost:8001/health
  ```

## Production Deployment (15 min)

- [ ] **Update environment variables**
  ```bash
  # Set in production:
  export FRED_API_KEY=<production_key>
  export POLYMARKET_API_KEY=<key>
  export KALSHI_API_KEY=<key>
  export DEBUG=false
  ```

- [ ] **Configure secrets**
  - Set SECRET_KEY in production
  - Use environment variables for all credentials
  - DO NOT commit secrets

- [ ] **Setup monitoring**
  - Configure logging to file: `/var/log/economics_predictor.log`
  - Setup alerts for:
    - Model AUC drop below 0.65
    - API response time > 5s
    - Market price fetch failures

- [ ] **Setup scheduled tasks**
  - Daily model retraining at 2 AM
  - Hourly edge opportunity scan
  - 6-hourly calendar refresh

- [ ] **Deploy to cloud**
  ```bash
  # AWS ECS
  aws ecs update-service --cluster betting --service economics-api --force-new-deployment
  
  # Or Kubernetes
  kubectl apply -f economics-predictor-deployment.yaml
  kubectl rollout status deployment/economics-api
  ```

- [ ] **Verify production endpoints**
  ```bash
  curl https://api.example.com/api/verticals/economics/predict-cpi
  ```

## Post-Deployment (5 min)

- [ ] **Monitor logs**
  ```bash
  tail -f /var/log/economics_predictor.log
  ```

- [ ] **Check model metrics**
  ```bash
  curl http://localhost:8000/api/verticals/economics/model-metrics
  ```

- [ ] **Save predictions (optional)**
  ```bash
  curl -X POST http://localhost:8000/api/verticals/economics/save-prediction \
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
  ```

- [ ] **Setup cron jobs** (optional)
  ```bash
  # Add to crontab
  0 2 * * * curl -X POST http://localhost:8000/api/verticals/economics/train-models
  0 * * * * curl http://localhost:8000/api/verticals/economics/edge-opportunities
  ```

## Verification Checklist

### Data Loading
- [ ] FRED API returns data
- [ ] Feature engineering completes
- [ ] Models train successfully
- [ ] Predictions generate

### API Endpoints
- [ ] `/predict-cpi` returns probability + edge
- [ ] `/predict-rate-cut` returns rate cut probability
- [ ] `/calendar` returns economic releases
- [ ] `/fomc-schedule` returns meetings
- [ ] `/edge-opportunities` returns edges > min_edge
- [ ] `/train-models` trains and returns metrics
- [ ] `/save-prediction` saves and returns ID
- [ ] `/user-predictions` retrieves history

### Frontend
- [ ] Dashboard loads without errors
- [ ] Shows CPI and rate cut predictions
- [ ] Shows edge opportunities
- [ ] Shows FOMC schedule
- [ ] Auto-refresh works

### Database
- [ ] Tables created
- [ ] Predictions save correctly
- [ ] Model metrics track
- [ ] Query performance acceptable

### Performance
- [ ] Predictions < 2 seconds
- [ ] Feature engineering < 5 seconds
- [ ] Model training < 30 seconds (incremental)
- [ ] Dashboard loads < 3 seconds

## Troubleshooting

### "FRED_API_KEY not set"
```bash
echo $FRED_API_KEY
# If empty, set it:
export FRED_API_KEY=your_key
```

### "Database connection failed"
```bash
# Check PostgreSQL
psql -U user -d betting_db -h localhost

# Verify URL
echo $DATABASE_URL
```

### "No module named pandas_datareader"
```bash
pip install --upgrade pandas-datareader
```

### "Models not found"
```bash
# Train models first:
curl -X POST http://localhost:8000/api/verticals/economics/train-models
```

### "Market prices not fetching"
- Polymarket/Kalshi integration is optional
- Predictions work with default market price (0.5)
- Add API keys later if needed

## Rollback Plan

If issues occur:

1. **Stop services**
   ```bash
   docker-compose down
   # or
   systemctl stop economics-api
   ```

2. **Revert database** (if data corrupted)
   ```bash
   alembic downgrade -1
   ```

3. **Restore from backup**
   ```bash
   pg_restore -d betting_db backup.sql
   ```

4. **Check logs**
   ```bash
   tail -100 /var/log/economics_predictor.log
   ```

## Success Criteria

✓ All checks passed when:
- [ ] Backend API runs without errors
- [ ] Frontend dashboard displays predictions
- [ ] Models trained with AUC > 0.65
- [ ] Edge opportunities identified
- [ ] Database records saved
- [ ] Deployments automated

## Timeline

- **Backend setup**: 10 min
- **Testing**: 10 min
- **Frontend setup**: 5 min
- **Integration testing**: 10 min
- **Production deployment**: 15 min
- **Verification**: 5 min

**Total: ~55 minutes to full deployment**

---

## Quick Commands Reference

```bash
# Install
pip install -r backend/requirements.txt
npm install --prefix frontend

# Train models
curl -X POST http://localhost:8000/api/verticals/economics/train-models

# Get predictions
curl "http://localhost:8000/api/verticals/economics/predict-cpi"
curl "http://localhost:8000/api/verticals/economics/edge-opportunities"

# Start servers
python -m uvicorn backend.main:app --reload &
npm run dev --prefix frontend &

# Run tests
pytest backend/tests/test_economics_predictor.py -v

# View docs
open http://localhost:8000/docs
```

Ready to deploy! 🚀
