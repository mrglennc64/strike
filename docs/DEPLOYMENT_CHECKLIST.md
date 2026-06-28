# Deployment Checklist - Production Betting Framework

**Last Updated**: 2026-06-28  
**Version**: 1.0.0  
**Owner**: DevOps / Platform Team

---

## Pre-Deployment Verification

### Code Quality & Testing
- [ ] All unit tests passing: `pytest backend/tests/ -v`
- [ ] Integration tests passing: `pytest backend/tests/integration/ -v`
- [ ] Code coverage >= 80%: `pytest --cov=backend --cov-report=html`
- [ ] No critical security vulnerabilities: `bandit -r backend/`
- [ ] Static type checking passing: `mypy backend/ --ignore-missing-imports`
- [ ] Linting clean: `flake8 backend/ --max-line-length=100`

### Environment & Dependencies
- [ ] Python 3.10+ installed and verified
- [ ] All dependencies installed: `pip install -r requirements.txt`
- [ ] Virtual environment activated and clean
- [ ] Node.js 18+ installed (for frontend)
- [ ] Frontend dependencies installed: `cd frontend && npm install`
- [ ] No conflicting Python versions in PATH
- [ ] Environment variables file reviewed and validated

### Database Readiness
- [ ] PostgreSQL 13+ server accessible and running
- [ ] Database credentials verified and secure
- [ ] Database encryption enabled
- [ ] Backup strategy confirmed (automated daily snapshots)
- [ ] Connection pooling configured (min: 5, max: 20 connections)
- [ ] Replication configured for high availability
- [ ] Monitoring alerts set up for database health

### Infrastructure Preparation
- [ ] API server (Railway/Render/K8s) provisioned with adequate resources
- [ ] Redis/Cache instance available and tested
- [ ] DNS records prepared and validated
- [ ] SSL/TLS certificates obtained and installed
- [ ] Domain registered and pointing to correct infrastructure
- [ ] CDN configured (for static assets)
- [ ] Load balancer configured and health checks enabled
- [ ] Auto-scaling policies defined (min: 2, max: 10 replicas)

### Security Hardening
- [ ] All secrets encrypted in configuration management
- [ ] API keys rotated and validated
- [ ] Database passwords changed from defaults
- [ ] CORS configuration correct for production domain
- [ ] Rate limiting configured (100 req/min default)
- [ ] Authentication middleware enabled
- [ ] HTTPS enforced (redirect HTTP to HTTPS)
- [ ] Security headers set (HSTS, CSP, X-Frame-Options)
- [ ] Firewall rules reviewed and applied

### Monitoring & Observability
- [ ] Logging configured (CloudWatch/ELK/Datadog)
- [ ] APM/tracing configured (Datadog, New Relic, or Sentry)
- [ ] Metrics collection enabled (Prometheus/CloudWatch)
- [ ] Alerting rules configured for critical thresholds
- [ ] Dashboard created for real-time monitoring
- [ ] Log retention policy set (7 days for debug, 90 days for audit)
- [ ] Error tracking enabled (Sentry or equivalent)

### Documentation & Runbooks
- [ ] Deployment guide reviewed
- [ ] Runbook created and reviewed
- [ ] API documentation generated and published
- [ ] Emergency contacts and escalation paths documented
- [ ] Rollback procedures documented and tested
- [ ] Post-incident review template prepared

### Team & Communication
- [ ] Deployment window scheduled and communicated
- [ ] On-call engineer assigned
- [ ] Stakeholders notified (business, support, product)
- [ ] Change management approval obtained
- [ ] Deployment plan reviewed by tech lead
- [ ] Team members trained on new features/changes

---

## Pre-Deployment Configuration

### Backend Configuration

```bash
# Set environment variables
export ENVIRONMENT=production
export DEBUG=False
export LOG_LEVEL=info
export DATABASE_URL=postgresql://user:pass@prod-db.example.com:5432/betting_db
export REDIS_URL=redis://prod-cache.example.com:6379/0
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
export ALGORITHM=HS256
export ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours
export CORS_ORIGINS=["https://betting-framework.ai"]
export MAX_SINGLE_BET_FRACTION=0.05
export MAX_DAILY_LOSS_FRACTION=0.10
export MAX_EXPOSURE_RATIO=0.30
export RATE_LIMIT_PER_MINUTE=100
export WORKERS=4  # Based on CPU cores
```

### Frontend Configuration

```bash
# Build optimized production bundle
cd frontend
npm run build

# Set environment variables
REACT_APP_API_URL=https://api.betting-framework.ai
REACT_APP_ENVIRONMENT=production
REACT_APP_SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
```

### Database Initialization

```bash
# Create database
createdb betting_db

# Run migrations
alembic upgrade head

# Load seed data if necessary
python backend/init_db.py

# Verify database schema
psql betting_db -c "\dt"
```

---

## Deployment Steps

### Phase 1: Pre-Flight (30 minutes)

1. **Create Backup**
   ```bash
   # Backup current production database
   pg_dump betting_db > backups/pre_deployment_$(date +%s).sql
   
   # Verify backup
   ls -lh backups/
   ```

