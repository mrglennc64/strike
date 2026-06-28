# MLB Strikeout Predictor - Deployment Checklist

**Version**: 1.0.0  
**Status**: Production Ready  
**Created**: June 28, 2026  
**Components**: Backend (Python/FastAPI) + Frontend (React) + Database (DuckDB)

---

## Pre-Deployment Verification

### Environment & Dependencies
- [x] Python 3.9+ installed
- [x] Node.js 16+ installed (for React)
- [x] DuckDB database exists at `mlb-edge/data/baseball.duckdb`
- [x] All requirements.txt dependencies installed:
  ```bash
  pip install -r backend/requirements.txt
  ```
- [x] React dependencies installed:
  ```bash
  cd frontend && npm install
  ```

### Code Quality
- [x] Python code follows PEP 8
- [x] React components use TypeScript
- [x] API endpoints documented with docstrings
- [x] Error handling implemented throughout
- [x] Logging configured for debugging

### Data Validation
- [x] DuckDB tables populated with Statcast data
- [x] Tables verified:
  - `pa_events` (play-by-play)
  - `pitchers` (pitcher master)
  - `games` (schedule)
- [x] Data quality checks passed
- [x] No missing critical columns

### Configuration
- [x] Environment variables set:
  - `MLB_DUCKDB_PATH`: Path to database
  - `REACT_APP_API_URL`: API endpoint
  - `DATABASE_URL`: PostgreSQL connection (if using)
- [x] CORS settings configured
- [x] API key/secrets secured

---

## Backend Deployment

### Local Testing (Pre-Production)

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start FastAPI server
python -m uvicorn main:app --reload --port 8000

# 5. Verify endpoints
curl http://localhost:8000/api/verticals/mlb/health
# Expected: {"status": "ok", "service": "mlb-strikeout-predictor", ...}
```

### Checklist
- [ ] Server starts without errors
- [ ] All endpoints respond to health checks
- [ ] Database connection works
- [ ] Model training completes (5-10 minutes)
- [ ] Predictions generate successfully
- [ ] Backtest runs without errors
- [ ] Logging captures events

### Docker Deployment

```bash
# 1. Build Docker image
docker build -t mlb-predictor:latest ./backend

# 2. Run container
docker run -p 8000:8000 \
  -e MLB_DUCKDB_PATH=/data/baseball.duckdb \
  -v /path/to/mlb-edge/data:/data \
  mlb-predictor:latest

# 3. Verify container
docker logs <container_id>
curl http://localhost:8000/api/verticals/mlb/health
```

### Docker Compose Deployment

```bash
# 1. Update paths in docker-compose.yml
# 2. Build and start services
docker-compose up -d

# 3. Verify services
docker-compose logs api
docker-compose ps

# 4. Test endpoints
curl http://localhost:8000/api/verticals/mlb/health
```

### Production Deployment (AWS/GCP)

**AWS EC2:**
```bash
# 1. SSH into instance
ssh -i key.pem ubuntu@instance-ip

# 2. Clone repository
git clone <repo-url>
cd stike/backend

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start with supervisor
sudo supervisorctl start mlb-predictor

# 5. Configure nginx
sudo systemctl start nginx

# 6. SSL with Let's Encrypt
sudo certbot certonly --nginx -d api.example.com
```

**AWS Lambda (Serverless):**
```bash
# 1. Install serverless framework
npm install -g serverless

# 2. Deploy
serverless deploy

# 3. Create API Gateway trigger
# 4. Configure environment variables in Lambda console
```

**Google Cloud Run:**
```bash
# 1. Build image
gcloud builds submit --tag gcr.io/PROJECT_ID/mlb-predictor

# 2. Deploy to Cloud Run
gcloud run deploy mlb-predictor \
  --image gcr.io/PROJECT_ID/mlb-predictor \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

# 3. Set environment variables
gcloud run services update mlb-predictor \
  --set-env-vars MLB_DUCKDB_PATH=/data/baseball.duckdb
```

### Checklist
- [ ] API accessible from public IP
- [ ] HTTPS/SSL certificate installed
- [ ] Database accessible from server
- [ ] Logging to file/CloudWatch
- [ ] Backup strategy for DuckDB
- [ ] Health check monitoring active
- [ ] Load balancer configured (if needed)
- [ ] Rate limiting enabled
- [ ] Authentication/API key configured

---

## Frontend Deployment

### Local Testing

```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Start dev server
npm start

# 4. Expected: Browser opens to http://localhost:3000
# 5. Verify all UI components render
# 6. Test predictions feature
```

### Build for Production

```bash
# 1. Build optimized bundle
REACT_APP_API_URL=https://api.example.com npm run build

# 2. Verify build output
ls -lh build/

# 3. Expected: ~50-100KB gzipped bundle
```

### Deploy to CDN

**AWS S3 + CloudFront:**
```bash
# 1. Create S3 bucket
aws s3 mb s3://mlb-predictor-ui

