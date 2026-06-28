# Portfolio Engine Deployment Package

**Generated:** 2026-06-28  
**Status:** Complete  
**Version:** 1.0

---

## Package Contents

This deployment package contains everything needed to deploy, monitor, and manage the portfolio engine system.

### 1. Docker Deployment

**File:** `docker-compose.portfolio.yml`  
**Size:** 3.6 KB

Extends the main docker-compose with portfolio engine service.

**Services Added:**
- `portfolio`: Portfolio engine API (port 8001)
- `portfolio-monitor`: Monitoring service (background)

**Usage:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.portfolio.yml up -d
```

**Environment Variables:**
```bash
PORTFOLIO_ENABLE_MONITORING=true
PORTFOLIO_REBALANCE_FREQUENCY=monthly
PORTFOLIO_MAX_CORRELATION_THRESHOLD=0.85
PORTFOLIO_REGIME_SHOCK_THRESHOLD=0.3
```

---

### 2. Deployment Script

**File:** `deploy.sh`  
**Size:** 17 KB

Complete deployment automation script for dev/staging/prod environments.

**Capabilities:**

1. **Pre-Deployment Checks**
   - Verify Docker/Docker Compose installed
   - Check Python3 available
   - Validate environment config

2. **Service Deployment**
   - Build and start Docker containers
   - Wait for services to become healthy
   - Run database migrations

3. **Test Suite**
   - Portfolio simulator test (500 simulations, 252 days)
   - Allocation optimization test (Kelly, Sharpe, Min-Variance, Equal-Weight)
   - Regime controller test (4 market conditions)
   - Health checks on all endpoints

4. **Logging & Reporting**
   - Detailed logs to `logs/deployment/`
   - Timestamped log files
   - Test result summaries

**Usage:**
```bash
# Development environment with tests
./deploy.sh dev

# Staging without tests (faster)
./deploy.sh staging --no-tests

# Production
./deploy.sh prod --verbose

# Check logs
tail -f logs/deployment/deploy_dev_20260628_150000.log
```

---

### 3. Monitoring Services

**Directory:** `monitoring/`  
**Files:** 5 Python modules + Dockerfile

#### 3.1 Allocation Monitor

**File:** `monitoring/allocation_monitor.py`  
**Size:** ~12 KB

Monitors actual portfolio allocation vs recommended allocation.

**Metrics Tracked:**
- Weight drift per strategy (%)
- Concentration (Herfindahl index)
- Rebalancing necessity
- Alert levels (INFO/WARNING/CRITICAL)

**Database:** SQLite with tables
- `allocation_history`: Snapshots of allocation state
- `rebalancing_events`: Log of rebalancing actions

**Check Interval:** 5 minutes (configurable)

**Alert Thresholds:**
- INFO: All metrics normal
- WARNING: Drift 3-5% or HHI > 0.35
- CRITICAL: Drift > 5%

**Sample Output:**
```
Allocation Snapshot (2026-06-28T15:30:00)
  Drift (pct): {'MLB': 1.2, 'Crypto': 2.8, 'Earnings': 0.5, 'AI': 1.8, 'Econ': 2.1}
  Max drift: 2.80%
  Concentration (HHI): 0.185
  Alert: WARNING - Rebalancing recommended - max drift 2.80%
```

---

#### 3.2 Correlation Monitor

**File:** `monitoring/correlation_monitor.py`  
**Size:** ~14 KB

Monitors correlation structure changes in real-time.

**Metrics Tracked:**
- Mean correlation
- Max correlation
- Clustering strength (increase vs baseline)
- Diversification ratio (DR = weighted_vol / portfolio_vol)
- Correlation spikes (>10% change)

**Database:** SQLite with tables
- `correlation_history`: Historical correlation matrices
- `correlation_events`: Detected correlation changes

**Check Interval:** 1 hour (configurable)

**Alert Thresholds:**
- NORMAL: DR > 1.3, mean corr < 0.60
- ELEVATED: DR 1.2-1.3, mild clustering
- HIGH: DR 1.1-1.2, significant clustering
- CRITICAL: DR < 1.1 or spike detected

**Sample Output:**
```
Correlation Snapshot (2026-06-28T15:00:00)
  Mean Correlation: 0.256
  Max Correlation: 0.751
  Clustering: 0.045
  Diversification Ratio: 1.32
  Alert: NORMAL - Correlation structure healthy
