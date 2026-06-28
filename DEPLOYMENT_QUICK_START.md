# Quick Start Deployment Guide
## strike.perfecthold.online

**TL;DR**: Run this to deploy to production VPS

---

## 1. PREPARE (5 minutes)

```bash
# On your local machine, ensure everything is committed to git:
cd /path/to/strike
git status  # Should show clean working directory
git push origin main
```

**Checklist:**
- [ ] DNS pointing to VPS IP
- [ ] SSH access confirmed: `ssh root@strike.perfecthold.online`
- [ ] VPS running Ubuntu 22.04 LTS
- [ ] Production secrets secured (NOT in git)

---

## 2. DEPLOY (10-15 minutes)

**SSH into your VPS:**

```bash
ssh root@strike.perfecthold.online
```

**Run automated deployment:**

```bash
# Download and run deployment script
cd /tmp
curl -fsSL https://raw.githubusercontent.com/yourusername/strike/main/deploy-vps.sh -o deploy-vps.sh
bash deploy-vps.sh
```

OR

**Manual deployment (step by step):**

```bash
# System setup
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh && bash get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose && chmod +x /usr/local/bin/docker-compose

# Install Nginx & Certbot
apt install -y nginx certbot python3-certbot-nginx

# Clone repository
mkdir -p /opt/strike && cd /opt/strike
git clone https://github.com/yourusername/strike.git .

# Create .env with production secrets
cp .env.example .env
nano .env  # Edit with real values

# Generate secrets (use these in .env):
# SECRET_KEY: openssl rand -hex 32
# POSTGRES_PASSWORD: openssl rand -base64 32
# REDIS_PASSWORD: openssl rand -base64 32

# Set permissions
chmod 600 .env

# Build and start services
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Wait for health
sleep 10
docker-compose -f docker-compose.prod.yml ps
```

---

## 3. VERIFY (5 minutes)

```bash
# All services healthy?
docker-compose -f docker-compose.prod.yml ps
# Expected: All services showing "Up (healthy)"

# API responding?
curl -s http://localhost:8000/health | jq .

# Frontend running?
curl -s http://localhost:3000 | head -20

# Database ready?
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# Redis ready?
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
```

**Expected Results:**
- [ ] PostgreSQL: `accepting connections`
- [ ] Redis: `PONG`
- [ ] API: `{"status": "ok"}` (or similar 200 response)
- [ ] Frontend: HTML content

---

## 4. CONFIGURE NGINX (5 minutes)

```bash
# Create nginx config
cat > /etc/nginx/sites-available/strike << 'EOF'
upstream api {
  server localhost:8000;
}

upstream web {
  server localhost:3000;
}

server {
  listen 80;
  server_name strike.perfecthold.online;
  return 301 https://$server_name$request_uri;
}

server {
  listen 443 ssl http2;
  server_name strike.perfecthold.online;

  ssl_protocols TLSv1.2 TLSv1.3;
  ssl_ciphers HIGH:!aNULL:!MD5;

  location /api/ {
    proxy_pass http://api;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }

  location / {
    proxy_pass http://web;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/strike /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and reload
nginx -t && systemctl reload nginx
```

---

## 5. SETUP SSL (5 minutes)

```bash
# Get SSL certificate from Let's Encrypt
certbot certonly --nginx -d strike.perfecthold.online

# Auto-renewal test
certbot renew --dry-run

# Verify it worked
curl -vvv https://strike.perfecthold.online/health
# Should have valid SSL certificate (no warnings)
```

---

## 6. SETUP CRON JOBS (2 minutes)

```bash
cd /opt/strike/deploy

# Install cron jobs for CLV tracking
bash cron-setup.sh install

# Verify
bash cron-setup.sh list
```

---

## 7. SETUP MONITORING (2 minutes)

```bash
cd /opt/strike

# Create logs directory
mkdir -p logs

# Add monitoring cron job (runs every 5 minutes)
(crontab -l 2>/dev/null || true; echo "*/5 * * * * cd /opt/strike && bash deploy/monitoring.sh >> logs/monitoring.log 2>&1") | crontab -

# Add daily backup job
(crontab -l 2>/dev/null || true; echo "0 2 * * * cd /opt/strike && docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U betting_user betting_db > backups/db_\$(date +\%Y\%m\%d).sql") | crontab -

# Verify
crontab -l | grep strike
```

---

## 8. TEST EVERYTHING (5 minutes)

