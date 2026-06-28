# Edge AI - Complete Unified Deployment Guide
## All 5 Betting Verticals (MLB, Tennis, Cricket, Horse, Hockey)

**Last Updated:** 2026-06-28  
**Version:** 1.0.0  
**Status:** Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Prerequisites](#prerequisites)
4. [Local Development Setup](#local-development-setup)
5. [Docker Deployment](#docker-deployment)
6. [Cloud Deployment (Railway + Vercel)](#cloud-deployment-railway--vercel)
7. [Domain Registration (edge-ai.io)](#domain-registration-edge-aiio)
8. [GitHub Actions CI/CD](#github-actions-cicd)
9. [Health Check & Monitoring](#health-check--monitoring)
10. [Troubleshooting](#troubleshooting)
11. [Scaling Considerations](#scaling-considerations)

---

## Overview

**Edge AI** is a unified betting platform integrating 5 sports edge models:

| Vertical | Sport | Model Type | Status |
|----------|-------|-----------|--------|
| **MLB** | Baseball | Classification (Strikeout Prediction) | ✅ Production |
| **Tennis** | Tennis | Ranking-based (Elo + Markov) | ✅ Production |
| **Cricket** | Cricket | Binary Classification (LBW Bias) | ✅ Production |
| **Horse** | Horse Racing | Regression (Benter Methodology) | 🟡 Beta |
| **Hockey** | Hockey | Time Series (Shots-on-Goal) | ✅ Production |

### Key Features

- **Unified API:** `/api/verticals/{vertical_name}` routes all sports models
- **PostgreSQL Database:** Centralized data storage
- **Redis Cache:** High-speed predictions and state management
- **React Frontend:** Multi-sport dashboard
- **Docker Compose:** Complete containerized deployment
- **CI/CD Automation:** GitHub Actions parallel testing & deployment
- **Cloud-Ready:** Railway (backend), Vercel (frontend)
- **Health Monitoring:** Comprehensive `/health` endpoint for all verticals

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        EDGE AI PLATFORM                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         REACT FRONTEND (Vercel)                      │   │
│  │  Dashboard • Analytics • Betting Interface           │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↑ HTTPS                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         FASTAPI BACKEND (Railway)                    │   │
│  │  /api/verticals/{vertical_name}                      │   │
│  │  ├─ /mlb        (Strikeout predictions)             │   │
│  │  ├─ /tennis     (Match predictions)                 │   │
│  │  ├─ /cricket    (LBW bias detection)                │   │
│  │  ├─ /horse      (Race predictions)                  │   │
│  │  └─ /hockey     (Goal predictions)                  │   │
│  │                                                      │   │
│  │  Core Routes:                                        │   │
│  │  ├─ /auth       (JWT authentication)                │   │
│  │  ├─ /bankroll   (Bet management)                    │   │
│  │  ├─ /kelly      (Kelly criterion)                   │   │
│  │  ├─ /health     (System health check)               │   │
│  │  └─ /docs       (API documentation)                 │   │
│  └──────────────────────────────────────────────────────┘   │
│         ↑ TCP:8000                              ↓ TCP         │
│  ┌──────────────────────┐  ┌──────────────────────────────┐  │
│  │  PostgreSQL DB       │  │  Redis Cache                 │  │
│  │  ├─ Users            │  │  ├─ Prediction Cache         │  │
│  │  ├─ Predictions      │  │  ├─ Session Store            │  │
│  │  ├─ Bets             │  │  └─ Rate Limits              │  │
│  │  └─ Audit Logs       │  │                              │  │
│  └──────────────────────┘  └──────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  EXTERNAL DATA SOURCES                               │   │
│  │  ├─ MLB: StatsBomb, MLB Savant                       │   │
│  │  ├─ Tennis: ATP, WTA, Tennis Explorer                │   │
│  │  ├─ Cricket: ESPN, CricketData                       │   │
│  │  ├─ Horse: Equibase, HKJC                            │   │
│  │  └─ Hockey: NHL Stats API                            │   │
│  │                                                       │   │
│  │  Bookmakers: Pinnacle, DraftKings, Polymarket        │   │
│  │  Economic: FRED, Yahoo Finance                       │   │
│  │  Crypto: CoinGecko, Binance, Kraken                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### System Requirements

- **Docker & Docker Compose** (latest)
- **Git** (for version control)
- **Python 3.11+** (for local development)
- **Node.js 18+** (for frontend)
- **PostgreSQL Client** (psql, for troubleshooting)

### Required Accounts & API Keys

Before deployment, obtain these API keys:

#### Sports Data
- [ ] **Pinnacle API** → https://www.pinnacle.com/en/api/sports/
- [ ] **DraftKings API** → https://developer.draftkings.com/
- [ ] **Polymarket API** → https://docs.polymarket.com/
- [ ] **ESPN API** → https://developer.espn.com/
- [ ] **MLB Savant** → https://baseballsavant.mlb.com/
- [ ] **Tennis Explorer** → (requires manual contract)
- [ ] **HKJC Racing** → https://racing.hkjc.com/
- [ ] **NHL Stats** → https://statsapi.web.nhl.com/

#### Economic Data
- [ ] **FRED API** → https://fredaccount.stlouisfed.org/login
- [ ] **Yahoo Finance** → https://developer.yahoo.com/
- [ ] **Alpha Vantage** → https://www.alphavantage.co/

#### Other Services
- [ ] **CoinGecko API** → https://www.coingecko.com/api
- [ ] **Sentry DSN** (error tracking)
- [ ] **Railway Account** (backend deployment)
- [ ] **Vercel Account** (frontend deployment)
- [ ] **GitHub Token** (for CI/CD)

---

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/edge-ai.git
cd edge-ai
```

### 2. Create Environment File

```bash
cp .env.example .env
# Edit .env with your actual API keys
nano .env
```

### 3. Start Services with Docker Compose

```bash
# Start all services (PostgreSQL, Redis, API, Frontend)
docker-compose up -d

# View logs
docker-compose logs -f api
docker-compose logs -f frontend

# Check health
curl http://localhost:8000/health
curl http://localhost:3000
```

### 4. Verify Services

```bash
# API Endpoints
curl http://localhost:8000/                        # Root
curl http://localhost:8000/health                  # Health check
curl http://localhost:8000/api/verticals           # All verticals
curl http://localhost:8000/api/verticals/mlb       # MLB endpoint
curl http://localhost:8000/docs                    # Swagger UI

# Frontend
open http://localhost:3000                         # React app

# Database
psql -h localhost -U betting_user -d betting_db

# Redis
redis-cli -a redis_password PING
```

---

## Docker Deployment

### Single Command Deployment

```bash
# With environment variables from .env
docker-compose up -d

# Force rebuild
docker-compose up -d --build

# Check status
docker-compose ps

# View logs for a service
docker-compose logs -f api
docker-compose logs -f frontend
docker-compose logs -f postgres
docker-compose logs -f redis
```

### Manual Service Startup

```bash
# Database
docker-compose up -d postgres

# Cache
docker-compose up -d redis

# API (after DB is healthy)
docker-compose up -d api

# Frontend
docker-compose up -d frontend
```

### Cleanup

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ WARNING: deletes data)
docker-compose down -v

# Remove images
docker rmi $(docker images | grep edge-ai)
```

---

## Cloud Deployment (Railway + Vercel)

### Deploy Backend to Railway

#### Step 1: Create Railway Project

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Create new project
railway init

# Set environment variables
railway variables add \
  DATABASE_URL=postgresql://... \
  REDIS_URL=redis://... \
  SECRET_KEY=your-secret-key \
  POLYMARKET_API_KEY=... \
  FRED_API_KEY=... \
  # ... add all required keys
```

#### Step 2: Deploy Backend

```bash
# Deploy from repository
railway up

# Monitor deployment
railway logs

# Check status
railway status

# Get service URL
railway domain
# Output: https://edge-ai-api-production.up.railway.app
```

#### Step 3: Connect Database

```bash
# Railway automatically provisions PostgreSQL
# Get connection details
railway database

# Migrate database
railway run python backend/db_migrate.py
```

### Deploy Frontend to Vercel

#### Step 1: Connect GitHub

1. Go to https://vercel.com/new
2. Select "Import Git Repository"
3. Choose your GitHub repository
4. Select "Next"

#### Step 2: Configure Project

```
Framework Preset: Vite
Root Directory: ./frontend
Environment Variables:
  VITE_API_URL=https://api.edge-ai.io
  VITE_APP_NAME=Edge AI
```

#### Step 3: Deploy

```bash
# Or deploy from CLI
npm install -g vercel
vercel --prod

# Monitor deployment
vercel logs

# Get deployment URL
# Output: https://edge-ai.vercel.app
```

---

## Domain Registration (edge-ai.io)

### Step 1: Register Domain

1. Go to **Namecheap** (or GoDaddy, Route53, Cloudflare)
2. Search for `edge-ai.io`
3. Register for 1 year (typically $8-12/year)

### Step 2: Configure DNS Records

For your domain registrar (Namecheap example):

```
Type: CNAME
Name: @
Value: cname.vercel-dns.com
```

OR if using Cloudflare:

```
Type: CNAME
Name: edge-ai.io
Target: cname.vercel-dns.com
```

### Step 3: Point Backend to Railway

```bash
# In Vercel dashboard, add custom domain
# Vercel will provide DNS records for Railway API

# Or use Railway's custom domain feature
railway domain add edge-ai.io
```

### Step 4: Configure Subdomains

```
Subdomain              Points To           Status
─────────────────────────────────────────────────────
www.edge-ai.io     → Vercel (Frontend)  ✅
api.edge-ai.io     → Railway (Backend)  ✅
docs.edge-ai.io    → API Swagger Docs   ✅
status.edge-ai.io  → Status Page        ✅
```

**DNS Configuration:**

```
api.edge-ai.io      CNAME → edge-ai-api.railway.app
www.edge-ai.io      CNAME → cname.vercel-dns.com
docs.edge-ai.io     CNAME → cname.vercel-dns.com
status.edge-ai.io   CNAME → status-page.io
```

### Step 5: SSL/TLS Certificate

```bash
# Vercel auto-provisions SSL
# Railway auto-provisions SSL
# No additional action needed

# Verify SSL
curl -I https://api.edge-ai.io
curl -I https://edge-ai.io
```

---

## GitHub Actions CI/CD

### Workflow: `.github/workflows/deploy-all-verticals.yml`

Automated pipeline:

1. **Parallel Testing** (5 verticals simultaneously)
   - MLB Strikeout Edge
   - Tennis Edge
   - Cricket Edge
   - Horse Racing Edge
   - Hockey Edge

2. **Build Docker Images**
   - API image
   - Frontend image
   - Push to GHCR

3. **Deploy to Railway** (backend)

4. **Deploy to Vercel** (frontend)

5. **Health Checks**
   - API `/health`
   - Frontend home page
   - All 5 verticals accessible

### Setup GitHub Actions Secrets

In GitHub repository settings:

```
RAILWAY_TOKEN              = (Railway API token)
VERCEL_TOKEN               = (Vercel authentication token)
VERCEL_ORG_ID              = (Vercel organization ID)
VERCEL_PROJECT_ID          = (Vercel project ID)
POLYMARKET_API_KEY         = (...)
FRED_API_KEY               = (...)
DRAFTKINGS_API_KEY         = (...)
# ... add all API keys needed
```

### Trigger Deployment

```bash
# Automatic: Push to main
git commit -m "Update verticals"
git push origin main

# Manual: Trigger from GitHub Actions UI
# Go to: Actions → Deploy All Verticals → Run workflow

# Via CLI
gh workflow run deploy-all-verticals.yml
```

### Monitor Deployment

```bash
# View workflow status
gh workflow view deploy-all-verticals.yml

# Watch logs
gh run watch <run-id>

# List recent runs
gh run list --workflow=deploy-all-verticals.yml
```

---

## Health Check & Monitoring

### Health Check Endpoint

```bash
# Basic health check
curl https://api.edge-ai.io/health

# Response:
{
  "status": "ok",
  "app": "Edge AI",
  "version": "1.0.0",
  "database": "ok",
  "cache": "ok",
  "verticals": {
    "mlb": "ok",
    "tennis": "ok",
    "cricket": "ok",
    "horse": "ok",
    "hockey": "ok"
  },
  "all_verticals_operational": true,
  "message": "5 edge verticals operational"
}
```

### Check Individual Verticals

```bash
# List all verticals
curl https://api.edge-ai.io/api/verticals

# Get vertical info
curl https://api.edge-ai.io/api/verticals/mlb
curl https://api.edge-ai.io/api/verticals/tennis
curl https://api.edge-ai.io/api/verticals/cricket
curl https://api.edge-ai.io/api/verticals/horse
curl https://api.edge-ai.io/api/verticals/hockey

# Verticals health check
curl https://api.edge-ai.io/api/verticals/health
```

### Monitoring Dashboard

Set up monitoring with:

- **Sentry** (error tracking)
- **Datadog** (APM)
- **UptimeRobot** (uptime monitoring)
- **LogRocket** (frontend monitoring)

```bash
# Configure in .env
SENTRY_DSN=https://...
DATADOG_API_KEY=...
LOGROCKET_APP_ID=...
```

---

## Troubleshooting

### Common Issues

#### 1. Docker Services Won't Start

```bash
# Check Docker is running
docker ps

# Verify compose file
docker-compose config

# Rebuild images
docker-compose up -d --build

# Check logs
docker-compose logs api
docker-compose logs postgres
```

#### 2. Database Connection Failed

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check connection string
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

#### 3. API Not Responding

```bash
# Check API container
docker-compose logs api

# Check port is accessible
curl http://localhost:8000/health

# Verify environment variables
docker-compose exec api env | grep DATABASE

# Restart API
docker-compose restart api
```

#### 4. Frontend Build Fails

```bash
# Clear node_modules
rm -rf frontend/node_modules
rm frontend/package-lock.json

# Reinstall
cd frontend
npm install
npm run build

# Check Vite config
cat vite.config.ts
```

#### 5. Redis Connection Issues

```bash
# Check Redis is running
docker ps | grep redis

# Test connection
redis-cli -a $(grep REDIS_PASSWORD .env | cut -d= -f2) PING

# Check logs
docker-compose logs redis

# Restart Redis
docker-compose restart redis
```

### Debug Mode

```bash
# Enable debug logging
DEBUG=True
LOG_LEVEL=DEBUG

# View detailed logs
docker-compose logs -f --tail=100 api

# SSH into container
docker exec -it betting-framework-api bash
docker exec -it betting-framework-db psql -U betting_user -d betting_db
```

---

## Scaling Considerations

### Horizontal Scaling

```bash
# Scale API service
docker-compose up -d --scale api=3

# Load balance with Nginx
# docker-compose.prod.yml includes Nginx configuration
```

### Database Optimization

```sql
-- Create indexes for common queries
CREATE INDEX idx_predictions_user_id ON predictions(user_id);
CREATE INDEX idx_bets_user_id ON bets(user_id);
CREATE INDEX idx_predictions_vertical ON predictions(vertical_name);
```

### Caching Strategy

```python
# Redis cache for predictions
CACHE_TTL = 3600  # 1 hour

# Cache key pattern
f"prediction:{vertical_name}:{input_hash}"
```

### Rate Limiting

```python
# Limit requests per user
MAX_REQUESTS_PER_MINUTE = 60
MAX_REQUESTS_PER_HOUR = 1000
```

---

## Maintenance & Updates

### Regular Tasks

```bash
# Weekly: Check logs and errors
docker-compose logs | grep ERROR

# Monthly: Update dependencies
pip install --upgrade -r requirements.txt
npm update

# Quarterly: Database optimization
docker-compose exec postgres VACUUM;

# Annually: Renew SSL certificates (auto with Vercel/Railway)
```

### Backup Database

```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump \
  -U betting_user betting_db > backup_$(date +%Y%m%d).sql

# Restore from backup
docker-compose exec -T postgres psql \
  -U betting_user betting_db < backup_20260628.sql
```

---

## Support & Contact

- **Documentation:** https://docs.edge-ai.io
- **API Docs:** https://api.edge-ai.io/docs
- **GitHub Issues:** https://github.com/yourusername/edge-ai/issues
- **Email:** support@edge-ai.io

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-06-28 | Initial unified deployment guide for all 5 verticals |
| 0.9.0 | 2026-06-01 | Beta version with 3 verticals |

---

**Last Updated:** 2026-06-28  
**License:** Proprietary - Restricted Distribution  
**Maintainer:** Glenn Carter (mrglenncarter@yahoo.com)