```

---

#### 3.3 Regime Alerter

**File:** `monitoring/regime_alerter.py`  
**Size:** ~13 KB

Detects market regime shifts and triggers portfolio rebalancing recommendations.

**Market Indicators Monitored:**
- VIX level (volatility index)
- VIX percentile (historical context)
- Crypto funding rate
- Market sentiment score (-1 to +1)

**Regime Classification:**
- **Low Vol** (VIX < 12): Increase risk exposure
- **Normal** (VIX 12-20): Baseline allocation
- **High Vol** (VIX 20-30): Reduce risk
- **Stress** (VIX > 30): Significant risk reduction

**Database:** SQLite with tables
- `regime_history`: Historical regime states
- `regime_shifts`: Detected transition events

**Check Interval:** 5 minutes (configurable)

**Alerts Sent On:**
- Regime classification change
- Regime score change > 0.15
- Shift magnitude > 0.3

**Alert Delivery:**
- Slack webhooks (formatted messages)
- HTTP webhooks (JSON payload)
- Application logs (CRITICAL level)

**Sample Output:**
```
Regime State (2026-06-28T15:30:00)
  Regime: High Vol
  VIX: 24.5 (percentile: 75)
  Funding: 0.025 (elevated)
  Sentiment: -0.3 (slightly negative)
  Score: 0.65 (elevated stress)
  Shift: True (magnitude: 0.28)
  Recommended: Reduce Risk
```

---

#### 3.4 Monitoring Main

**File:** `monitoring/__main__.py`  
**Size:** ~4 KB

Orchestrates all monitoring services running concurrently.

**Features:**
- Async execution of all monitors
- Configurable check intervals
- Error handling and retry logic
- Clean shutdown on SIGINT

**Usage:**
```bash
# Run monitoring service
python -m monitoring

