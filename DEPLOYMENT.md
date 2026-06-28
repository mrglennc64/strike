# Betting Framework - Complete Deployment Guide

## Overview

This guide covers deploying the Betting Framework application to production using:
- **Frontend**: Vercel (recommended for React apps)
- **Backend**: Railway or Render (PostgreSQL + FastAPI)
- **Domain**: betting-framework.ai (recommended) or your custom domain

**Total Cost Estimate (Monthly)**:
- Vercel Frontend: $20/month (with generous free tier for low traffic)
- Railway Backend: $15-50/month (PostgreSQL + API)
- Domain: $12-15/year

---

## Option 1: Railway (Recommended - Simplest)

Railway is ideal for full-stack deployment with built-in PostgreSQL, Redis, and easy scaling.

### 1. Create Railway Project

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Create new project
railway init

# Link project
railway link
```

### 2. Add Services

```bash
# Add PostgreSQL database
railway add

# Add Redis cache
railway add

# Add backend environment variables
railway variables
```

Set these environment variables in Railway dashboard:

```
DATABASE_URL=postgresql://[user]:[pass]@[host]:5432/betting_db
SECRET_KEY=[generate strong random key]
DEBUG=False
MAX_SINGLE_BET_FRACTION=0.05
MAX_DAILY_LOSS_FRACTION=0.10
```

### 3. Deploy Backend

```bash
cd backend

# Create Procfile
echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy
railway up
```

### 4. Verify Deployment

```bash
# Check logs
railway logs

# Test health endpoint
curl https://betting-framework-api.up.railway.app/health
```

---

## Option 2: Render (Docker-based Alternative)

### 1. Connect Repository

1. Go to https://dashboard.render.com
2. Click "New +"
3. Select "Web Service"
4. Connect your GitHub repository
5. Select `betting-framework` repo

### 2. Configure Service

**Backend Service Settings:**

```
Name: betting-framework-api
Region: us-east (or closest)
Runtime: Docker
Build Command: (leave empty, uses Dockerfile)
Start Command: (leave empty, uses Dockerfile)
```

**Environment Variables:**

```
DATABASE_URL=postgresql://[user]:[pass]@[host]:5432/betting_db
SECRET_KEY=[strong random key]
DEBUG=False
```

### 3. Add PostgreSQL Database

1. Click "New +"
2. Select "PostgreSQL"
3. Configure:
   - Name: `betting-framework-db`
   - Database: `betting_db`
   - User: `betting_user`
   - Set strong password

4. Copy `DATABASE_URL` from PostgreSQL service
5. Add to backend service environment

### 4. Deploy

1. Select branch: `main`
2. Click "Deploy"
3. Monitor logs for success

---

## Option 3: Docker Compose (Self-Hosted / VPS)

For DigitalOcean, AWS EC2, Linode, or any Linux server.

### 1. Provision Server

**Minimum specs:**
- 2GB RAM
- 20GB SSD
- Ubuntu 22.04 LTS

**Recommended providers:**
- DigitalOcean (Droplet, $6/month)
- Linode ($6/month)
- Vultr ($3.50/month)

### 2. Setup Server

```bash
# SSH into server
ssh root@your_server_ip

# Update system
apt update && apt upgrade -y

# Install Docker & Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Add user to docker group
usermod -aG docker $USER

# Install docker-compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create app directory
mkdir -p /opt/betting-framework
cd /opt/betting-framework
```

### 3. Clone Repository

```bash
git clone https://github.com/yourusername/betting-framework.git .
```

### 4. Configure Environment

```bash
cp .env.example .env

# Edit .env with production values
nano .env
```

**Critical values to set:**

```
POSTGRES_PASSWORD=VERY_STRONG_PASSWORD_MIN_32_CHARS
SECRET_KEY=VERY_LONG_RANDOM_STRING_MIN_32_CHARS
DEBUG=False
```

Generate strong keys:

```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate POSTGRES_PASSWORD
openssl rand -base64 32
```

### 5. Deploy with Docker Compose

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f api

# Verify API health
curl http://localhost:8000/health
```

### 6. Setup SSL Certificate (Let's Encrypt)

```bash
# Install certbot
apt install certbot python3-certbot-nginx -y

# Get certificate
certbot certonly --standalone -d betting-framework.ai

# Auto-renew
certbot renew --dry-run
```

### 7. Setup Nginx Reverse Proxy