```bash
#!/bin/bash
# Quick test script

echo "=== FINAL VERIFICATION ==="

# Check services
echo "1. Services:"
docker-compose -f /opt/strike/docker-compose.prod.yml ps

# Check URLs
echo ""
echo "2. Testing URLs:"
echo -n "API Health: "
curl -s http://localhost:8000/health | jq -r '.status // "ERROR"'

echo -n "Frontend: "
curl -s http://localhost:3000 | head -1 | grep -q "html" && echo "OK" || echo "ERROR"

# Check database
echo ""
echo "3. Database:"
docker-compose -f /opt/strike/docker-compose.prod.yml exec postgres pg_isready

# Check SSL
echo ""
echo "4. SSL Certificate:"
echo | openssl s_client -servername strike.perfecthold.online -connect localhost:443 2>/dev/null | grep -E "subject=|Not After"

echo ""
echo "=== VERIFICATION COMPLETE ==="
```

Run it:
```bash
bash /opt/strike/test-deployment.sh
```

---

## DEPLOYMENT COMPLETE! ✓

Your application is now live at:
- **Frontend**: https://strike.perfecthold.online
- **API**: https://strike.perfecthold.online/api
- **API Docs**: https://strike.perfecthold.online/api/docs
- **Health Check**: https://strike.perfecthold.online/api/health

---

## POST-DEPLOYMENT

### Daily Checks (1 minute)

```bash
# Status
docker-compose -f /opt/strike/docker-compose.prod.yml ps

# Health
curl https://strike.perfecthold.online/api/health

# Errors
docker-compose -f /opt/strike/docker-compose.prod.yml logs | grep ERROR
```

### Weekly Tasks (15 minutes)

```bash
# Review logs
docker-compose -f /opt/strike/docker-compose.prod.yml logs --tail=500

# Check disk space
du -sh /opt/strike/backups
df -h /opt/strike

# Verify SSL cert
sudo certbot certificates
```

### Monthly Tasks (30 minutes)

```bash
# Update Docker images
docker-compose -f /opt/strike/docker-compose.prod.yml pull

# Restart services
docker-compose -f /opt/strike/docker-compose.prod.yml up -d

# Apply security patches
apt update && apt upgrade -y

# Clean old backups
find /opt/strike/backups -mtime +30 -delete
```

---

## TROUBLESHOOTING

### Service won't start?

```bash
cd /opt/strike

# Check logs
docker-compose -f docker-compose.prod.yml logs api

# Restart
docker-compose -f docker-compose.prod.yml restart api

# Full rebuild if needed
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

### Can't connect to database?

```bash
cd /opt/strike

# Check status
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# Restart database
docker-compose -f docker-compose.prod.yml restart postgres

# Check connectivity
docker-compose -f docker-compose.prod.yml exec api python -c "from sqlalchemy import create_engine; engine = create_engine('postgresql://...'); print('Connected!')"
```

### HTTPS not working?

```bash
# Check certificate
sudo certbot certificates | grep strike.perfecthold.online

# Verify nginx config
sudo nginx -t

# Check nginx logs
sudo tail -f /var/log/nginx/error.log

# Reload nginx
sudo systemctl reload nginx
```

### Out of disk space?

```bash
# Check usage
df -h

# Find large files
du -sh /opt/strike/* | sort -rh

# Clean up
rm -rf /opt/strike/logs/*.log.old  # Old logs
find /opt/strike/backups -mtime +30 -delete  # Old backups
docker system prune -a  # Docker cleanup (careful!)
```

---

## IMPORTANT FILES

- `.env` - Production secrets (NEVER commit, keep safe)
- `docker-compose.prod.yml` - Production configuration
- `PRODUCTION_DEPLOYMENT_VPS.md` - Full deployment guide
- `DEPLOYMENT_VERIFICATION_CHECKLIST.md` - Detailed checklist
- `MONITORING_AND_MAINTENANCE.md` - Ongoing operations
- `deploy-vps.sh` - Automated deployment script
- `deploy/cron-setup.sh` - Cron job installer
- `deploy/monitoring.sh` - Health monitoring

---

## SUPPORT

**Quick status check:**
```bash
cd /opt/strike
docker-compose -f docker-compose.prod.yml ps
curl https://strike.perfecthold.online/api/health
```

**View logs:**
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

**Check specific service:**
```bash
docker-compose -f docker-compose.prod.yml logs api
docker-compose -f docker-compose.prod.yml logs frontend
```

**Full documentation:** See `PRODUCTION_DEPLOYMENT_VPS.md`

---

## SECURITY REMINDERS

- [ ] Never commit `.env` to git
- [ ] Keep `.env` permissions as 600 (owner read/write only)
- [ ] Rotate `SECRET_KEY` every 90 days
- [ ] Rotate database password every 90 days
- [ ] Keep Docker images updated
- [ ] Monitor SSL certificate expiration
- [ ] Regular database backups (automated)
- [ ] Monitor logs for unauthorized access

---

**Deployment Status**: Ready for Production  
**Last Updated**: June 28, 2026  
**Version**: 1.0.0

---

**Your deployment is now running in production! 🚀**

Questions? Check the full guide: `PRODUCTION_DEPLOYMENT_VPS.md`
