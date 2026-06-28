# Monitoring Guide - Production Betting Framework

**Last Updated**: 2026-06-28  
**Version**: 1.0.0  
**Primary Tool**: Datadog  
**Backup Tools**: Prometheus, Grafana, ELK Stack

---

## Table of Contents

1. [Dashboards](#dashboards)
2. [Alerts & Thresholds](#alerts--thresholds)
3. [Metrics](#metrics)
4. [Logs](#logs)
5. [SLOs & Service Levels](#slos--service-levels)
6. [Debugging with Monitoring](#debugging-with-monitoring)

---

## Dashboards

### Main Production Dashboard

**URL**: https://app.datadoghq.com/dashboard/betting-prod

**Key Sections**:

#### 1. System Health (Top Row)
- **API Response Time**: P50/P95/P99 latency trend
- **Error Rate**: % of requests returning 5xx
- **Request Volume**: Requests/second over time
- **Active Users**: Real-time connected sessions

#### 2. Database Performance (Second Row)
- **Query Latency**: P95 database response time
- **Connection Pool**: Current vs max connections
- **Replication Lag**: Seconds behind primary (if applicable)
- **Slow Queries**: Count of queries > 100ms

#### 3. Infrastructure (Third Row)
- **CPU Usage**: % usage across instances
- **Memory Usage**: % usage and trend
- **Disk Space**: % used and forecast to full
- **Network I/O**: Bytes in/out per second

#### 4. Betting Metrics (Fourth Row)
- **Bets Placed**: Hourly volume
- **Settlement Success**: % successful settlements
- **Kelly Compliance**: % of bets following Kelly limits
- **Average Bet Size**: Mean stake over time

#### 5. Portfolio Health (Fifth Row)
- **Portfolio Value**: Total value trend
- **Sharpe Ratio**: Weekly Sharpe ratio
- **Max Drawdown**: Current max drawdown from peak
- **Win Rate**: % of settled bets that are wins

### Vertical-Specific Dashboards

**MLB Dashboard**: `betting-mlb-detail`
- Strikeout predictions accuracy
- Model confidence vs accuracy scatter
- Prediction volume by pitcher/batter type
- Edge capture statistics

**Tennis Dashboard**: `betting-tennis-detail`
- Elo model accuracy
- Surface-specific performance
- Tournament stage analysis
- Player comeback probability

**Cricket Dashboard**: `betting-cricket-detail`
- LBW decision accuracy
- Umpire decision patterns
- Pitch condition impact
- Signal persistence (split-half reliability)

**Horse Racing Dashboard**: `betting-horse-detail`
- Sectional time analysis
- Track condition impact
- Benter model accuracy
- Win probability calibration

**Hockey Dashboard**: `betting-hockey-detail`
- SOG differential strength
- Team-based model performance
- Season progress and trends
- Year-over-year correlation

### Business Dashboards

**Bankroll Dashboard**: `betting-bankroll-overview`
- Total user bankroll
- New user acquisition rate
- Average bankroll size
- Churn rate (inactive users)

**Revenue Dashboard**: `betting-revenue-dashboard`
- Commission earned
- User LTV (lifetime value)
- Retention cohorts
- Payment method distribution

---

## Alerts & Thresholds

### Critical Alerts (P1 - Page immediately)

| Metric | Threshold | Duration | Action |
|--------|-----------|----------|--------|
| API Error Rate | > 1% | 5 min | Restart API, check logs |
| Database Offline | Connection failed | 1 min | Verify DB, check firewall |
| Disk Full | > 90% | Immediate | Cleanup or expand |
| API Down | No response | 2 min | Check health endpoint |
| Data Loss | Rows deleted unexpectedly | Immediate | Restore from backup |

**Alert Example**:
```
ALERT: API Error Rate High
Status: FIRING
Value: 2.3% (threshold: 1%)
Duration: 8 minutes
Action: Check /logs for errors
    kubectl logs deployment/betting-api -n production | grep ERROR
```

### High Alerts (P2 - Respond within 15 min)

| Metric | Threshold | Duration | Action |
|--------|-----------|----------|--------|
| Response Time P95 | > 1000ms | 10 min | Add replicas, check DB queries |
| Connection Pool | > 80% | 5 min | Increase pool size |
| Memory Usage | > 85% | 10 min | Check for memory leaks |
| Query Latency | > 100ms | 10 min | Create indexes, analyze stats |
| Replication Lag | > 1 sec | 5 min | Check network, restart replica |

### Medium Alerts (P3 - Respond within 1 hour)

| Metric | Threshold | Duration | Action |
|--------|-----------|----------|--------|
| CPU Usage | > 75% | 15 min | Scale up or optimize code |
| Cache Hit Rate | < 80% | 30 min | Check cache configuration |
| Settlement Queue | > 100 items | 30 min | Increase worker threads |
| Disk Usage | > 75% | Immediate | Plan cleanup |
| Log Volume | > 1GB/hour | 1 hour | Check for verbose logging |

### Low Alerts (P4 - Handle during business hours)

| Metric | Threshold | Duration | Action |
|--------|-----------|----------|--------|
| External API Latency | > 5s | 10 min | Monitor, may be their issue |
| Failed Email Sends | > 5/hour | 1 hour | Check email service status |
| Unused Indexes | Detected | Anytime | Review and drop |
| Deprecated Endpoints | Detected | Anytime | Plan removal |

---

## Metrics

### API Metrics

```
api.requests.total
  labels: method, endpoint, status_code
  type: counter
  example: api.requests.total{method="POST", endpoint="/place-bet", status_code="201"} = 15234

api.request.duration_ms
  labels: method, endpoint
  type: histogram (P50, P95, P99)
  example: api.request.duration_ms{method="GET", endpoint="/health", quantile="0.95"} = 45ms

api.errors
  labels: error_code, endpoint
  type: counter
  example: api.errors{error_code="AUTH_FAILED", endpoint="/login"} = 12

api.request.size_bytes
  labels: endpoint
  type: gauge
  example: api.request.size_bytes{endpoint="/place-bet"} = 512

api.response.size_bytes
  labels: endpoint
  type: gauge
  example: api.response.size_bytes{endpoint="/predictions"} = 2048
```

### Database Metrics

```
database.connections
  labels: state (active, idle)
  type: gauge
  example: database.connections{state="active"} = 23

database.query.duration_ms
  labels: query_type, table
  type: histogram
  example: database.query.duration_ms{query_type="SELECT", table="bets", quantile="0.95"} = 35ms

database.connections.max
  type: gauge
  example: database.connections.max = 100

database.replication.lag_ms
  type: gauge
  example: database.replication.lag_ms = 234

database.slow_queries
  type: counter
  example: database.slow_queries = 45

database.transactions.committed
  type: counter
  example: database.transactions.committed = 1000000

database.transactions.aborted
  type: counter
  example: database.transactions.aborted = 234

database.disk_usage_gb
  type: gauge
  example: database.disk_usage_gb = 45.2
```

### Cache Metrics

```
cache.hit_rate
  type: gauge (0-1)
  example: cache.hit_rate = 0.94

cache.memory_usage_mb
  type: gauge
  example: cache.memory_usage_mb = 512

cache.evictions
  type: counter
  example: cache.evictions = 1234

cache.key_expiration_rate
  type: gauge
  example: cache.key_expiration_rate = 0.05

cache.operations
  labels: operation (get, set, delete)
  type: counter
  example: cache.operations{operation="get"} = 1000000
```

### Application Metrics

```
bets.placed
  labels: vertical, user_id
  type: counter
  example: bets.placed{vertical="mlb"} = 5234

bets.settled
  labels: vertical, outcome (win, loss)
  type: counter
  example: bets.settled{vertical="mlb", outcome="win"} = 2850

bets.settlement_success_rate
  type: gauge (0-1)
  example: bets.settlement_success_rate = 0.9995

portfolio.total_value_usd
  type: gauge
  example: portfolio.total_value_usd = 125000.50

portfolio.unrealized_pnl_usd
  type: gauge
  example: portfolio.unrealized_pnl_usd = 12500.00

portfolio.sharpe_ratio
  type: gauge
  example: portfolio.sharpe_ratio = 1.85

portfolio.max_drawdown
  type: gauge (-1 to 0)
  example: portfolio.max_drawdown = -0.15

portfolio.win_rate
  type: gauge (0-1)
  example: portfolio.win_rate = 0.5667

kelly.calculator.calls
  labels: status (success, error)
  type: counter
  example: kelly.calculator.calls{status="success"} = 12345

kelly.compliance
  type: gauge (0-1)
  example: kelly.compliance = 0.98

risk.limit_breaches
  labels: limit_type (daily_loss, exposure, bet_size)
  type: counter
  example: risk.limit_breaches{limit_type="daily_loss"} = 2
```

### Infrastructure Metrics

```
system.cpu.percent
  type: gauge
  example: system.cpu.percent = 65.2

system.memory.percent
  type: gauge
  example: system.memory.percent = 72.1

system.disk.percent
  type: gauge
  example: system.disk.percent = 68.5

system.network.bytes_in
  type: counter
  example: system.network.bytes_in = 1000000000

system.network.bytes_out
  type: counter
  example: system.network.bytes_out = 500000000

pod.restart_count
  labels: pod_name, namespace
  type: gauge
  example: pod.restart_count{pod_name="betting-api-5d4f8c7b9", namespace="production"} = 0

pod.cpu_cores
  type: gauge
  example: pod.cpu_cores = 0.8

pod.memory_mb
  type: gauge
  example: pod.memory_mb = 1024
```

---

## Logs

### Log Collection

**Centralized Logging**: https://logs.betting-framework.ai

**Log Streams**:
```
source:betting-api
source:database
source:cache
source:worker-settlement
source:worker-reconciliation
```

### Log Levels

```
DEBUG - Development only, extremely verbose
INFO - General application flow (default level)
WARN - Suspicious conditions, possible issues
ERROR - Error conditions that prevented an operation
CRITICAL - System failure, requires immediate attention
```

### Production Log Queries

**Recent errors**:
```
source:betting-api AND level:ERROR AND timestamp > -30m
```

**High latency requests**:
```
source:betting-api AND duration_ms > 1000
```

**Database errors**:
```
source:database AND level:ERROR
```

**Slow queries**:
```
source:database AND query_duration_ms > 100
```

**Authentication failures**:
```
source:betting-api AND event_type:AUTH_FAILED
```

**Risk limit breaches**:
```
source:betting-api AND event_type:RISK_LIMIT_BREACH
```

**Settlement failures**:
```
source:settlement-worker AND status:FAILED
```

### Log Retention Policy

```
DEBUG logs:    7 days
INFO logs:     30 days
WARN logs:     90 days
ERROR logs:    180 days
CRITICAL logs: 1 year
Audit logs:    7 years (compliance)
```

### Log Format (Structured JSON)

```json
{
  "timestamp": "2026-06-28T10:30:45.123Z",
  "level": "INFO",
  "logger": "api.handlers.bets",
  "message": "Bet placed successfully",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "bet_id": "550e8400-e29b-41d4-a716-446655440200",
  "stake": 289.00,
  "expected_value": 0.102,
  "duration_ms": 45,
  "request_id": "req-12345",
  "service": "betting-api",
  "version": "1.0.0",
  "environment": "production"
}
```

### Key Fields to Log

- `user_id`: For tracking user-specific issues
- `request_id`: For tracing requests across services
- `duration_ms`: For performance monitoring
- `error_code`: Standard error classification
- `bet_id` / `position_id`: For transaction tracking
- `service`: Source of the log
- `environment`: production, staging, development

---

## SLOs & Service Levels

### API Availability SLO

**Target**: 99.5% uptime per month

```
Calculation: Successful requests / Total requests * 100
Success: Status code 2xx or 3xx
Failure: Status code 5xx or timeout

Monthly budget: 21.6 minutes of downtime
```

**Error budget alerts**:
- 50% consumed: Warning (10.8 min remaining)
- 80% consumed: Alert (4.3 min remaining)
- 100% consumed: Critical (SLO breached)

### Response Time SLO

**Target**: P95 < 500ms, P99 < 1000ms

```
Measured: All non-admin endpoints
Excluded: /docs (documentation), health checks
Baseline: Measured monthly, 10% variance allowed
```

### Error Rate SLO

**Target**: < 0.5% error rate

```
Measured: 5xx errors / total requests
Calculation: Rolling 5-minute window
Threshold: > 0.5% for > 5 consecutive minutes triggers alert
```

### Settlement Success SLO

**Target**: 99.9% successful settlements

```
Measured: Settlements completed successfully / total settlements
Failures: Status='ERROR' or timeout after 24h
```

### Data Consistency SLO

**Target**: 100% (zero data loss incidents)

```
Measured: Database integrity checks
Frequency: Nightly automated verification
Failure: Any detected corruption triggers P1 alert
```

---

## Debugging with Monitoring

### Finding the Root Cause: Flowchart

```
High Error Rate?
├─ Yes: Check API logs for errors
│   ├─ AuthenticationError → Check JWT secret
│   ├─ DatabaseError → Check DB connection
│   ├─ TimeoutError → Scale up replicas
│   └─ ValidationError → Check input validation
│
├─ No: Check response time
   ├─ P95 > 500ms → Database slow?
   │   ├─ Yes: Check slow queries, create indexes
   │   └─ No: Check external APIs
   │
   └─ P95 < 500ms → Look at throughput
       ├─ High volume? → Scale up
       └─ Normal volume? → Check for memory leaks
```

### Example: High CPU Usage

1. **Observe**: Dashboard shows CPU > 85%
2. **Drill down**: Check which pods using most CPU
   ```bash
   kubectl top pods -n production --sort-by=cpu
   ```
3. **Analyze**: Profile the running code
   ```bash
   # In pod
   python -m cProfile -o profile.stats main:app
   ```
4. **Identify**: bottleneck (e.g., N+1 queries)
5. **Fix**: Optimize query or add caching
6. **Verify**: CPU drops below threshold

### Example: High Latency

1. **Observe**: P95 response time > 1000ms
2. **Check database**: Is DB query slow?
   ```sql
   SELECT query, calls, mean_time FROM pg_stat_statements 
   ORDER BY mean_time DESC LIMIT 5;
   ```
3. **If slow query found**:
   - Check if indexes exist
   - Run ANALYZE
   - Consider pagination
4. **If not database**:
   - Check external API calls
   - Look for blocking operations
   - Check network latency

### Example: High Memory Usage

1. **Observe**: Memory > 85%
2. **Check trend**: Is it growing over time (leak)?
3. **Identify memory-heavy endpoints**:
   ```bash
   kubectl logs deployment/betting-api | grep "memory"
   ```
4. **Options**:
   - Increase memory limits
   - Fix memory leak in code
   - Reduce batch sizes
   - Add rate limiting

---

## Custom Metrics Setup

### Prometheus Scrape Config

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'betting-api'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - production
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: betting-api
      - source_labels: [__meta_kubernetes_pod_port_name]
        action: keep
        regex: metrics

  - job_name: 'postgres'
    static_configs:
      - targets: ['prod-db.example.com:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['prod-cache.example.com:9121']
```

### Datadog Agent Config

```yaml
# datadog.yaml
api_key: <YOUR_API_KEY>
site: datadoghq.com

# Custom metrics
custom_metrics:
  - name: bets.placed
    type: gauge
    
apm:
  enabled: true
  port: 8126

logs:
  enabled: true
  config:
    - type: file
      path: /var/log/betting-api.log
      service: betting-api
      source: python
```

### Instrument Code

```python
from datadog import initialize, api
from statsd import StatsClient

# Initialize Datadog
options = {
    'api_key': os.getenv('DD_API_KEY'),
    'app_key': os.getenv('DD_APP_KEY')
}
initialize(**options)

# StatsD client for metrics
statsd = StatsClient(host='localhost', port=8125)

# In FastAPI endpoint
@app.post("/api/place-bet")
def place_bet(request: BetCreate):
    start_time = time.time()
    
    try:
        # Place bet logic
        bet = create_bet(request)
        
        # Track metric
        duration_ms = (time.time() - start_time) * 1000
        statsd.timing('api.request.duration_ms', duration_ms, 
                     tags=[f"endpoint:/place-bet", "status:success"])
        statsd.increment('bets.placed', 
                        tags=[f"vertical:{bet.vertical}"])
        
        return bet
        
    except Exception as e:
        statsd.increment('api.errors',
                        tags=[f"error_code:{e.error_code}"])
        raise
```

---

## Alert Tuning

### Reduce False Positives

**Before**: Alert on every database query > 100ms
**After**: Alert when P95 query latency > 100ms for 10 consecutive minutes

**Before**: Alert on any memory spike
**After**: Alert when memory > 80% AND growing at > 5%/min

**Before**: Alert on high error rate at any time
**After**: Alert on error rate > 1% during business hours (8 AM - 8 PM)

### Escalation Policies

```
P1 (Critical): Page on-call immediately
  └─ Escalate to manager if no response in 5 min

P2 (High): Slack notification + email
  └─ Escalate to on-call if no ack in 15 min

P3 (Medium): Slack notification only
  └─ Create ticket for business hours

P4 (Low): Daily digest email
  └─ Review and close non-critical issues
```

---

## Monitoring Checklist

- [ ] All 5 verticals showing operational status
- [ ] API response times < 500ms P95
- [ ] Error rate < 0.5%
- [ ] Database replication lag < 1 second
- [ ] Cache hit rate > 90%
- [ ] CPU usage < 70%
- [ ] Memory usage < 75%
- [ ] Disk usage < 80%
- [ ] All alerts configured and tuned
- [ ] Logs being collected and searchable
- [ ] Dashboards loading and updating
- [ ] SLO tracking accurate
- [ ] No data loss incidents
- [ ] Incident response time < SLA
- [ ] Post-mortem reviews completed