2. **Verify All Services Are Running**
   ```bash
   # Check database
   psql -U user -h prod-db.example.com -c "SELECT 1"
   
   # Check Redis
   redis-cli -h prod-cache.example.com ping
   
   # Check current API
   curl -s https://api.betting-framework.ai/health | jq .
   ```

3. **Create Canary Environment** (optional)
   ```bash
   # Deploy to staging/canary with new version
   # Run smoke tests
   # Monitor for 1 hour before proceeding
   ```

### Phase 2: Backend Deployment (20 minutes)

1. **Build Docker Image**
   ```bash
   # Build image
   docker build -t betting-framework-api:v1.0.0 -f backend/Dockerfile backend/
   
   # Tag for registry
   docker tag betting-framework-api:v1.0.0 registry.example.com/betting-framework-api:v1.0.0
   docker tag betting-framework-api:v1.0.0 registry.example.com/betting-framework-api:latest
   
   # Push to registry
   docker push registry.example.com/betting-framework-api:v1.0.0
   docker push registry.example.com/betting-framework-api:latest
   ```

2. **Deploy to Production**
   
   **Option A: Railway**
   ```bash
   railway link --project=betting-framework-prod
   railway up
   railway logs  # Monitor logs
   ```
   
   **Option B: Kubernetes**
   ```bash
   # Update deployment image
   kubectl set image deployment/betting-api \
     betting-api=registry.example.com/betting-framework-api:v1.0.0 \
     --namespace=production
   
   # Watch rollout
   kubectl rollout status deployment/betting-api -n production
   
   # Verify new pods are running
   kubectl get pods -n production -l app=betting-api
   ```
   
   **Option C: Docker Compose**
   ```bash
   # Pull new image
   docker pull registry.example.com/betting-framework-api:v1.0.0
   
   # Update docker-compose.yml and deploy
   docker-compose -f docker-compose.prod.yml up -d
   
   # Verify
   docker-compose ps
   ```

3. **Verify API Health**
   ```bash
   # Wait 30 seconds for service startup
   sleep 30
   
   # Check health endpoint
   curl -s https://api.betting-framework.ai/health | jq .
   
   # Verify response includes:
   # - status: "healthy"
   # - database: "ok"
   # - all verticals operational
   ```

### Phase 3: Frontend Deployment (10 minutes)

1. **Deploy to Vercel** (if using)
   ```bash
   # Push to main branch (triggers automatic deployment)
   git push origin main
   
   # Or deploy manually
   vercel --prod
   
   # Check deployment status
   vercel list
   ```

2. **Verify Frontend**
   ```bash
   # Test homepage
   curl -s https://betting-framework.ai | grep -q "<!DOCTYPE html" && echo "OK" || echo "FAILED"
   
   # Check API connectivity (from browser console)
   # Test login page loads
   ```

### Phase 4: Smoke Tests (15 minutes)

Run critical tests immediately after deployment:

```bash
# Run smoke test suite
pytest backend/tests/smoke/ -v --tb=short

# Tests should include:
# - POST /api/auth/signup
# - POST /api/auth/login
# - GET /api/bankroll
# - POST /api/place-bet
# - GET /health (all 4 endpoints)
```

**Expected Results**:
- All endpoints responding with 200/201 status codes
- Response times < 500ms for non-ML endpoints
- No errors in logs

---

## Post-Deployment Verification

### Immediate Checks (First 5 minutes)

```bash
#!/bin/bash
set -e

echo "=== Post-Deployment Verification ==="

# Check API health
echo "Checking API health..."
health=$(curl -s https://api.betting-framework.ai/health)
echo "$health" | jq .

# Verify database connection
echo "Verifying database..."
db_status=$(echo "$health" | jq -r '.database.status')
[[ "$db_status" == "ok" ]] || { echo "Database check failed"; exit 1; }

# Verify all verticals operational
echo "Checking verticals..."
verticals=$(echo "$health" | jq '.verticals')
echo "$verticals" | jq .

# Verify auth works
echo "Testing authentication..."
signup=$(curl -s -X POST https://api.betting-framework.api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"TestPass123!"}')
echo "$signup" | jq .

echo "=== Verification Complete ==="
```

### Short-Term Monitoring (First Hour)

- [ ] Monitor error rate < 0.1%
- [ ] Monitor response times: P50 < 100ms, P95 < 500ms, P99 < 1000ms
- [ ] Monitor database query latency < 50ms
- [ ] Monitor CPU usage < 70%
- [ ] Monitor memory usage < 75%
- [ ] Monitor disk space > 20% free
- [ ] Check logs for errors: `grep ERROR logs/production.log | wc -l`
- [ ] Verify SSL certificate valid: `openssl s_client -connect api.betting-framework.ai:443`
- [ ] Check DNS resolution: `nslookup betting-framework.ai`

### Full Verification Checklist