# Configuration via environment variables
ALLOCATION_CHECK_INTERVAL=300
CORRELATION_CHECK_INTERVAL=3600
REGIME_CHECK_INTERVAL=300
```

---

#### 3.5 Dockerfile & Requirements

**Files:** 
- `monitoring/Dockerfile` (18 lines)
- `monitoring/requirements.txt` (9 dependencies)

**Key Dependencies:**
- numpy, scipy (numerical computing)
- pandas (data handling)
- requests (HTTP client)
- pydantic (data validation)
- sqlalchemy, psycopg2 (database)
- redis (caching)
- python-dotenv (configuration)

---

### 4. Documentation

**Directory:** `docs/`  
**Files:** 3 comprehensive markdown documents

#### 4.1 Portfolio Engine Architecture

**File:** `docs/portfolio_engine_architecture.md`  
**Size:** ~20 KB

**Sections:**
1. System overview and components
2. PortfolioSimulator (Monte Carlo, correlation, regime shocks)
3. PortfolioAllocator (Kelly, Sharpe, Min-Variance, Equal-Weight)
4. RegimeController (VIX-based adjustment, sentiment effects)
5. Monitoring services (allocation, correlation, regime)
6. Data flow diagrams
7. Strategy profiles (MLB, Crypto, Earnings, AI, Econ)
8. API integration points
9. Database schemas (4 main tables)
10. Configuration reference
11. Performance characteristics
12. Failure modes & recovery
13. Future enhancements

**Audience:** Architects, engineers, decision-makers

---

#### 4.2 API Reference

**File:** `docs/api_portfolio.md`  
**Size:** ~25 KB

**Endpoints Documented:**
1. `POST /api/portfolio/simulate` - Monte Carlo simulation
2. `POST /api/portfolio/allocation` - Optimal allocation
3. `POST /api/portfolio/regime` - Regime assessment
4. `GET /api/portfolio/health` - Health check

**For Each Endpoint:**
- Full request/response schemas
- Parameter descriptions with types/ranges
- Example cURL commands
- Response field explanations
- Error codes and recovery

**Common Use Cases:**
1. Portfolio backtesting
2. Optimal reallocation
3. Regime-based adjustment
4. Monitoring pipeline

**Additional Topics:**
- Error handling & retry logic
- Rate limiting recommendations
- Authentication (future)
- API versioning

**Audience:** API consumers, frontend developers, integrations

---

#### 4.3 Allocation Rules

**File:** `docs/allocation_rules.md`  
**Size:** ~18 KB

**Optimization Methods Explained:**

1. **Kelly Criterion** (Growth-optimal)
   - Theory: w = inv(Σ) @ r
   - Full example calculation
   - When to use / advantages / disadvantages
   - Fractional Kelly (0.25 default)

2. **Maximum Sharpe Ratio** (Risk-adjusted)
   - Convex optimization problem
   - SLSQP solver details
   - When to use / advantages / disadvantages

3. **Minimum Variance** (Risk-parity)
   - Pure volatility minimization
   - Defensive positioning
   - When to use

4. **Equal Weight** (Baseline)
   - Simple 20% per strategy
   - Reference point

**Regime Adjustments:**
- VIX-based multipliers (0.6 to 1.2x)
- Sentiment adjustments (reduce risky/increase defensive)
- Funding rate adjustments (Crypto-specific)
- Example full calculation walkthrough

**Portfolio Metrics:**
- Expected return calculation
- Volatility from covariance matrix
- Sharpe ratio
- Herfindahl concentration index
- Kelly fractions for position sizing

**Rebalancing Rules:**
- Drift threshold (3%)
- Concentration alert (HHI > 0.35)
- Regime shift triggers
- Periodic rebalancing
- Transaction cost calculation

**Constraints & Limits:**
- Position limits
- Leverage bounds
- Diversification requirements

**Parameter Estimation:**
- Expected returns (sources, considerations)
- Volatility (historical, GARCH, implied)
- Correlation (rolling windows, tail dependence)

**Sensitivity Analysis:**
- Parameter robustness
- Weight stability testing

**Audience:** Portfolio managers, quants, risk officers

---

## Quick Start Guide

### 1. Deploy Portfolio Service

```bash
# From stike root directory
chmod +x deploy.sh
./deploy.sh dev

# Expected output:
# ✓ Docker services deployed
# ✓ Portfolio simulator test passed
# ✓ Allocation optimization tests passed
# ✓ Regime controller tests passed
# ✓ Deployment complete
```

### 2. Test API Endpoints

```bash
# Simulate portfolio
curl -X POST http://localhost:8001/api/portfolio/simulate \
  -H "Content-Type: application/json" \
  -d @test_simulation.json

# Get optimal allocation
curl -X POST http://localhost:8001/api/portfolio/allocation \
  -H "Content-Type: application/json" \
  -d @test_allocation.json

# Check current regime
curl -X POST http://localhost:8001/api/portfolio/regime \
  -H "Content-Type: application/json" \
  -d @test_regime.json

# Health check
curl http://localhost:8001/api/portfolio/health
```

### 3. Monitor Portfolio

Monitoring services start automatically with Docker. View logs:

```bash
# Portfolio service logs
docker-compose logs -f portfolio

# Monitoring service logs
docker-compose logs -f portfolio-monitor