```bash
apt install nginx -y

# Create config
cat > /etc/nginx/sites-available/betting-framework << 'EOF'
upstream api {
  server api:8000;
}

upstream web {
  server frontend:3000;
}

server {
  listen 80;
  server_name betting-framework.ai;
  
  # Redirect to HTTPS
  return 301 https://$server_name$request_uri;
}

server {
  listen 443 ssl http2;
  server_name betting-framework.ai;
  
  ssl_certificate /etc/letsencrypt/live/betting-framework.ai/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/betting-framework.ai/privkey.pem;
  
  # API routes
  location /api/ {
    proxy_pass http://api;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
  
  # Frontend
  location / {
    proxy_pass http://web;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }
}
EOF

# Enable site
ln -s /etc/nginx/sites-available/betting-framework /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default

# Test and reload
nginx -t
systemctl reload nginx
```

### 8. Setup Monitoring

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Monitor resource usage
docker stats

# Setup log rotation
cat > /etc/logrotate.d/betting-framework << 'EOF'
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
```

---

## Option 4: AWS ECS (Enterprise)

### 1. Create ECR Repositories

```bash
aws ecr create-repository --repository-name betting-framework-api
aws ecr create-repository --repository-name betting-framework-web
```

### 2. Build and Push Images

```bash
# Build backend
docker build -t betting-framework-api ./backend
docker tag betting-framework-api:latest \
  ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/betting-framework-api:latest
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/betting-framework-api:latest

# Build frontend
docker build -t betting-framework-web ./frontend
docker tag betting-framework-web:latest \
  ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/betting-framework-web:latest
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/betting-framework-web:latest
```

### 3. Create RDS PostgreSQL

```bash
aws rds create-db-instance \
  --db-instance-identifier betting-framework-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username betting_user \
  --master-user-password YOUR_STRONG_PASSWORD \
  --allocated-storage 20 \
  --backup-retention-period 7
```

### 4. Create ECS Cluster

```bash
aws ecs create-cluster --cluster-name betting-framework

# Register task definitions
aws ecs register-task-definition --cli-input-json file://task-definition-api.json
aws ecs register-task-definition --cli-input-json file://task-definition-web.json

# Create services
aws ecs create-service --cluster betting-framework \
  --service-name api \
  --task-definition betting-framework-api \
  --desired-count 2
```

---

## Vercel Frontend Deployment

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/betting-framework.git
git push -u origin main
```

### 2. Import to Vercel

1. Go to https://vercel.com/import
2. Select GitHub account
3. Find `betting-framework` repository
4. Click "Import"

### 3. Configure Environment

In Vercel project settings:

```
VITE_API_URL=https://betting-framework-api.up.railway.app
VITE_APP_NAME=Betting Framework
```

### 4. Deploy

1. Click "Deploy"
2. Vercel builds and deploys automatically
3. Get your Vercel URL: `https://betting-framework.vercel.app`

---

## Domain Setup

### Register Domain

**Recommended registrars:**
- Google Domains ($10/year)
- Namecheap ($8-12/year)
- Route 53 ($0.50/query)

**Recommended domain names:**

1. **betting-framework.ai** (preferred, memorable, clear intent)
2. **edge-finder.ai** (if framework needs branding)
3. **kelly-bet.com** (descriptive)
4. **edge-optimizer.io** (technical focus)

### Configure DNS

**For Vercel:**

1. Add domain in Vercel dashboard
2. Vercel provides nameservers
3. Update domain registrar to use Vercel nameservers
4. Wait 24-48 hours for propagation

**For Railway/Docker:**

1. Get public IP address
2. Create A record pointing to IP
3. Create CNAME for `api.` subdomain (if separating)

**Example DNS Configuration:**

```
Type    Name           Value
A       @              1.2.3.4 (server IP)
CNAME   www            betting-framework.vercel.app
CNAME   api            betting-framework-api.up.railway.app
TXT     @              v=spf1 include:sendgrid.net ~all (email)
```

---

## GitHub Actions CI/CD

### 1. Create Secrets

In GitHub repository Settings > Secrets:

```
RAILWAY_TOKEN
VERCEL_TOKEN
VERCEL_ORG_ID
VERCEL_PROJECT_ID
POSTGRES_PASSWORD
SECRET_KEY
```

### 2. Workflows Run Automatically

- **On PR**: Run tests, type checks, builds
- **On Merge to Main**: Deploy to production

Check `.github/workflows/` for workflow definitions.

---

## Monitoring & Logs

### Railway Monitoring

```bash
# View logs
railway logs -s api

# Monitor metrics
railway status
```

### Docker Logs

```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f api

# Follow output
docker-compose -f docker-compose.prod.yml logs -f --tail=100
```

### Setup External Monitoring

