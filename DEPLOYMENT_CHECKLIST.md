# Edge AI - Complete Deployment Checklist
## All 5 Verticals Ready for Production

**Date:** 2026-06-28  
**Version:** 1.0.0

---

## ✅ Pre-Deployment Phase

### Environment Setup
- [ ] Git repository cloned locally
- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed
- [ ] Docker & Docker Compose installed
- [ ] PostgreSQL client installed (psql)
- [ ] Redis CLI installed (redis-cli)

### File Verification
- [ ] `.env.example` exists and is complete
- [ ] `docker-compose.yml` exists at root level
- [ ] `backend/routes/verticals.py` created
- [ ] `backend/main.py` updated with verticals_router
- [ ] `.github/workflows/deploy-all-verticals.yml` created
- [ ] `DEPLOYMENT_ALL_VERTICALS.md` created
- [ ] `DOMAIN_SETUP_GUIDE.md` created

### Configuration
- [ ] `.env.example` reviewed
- [ ] `.env` created from `.env.example`
- [ ] API keys obtained for at least 2 verticals
  - [ ] Polymarket API key
  - [ ] DraftKings API key
  - [ ] FRED API key
  - [ ] Yahoo Finance API key
  - [ ] CoinGecko API key
- [ ] Database credentials set
- [ ] Redis password configured
- [ ] SECRET_KEY generated (32+ chars)

---

## 🏠 Local Development Phase

### Docker Compose Startup
- [ ] `docker-compose up -d` executed without errors
- [ ] All 4 services running:
  - [ ] PostgreSQL (port 5432)
  - [ ] Redis (port 6379)
  - [ ] FastAPI (port 8000)
  - [ ] Frontend (port 3000)

### Service Health Checks
- [ ] PostgreSQL healthcheck passing
  ```bash
  docker-compose ps postgres  # Status: healthy
  ```
- [ ] Redis healthcheck passing
  ```bash
  docker-compose ps redis     # Status: healthy
  ```
- [ ] API healthcheck passing
  ```bash
  curl http://localhost:8000/health
  ```
- [ ] Frontend accessible
  ```bash
  curl http://localhost:3000
  ```

### API Testing
- [ ] Root endpoint responds
  ```bash
  curl http://localhost:8000/
  ```
- [ ] Health endpoint returns all verticals
  ```bash
  curl http://localhost:8000/health | jq '.all_verticals_operational'
  # Should return: true
  ```
- [ ] Verticals endpoint lists all 5
  ```bash
  curl http://localhost:8000/api/verticals | jq '.count'
  # Should return: 5
  ```

### Individual Vertical Testing
- [ ] MLB endpoint accessible
  ```bash
  curl http://localhost:8000/api/verticals/mlb | jq '.vertical'
  # Returns: mlb
  ```
- [ ] Tennis endpoint accessible
  ```bash
  curl http://localhost:8000/api/verticals/tennis | jq '.vertical'
  # Returns: tennis
  ```
- [ ] Cricket endpoint accessible
  ```bash
  curl http://localhost:8000/api/verticals/cricket | jq '.vertical'
  # Returns: cricket
  ```
- [ ] Horse endpoint accessible
  ```bash
  curl http://localhost:8000/api/verticals/horse | jq '.vertical'
  # Returns: horse
  ```
- [ ] Hockey endpoint accessible
  ```bash
  curl http://localhost:8000/api/verticals/hockey | jq '.vertical'
  # Returns: hockey
  ```

### Database Testing
- [ ] Database connection works
  ```bash
  docker-compose exec postgres psql -U betting_user -d betting_db -c "SELECT 1"
  ```
- [ ] Tables created successfully
  ```bash
  docker-compose exec postgres psql -U betting_user -d betting_db -c "\dt"
  ```

### Cache Testing
- [ ] Redis connection works
  ```bash
  redis-cli -a redis_password PING
  # Returns: PONG
  ```

### Frontend Testing
- [ ] React app loads at http://localhost:3000
- [ ] No console errors
- [ ] Dashboard accessible
- [ ] Can view all 5 verticals

---

## 🌐 Cloud Deployment Phase

### Railway Setup (Backend)