# Check monitoring databases
sqlite3 /app/data/allocation_history.db "SELECT * FROM allocation_history LIMIT 5;"
sqlite3 /app/data/correlation_history.db "SELECT timestamp, clustering_strength FROM correlation_history LIMIT 5;"
sqlite3 /app/data/regime_history.db "SELECT timestamp, regime_type, vix FROM regime_history LIMIT 5;"
```

### 4. Set Up Alerts

Configure alert delivery:

```bash
# In .env file
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
ALERT_WEBHOOK_URL=https://your-domain.com/api/alerts
ALERT_EMAIL=portfolio-alerts@example.com
```

Alerts are sent on:
- Regime shifts (VIX changes, sentiment reversal)
- Allocation drift > 5%
- Correlation clustering
- Diversification breakdown

---

## File Structure

```
stike/
├── docker-compose.portfolio.yml          # Portfolio service definition
├── deploy.sh                             # Deployment automation
├── monitoring/                           # Monitoring services
│   ├── __main__.py                      # Main entry point
│   ├── allocation_monitor.py            # Allocation tracking
│   ├── correlation_monitor.py           # Correlation monitoring
│   ├── regime_alerter.py                # Regime detection
│   ├── requirements.txt                 # Python dependencies
│   └── Dockerfile                       # Container image
└── docs/                                # Documentation
    ├── portfolio_engine_architecture.md  # System design
    ├── api_portfolio.md                 # API reference
    └── allocation_rules.md              # Weight calculation rules
```

---

## Performance Benchmarks

### Simulation Performance
- 500 simulations, 252 days: 2-5 seconds
- 1000 simulations, 252 days: 4-10 seconds
- Linear scaling with simulations

### Allocation Optimization
- Kelly criterion: ~0.5 seconds
- Sharpe optimization: ~1-2 seconds
- Min-variance optimization: ~1-2 seconds

### Monitoring Overhead
- Allocation monitor: ~100ms per check (every 5 min)
- Correlation monitor: ~500ms per check (every hour)
- Regime alerter: ~200ms per check (every 5 min)
- Total CPU impact: < 0.5%

---

## Configuration Reference

### Portfolio Service

```bash
PORTFOLIO_ENABLE_MONITORING=true              # Enable monitors
PORTFOLIO_REBALANCE_FREQUENCY=monthly         # daily/weekly/monthly/quarterly
PORTFOLIO_MAX_CORRELATION_THRESHOLD=0.85     # Alert if > 0.85
PORTFOLIO_REGIME_SHOCK_THRESHOLD=0.3         # Alert if > 0.3
```

### Monitoring Service

```bash
MONITOR_ENABLED=true                          # Enable all monitors
ALLOCATION_CHECK_INTERVAL=300                # Seconds (5 min)
CORRELATION_CHECK_INTERVAL=3600              # Seconds (1 hour)
REGIME_CHECK_INTERVAL=300                    # Seconds (5 min)
LOG_LEVEL=INFO                               # DEBUG/INFO/WARNING/ERROR
```

### Alerts

```bash
ALERT_WEBHOOK_URL=https://...                # HTTP webhook for alerts
SLACK_WEBHOOK_URL=https://hooks.slack.com/..# Slack webhook
ALERT_EMAIL=alerts@example.com               # Email alerts
```

---

## Testing

All tests are automated in `deploy.sh`:

### 1. Portfolio Simulator Test
```
- 5 strategies
- 500 Monte Carlo simulations
- 252-day horizon
- Validates: return stats, risk metrics, diversification
- ~15 seconds
```

### 2. Allocation Optimization Test
```
- 4 methods tested: Kelly, Sharpe, Min-Variance, Equal-Weight
- Validates: weights sum to 1.0, valid ranges, metrics calculation
- ~8 seconds total
```

### 3. Regime Controller Test
```
- 4 regime scenarios: Low Vol, Normal, High Vol, Stress
- Validates: regime classification, weight adjustments, recommendations
- ~8 seconds total
```

### 4. Health Checks
```
- Portfolio API /health endpoint
- Main API /health endpoint
- Database connectivity
- Service dependencies
```

---

## Troubleshooting

### Portfolio API won't start

```bash
# Check logs
docker-compose logs portfolio

