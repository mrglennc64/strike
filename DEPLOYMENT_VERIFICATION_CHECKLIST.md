# Production Deployment Verification Checklist
## strike.perfecthold.online

**Deployment Date**: _______________  
**Deployed By**: _______________  
**VPS Provider**: _______________  
**IP Address**: _______________  

---

## PRE-DEPLOYMENT CHECKLIST

### Prerequisites
- [ ] SSH credentials saved securely
- [ ] GitHub repository access verified
- [ ] Production secrets ready (not in any git commits)
- [ ] Domain (strike.perfecthold.online) ready
- [ ] DNS pointed to VPS IP address
- [ ] Domain registrar DNS settings updated (wait 24-48 hours for propagation)

### Infrastructure
- [ ] VPS provisioned (Ubuntu 22.04 LTS, 2GB+ RAM, 20GB+ SSD)
- [ ] SSH access verified
- [ ] sudo/root access confirmed
- [ ] Firewall configured (ports 22, 80, 443 open)
- [ ] DNS propagation verified with: `nslookup strike.perfecthold.online`

---

## DEPLOYMENT STEPS

### Step 1: System Preparation
- [ ] SSH into VPS: `ssh root@strike.perfecthold.online`
- [ ] Update system: `apt update && apt upgrade -y`
- [ ] Verify Linux OS: `uname -a`
- [ ] Check available disk space: `df -h` (should have 20GB+)
- [ ] Check available RAM: `free -h` (should have 2GB+)

### Step 2: Docker Installation
- [ ] Docker installed: `docker --version`
- [ ] Docker Compose installed: `docker-compose --version`
- [ ] Docker daemon running: `systemctl status docker`
- [ ] Current user in docker group: `groups $USER` (should include docker)

### Step 3: Repository Setup
- [ ] Repository cloned to `/opt/strike`: `ls -la /opt/strike`
- [ ] On main branch: `cd /opt/strike && git branch`
- [ ] Latest code pulled: `git log --oneline -3`
- [ ] Docker files present:
  - [ ] docker-compose.prod.yml exists
  - [ ] backend/Dockerfile exists
  - [ ] frontend/Dockerfile exists

### Step 4: Environment Configuration
- [ ] .env file created: `ls -la /opt/strike/.env`
- [ ] .env permissions are 600: `ls -l /opt/strike/.env` (should show `-rw-------`)
- [ ] .env NOT in git: `git check-ignore .env` (should return .env)
- [ ] Required variables set:
  - [ ] DATABASE_URL
  - [ ] POSTGRES_PASSWORD
  - [ ] REDIS_PASSWORD
  - [ ] SECRET_KEY
  - [ ] DEBUG=False
  - [ ] VITE_API_URL=https://strike.perfecthold.online/api

### Step 5: Docker Services Build
- [ ] Images built successfully: `docker-compose -f docker-compose.prod.yml build`
- [ ] No build errors in output
- [ ] Images listed: `docker-compose -f docker-compose.prod.yml images`
- [ ] Expected images:
  - [ ] betting-framework-api (backend)
  - [ ] betting-framework-web (frontend)
  - [ ] postgres:15-alpine
  - [ ] redis:7-alpine

### Step 6: Services Startup
- [ ] Services started: `docker-compose -f docker-compose.prod.yml up -d`
- [ ] All services healthy within 30 seconds:

```bash
docker-compose -f docker-compose.prod.yml ps
```

- [ ] PostgreSQL: Up (healthy)
- [ ] Redis: Up (healthy)
- [ ] API: Up (healthy)
- [ ] Frontend: Up (healthy)

### Step 7: Health Checks - Database

```bash
# PostgreSQL health check
docker-compose -f docker-compose.prod.yml exec postgres pg_isready
```

- [ ] Result: `accepting connections` ✓
- [ ] Database user created: `betting_user`
- [ ] Database name: `betting_db`
- [ ] Can query: `docker-compose -f docker-compose.prod.yml exec postgres psql -U betting_user -d betting_db -c "SELECT 1;"`

### Step 8: Health Checks - Cache

```bash
# Redis health check
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
```

- [ ] Result: `PONG` ✓
- [ ] Redis listening on port 6379
- [ ] Redis persistence enabled (RDB)

### Step 9: Health Checks - API

```bash
# API health endpoint
curl -s http://localhost:8000/health | jq .
```

- [ ] Status code: 200 ✓
- [ ] Response: `{"status": "ok"}` or similar
- [ ] No error logs in: `docker-compose -f docker-compose.prod.yml logs api`
- [ ] API accessible at:
  - [ ] http://localhost:8000/health
  - [ ] http://localhost:8000/docs (should show Swagger UI)
  - [ ] http://localhost:8000/redoc (should show ReDoc)

### Step 10: Health Checks - Frontend

