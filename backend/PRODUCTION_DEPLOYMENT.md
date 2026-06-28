# Production Deployment Guide

Complete guide for deploying the Betting Framework Backend to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Setup](#database-setup)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Middleware & Security](#middleware--security)
7. [Health Checks](#health-checks)
8. [Running the Application](#running-the-application)
9. [Monitoring](#monitoring)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- Python 3.10+
- PostgreSQL 13+
- Redis 6+ (optional, for caching)
- Docker & Docker Compose (recommended)
- 2GB+ RAM
- 10GB+ disk space

### Required Credentials

Before deployment, ensure you have:

- PostgreSQL database credentials
- API keys for:
  - Odds API (The Odds API)
  - Polymarket API
  - Kalshi API
  - FRED API (Federal Reserve Economic Data)
  - Alpha Vantage API
  - Finnhub API
- JWT secret key
- SMTP credentials (optional, for alerts)
- Sentry DSN (optional, for error tracking)

## Environment Setup

### 1. Clone Repository

```bash
cd /path/to/stike/backend
```

### 2. Create Virtual Environment

```bash
# Using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Using conda
conda create -n betting-framework python=3.10
conda activate betting-framework
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Database Setup

### 1. PostgreSQL Configuration

```bash
# Create database and user
psql -U postgres

CREATE USER betting_user WITH PASSWORD 'secure_password_here';
CREATE DATABASE betting_db OWNER betting_user;

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE betting_db TO betting_user;

# Exit psql
\q
```

### 2. Initialize Database Schema

```bash
# Using Python script
python init_db.py

# Or with options
python init_db.py --drop-all  # Reset schema (WARNING: loses data)
python init_db.py --seed       # Add test data
python init_db.py --verify     # Verify connection
```

### 3. Verify Database

```bash
psql -U betting_user -d betting_db -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';"

# Should return the number of created tables
```

## Installation

### 1. Install System Dependencies

```bash
# Ubuntu/Debian
sudo apt-get install python3-dev postgresql postgresql-contrib redis-server

# macOS
brew install python postgresql redis

# Windows
# Use PostgreSQL installer and WSL for Unix tools
```

### 2. Create Application Directory Structure

```bash
mkdir -p /var/www/betting-framework
mkdir -p /var/log/betting_framework
mkdir -p /var/lib/betting_framework/models

# Set permissions
sudo chown -R app_user:app_user /var/www/betting-framework
sudo chown -R app_user:app_user /var/log/betting_framework
```

### 3. Deploy Application Files

```bash
cp -r * /var/www/betting-framework/
cd /var/www/betting-framework
```

## Configuration

### 1. Create Environment File

```bash
cp .env.production.example .env.production

# Edit with production values
nano .env.production
```

### 2. Key Configuration Variables

```bash
# Application
ENVIRONMENT=production
DEBUG=false
WORKERS=4

# Database
DATABASE_URL=postgresql://betting_user:password@localhost:5432/betting_db
DATABASE_POOL_SIZE=20

# Security
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# APIs
ODDS_API_KEY=your_key
POLYMARKET_KEY=your_key
KALSHI_API_KEY=your_key
FRED_API_KEY=your_key

# Rate Limiting
ENABLE_RATE_LIMITING=true
RATE_LIMIT_PER_MINUTE=100

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/betting_framework/app.log

# Cache
ENABLE_CACHE=true
REDIS_URL=redis://localhost:6379/0
```

### 3. Generate Secure Secret Key

```bash
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
```

## Middleware & Security

### 1. Middleware Stack (in application)

The application includes:

- **LoggingMiddleware**: Logs all HTTP requests/responses
- **ErrorHandlingMiddleware**: Catches and handles exceptions
- **RateLimitMiddleware**: Rate limiting per IP address
- **RiskLimitsMiddleware**: Enforces bet sizing limits
- **CORSMiddleware**: Cross-origin request handling
- **GZIPMiddleware**: Response compression

### 2. Security Configuration

```python
# In main.py - already configured:
- CORS restricted to allowed origins
- Rate limiting enabled
- Error details hidden in production
- Logging middleware for audit trail
```

### 3. CORS Configuration

Update `CORS_ORIGINS` in `.env.production`:

```bash
CORS_ORIGINS=https://app.example.com,https://api.example.com
```

## Health Checks

### 1. Health Check Endpoints

The application provides multiple health check endpoints:

```bash
# Full health check
curl http://localhost:8000/health

# Database only
curl http://localhost:8000/health/database

# Kubernetes readiness probe
curl http://localhost:8000/health/ready

# Kubernetes liveness probe
curl http://localhost:8000/health/live
```

### 2. Example Health Response

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:45.123456",
  "version": "1.0.0",
  "environment": "production",
  "components": {
    "database": {"status": "ok", "type": "PostgreSQL", "table_count": 25},
    "apis": {
      "odds_api": {"configured": true, "status": "ready"},
      "polymarket": {"configured": true, "status": "ready"},
      "kalshi": {"configured": true, "status": "ready"},
      "fred": {"configured": true, "status": "ready"}
    },
    "cache": {"enabled": true, "status": "ok", "provider": "Redis"}
  },
  "verticals": {
    "mlb": {"status": "operational"},
    "tennis": {"status": "operational"},
    "cricket": {"status": "operational"},
    "horse": {"status": "operational"},
    "hockey": {"status": "operational"}
  },
  "summary": {
    "database_ok": true,
    "apis_configured": 4,
    "verticals_enabled": 5,
    "all_critical_ok": true
  }
}
```

### 3. Monitoring Health Checks

```bash
# Check health every 30 seconds
watch -n 30 'curl -s http://localhost:8000/health | jq .'

# Log health checks
*/5 * * * * curl -s http://localhost:8000/health >> /var/log/betting_framework/health.log 2>&1
```

## Running the Application

### 1. Using Uvicorn (Development/Testing)

```bash
# Single worker
uvicorn main:app --host 0.0.0.0 --port 8000

# With reload (development only)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Using Gunicorn (Production)

```bash
# Install gunicorn
pip install gunicorn

# Start with gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 main:app

# With custom config
gunicorn -c gunicorn.conf.py main:app
```

### 3. Gunicorn Configuration (gunicorn.conf.py)

```python
import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000

# Logging
accesslog = "/var/log/betting_framework/access.log"
errorlog = "/var/log/betting_framework/error.log"
loglevel = "info"

# Process naming
proc_name = "betting-framework"

# Server mechanics
daemon = False
pidfile = "/var/run/betting_framework.pid"
timeout = 120
keepalive = 5
```

### 4. Using Docker

```bash
# Build image
docker build -t betting-framework:1.0.0 .

# Run container
docker run -d \
  --name betting-framework \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://..." \
  -e SECRET_KEY="..." \
  -v /var/log/betting_framework:/app/logs \
  betting-framework:1.0.0
```

### 5. Using Docker Compose

```bash
# Start services
docker-compose -f docker-compose.yml up -d

# View logs
docker-compose logs -f betting-framework

# Stop services
docker-compose down
```

### 6. Using Systemd Service

Create `/etc/systemd/system/betting-framework.service`:

```ini
[Unit]
Description=Betting Framework Backend
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=app_user
WorkingDirectory=/var/www/betting-framework
Environment="PATH=/var/www/betting-framework/venv/bin"

# Use gunicorn with uvicorn worker
ExecStart=/var/www/betting-framework/venv/bin/gunicorn \
    -w 4 \
    -b 127.0.0.1:8000 \
    --worker-class uvicorn.workers.UvicornWorker \
    main:app

Restart=on-failure
RestartSec=10
StandardOutput=append:/var/log/betting_framework/app.log
StandardError=append:/var/log/betting_framework/error.log

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable betting-framework
sudo systemctl start betting-framework
sudo systemctl status betting-framework
```

## Monitoring

### 1. Application Logs

```bash
# View logs
tail -f /var/log/betting_framework/app.log

# Search logs
grep ERROR /var/log/betting_framework/app.log

# Log rotation (add to logrotate)
/var/log/betting_framework/*.log {
    daily
    rotate 10
    compress
    delaycompress
    notifempty
    create 0640 app_user app_user
    sharedscripts
    postrotate
        systemctl reload betting-framework > /dev/null 2>&1 || true
    endscript
}
```

### 2. Database Monitoring

```bash
# Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

# Check connections
SELECT count(*) as connections FROM pg_stat_activity;

# Check slow queries
SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;
```

### 3. Performance Metrics

Monitor these metrics:

- Request latency (p50, p95, p99)
- Error rate
- Database query time
- Cache hit rate
- Memory usage
- CPU usage
- Disk usage

### 4. Sentry Integration

```bash
# Set in .env.production
SENTRY_DSN=https://your_key@sentry.io/project_id

# Application will automatically track errors
```

### 5. Prometheus Metrics (Optional)

```bash
# Available at http://localhost:8001/metrics
# Configure in .env.production
ENABLE_METRICS=true
METRICS_PORT=8001
```

## Troubleshooting

### Database Connection Issues

```bash
# Test connection
psql -U betting_user -d betting_db -c "SELECT 1;"

# Check credentials in .env
grep DATABASE_URL .env.production

# Verify PostgreSQL is running
sudo systemctl status postgresql

# Check database logs
sudo tail -f /var/log/postgresql/postgresql.log
```

### API Key Issues

```bash
# Verify APIs are configured
python -c "from config import settings; print(settings.ODDS_API_KEY)"

# Test API connectivity
curl -H "Authorization: Bearer KEY" https://api.the-odds-api.com/v4/sports
```

### Memory Issues

```bash
# Monitor memory usage
watch -n 1 'ps aux | grep gunicorn'

# Increase worker memory limit
# Adjust DATABASE_POOL_SIZE and WORKERS in .env

# Clear cache if enabled
redis-cli FLUSHDB
```

### High Latency

```bash
# Check slow database queries
# Enable query logging in PostgreSQL

# Check network connectivity
ping api.the-odds-api.com

# Monitor cache hit rate
redis-cli INFO stats
```

### Rate Limiting Issues

```bash
# Adjust in .env.production
RATE_LIMIT_PER_MINUTE=150  # Increase limit

# Or disable for testing
ENABLE_RATE_LIMITING=false
```

## Verification Checklist

After deployment, verify:

- [ ] Environment file created with production values
- [ ] Database initialized and schema created
- [ ] All API keys configured
- [ ] Health check endpoint returns "healthy"
- [ ] Application starts without errors
- [ ] Database connectivity verified
- [ ] Logging working (check log files)
- [ ] Rate limiting working
- [ ] CORS configured correctly
- [ ] External APIs responding
- [ ] Cache initialized (if Redis enabled)
- [ ] SSL/TLS configured (recommended)
- [ ] Backup strategy in place
- [ ] Monitoring configured
- [ ] Load balancer configured (if applicable)

## Next Steps

1. **Set up reverse proxy** (Nginx/Apache):
   - SSL/TLS termination
   - Load balancing
   - Compression

2. **Configure monitoring**:
   - Set up Prometheus for metrics
   - Configure alerts in Sentry
   - Monitor health check endpoint

3. **Set up backup strategy**:
   - Daily database backups
   - Model file backups
   - Configuration backups

4. **Performance tuning**:
   - Adjust worker count based on CPU cores
   - Optimize database pool size
   - Enable caching for frequently accessed data

5. **Security hardening**:
   - Keep dependencies updated
   - Enable firewall rules
   - Implement API rate limiting
   - Set up DDoS protection

## Support

For issues or questions:
1. Check logs: `/var/log/betting_framework/`
2. Run health checks: `curl http://localhost:8000/health`
3. Review this guide's troubleshooting section
4. Check component status via health endpoints