#### Account & Project
- [ ] Railway account created (https://railway.app)
- [ ] GitHub repository connected to Railway
- [ ] Railway project created
- [ ] PostgreSQL service provisioned
- [ ] Redis service provisioned

#### Environment Variables
- [ ] All 71 environment variables configured in Railway
  - [ ] Database credentials
  - [ ] API keys (Polymarket, FRED, etc.)
  - [ ] Security keys (SECRET_KEY)
  - [ ] Risk parameters
  - [ ] Deployment settings
- [ ] Variables validated in Railway dashboard

#### Deployment
- [ ] Backend built successfully on Railway
- [ ] Build logs reviewed (no errors)
- [ ] Service health check passing
- [ ] API accessible at Railway URL
  ```bash
  curl https://<railway-domain>/health
  ```

### Vercel Setup (Frontend)

#### Account & Project
- [ ] Vercel account created (https://vercel.com)
- [ ] GitHub repository connected to Vercel
- [ ] Vercel project created
- [ ] Project settings reviewed

#### Environment Variables
- [ ] VITE_API_URL configured
  ```
  VITE_API_URL=https://<railway-domain>
  ```
- [ ] VITE_APP_NAME configured
  ```
  VITE_APP_NAME=Edge AI
  ```

#### Deployment
- [ ] Frontend built successfully on Vercel
- [ ] Build logs reviewed (no errors)
- [ ] Deployment preview accessible
- [ ] Frontend accessible at Vercel URL
  ```bash
  curl https://<vercel-domain>
  ```

### GitHub Actions CI/CD

#### Configuration
- [ ] `.github/workflows/deploy-all-verticals.yml` exists
- [ ] Workflow file syntax valid
  ```bash
  git push origin main  # Triggers workflow
  ```

#### GitHub Secrets
- [ ] RAILWAY_TOKEN configured
- [ ] VERCEL_TOKEN configured
- [ ] VERCEL_ORG_ID configured
- [ ] VERCEL_PROJECT_ID configured
- [ ] All API keys added to secrets

#### First Deployment
- [ ] Commit to main branch
  ```bash
  git add .
  git commit -m "Deploy unified verticals"
  git push origin main
  ```
- [ ] GitHub Actions workflow triggered
- [ ] All 5 verticals tested in parallel
  - [ ] MLB test passed
  - [ ] Tennis test passed
  - [ ] Cricket test passed
  - [ ] Horse test passed
  - [ ] Hockey test passed
- [ ] Docker images built successfully
- [ ] Backend deployed to Railway
- [ ] Frontend deployed to Vercel
- [ ] Post-deployment health checks passed

---

## 🌍 Domain Configuration Phase

### Domain Registration
- [ ] Domain edge-ai.io researched (https://www.whatsmydns.net)
- [ ] Domain pricing compared (Namecheap ~$10.56/year)
- [ ] Domain purchased at registrar:
  - [ ] Namecheap
  - [ ] Cloudflare Registrar
  - [ ] or Route53
- [ ] Payment completed
- [ ] Domain confirmation email received

### DNS Configuration

#### Nameserver Setup
- [ ] Cloudflare account created (optional but recommended)
- [ ] Cloudflare nameservers noted:
  ```
  ns1.cloudflare.com
  ns2.cloudflare.com
  ```
- [ ] Registrar nameservers updated to Cloudflare
- [ ] Wait 24-48 hours for propagation

#### DNS Records Created
- [ ] A record for edge-ai.io → Vercel IP
- [ ] CNAME for www.edge-ai.io → Vercel
- [ ] CNAME for api.edge-ai.io → Railway domain
- [ ] TLS records created automatically
- [ ] DNS propagation verified
  ```bash
  nslookup edge-ai.io
  dig edge-ai.io
  ```

### SSL/TLS Certificates

#### Vercel
- [ ] Automatic SSL provisioned by Vercel
- [ ] Certificate verified
  ```bash
  openssl s_client -connect edge-ai.io:443
  ```
- [ ] HTTPS accessible at https://edge-ai.io

#### Railway
- [ ] Automatic SSL provisioned by Railway
- [ ] Certificate verified
  ```bash
  openssl s_client -connect api.edge-ai.io:443
  ```
- [ ] HTTPS accessible at https://api.edge-ai.io

### Domain Verification
- [ ] Ping all subdomains:
  ```bash
  curl -I https://edge-ai.io
  curl -I https://www.edge-ai.io
  curl -I https://api.edge-ai.io
  ```
- [ ] All return 200/301 status codes

---

## 📊 Production Verification Phase

### Frontend Access
- [ ] https://edge-ai.io loads successfully
- [ ] https://www.edge-ai.io redirects correctly
- [ ] React app renders without errors
- [ ] Dashboard fully functional
- [ ] No console errors (F12)

### Backend Access
- [ ] https://api.edge-ai.io/health returns 200
- [ ] Health check shows all verticals "ok"
  ```bash
  curl https://api.edge-ai.io/health | jq '.all_verticals_operational'
  # Returns: true
  ```
- [ ] Swagger UI accessible at https://api.edge-ai.io/docs
- [ ] OpenAPI schema valid at https://api.edge-ai.io/openapi.json

### Vertical Endpoints (Production)
- [ ] https://api.edge-ai.io/api/verticals returns all 5
  ```bash
  curl https://api.edge-ai.io/api/verticals | jq '.count'
  # Returns: 5
  ```
- [ ] MLB at https://api.edge-ai.io/api/verticals/mlb
- [ ] Tennis at https://api.edge-ai.io/api/verticals/tennis
- [ ] Cricket at https://api.edge-ai.io/api/verticals/cricket
- [ ] Horse at https://api.edge-ai.io/api/verticals/horse
- [ ] Hockey at https://api.edge-ai.io/api/verticals/hockey

### Database (Production)
- [ ] PostgreSQL service running on Railway
- [ ] Database created and accessible
- [ ] Tables auto-created on first run
- [ ] Backups configured (if available)

### Cache (Production)
- [ ] Redis service running on Railway
- [ ] Cache accessible from API
- [ ] No cache connection errors

### Monitoring & Logging
- [ ] Sentry DSN configured
- [ ] Error tracking operational
- [ ] Datadog configured (if available)
- [ ] Log aggregation working

---

## 🔐 Security Phase

### Credentials & Secrets
- [ ] No `.env` file committed to git
- [ ] `.gitignore` prevents `.env` commits
- [ ] All secrets in GitHub Secrets (not in code)
- [ ] All secrets in Railway/Vercel environment
- [ ] Database password strong (12+ chars)
- [ ] Redis password set (not empty)
- [ ] SECRET_KEY unique and strong

### Access Control
- [ ] GitHub repository private or branch-protected
- [ ] Deployment keys rotated (if applicable)
- [ ] API rate limiting configured
- [ ] CORS properly configured
  ```python
  allow_origins=["https://edge-ai.io", "https://www.edge-ai.io"]
  ```

### SSL/TLS
- [ ] SSL certificates valid (auto-renewed)
- [ ] HTTPS enforced (no HTTP)
- [ ] Certificate chain valid
- [ ] Security headers configured

---

## 📈 Performance Phase

### Load Testing
- [ ] Basic load test on healthcheck
  ```bash
  for i in {1..100}; do curl https://api.edge-ai.io/health; done
  ```
- [ ] Response times acceptable (<500ms)
- [ ] No timeout errors

### Database Performance
- [ ] Query performance acceptable
- [ ] Indexes created on key columns
- [ ] Connection pooling configured
- [ ] Slow query logging enabled

### Cache Performance
- [ ] Redis cache hit rate acceptable
- [ ] Cache keys expire correctly
- [ ] No memory leaks
- [ ] Cache size within limits

### Frontend Performance
- [ ] Page load time <3 seconds
- [ ] No JavaScript errors
- [ ] Images optimized
- [ ] Bundle size acceptable

---

## 📚 Documentation Phase

### README
- [ ] README.md updated with:
  - [ ] Quick start instructions
  - [ ] Deployment links
  - [ ] API documentation link
  - [ ] Support contact info

### API Documentation
- [ ] Swagger UI accessible at `/docs`
- [ ] All endpoints documented
- [ ] Request/response examples provided
- [ ] Error codes documented

### Deployment Documentation
- [ ] DEPLOYMENT_ALL_VERTICALS.md completed
- [ ] DOMAIN_SETUP_GUIDE.md completed
- [ ] Troubleshooting guide available
- [ ] Architecture diagram clear

### Vertical Documentation
- [ ] Each vertical documented:
  - [ ] Model type
  - [ ] Input features
  - [ ] Output prediction
  - [ ] Accuracy metrics
  - [ ] Usage examples

---

## 📢 Release Phase

### Stakeholder Notification
- [ ] Product team notified
- [ ] Customers notified (if applicable)
- [ ] Release notes prepared
- [ ] Changelog updated

### Launch
- [ ] All checks complete
- [ ] Monitoring active
- [ ] Support team ready
- [ ] Incident response plan ready

### Post-Launch
- [ ] Monitor error logs for first 24 hours
- [ ] Check user feedback
- [ ] Verify all verticals running normally
- [ ] Review performance metrics

---

## 🔄 Ongoing Maintenance

### Daily
- [ ] Check error logs (Sentry)
- [ ] Monitor health checks
- [ ] Verify all 5 verticals operational

### Weekly
- [ ] Review performance metrics
- [ ] Check database size
- [ ] Verify backups completed
- [ ] Update external data sources

### Monthly
- [ ] Review and update dependencies
- [ ] Check SSL certificate status
- [ ] Optimize database (VACUUM)
- [ ] Review and refine security settings

### Quarterly
- [ ] Full security audit
- [ ] Performance optimization review
- [ ] Disaster recovery test
- [ ] Update documentation

### Annually
- [ ] Renew domain registration
- [ ] Security penetration test
- [ ] Major dependency updates
- [ ] Architecture review

---

## 🎯 Sign-Off

| Role | Name | Date | Status |
|------|------|------|--------|
| Developer | _________________ | _________ | ☐ Approved |
| DevOps | _________________ | _________ | ☐ Approved |
| QA | _________________ | _________ | ☐ Approved |
| Product Manager | _________________ | _________ | ☐ Approved |

---

## 📝 Notes & Comments

```
[Space for deployment notes and issues encountered]

Issue 1: _________________________________
Resolution: _____________________________

Issue 2: _________________________________
Resolution: _____________________________

Issue 3: _________________________________
Resolution: _____________________________
```

---

## 🚀 Deployment Complete!

**Status:** ✅ Ready for Production  
**Date:** 2026-06-28  
**Contact:** support@edge-ai.io

All 5 verticals (MLB, Tennis, Cricket, Horse, Hockey) are now deployed and operational!

- **Frontend:** https://edge-ai.io
- **API:** https://api.edge-ai.io
- **Docs:** https://api.edge-ai.io/docs
- **Health:** https://api.edge-ai.io/health

---

**Document Version:** 1.0.0  
**Last Updated:** 2026-06-28