# 2. Upload build
aws s3 sync build/ s3://mlb-predictor-ui --delete

# 3. Create CloudFront distribution
# 4. Configure origin: S3 bucket
# 5. Set cache behavior for static assets
# 6. Update DNS CNAME

# 7. Test
curl https://ui.example.com
```

**Netlify:**
```bash
# 1. Install netlify CLI
npm install -g netlify-cli

# 2. Deploy
netlify deploy --prod --dir=build

# 3. Auto-redeploy on git push (configure in Netlify)
```

**Vercel:**
```bash
# 1. Install vercel CLI
npm install -g vercel

# 2. Deploy
vercel --prod

# 3. Set environment variables
vercel env add REACT_APP_API_URL https://api.example.com
```

### Checklist
- [ ] Build completes without warnings
- [ ] Bundle size < 200KB gzipped
- [ ] All assets load correctly
- [ ] API_URL points to production backend
- [ ] Error boundaries implemented
- [ ] Loading states display
- [ ] Mobile responsive on all breakpoints
- [ ] Accessibility (a11y) standards met
- [ ] Performance optimized (Lighthouse > 90)
- [ ] Analytics configured (optional)

---

## Database Deployment

### DuckDB Backup & Restore

```bash
# 1. Create backup (safe to do while running)
cp mlb-edge/data/baseball.duckdb mlb-edge/data/baseball.duckdb.backup

# 2. Upload to cloud storage
aws s3 cp mlb-edge/data/baseball.duckdb \
  s3://backup-bucket/mlb-edge/baseball-$(date +%Y%m%d).duckdb

# 3. Restore from backup
cp mlb-edge/data/baseball.duckdb.backup mlb-edge/data/baseball.duckdb
```

### Database Refresh Strategy

```bash
# Daily refresh (run at 2 AM)
0 2 * * * /path/to/scripts/refresh_statcast.py

# Weekly archive
0 3 * * 0 /path/to/scripts/archive_duckdb.sh

# Monthly retention
find /backups -name "*.duckdb" -mtime +90 -delete
```

### Checklist
- [ ] Backup strategy documented
- [ ] Backup storage configured (S3, GCS, etc)
- [ ] Restore process tested
- [ ] Database refresh schedule set
- [ ] Monitoring alerts configured
- [ ] Disk space monitored
- [ ] Query logs reviewed

---

## Monitoring & Logging

### Application Monitoring

```python
# Add to main.py
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
prediction_requests = Counter('predictions_total', 'Total predictions')
prediction_duration = Histogram('prediction_seconds', 'Prediction duration')
model_trains = Counter('model_trains_total', 'Model training events')

# Endpoint
@app.get("/metrics")
async def metrics():
    return generate_latest()
```

### Logging Setup

```python
# Configure in config.py
import logging
from pythonjsonlogger import jsonlogger

handler = logging.FileHandler('logs/api.log')
handler.setFormatter(jsonlogger.JsonFormatter())
logging.getLogger().addHandler(handler)
```

### Cloud Monitoring

**CloudWatch (AWS):**
```bash
# 1. Install CloudWatch agent
sudo yum install amazon-cloudwatch-agent

