# Quick Start - Production Deployment

Fast track to get the Betting Framework Backend running in production.

## 1. Prerequisites (5 minutes)

```bash
# Install system dependencies
# macOS
brew install postgresql redis python@3.10

# Ubuntu/Debian
sudo apt-get install python3.10 postgresql redis-server postgresql-contrib

# Windows: Use WSL or Docker
```

## 2. Clone & Setup (5 minutes)

```bash
cd stike/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 3. Database (5 minutes)

```bash
# Create PostgreSQL database
psql -U postgres
> CREATE USER betting_user WITH PASSWORD 'secure_password_here';
> CREATE DATABASE betting_db OWNER betting_user;
> \q

# Initialize schema
python init_db.py

# Verify (should return table count)
psql -U betting_user -d betting_db -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';"
```

## 4. Configure (5 minutes)

```bash
# Create production environment file
cp .env.production.example .env.production

# Edit with your values (CRITICAL)
nano .env.production

# Required settings:
# - ENVIRONMENT=production
# - SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">
# - DATABASE_URL=postgresql://betting_user:password@localhost:5432/betting_db
# - ODDS_API_KEY=<your key>
```

## 5. Run (2 minutes)

### Option A: Development (Single Process)
```bash
python main.py
# API running at http://localhost:8000
```

### Option B: Production (Gunicorn)
```bash
gunicorn -w 4 -b 0.0.0.0:8000 --worker-class uvicorn.workers.UvicornWorker main:app
```

### Option C: Docker (Full Stack)
```bash
# Build
docker build -f Dockerfile.production -t betting-framework:1.0.0 .

# Run with compose (includes PostgreSQL, Redis, Nginx)
docker-compose -f docker-compose.production.yml up -d
```

## 6. Verify (2 minutes)

```bash
# Check health (all components)
curl http://localhost:8000/health | jq .

# Database connectivity
curl http://localhost:8000/health/database

# API documentation
open http://localhost:8000/docs

# Kubernetes readiness
curl http://localhost:8000/health/ready
```

## Routes by Category

### Core Betting (8 routes)
- `POST /api/auth/login` - Login
- `POST /api/auth/register` - Register
- `GET /api/bankroll` - Account balance
- `POST /api/predictions` - Submit prediction
- `POST /api/kelly` - Calculate Kelly
- `POST /api/place-bet` - Place bet
- `GET /api/positions` - View positions
- `POST /api/settle` - Settle bet

### Predictors (4 routes)
- `POST /api/verticals/mlb` - MLB prediction
- `POST /api/verticals/economics` - Fed/Econ prediction
- `POST /api/verticals/earnings` - Earnings prediction
- `GET /api/verticals` - All verticals

### Advanced (4 routes)
- `POST /api/clv/record-bet` - Record CLV bet
- `GET /api/clv/analysis` - CLV analysis
- `POST /api/portfolio/simulate` - Simulate portfolio
- `GET /api/audit-log` - Audit trail

### Health (4 routes)
- `GET /health` - Full system health
- `GET /health/database` - DB check
- `GET /health/ready` - Readiness probe
- `GET /health/live` - Liveness probe

## Environment Variables (Critical)

```bash
# Application
ENVIRONMENT=production
DEBUG=false
WORKERS=4

# Database (REQUIRED)
DATABASE_URL=postgresql://betting_user:password@localhost:5432/betting_db

# Security (REQUIRED - generate new!)
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">

# APIs (Get free keys)
ODDS_API_KEY=<https://the-odds-api.com>
POLYMARKET_KEY=<optional>
FRED_API_KEY=<https://fred.stlouisfed.org>

# Middleware
ENABLE_RATE_LIMITING=true
RATE_LIMIT_PER_MINUTE=100

# Cache (optional)
ENABLE_CACHE=true
REDIS_URL=redis://localhost:6379/0
```

## Monitoring

```bash
# Watch health in real-time
watch -n 5 'curl -s http://localhost:8000/health | jq .'

# View application logs
tail -f logs/app.log

# Check database
psql -U betting_user -d betting_db -c "SELECT COUNT(*) as bet_count FROM bets;"

# Monitor with curl loop
for i in {1..10}; do curl -s http://localhost:8000/health | jq .status; sleep 5; done
```

## Database Tables (Quick Reference)

```sql
-- Core tables
users, bankrolls, predictions, bets, positions, settlements