- [ ] All 20+ API endpoints responding correctly
- [ ] Database transactions working (test bet placement)
- [ ] Email notifications sending (test password reset)
- [ ] External API integrations working (odds API, ML models)
- [ ] Background jobs processing (Celery/RQ tasks)
- [ ] Real-time features working (WebSockets, Pub/Sub)
- [ ] Frontend accessible and loading correctly
- [ ] Frontend API calls succeeding
- [ ] Mobile responsiveness verified
- [ ] Third-party integrations working (Stripe, OAuth)
- [ ] Logs being collected and searchable
- [ ] Metrics being collected and visualized
- [ ] Alerts configured and working

---

## Rollback Plan

### Conditions for Rollback

Rollback immediately if any of:
- [ ] Critical endpoints returning 5xx errors for > 5 minutes
- [ ] Error rate > 1%
- [ ] Database connectivity lost
- [ ] Data corruption detected
- [ ] Security breach detected
- [ ] Performance degradation > 50% from baseline

### Rollback Steps

**Step 1: Declare Incident**
```bash
# Notify team
slack-notify "INCIDENT: Rolling back to previous version"

# Page on-call
page-oncall "Deployment rollback in progress"
```

**Step 2: Revert to Previous Version**

**Option A: Kubernetes**
```bash
# Rollback to previous deployment
kubectl rollout undo deployment/betting-api -n production

# Verify
kubectl rollout status deployment/betting-api -n production

# Confirm healthy
curl -s https://api.betting-framework.ai/health | jq .
```

**Option B: Railway**
```bash
# Check previous deployments
railway deployments

# Rollback to previous version
railway rollback <previous-deployment-id>
```

**Option C: Docker Compose**
```bash
# Restore previous image
docker-compose -f docker-compose.prod.yml down
docker pull registry.example.com/betting-framework-api:previous-tag
docker-compose -f docker-compose.prod.yml up -d

# Verify
curl -s https://api.betting-framework.ai/health
```

**Step 3: Verify Rollback**
```bash
# Check health
curl -s https://api.betting-framework.ai/health | jq .

# Run smoke tests
pytest backend/tests/smoke/ -v

# Monitor metrics
# - Error rate should return to normal
# - Performance should normalize
# - No new errors in logs
```

**Step 4: Database Recovery** (if needed)
```bash
# If database was affected, restore from backup
pg_restore -d betting_db backups/pre_deployment_*.sql

# Verify data integrity
psql betting_db -c "SELECT COUNT(*) FROM users"
psql betting_db -c "SELECT COUNT(*) FROM bets"
psql betting_db -c "SELECT COUNT(*) FROM positions"
```

**Step 5: Post-Rollback**
- [ ] Notify stakeholders of rollback
- [ ] Create incident report
- [ ] Identify root cause
- [ ] Schedule post-mortem (within 24 hours)
- [ ] Plan fixes for next deployment attempt

### Rollback Testing

Test rollback procedures **before production deployment**:

```bash
# Test rollback in staging
# 1. Deploy new version to staging
# 2. Verify new version working
# 3. Trigger rollback procedure
# 4. Verify previous version restored
# 5. Document any issues
```

---

## Deployment Sign-Off

| Role | Name | Date | Time | Status |
|------|------|------|------|--------|
| Tech Lead | | | | [ ] Approved |
| DevOps | | | | [ ] Approved |
| QA Lead | | | | [ ] Approved |
| Product | | | | [ ] Approved |
| Security | | | | [ ] Approved |

---

## Deployment Timeline

```
Time (UTC)    | Activity                           | Owner      | Duration
0:00          | Pre-flight verification            | DevOps     | 30 min
0:30          | Database backup                    | DevOps     | 5 min
0:35          | Backend deployment                 | DevOps     | 20 min
0:55          | API health checks                  | QA         | 5 min
1:00          | Frontend deployment                | DevOps     | 10 min
1:10          | Frontend verification              | QA         | 5 min
1:15          | Smoke tests                        | QA         | 15 min
1:30          | Production validation               | Product    | 30 min
2:00          | Deployment complete & signed off   | All        | -
```

---

## Emergency Contacts

| Role | Name | Phone | Slack | Email |
|------|------|-------|-------|-------|
| On-Call Lead | | | | |
| DevOps Lead | | | | |
| Database Admin | | | | |
| Security Lead | | | | |
| Product Manager | | | | |

---

## Post-Deployment Communication

### Stakeholder Notification Template

```
DEPLOYMENT COMPLETE - Betting Framework v1.0.0

Status: SUCCESS

What was deployed:
- [List of features/fixes]

Timeline:
- Start: 2026-06-28 UTC 00:00
- Complete: 2026-06-28 UTC 02:00
- Duration: 2 hours

Impact:
- Zero downtime deployment
- All services operational
- All tests passing

Next Steps:
- Monitor for 24 hours
- Collect user feedback
- Schedule retrospective

Questions? Contact: @devops on Slack
```

---

## Deployment Artifacts

Save these for audit and troubleshooting:
- [ ] Deployment logs (save as `deployment-2026-06-28.log`)
- [ ] Error logs (save as `errors-2026-06-28.log`)
- [ ] Health check results
- [ ] Performance baseline metrics
- [ ] Smoke test results
- [ ] Database backup file
- [ ] Docker image SHA
- [ ] Git commit SHA for release