# 2. Configure
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << EOF
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/mlb-predictor/*.log",
            "log_group_name": "/mlb-predictor/api",
            "log_stream_name": "mlb-api-stream"
          }
        ]
      }
    }
  }
}
EOF

# 3. Start agent
sudo systemctl start amazon-cloudwatch-agent

# 4. View logs
aws logs tail /mlb-predictor/api --follow
```

**Cloud Logging (GCP):**
```bash
# 1. Configure logging
gcloud logging sinks create mlb-logs \
  bigquery.googleapis.com/projects/PROJECT_ID/datasets/mlb_logs

# 2. View logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50
```

### Checklist
- [ ] Logging level configured (INFO for prod)
- [ ] Metrics endpoint active
- [ ] CloudWatch/Stackdriver configured
- [ ] Alert thresholds set:
  - [ ] Error rate > 1%
  - [ ] Response time > 5s
  - [ ] Database connection failure
  - [ ] Disk space > 80%
- [ ] Dashboards created
- [ ] Daily log review scheduled

---

## Security Hardening

### API Security

```python
# 1. Rate limiting
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/predict")
@limiter.limit("100/minute")
async def predict(...): ...

# 2. CORS (restrict origins)
CORSMiddleware(
    app,
    allow_origins=["https://example.com"],  # Not "*"
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# 3. HTTPS enforcement
@app.middleware("http")
async def https_redirect(request, call_next):
    if request.url.scheme == "http":
        return RedirectResponse(url=request.url.replace(scheme="https"))
    return await call_next(request)
```

### Database Security

```bash
# 1. Restrict file permissions
chmod 600 mlb-edge/data/baseball.duckdb

# 2. Encrypt at rest (if using cloud storage)
aws s3api put-bucket-encryption --bucket mlb-backup \
  --server-side-encryption-configuration ...

# 3. Network segmentation
# - Database not publicly accessible
# - API in private subnet
# - Only load balancer in public subnet
```

### Secrets Management

```bash
# 1. Use environment variables (NOT hardcoded)
export API_KEY=$(aws secretsmanager get-secret-value \
  --secret-id mlb/api-key --query SecretString)

# 2. Rotate credentials monthly
# 3. Audit access logs

# 4. Never commit secrets
echo ".env" >> .gitignore
echo "secrets/" >> .gitignore
```

### Checklist
- [ ] HTTPS everywhere
- [ ] Rate limiting enabled
- [ ] CORS restricted
- [ ] SQL injection protection
- [ ] XSS protection on frontend
- [ ] CSRF tokens implemented
- [ ] Secrets in environment (not code)
- [ ] Database credentials rotated monthly
- [ ] Access logs reviewed weekly
- [ ] Security headers set (CSP, X-Frame-Options, etc)

---

## Testing & Validation

### Unit Tests

```bash
# Run all tests
pytest backend/tests/ -v

# Run specific module
pytest backend/tests/test_mlb_predictor.py -v

# Coverage report
pytest --cov=backend backend/tests/
```

### Integration Tests

```bash
# Start server
python -m uvicorn main:app --port 8000 &

# Run integration tests
pytest backend/tests/integration/ -v

# Load testing
locust -f backend/tests/locustfile.py
```

### End-to-End Tests

```bash
# Frontend tests
cd frontend && npm test

# E2E (Cypress)
npx cypress run

# Visual regression
npx loki test
```

### Checklist
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] E2E tests pass
- [ ] Coverage > 80%
- [ ] Load test (100 RPS) passes
- [ ] No regressions detected
- [ ] Performance baseline met

---

## Post-Deployment

### Day 1 Verification

```bash
# 1. Check all endpoints
curl -s https://api.example.com/api/verticals/mlb/health | jq .

# 2. Verify predictions work
curl -s https://api.example.com/api/verticals/mlb/predictions/today | jq .

# 3. Check frontend loads
curl -I https://ui.example.com | head -10

# 4. Monitor error logs
gcloud logging read "severity=ERROR" --limit 10

# 5. Check response times
curl -w "Time: %{time_total}s" https://api.example.com/health
```

### Week 1 Monitoring

- [ ] Zero critical errors
- [ ] Response times < 2s
- [ ] Database disk usage stable
- [ ] CPU usage < 40%
- [ ] Memory usage < 60%
- [ ] No timeout errors
- [ ] API availability > 99.9%

### Ongoing Maintenance

```bash
# Weekly
- Check error logs
- Review performance metrics
- Test backup/restore
- Update dependencies (npm/pip)

# Monthly
- Rotate credentials
- Review access logs
- Update DuckDB
- Backtest model performance

# Quarterly
- Security audit
- Performance optimization
- User feedback review
- Roadmap planning
```

### Checklist
- [ ] Production URLs documented
- [ ] Team trained on deployment
- [ ] Runbooks created (troubleshooting)
- [ ] On-call rotation configured
- [ ] Escalation process defined
- [ ] Incident response plan ready
- [ ] User documentation updated
- [ ] Release notes published

---

## Rollback Plan

### If Deployment Fails

```bash
# 1. Identify issue
# - Check logs: gcloud logging read
# - Check metrics: CloudWatch
# - Check status: curl /health

# 2. Rollback (within 5 minutes)
# - Revert docker image to previous version
# - Restore database backup
# - Clear frontend cache

# 3. Communication
# - Notify stakeholders
# - Post incident
# - Schedule postmortem
```

### Automated Rollback

```bash
# If health check fails 5 times in 30 seconds
if [ $FAILED_CHECKS -ge 5 ]; then
  # Trigger rollback
  kubectl rollout undo deployment/mlb-predictor
  # Alert on-call engineer
  sns-publish "Automatic rollback triggered"
fi
```

---

## Success Criteria

✓ **Backend**
- API responding in < 2s
- Zero unhandled exceptions
- Database queries < 500ms
- Memory usage stable
- All endpoints tested

✓ **Frontend**
- Page loads < 3s
- Predictions display correctly
- Responsive on mobile/desktop
- No console errors
- Analytics working

✓ **Infrastructure**
- 99.9% uptime
- Auto-scaling working
- Backups automated
- Monitoring active
- Logs centralized

✓ **Data**
- Statcast data fresh (< 24h old)
- Model trained and ready
- Predictions generating
- Backtest working
- DKings odds updating

---

## Contact & Support

- **Primary**: mrglenncarter@yahoo.com
- **GitHub Issues**: [Project Repo]
- **Slack**: #mlb-predictor
- **Status Page**: status.example.com

---

**Last Updated**: June 28, 2026  
**Next Review**: July 15, 2026  
**Approved By**: Glenn Carter