-- Prediction tables
earnings_predictions, earnings_history, economics_predictions

-- CLV tables
clv_bets, line_captures

-- Portfolio tables
portfolio_allocations, risk_limits_history

-- Audit
audit_logs

-- Views
user_performance, recent_bets
```

## Docker Commands

```bash
# Start full production stack
docker-compose -f docker-compose.production.yml up -d

# View logs
docker-compose -f docker-compose.production.yml logs -f api

# Stop everything
docker-compose -f docker-compose.production.yml down

# Rebuild image
docker-compose -f docker-compose.production.yml build --no-cache api
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Database connection error | Check DATABASE_URL in .env.production |
| Rate limit exceeded | Check RATE_LIMIT_PER_MINUTE setting |
| 500 errors | Check logs: `tail -f logs/app.log` |
| Health check fails | Run `curl http://localhost:8000/health/database` |
| Port already in use | Change PORT in .env or kill process: `lsof -i :8000` |
| Missing API keys | Set in .env, default to "not_configured" in health check |

## Performance Tuning

```bash
# Adjust workers (rule: 2*cpu_cores + 1)
WORKERS=9  # For 4-core CPU

# Adjust database pool
DATABASE_POOL_SIZE=30  # For high load

# Adjust rate limiting
RATE_LIMIT_PER_MINUTE=200  # For production load

# Enable caching
ENABLE_CACHE=true
REDIS_URL=redis://your-redis:6379/0
```

## Security Checklist

- [ ] Changed SECRET_KEY (don't use default)
- [ ] Set DATABASE_URL with strong password
- [ ] Set ENVIRONMENT=production and DEBUG=false
- [ ] Configured CORS_ORIGINS with your domain(s)
- [ ] Obtained all required API keys
- [ ] Enabled HTTPS/SSL in reverse proxy
- [ ] Set up firewall rules
- [ ] Configured backup strategy
- [ ] Set up monitoring/alerts

## Files Created/Updated

✓ **main.py** - Enhanced with 6 middleware layers  
✓ **config.py** - Complete environment configuration  
✓ **requirements.txt** - 50+ dependencies  
✓ **init_database.sql** - PostgreSQL schema (25+ tables)  
✓ **init_db.py** - Database initialization CLI  
✓ **health.py** - Health check system  
✓ **.env.production.example** - Configuration template  
✓ **Dockerfile.production** - Production Docker image  
✓ **docker-compose.production.yml** - Full stack (6 services)  
✓ **PRODUCTION_DEPLOYMENT.md** - Comprehensive guide (500+ lines)  
✓ **PRODUCTION_FINALIZATION_SUMMARY.md** - Complete summary  
✓ **QUICK_START_PRODUCTION.md** - This guide  

## Next Steps

1. **Before Production**:
   - [ ] Set up PostgreSQL instance
   - [ ] Obtain API keys
   - [ ] Generate SECRET_KEY
   - [ ] Configure .env.production
   - [ ] Run health checks

2. **Production Deployment**:
   - [ ] Use Docker Compose or Systemd service
   - [ ] Set up Nginx reverse proxy
   - [ ] Configure SSL/TLS certificates
   - [ ] Set up log rotation
   - [ ] Configure monitoring

3. **Post-Deployment**:
   - [ ] Run load tests
   - [ ] Monitor logs and metrics
   - [ ] Verify all endpoints working
   - [ ] Test failover procedures
   - [ ] Document runbooks

## Support Links

- [FastAPI Docs](https://fastapi.tiangolo.com)
- [Uvicorn Guide](https://www.uvicorn.org)
- [Gunicorn Docs](https://gunicorn.org)
- [Docker Compose Reference](https://docs.docker.com/compose)
- [PostgreSQL Documentation](https://www.postgresql.org/docs)

## Key Endpoints

```
Health:       GET  http://localhost:8000/health
Database:     GET  http://localhost:8000/health/database
Readiness:    GET  http://localhost:8000/health/ready
Liveness:     GET  http://localhost:8000/health/live
Docs:         GET  http://localhost:8000/docs
API Info:     GET  http://localhost:8000/
```

**Deployment time: ~15-20 minutes** ⏱️

---

For detailed information, see:
- `PRODUCTION_DEPLOYMENT.md` - Full deployment guide
- `PRODUCTION_FINALIZATION_SUMMARY.md` - Complete summary of all changes
- `.env.production.example` - All configuration options