```bash
# Frontend health check
curl -s http://localhost:3000 | head -20
```

- [ ] Status code: 200 ✓
- [ ] HTML response with `<html>` tag
- [ ] No error logs in: `docker-compose -f docker-compose.prod.yml logs frontend`

### Step 11: Nginx Reverse Proxy

```bash
# Check nginx status
sudo systemctl status nginx
```

- [ ] Nginx installed: `nginx --version`
- [ ] Nginx running: `sudo systemctl is-active nginx` (returns: active)
- [ ] Nginx enabled: `sudo systemctl is-enabled nginx` (returns: enabled)
- [ ] Config valid: `sudo nginx -t` (returns: successful)
- [ ] Nginx config file created: `/etc/nginx/sites-available/strike`
- [ ] Nginx site enabled: `/etc/nginx/sites-enabled/strike` exists

### Step 12: Reverse Proxy Testing (HTTP)

```bash
# Test HTTP routes
curl -v http://localhost/api/
curl -v http://localhost/health
curl -v http://localhost/
```

- [ ] API routes return 200 or redirect to HTTPS
- [ ] Frontend returns 200 or redirect to HTTPS
- [ ] Health endpoint returns 200

### Step 13: SSL Certificate

```bash
# Check certificate status
sudo certbot certificates | grep strike.perfecthold.online
```

- [ ] Certbot installed: `sudo certbot --version`
- [ ] Certificate obtained for strike.perfecthold.online
- [ ] Certificate valid: `sudo certbot certificates` (should show expiration date)
- [ ] Certificate auto-renewal enabled: `sudo systemctl status certbot.timer`
- [ ] Test renewal dry-run: `sudo certbot renew --dry-run` (should show success)

### Step 14: HTTPS Access

```bash
# Test HTTPS (from external machine or via VPS)
curl -vvv https://strike.perfecthold.online/health
```

- [ ] HTTPS redirect working: HTTP -> HTTPS
- [ ] Certificate valid (no SSL warnings)
- [ ] API accessible via: https://strike.perfecthold.online/api
- [ ] Frontend accessible via: https://strike.perfecthold.online

### Step 15: Test Suite (Optional)

```bash
# Run test suite if available
cd /opt/strike
bash mlb-edge/backend/test-suite.sh 2>/dev/null || echo "No test suite"
```

- [ ] Tests run successfully or no test suite found
- [ ] All endpoint tests pass (if applicable)

### Step 16: Cron Jobs Setup

```bash
# Install cron jobs
bash /opt/strike/deploy/cron-setup.sh install

# Verify installation
bash /opt/strike/deploy/cron-setup.sh list
```

- [ ] Cron setup script executed
- [ ] CLV capture job scheduled (1:00 PM UTC): `0 13 * * *`
- [ ] CLV close job scheduled (10:15 PM UTC): `15 22 * * *`
- [ ] CLV calculate job scheduled (10:30 PM UTC): `30 22 * * *`
- [ ] Monitoring job scheduled (every 5 minutes): `*/5 * * * *`
- [ ] Jobs visible in: `crontab -l`
- [ ] Log directory created: `/opt/strike/logs`

---

## POST-DEPLOYMENT CHECKS

### Logs and Monitoring

```bash
# View recent logs
docker-compose -f docker-compose.prod.yml logs --tail=50

# View logs by service
docker-compose -f docker-compose.prod.yml logs --tail=20 api
docker-compose -f docker-compose.prod.yml logs --tail=20 frontend
docker-compose -f docker-compose.prod.yml logs --tail=20 postgres

# Monitor in real-time
docker-compose -f docker-compose.prod.yml logs -f
```

- [ ] No ERROR or CRITICAL messages in logs
- [ ] Services starting up cleanly
- [ ] Database migrations (if any) completed
- [ ] No connection refused errors

### Backup Verification

```bash
# Create manual backup
docker-compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U betting_user betting_db > /opt/strike/backups/db_test.sql

# Verify backup
ls -lh /opt/strike/backups/
```

- [ ] Backup directory created: `/opt/strike/backups`
- [ ] Manual backup successful
- [ ] Backup file has content (> 1 KB)
- [ ] Automated backup cron job added

### Security Verification

```bash
# Check firewall rules
sudo ufw status

# Verify .env is protected
ls -la /opt/strike/.env

# Check for exposed secrets
git log --all -S "POSTGRES_PASSWORD" --oneline
```

- [ ] Firewall configured:
  - [ ] SSH (22) open to trusted IPs
  - [ ] HTTP (80) open to all
  - [ ] HTTPS (443) open to all
  - [ ] Other ports closed
- [ ] .env file permissions: 600 (owner read/write only)
- [ ] .env in .gitignore
- [ ] No secrets in git history
- [ ] DEBUG=False in production .env

### Resource Monitoring

