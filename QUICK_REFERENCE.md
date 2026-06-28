# Edge AI - Quick Reference Guide
## All Commands & Endpoints at a Glance

**Last Updated:** 2026-06-28

---

## 🚀 Quick Start Commands

### Local Setup (3 commands)
```bash
cp .env.example .env          # Copy environment template
nano .env                      # Edit API keys
docker-compose up -d          # Start all services
```

### Verify Setup
```bash
curl http://localhost:8000/health           # API health
curl http://localhost:3000                   # Frontend
curl http://localhost:8000/api/verticals     # All verticals
```

### Stop Services
```bash
docker-compose down           # Stop all services
docker-compose down -v        # Stop and delete volumes (⚠️ WARNING)
```

---

## 🔌 API Endpoints

### Health & Status
```
GET  /                                    Root endpoint
GET  /health                              System health (all 5 verticals)
GET  /docs                                Swagger UI documentation
GET  /openapi.json                        OpenAPI schema
```

### Unified Verticals
```
GET  /api/verticals                       List all 5 verticals
GET  /api/verticals/health                Verticals health check
GET  /api/verticals/{vertical_name}       Get vertical info
POST /api/verticals/{vertical_name}/predict      Make prediction
GET  /api/verticals/{vertical_name}/stats        Get statistics
GET  /api/verticals/{vertical_name}/backtest     Get backtest results
```

### Vertical Names
```
/api/verticals/mlb              ⚾ MLB Strikeout Edge
/api/verticals/tennis           🎾 Tennis Edge
/api/verticals/cricket          🏏 Cricket LBW Edge
/api/verticals/horse            🐴 Horse Racing Edge
/api/verticals/hockey           🏒 Hockey Shots-on-Goal Edge
```

### Core Betting Framework
```
POST /api/auth/register         Register new user
POST /api/auth/login            Login (JWT token)
GET  /api/bankroll              Get user bankroll
POST /api/place-bet             Place new bet
GET  /api/kelly                 Calculate Kelly criterion
GET  /api/positions             Get open positions
POST /api/settle                Settle completed bet
GET  /api/audit-log             View audit trail
GET  /api/predictions           Get all predictions
```

---

## 🐳 Docker Compose Commands

### Service Management
```bash
docker-compose ps                         # List running services
docker-compose logs -f api                # Stream API logs
docker-compose logs -f frontend           # Stream frontend logs
docker-compose logs -f postgres           # Stream database logs
docker-compose logs -f redis              # Stream cache logs

docker-compose restart api                # Restart API service
docker-compose restart frontend           # Restart frontend
docker-compose rebuild api                # Rebuild API image
```

### Database Access
```bash
# Access PostgreSQL
docker-compose exec postgres psql -U betting_user -d betting_db

# Useful SQL commands in psql:
\dt                                       # List tables
SELECT * FROM users;                      # Query users
\q                                        # Quit psql
```

### Cache Access
```bash
# Access Redis
redis-cli -a redis_password
PING                                      # Test connection
KEYS *                                    # List all keys
FLUSHDB                                   # Clear cache (⚠️ WARNING)
```

---

## 📡 Testing Endpoints with curl

### Health Checks
```bash
# System health
curl http://localhost:8000/health

# Verticals health
curl http://localhost:8000/api/verticals/health

# Individual vertical
curl http://localhost:8000/api/verticals/mlb
```

### Make Predictions
```bash
# MLB prediction
curl -X POST http://localhost:8000/api/verticals/mlb/predict \
  -H "Content-Type: application/json" \
  -d '{"pitcher_type":"fastball_dominant","batter_type":"aggressive"}'

# Tennis prediction
curl -X POST http://localhost:8000/api/verticals/tennis/predict \
  -H "Content-Type: application/json" \
  -d '{"player_elo":1800,"surface":"grass"}'
```

### Get Statistics
```bash
curl http://localhost:8000/api/verticals/mlb/stats
curl http://localhost:8000/api/verticals/tennis/stats
```

---

## 🌍 Production URLs

### Live Endpoints (Production)
```
Frontend:       https://edge-ai.io
API Root:       https://api.edge-ai.io
API Health:     https://api.edge-ai.io/health
API Docs:       https://api.edge-ai.io/docs

All Verticals:  https://api.edge-ai.io/api/verticals
MLB:            https://api.edge-ai.io/api/verticals/mlb
Tennis:         https://api.edge-ai.io/api/verticals/tennis
Cricket:        https://api.edge-ai.io/api/verticals/cricket
Horse:          https://api.edge-ai.io/api/verticals/horse
Hockey:         https://api.edge-ai.io/api/verticals/hockey
```

---

## 🔧 Useful Environment Variables

```bash
# Application
DEBUG=False
APP_NAME="Edge AI"

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db
POSTGRES_PASSWORD=strong_password

# Cache
REDIS_URL=redis://:password@localhost:6379
REDIS_PASSWORD=redis_password

# Security
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256

# External APIs (Sample)
POLYMARKET_API_KEY=your_key
FRED_API_KEY=your_key
YAHOO_FINANCE_API_KEY=your_key
COINGECKO_API_KEY=your_key
DRAFTKINGS_API_KEY=your_key

# Deployment
VITE_API_URL=https://api.edge-ai.io
```

---

## 📊 Common Curl Examples

### Check All 5 Verticals
```bash
#!/bin/bash
for vertical in mlb tennis cricket horse hockey; do
  echo "Checking $vertical..."
  curl http://localhost:8000/api/verticals/$vertical | jq '.vertical'
done
```

### Load Test
```bash
#!/bin/bash
for i in {1..100}; do
  curl -s http://localhost:8000/health > /dev/null
  echo "$i requests completed"
done
```