# Common issues:
# - Port 8001 in use: change PORTFOLIO_PORT in docker-compose
# - Database connection: verify DATABASE_URL env var
# - Missing dependencies: rebuild Docker image
```

### Monitoring service crashes

```bash
# Check logs
docker-compose logs portfolio-monitor

# Issues:
# - Database permission denied: ensure data/monitoring dir writable
# - API unreachable: check portfolio service is running
# - Memory issues: increase container memory limit
```

### Allocation drift alerts

```bash
# Check actual vs recommended
curl http://localhost:8001/api/portfolio/allocation \
  -X POST -H "Content-Type: application/json" -d '{...}'

# Compare with current portfolio positions
# Rebalance if drift > 3%
```

### High correlation clustering

```bash
# Check correlation matrix
sqlite3 data/correlation_history.db \
  "SELECT timestamp, mean_correlation, clustering_strength \
   FROM correlation_history ORDER BY timestamp DESC LIMIT 10;"

# Indicates: diversification benefits reducing, market stress increasing
# Action: reduce risk exposure, move to defensive assets
```

---

## Support & Maintenance

### Regular Maintenance

- **Weekly**: Review allocation drift logs
- **Monthly**: Check correlation clustering trends
- **Quarterly**: Backtest with new data, validate parameters
- **Yearly**: Update strategy parameters and correlation matrix

### Monitoring Database Cleanup

```bash
# Archive old records (older than 1 year)
sqlite3 data/allocation_history.db \
  "DELETE FROM allocation_history WHERE timestamp < datetime('now', '-1 year');"
```

### Performance Monitoring

```bash
# Check deployment logs
tail -f logs/deployment/deploy_*.log

# Monitor Docker resource usage
docker stats betting-framework-portfolio

# Check API response times (request logs)
docker-compose logs portfolio | grep "ms"
```

---

## Next Steps

1. **Deploy to Dev:** Run `./deploy.sh dev` and verify all tests pass
2. **Configure Alerts:** Set up Slack/webhook URLs for regime shifts
3. **Create Dashboard:** Use monitoring databases to build real-time dashboard
4. **Backtest Strategy:** Run simulator with your own parameter estimates
5. **Document Integration:** Add portfolio API calls to your trading system
6. **Monitor Live:** Set cron job to run monitoring every 5 minutes
7. **Scale to Prod:** Deploy with `./deploy.sh prod` when confident

---

## Files Checklist

- [x] `docker-compose.portfolio.yml` - Docker service definition
- [x] `deploy.sh` - Deployment script with tests
- [x] `monitoring/allocation_monitor.py` - Allocation tracking
- [x] `monitoring/correlation_monitor.py` - Correlation monitoring
- [x] `monitoring/regime_alerter.py` - Regime alerting
- [x] `monitoring/__main__.py` - Monitor orchestrator
- [x] `monitoring/requirements.txt` - Python dependencies
- [x] `monitoring/Dockerfile` - Container image
- [x] `docs/portfolio_engine_architecture.md` - System design
- [x] `docs/api_portfolio.md` - API reference
- [x] `docs/allocation_rules.md` - Weight calculations

---

## License & Attribution

Portfolio Engine v1.0  
Built with: FastAPI, NumPy, SciPy, SQLite, Docker  
Last Updated: 2026-06-28

---

## Questions?

Refer to the comprehensive documentation:
- **System Design**: `docs/portfolio_engine_architecture.md`
- **API Usage**: `docs/api_portfolio.md`
- **Weight Calculations**: `docs/allocation_rules.md`
- **Deployment**: This file (PORTFOLIO_DEPLOYMENT_PACKAGE.md)