```bash
# Check resource usage
docker stats
df -h
free -h
```

- [ ] CPU usage reasonable (< 50%)
- [ ] Memory usage reasonable (< 1.5GB used)
- [ ] Disk space available (> 5GB free)
- [ ] No containers with restart loops

---

## FUNCTIONAL TESTING

### API Endpoint Tests

```bash
# Test health endpoint
curl -s https://strike.perfecthold.online/api/health | jq .
```

- [ ] GET /api/health returns 200
- [ ] Response: `{"status": "ok"}` or similar

```bash
# Test swagger docs
curl -s https://strike.perfecthold.online/api/docs | head -20
```

- [ ] GET /api/docs returns HTML (Swagger UI)
- [ ] Status code: 200

### Frontend Tests

```bash
# Test frontend loads
curl -s https://strike.perfecthold.online | head -50
```

- [ ] Status code: 200
- [ ] Contains valid HTML
- [ ] No 404 or 5xx errors
- [ ] JavaScript bundles load (check Network tab in browser)

### Database Tests

```bash
# Connect to database
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U betting_user -d betting_db

# In psql prompt, run:
SELECT version();
\dt  # List tables
\q   # Quit
```

- [ ] Connected to PostgreSQL successfully
- [ ] Database version shown
- [ ] Tables exist (if migrations run)

### Browser Testing

- [ ] Visit https://strike.perfecthold.online
  - [ ] Page loads completely
  - [ ] No console errors (F12 -> Console)
  - [ ] All assets load (images, CSS, JS)
  - [ ] Responsive on mobile (check responsive view)
- [ ] HTTPS padlock visible
- [ ] No SSL warnings
- [ ] Check in different browsers:
  - [ ] Chrome/Edge
  - [ ] Firefox
  - [ ] Safari (if available)

---

## ONGOING MONITORING CHECKLIST

### Daily
- [ ] Services running: `docker-compose -f docker-compose.prod.yml ps`
- [ ] No error logs: `docker-compose -f docker-compose.prod.yml logs | grep ERROR`
- [ ] Health endpoint responds: `curl https://strike.perfecthold.online/api/health`

### Weekly
- [ ] Review logs for patterns: `docker-compose -f docker-compose.prod.yml logs --tail=500`
- [ ] Database backup successful: `ls -lh /opt/strike/backups/ | head -1`
- [ ] Resource usage healthy: `docker stats --no-stream`
- [ ] SSL certificate still valid: `sudo certbot certificates`

### Monthly
- [ ] Security patches applied: `apt update && apt list --upgradable`
- [ ] Old backups cleaned up: `ls /opt/strike/backups/ | wc -l` (should have ~30)
- [ ] Cron jobs still running: `crontab -l | grep strike`
- [ ] Update Docker images: `docker-compose -f docker-compose.prod.yml pull`

---

## DISASTER RECOVERY TESTING

- [ ] Backup restoration tested:
  ```bash
  # Restore from backup
  docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U betting_user betting_db < /opt/strike/backups/db_test.sql
  ```
- [ ] Documented rollback procedure
- [ ] Previous git commit is accessible for rollback
- [ ] Recovery Time Objective (RTO) documented
- [ ] Recovery Point Objective (RPO) documented

---

## SIGN-OFF

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Deployer | | | |
| Reviewer | | | |
| Ops Lead | | | |

---

## DEPLOYMENT STATUS

**Status**: [ ] PASS / [ ] FAIL / [ ] PARTIAL

**Issues Found**:
```
(List any issues found during deployment)
```

**Resolution**:
```
(Document how issues were resolved)
```

**Next Steps**:
```
(Document any remaining tasks or follow-ups)
```

---

## USEFUL COMMANDS

### Quick Status Check
```bash
cd /opt/strike
docker-compose -f docker-compose.prod.yml ps
curl -s https://strike.perfecthold.online/api/health | jq .
```

### View Logs
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f api
docker-compose -f docker-compose.prod.yml logs -f frontend
```

### Restart Services
```bash
# All services
docker-compose -f docker-compose.prod.yml restart

# Specific service
docker-compose -f docker-compose.prod.yml restart api
```

### Stop/Start Services
```bash
# Stop all
docker-compose -f docker-compose.prod.yml down

# Start all
docker-compose -f docker-compose.prod.yml up -d
```

### Database Backup
```bash
docker-compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U betting_user betting_db > /opt/strike/backups/db_$(date +%Y%m%d_%H%M%S).sql
```

### View Database
```bash
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U betting_user -d betting_db
```

---

**Deployment Guide**: `PRODUCTION_DEPLOYMENT_VPS.md`  
**Automated Script**: `deploy-vps.sh`  
**Configuration**: `/opt/strike/.env` (never commit)  
**Logs**: `docker-compose -f docker-compose.prod.yml logs -f`