### Check JSON Response
```bash
curl -s http://localhost:8000/api/verticals | jq
curl -s http://localhost:8000/health | jq '.all_verticals_operational'
```

---

## 🐛 Troubleshooting Commands

### Check Service Status
```bash
docker-compose ps                         # All services
docker-compose logs api | tail -20        # Last 20 API logs
docker-compose logs postgres | tail -20   # Last 20 DB logs
```

### Reset Services
```bash
docker-compose down                       # Stop all
docker-compose up -d --build              # Rebuild and start
```

### Database Issues
```bash
# Check connection
docker-compose exec postgres psql -U betting_user -d betting_db -c "SELECT 1"

# Reset database
docker-compose exec postgres dropdb -U betting_user betting_db
docker-compose exec postgres createdb -U betting_user betting_db

# View logs
docker-compose logs postgres | grep -i error
```

### Cache Issues
```bash
# Test Redis
redis-cli -a redis_password PING

# Clear cache
redis-cli -a redis_password FLUSHDB

# View Redis logs
docker-compose logs redis
```

---

## 📈 Performance Monitoring

### Check Response Time
```bash
time curl http://localhost:8000/health    # Shows total time

# More detailed timing
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health
```

### Database Query Performance
```sql
-- In PostgreSQL
EXPLAIN ANALYZE SELECT * FROM predictions WHERE vertical='mlb';
SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC;
```

### Monitor Container Resources
```bash
docker stats                              # CPU/Memory per container
docker inspect betting-framework-api | jq '.HostConfig.Memory'
```

---

## 🚀 Deployment Commands

### GitHub Actions
```bash
# Trigger workflow manually
gh workflow run deploy-all-verticals.yml

# View workflow status
gh workflow view deploy-all-verticals.yml

# Watch deployment
gh run watch <run-id>
```

### Railway (Backend)
```bash
railway login                              # Login to Railway
railway init                               # Initialize project
railway up                                 # Deploy
railway logs                               # View logs
railway status                             # Check status
railway domain                             # Get domain
```

### Vercel (Frontend)
```bash
vercel login                               # Login to Vercel
vercel --prod                              # Deploy to production
vercel list                                # List deployments
vercel env ls                              # List environment variables
```

---

## 📚 Important Files

| File | Purpose | Edit? |
|------|---------|-------|
| `.env.example` | Environment template | No |
| `.env` | Actual environment values | Yes (never commit) |
| `docker-compose.yml` | Container orchestration | Read only |
| `backend/main.py` | FastAPI app | Yes (code changes) |
| `backend/routes/verticals.py` | Unified verticals | Read only |
| `DEPLOYMENT_ALL_VERTICALS.md` | Deployment guide | No |
| `DOMAIN_SETUP_GUIDE.md` | Domain configuration | No |
| `.github/workflows/deploy-all-verticals.yml` | CI/CD pipeline | Read only |

---

## 🔐 Security Checklist

```bash
# Never commit .env
git status | grep .env                    # Should be empty

# Verify secrets in GitHub
gh secret list                             # List all secrets

# Check production env
curl https://api.edge-ai.io/health | jq '.database, .cache'
# Should both return "ok" (not actual credentials)
```

---

## 💾 Backup & Recovery

### Database Backup
```bash
# Backup
docker-compose exec postgres pg_dump \
  -U betting_user betting_db > backup_$(date +%Y%m%d).sql

# Restore
docker-compose exec -T postgres psql \
  -U betting_user betting_db < backup_20260628.sql
```

### Volume Backup
```bash
docker run --rm -v stike_postgres_data:/data \
  -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

---

## 🎯 Key Metrics to Monitor

```
✅ Health Endpoint Response: < 100ms
✅ API Vertical Response: < 500ms
✅ Database Query Time: < 1000ms
✅ Redis Cache Hit Rate: > 80%
✅ Error Rate: < 0.1%
✅ Uptime: > 99.9%
```

---

## 📞 Quick Support

### Common Issues

**API not responding?**
```bash
docker-compose restart api
docker-compose logs api | tail -20
```

**Database connection failed?**
```bash
docker-compose logs postgres
docker-compose exec postgres psql -U betting_user -d betting_db -c "SELECT 1"
```

**Frontend not loading?**
```bash
docker-compose logs frontend
docker-compose restart frontend
```

**Domain not resolving?**
```bash
nslookup edge-ai.io
dig edge-ai.io
# Wait 24-48 hours if just configured
```

---

## 🔗 Important Links

- **Frontend:** https://edge-ai.io
- **API:** https://api.edge-ai.io
- **Docs:** https://api.edge-ai.io/docs
- **GitHub:** https://github.com/yourusername/edge-ai
- **Railway:** https://railway.app/dashboard
- **Vercel:** https://vercel.com/dashboard
- **Email:** support@edge-ai.io

---

## 📝 Quick Script: Full System Check

```bash
#!/bin/bash
echo "=== Edge AI System Check ==="

echo "✓ Checking services..."
docker-compose ps

echo "✓ API health..."
curl -s http://localhost:8000/health | jq '.all_verticals_operational'

echo "✓ Database..."
docker-compose exec postgres psql -U betting_user -d betting_db -c "SELECT COUNT(*) FROM users" || echo "DB not ready"

echo "✓ Redis..."
redis-cli -a redis_password PING 2>/dev/null || echo "Redis not available"

echo "✓ Verticals..."
curl -s http://localhost:8000/api/verticals | jq '.count'

echo "=== Check Complete ==="
```

---

**Version:** 1.0.0  
**Last Updated:** 2026-06-28  
**Status:** ✅ Ready for Production
