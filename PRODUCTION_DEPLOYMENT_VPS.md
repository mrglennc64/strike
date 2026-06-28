# Production VPS Deployment Guide
## strike.perfecthold.online

**Date**: June 28, 2026  
**Status**: Ready for deployment  
**Target**: Docker Compose on Linux VPS

---

## PREREQUISITES

Before starting, ensure you have:
- [ ] SSH access to strike.perfecthold.online
- [ ] Admin/sudo privileges on VPS
- [ ] Git installed on VPS
- [ ] Docker & Docker Compose installed
- [ ] Production secrets ready (in secure location, NOT in repo)
- [ ] Domain configured with DNS records pointing to VPS IP
- [ ] SSL certificates ready (or plan to generate with Let's Encrypt)

---

## STEP 1: SSH INTO VPS AND PREPARE ENVIRONMENT

```bash
# SSH into your VPS
ssh root@strike.perfecthold.online
# OR
ssh ubuntu@strike.perfecthold.online

# Update system packages
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Add current user to docker group (avoid sudo for docker commands)
usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version

# Create application directory
sudo mkdir -p /opt/strike
cd /opt/strike
sudo chown $USER:$USER /opt/strike
```

---

## STEP 2: CLONE REPOSITORY

```bash
cd /opt/strike

# Clone from GitHub
git clone https://github.com/yourusername/strike.git .

# OR if already cloned, pull latest
cd /opt/strike
git pull origin main

# Verify directory structure
ls -la
# Expected: backend/, frontend/, docker-compose.prod.yml, deploy/, etc.
```

---

## STEP 3: CREATE PRODUCTION .ENV FILE

**IMPORTANT**: Never commit secrets to git. Create .env locally on VPS.

```bash
cd /opt/strike

# Copy example
cp .env.example .env

# Edit with production values
nano .env
```

**Required secrets to set** (generate strong random values):

```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate POSTGRES_PASSWORD (32+ chars)
openssl rand -base64 32

# Generate REDIS_PASSWORD (32+ chars)
openssl rand -base64 32
```

**Fill in .env with ONLY these required values:**

```env
# Application
DEBUG=False
APP_NAME=Strike Betting Platform

# Database (PostgreSQL)
POSTGRES_USER=betting_user
POSTGRES_PASSWORD=<GENERATE_RANDOM_32_CHAR_PASSWORD>
POSTGRES_DB=betting_db
DATABASE_URL=postgresql://betting_user:<PASSWORD>@postgres:5432/betting_db

# Cache (Redis)
REDIS_PASSWORD=<GENERATE_RANDOM_32_CHAR_PASSWORD>
REDIS_URL=redis://:@redis:6379

# Security
SECRET_KEY=<GENERATE_RANDOM_32_CHAR_SECRET>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Risk Management
MAX_SINGLE_BET_FRACTION=0.05
MAX_DAILY_LOSS_FRACTION=0.10
MAX_KELLY_FRACTION=0.25
MIN_KELLY_FRACTION=0.01

# Frontend
VITE_API_URL=https://api.strike.perfecthold.online
API_URL=http://api:8000

# API Keys (optional - only if using external services)
PINNACLE_API_KEY=<your_key_here>
ODDS_API_KEY=<your_key_here>
```

**Protect .env:**
```bash
chmod 600 .env
```

---

## STEP 4: DOCKER IMAGES BUILD & VERIFY

```bash
# Build Docker images
docker-compose -f docker-compose.prod.yml build

# Verify build succeeded
docker-compose -f docker-compose.prod.yml images
```

---

## STEP 5: START SERVICES (DOCKER COMPOSE)

```bash
cd /opt/strike

# Start all services in background
docker-compose -f docker-compose.prod.yml up -d

# Wait 10 seconds for services to initialize
sleep 10

# Check status
docker-compose -f docker-compose.prod.yml ps
```

**Expected output:**
```
NAME                           STATUS
betting-framework-db           Up (healthy)
betting-framework-cache        Up (healthy)
betting-framework-api          Up (healthy)
betting-framework-web          Up (healthy)
```

---

## STEP 6: HEALTH CHECKS

```bash
# Check PostgreSQL
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# Check Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
# Expected: PONG

# Check API health
curl http://localhost:8000/health
# Expected: {"status": "ok"}

# Check frontend
curl http://localhost:3000
# Expected: HTML response

# View service logs (if any errors)
docker-compose -f docker-compose.prod.yml logs -f api
docker-compose -f docker-compose.prod.yml logs -f frontend
```

---

## STEP 7: RUN TEST SUITE

```bash
cd /opt/strike

# Run test suite if available
if [ -f "mlb-edge/backend/test-suite.sh" ]; then
  bash mlb-edge/backend/test-suite.sh
fi

# Or run manual tests
docker-compose -f docker-compose.prod.yml exec api \
  curl -f http://localhost:8000/health || echo "API test failed"
```

---

## STEP 8: SETUP CRON JOBS FOR CLV TRACKING

```bash
cd /opt/strike/deploy

# Make script executable
chmod +x cron-setup.sh

# Install cron jobs (will auto-detect systemd or crontab)
bash cron-setup.sh install

# Verify jobs installed
bash cron-setup.sh list
```

**Jobs installed:**
- 1:00 PM UTC: CLV capture (open odds)
- 10:15 PM UTC: CLV capture (close odds)
- 10:30 PM UTC: CLV calculation
- Every 5 minutes: Health check monitoring

---

## STEP 9: CONFIGURE NGINX REVERSE PROXY

```bash
# Install nginx if not already installed
sudo apt install nginx -y

# Create nginx config
sudo tee /etc/nginx/sites-available/strike > /dev/null << 'EOF'
# Upstream services (docker containers)
upstream api {
  server localhost:8000;
}

upstream web {
  server localhost:3000;
}

# Redirect HTTP to HTTPS
server {
  listen 80;
  listen [::]:80;
  server_name strike.perfecthold.online;
  
  return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
  listen 443 ssl http2;
  listen [::]:443 ssl http2;
  server_name strike.perfecthold.online;

  # SSL certificates (update paths if using Let's Encrypt)
  ssl_certificate /etc/letsencrypt/live/strike.perfecthold.online/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/strike.perfecthold.online/privkey.pem;
  
  # SSL security settings
  ssl_protocols TLSv1.2 TLSv1.3;
  ssl_ciphers HIGH:!aNULL:!MD5;
  ssl_prefer_server_ciphers on;

  # API routes
  location /api/ {
    proxy_pass http://api;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
  }

  # Health endpoint (for monitoring)
  location /health {
    proxy_pass http://api;
  }

  # Frontend (everything else)
  location / {
    proxy_pass http://web;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/strike /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# Verify nginx is running
sudo systemctl status nginx
```

---

## STEP 10: SETUP SSL CERTIFICATE (Let's Encrypt)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate (ensure domain is pointing to VPS IP first)
sudo certbot certonly --nginx -d strike.perfecthold.online

# Test auto-renewal
sudo certbot renew --dry-run

# Auto-renew runs automatically via systemd timer
sudo systemctl status certbot.timer
```

---

## STEP 11: SETUP MONITORING & LOGS

```bash
# Create logs directory
mkdir -p /opt/strike/logs

# Setup log rotation for Docker containers
sudo tee /etc/logrotate.d/strike > /dev/null << 'EOF'
/var/lib/docker/containers/*/*.log {
  rotate 7
  daily
  compress
  delaycompress
  missingok
  copytruncate
  maxage 30
}
EOF

# Monitor logs in real-time (run in separate terminal)
cd /opt/strike
docker-compose -f docker-compose.prod.yml logs -f

# Or view specific service
docker-compose -f docker-compose.prod.yml logs -f api
docker-compose -f docker-compose.prod.yml logs -f frontend

# Check resource usage
docker stats
```

---

## STEP 12: BACKUP & RECOVERY SETUP

```bash
# Create backup directory
mkdir -p /opt/strike/backups
chmod 700 /opt/strike/backups

# Manual database backup
docker-compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U betting_user betting_db \
  > /opt/strike/backups/db_$(date +%Y%m%d_%H%M%S).sql

# Setup automated daily backups via cron
(crontab -l 2>/dev/null; echo "0 2 * * * cd /opt/strike && docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U betting_user betting_db > /opt/strike/backups/db_\$(date +\%Y\%m\%d).sql") | crontab -

# Verify backup
ls -lh /opt/strike/backups/
```

---

## VERIFICATION CHECKLIST

Run these commands to verify full deployment:

```bash
#!/bin/bash
# Deployment verification script

echo "=== DEPLOYMENT VERIFICATION ==="
echo ""

# 1. Check Docker services
echo "1. Docker Services:"
docker-compose -f docker-compose.prod.yml ps
echo ""

# 2. Check health endpoints
echo "2. Health Checks:"
curl -s http://localhost:8000/health | jq . && echo "✓ API healthy"
curl -s http://localhost:3000 > /dev/null && echo "✓ Frontend running"
docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready && echo "✓ Database ready"
docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping && echo "✓ Redis ready"
echo ""

# 3. Check nginx
echo "3. Nginx Status:"
sudo systemctl status nginx | grep "active"
echo ""

# 4. Check SSL
echo "4. SSL Certificate:"
sudo certbot certificates | grep strike.perfecthold.online
echo ""

# 5. Check cron jobs
echo "5. Cron Jobs:"
crontab -l | grep -E "strike|clv"
echo ""

# 6. Check logs for errors
echo "6. Recent Error Logs:"
docker-compose -f docker-compose.prod.yml logs --tail=20 api | grep -i error || echo "✓ No errors"
echo ""

echo "=== VERIFICATION COMPLETE ==="
```

---

## MONITORING & ONGOING MAINTENANCE

### Daily Checks

```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# Check logs for errors
docker-compose -f docker-compose.prod.yml logs --tail=50 | grep -i error

# Check disk space
df -h /opt/strike

# Check memory usage
free -h
```

### Weekly Tasks

```bash
# Backup database
docker-compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U betting_user betting_db > /opt/strike/backups/db_weekly.sql

# Review security
docker-compose -f docker-compose.prod.yml logs | grep -i "unauthorized\|failed"

# Update system patches
apt update && apt upgrade -y
```

### Monthly Tasks

```bash
# Review SSL certificate expiration
sudo certbot certificates

# Clean up old logs/backups
find /opt/strike/backups -mtime +30 -delete
find /opt/strike/logs -mtime +30 -delete

# Check disk usage
du -sh /opt/strike/*

# Update Docker images
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

---

## DEPLOYMENT SUMMARY

| Component | Status | URL | Port |
|-----------|--------|-----|------|
| Frontend | Docker | https://strike.perfecthold.online | 443 |
| API | Docker | https://strike.perfecthold.online/api | 443 |
| Database | PostgreSQL | localhost:5432 (internal) | 5432 |
| Cache | Redis | localhost:6379 (internal) | 6379 |
| Nginx | Reverse Proxy | https://strike.perfecthold.online | 80/443 |

---

## TROUBLESHOOTING

### Service won't start
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs api

# Restart service
docker-compose -f docker-compose.prod.yml restart api

# Full rebuild
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

### Database connection error
```bash
# Verify database is running
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# Check database exists
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U betting_user -l

# Restart database
docker-compose -f docker-compose.prod.yml restart postgres
```

### Nginx not proxying correctly
```bash
# Test nginx config
sudo nginx -t

# View nginx logs
sudo tail -f /var/log/nginx/error.log

# Reload nginx
sudo systemctl reload nginx
```

### SSL certificate issues
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate manually
sudo certbot renew

# Update nginx config with new cert paths if needed
sudo nginx -t && sudo systemctl reload nginx
```

---

## ROLLBACK PROCEDURE

If deployment fails, rollback to previous version:

```bash
# Stop all services
docker-compose -f docker-compose.prod.yml down

# Checkout previous version
git reset --hard HEAD~1

# Start services again
docker-compose -f docker-compose.prod.yml up -d

# Verify
docker-compose -f docker-compose.prod.yml ps
```

---

## IMPORTANT SECURITY REMINDERS

- [ ] Never commit .env to git (use .gitignore)
- [ ] Rotate SECRET_KEY and passwords every 90 days
- [ ] Enable firewall to block unnecessary ports:
  ```bash
  sudo ufw allow 22/tcp
  sudo ufw allow 80/tcp
  sudo ufw allow 443/tcp
  sudo ufw enable
  ```
- [ ] Monitor logs for unauthorized access
- [ ] Keep Docker images updated
- [ ] Regular database backups (automated)
- [ ] Monitor SSL certificate expiration (30 days before)

---

## SUCCESS INDICATORS

You'll know deployment is successful when:

✓ All 4 Docker services are "Up (healthy)"  
✓ API responds to /health endpoint with 200 status  
✓ Frontend loads on https://strike.perfecthold.online  
✓ HTTPS works (padlock in browser)  
✓ Nginx is proxying requests correctly  
✓ Database backups are being created  
✓ Cron jobs are running on schedule  
✓ No error logs in docker-compose logs  

---

**Next Steps:**
1. SSH into VPS and run steps 1-4
2. Start services (step 5)
3. Run health checks (step 6)
4. Configure nginx and SSL (steps 9-10)
5. Setup cron jobs and backups (steps 8, 12)
6. Run verification checklist above

**Questions?** Check Docker logs: `docker-compose -f docker-compose.prod.yml logs -f`