**Option 1: Sentry (Error Tracking)**

1. Create account at https://sentry.io
2. Create Django project
3. Add `SENTRY_DSN` to environment

**Option 2: Datadog (APM)**

1. Create account at https://datadog.com
2. Copy API key
3. Install Datadog agent

**Option 3: CloudWatch (AWS)**

Configure in Docker containers to send logs to CloudWatch.

---

## Backup & Recovery

### Automated Backups

**Railway:** Automatic daily backups (7 days retention)

**Docker/Render:** Enable backup

```bash
# Create manual backup
pg_dump postgresql://user:pass@host:5432/betting_db > backup.sql

# Restore from backup
psql postgresql://user:pass@host:5432/betting_db < backup.sql
```

### Database Backup Strategy

```bash
# Weekly backup to S3
aws s3 cp backup.sql s3://betting-framework-backups/db-$(date +%Y%m%d).sql

# Keep 30-day retention
aws s3 ls s3://betting-framework-backups/ | grep -oE '[^/]*/?$' | sort | head -n -4 | xargs -I {} aws s3 rm s3://betting-framework-backups/{}
```

---

## Performance Optimization

### 1. Enable Caching

**Frontend:**
- Vercel CDN caches static assets globally
- SWCache assets in browser

**Backend:**
- Redis caches hot queries
- Set cache headers on API responses

### 2. Database Optimization

```sql
-- Create indexes for common queries
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_predictions_event_id ON predictions(event_id);
CREATE INDEX idx_bets_status ON bets(status);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
```

### 3. API Rate Limiting

See `backend/middleware/risk_limits.py` for rate limiting configuration.

### 4. CDN for Static Assets

**Vercel** handles this automatically.

**Self-hosted:** Use CloudFront or CloudFlare.

---

## Security Checklist

- [ ] Change default credentials
- [ ] Set `DEBUG=False` in production
- [ ] Use strong `SECRET_KEY` (min 32 chars)
- [ ] Enable HTTPS/SSL (Let's Encrypt)
- [ ] Setup firewall rules
- [ ] Enable database backups
- [ ] Configure CORS whitelist
- [ ] Setup API rate limiting
- [ ] Enable database encryption at rest
- [ ] Rotate secrets monthly
- [ ] Monitor audit logs
- [ ] Setup intrusion detection

---

## Troubleshooting

### API won't start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs api

# Verify database connection
docker-compose -f docker-compose.prod.yml exec api python -c "from database import engine; engine.connect()"

# Check environment variables
docker-compose -f docker-compose.prod.yml exec api env | grep DATABASE
```

### Database connection refused

```bash
# Verify postgres is running
docker-compose -f docker-compose.prod.yml ps

# Check database health
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# Restart database
docker-compose -f docker-compose.prod.yml restart postgres
```

### Frontend won't load

```bash
# Check frontend logs
docker-compose -f docker-compose.prod.yml logs frontend

# Verify API connectivity
docker-compose -f docker-compose.prod.yml exec frontend curl http://api:8000/health
```

### DNS not resolving

```bash
# Check DNS propagation
nslookup betting-framework.ai
dig betting-framework.ai

# Verify nameservers
whois betting-framework.ai
```

---

## Cost Estimate & Optimization

### Development ($0/month)

- localhost development
- Free tier databases

### Production (Recommended - Railway)

| Component | Service | Cost/Month | Notes |
|-----------|---------|-----------|-------|
| Frontend | Vercel | $0-20 | Free tier covers most apps |
| API | Railway | $15-50 | Scales with usage |
| Database | Railway | $15-30 | PostgreSQL included |
| Domain | Route53 | $1 | Annual domain extra |
| **Total** | | **$31-101** | Highly scalable |

### Cost Optimization Tips

1. Use free tier services when possible
2. Enable auto-scaling (pay only for what you use)
3. Archive old audit logs to S3
4. Use Vercel for frontend (CDN included)
5. Use Railway for backend (built-in scaling)

---

## Next Steps

1. **Choose deployment option** (Railway recommended for fastest setup)
2. **Register domain** (betting-framework.ai or custom)
3. **Set up secrets** in GitHub
4. **Deploy** backend first, then frontend
5. **Test** all endpoints
6. **Monitor** logs and metrics
7. **Setup backups** and alerts

---

## Support

For deployment issues:

1. Check GitHub Workflows logs
2. Review service-specific documentation
3. Check `.github/workflows/` for CI/CD config
4. Review Docker logs: `docker-compose -f docker-compose.prod.yml logs -f`

---

**Last Updated**: June 28, 2026
**Version**: 1.0.0
