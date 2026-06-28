# Production Runbook - Betting Framework

**Last Updated**: 2026-06-28  
**Version**: 1.0.0  
**On-Call**: Rotate weekly, escalation via Slack #ops  
**SLA**: 99.5% uptime, P50 < 100ms, P99 < 1000ms

---

## Table of Contents

1. [Monitoring](#monitoring)
2. [Debugging](#debugging)
3. [Common Issues & Fixes](#common-issues--fixes)
4. [Scaling & Performance](#scaling--performance)
5. [Incident Response](#incident-response)
6. [Maintenance Windows](#maintenance-windows)

---

## Monitoring

### Dashboard Access

**Primary Dashboard**: https://datadog.betting-framework.ai/dashboard/betting-prod
- Real-time metrics for all 5 verticals
- User activity and transaction volume
- API latency and error rates
- Database performance and connection pool status

**Backup Dashboard**: https://monitoring.betting-framework.ai/grafana/

### Key Metrics to Watch

```yaml
API Performance:
  - Request Rate: target > 100 req/s, alert if > 1000 req/s
  - Response Time P50: target < 100ms, alert if > 200ms
  - Response Time P95: target < 500ms, alert if > 1000ms
  - Response Time P99: target < 1000ms, alert if > 2000ms
  - Error Rate: target < 0.1%, alert if > 1%
  - 5xx Error Rate: alert if > 0.01%

Database:
  - Query Latency P95: target < 50ms, alert if > 100ms
  - Connection Pool Usage: alert if > 80% of max
  - Replication Lag: alert if > 1s
  - Disk Usage: alert if > 80%
  - Transaction Rollback Rate: alert if > 0.1%

Cache (Redis):
  - Hit Rate: target > 95%, alert if < 80%
  - Eviction Rate: alert if > 0
  - Memory Usage: alert if > 80%
  - Connection Count: alert if > 100

Infrastructure:
  - CPU Usage: alert if > 75%
  - Memory Usage: alert if > 80%
  - Disk Usage: alert if > 85%
  - Network I/O: alert if saturated
  - Pod Restart Count: alert if > 0

Application:
  - Active Users: track daily/hourly
  - Bets Placed/Hour: track volume
  - Settlement Success Rate: target > 99.9%
  - Kelly Calculator Success Rate: target > 99.5%
  - Portfolio Health Score: target > 0.8
```

### Alert Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| API Error Rate | 0.5% | 1.0% | Page on-call |
| Database Query Latency | 75ms | 150ms | Check slow queries |
| API Response Time P95 | 700ms | 1500ms | Check logs for bottleneck |
| Connection Pool Usage | 70% | 85% | Increase pool size |
| Disk Usage | 75% | 85% | Cleanup old logs/data |
| Memory Usage | 75% | 85% | Check for memory leaks |
| Pod Restart Count | 1 | 3+ | Investigate pod crashes |

### Log Locations

```bash
# Application logs
tail -f /var/log/betting-framework/app.log
tail -f /var/log/betting-framework/error.log

# Database logs
tail -f /var/log/postgresql/postgresql.log

# Infrastructure logs
# Railway: https://railway.app/project/[project-id]/logs
# Kubernetes: kubectl logs -f deployment/betting-api -n production

# Centralized logging (ELK/Datadog)
# Query: service:betting-api AND level:ERROR
# Link: https://logs.betting-framework.ai
```

---

## Debugging

### Enable Debug Logging

```bash
# Increase log level temporarily
kubectl set env deployment/betting-api LOG_LEVEL=debug -n production

# Monitor logs
kubectl logs -f deployment/betting-api -n production

# Revert to production log level
kubectl set env deployment/betting-api LOG_LEVEL=info -n production
```

### Check Health Endpoints

```bash
# Full health check
curl -s https://api.betting-framework.ai/health | jq .

# Database health
curl -s https://api.betting-framework.ai/health/database | jq .

# Readiness (for load balancer)
curl -s https://api.betting-framework.ai/health/ready | jq .

# Liveness (for Kubernetes)
curl -s https://api.betting-framework.ai/health/live | jq .
```

### Database Debugging

```bash
# Connect to production database
psql -U prod_user -h prod-db.example.com -d betting_db

# Check current connections
SELECT * FROM pg_stat_activity;

# Find long-running queries
SELECT pid, usename, application_name, state, query, query_start 
FROM pg_stat_activity 
WHERE state != 'idle' 
ORDER BY query_start DESC;

# Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables 
WHERE schemaname NOT IN ('pg_catalog','information_schema') 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

# Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch 
FROM pg_stat_user_indexes 
ORDER BY idx_scan DESC;

# Monitor replication lag
SELECT slot_name, restart_lsn, confirmed_flush_lsn FROM pg_replication_slots;
```

### API Debugging

```bash
# Test specific endpoint with verbose output
curl -v -X GET https://api.betting-framework.ai/api/bankroll \
  -H "Authorization: Bearer <token>" \
  -H "X-Request-ID: debug-123"

# Check response headers
curl -I https://api.betting-framework.ai/health

# Test with timing
curl -w "@curl-format.txt" -o /dev/null -s https://api.betting-framework.ai/health

# Monitor real-time requests (tcpdump)
sudo tcpdump -i eth0 -A 'tcp port 443' | grep -i "GET\|POST"
```

### Cache (Redis) Debugging

```bash
# Connect to Redis
redis-cli -h prod-cache.example.com -p 6379

# Check memory
INFO memory

# Check connected clients
INFO clients

# List keys matching pattern
KEYS "user:*"

# Check specific key
GET "user:123:token"

# Monitor commands in real-time
MONITOR

# Check replication status
INFO replication

# Clear cache if needed (use cautiously!)
FLUSHDB ASYNC
```

### Kubernetes Debugging

```bash
# Get all pods
kubectl get pods -n production

# Check pod logs
kubectl logs -f betting-api-5d4f8c7b9-xyz123 -n production

# Describe pod for events
kubectl describe pod betting-api-5d4f8c7b9-xyz123 -n production

# Execute command in pod
kubectl exec -it betting-api-5d4f8c7b9-xyz123 -n production -- bash

# Check resource usage
kubectl top pods -n production

# Check deployment status
kubectl rollout status deployment/betting-api -n production

# Check recent changes
kubectl rollout history deployment/betting-api -n production

# Scale deployment
kubectl scale deployment betting-api --replicas=5 -n production
```

---

## Common Issues & Fixes

### 1. High API Error Rate (500 errors)

**Symptoms**: 
- Dashboard shows error rate > 1%
- Users reporting API failures
- Logs showing "Internal Server Error"

**Investigation**:
```bash
# Check recent errors
kubectl logs deployment/betting-api -n production | grep ERROR | tail -50

# Check application health
curl -s https://api.betting-framework.ai/health | jq .

# Check database status
psql -U prod_user -h prod-db.example.com -d betting_db -c "SELECT 1"

# Check memory/CPU
kubectl top pods -n production | grep betting-api
```

**Solutions** (in order):
1. **Restart pods** (if temporary memory leak)
   ```bash
   kubectl rollout restart deployment/betting-api -n production
   kubectl rollout status deployment/betting-api -n production
   ```

2. **Increase memory limits**
   ```bash
   kubectl set resources deployment/betting-api \
     --limits=memory=2Gi,cpu=1000m \
     --requests=memory=1Gi,cpu=500m \
     -n production
   ```

3. **Increase replicas**
   ```bash
   kubectl scale deployment/betting-api --replicas=6 -n production
   ```

4. **Rollback to previous version**
   ```bash
   kubectl rollout undo deployment/betting-api -n production
   kubectl rollout status deployment/betting-api -n production
   ```

### 2. Database Connection Pool Exhausted

**Symptoms**:
- Errors: "too many connections" or "connection timeout"
- Query latency increases
- API errors with database connection errors

**Investigation**:
```bash
# Check active connections
psql -c "SELECT count(*) FROM pg_stat_activity WHERE state != 'idle';"

# See what queries are running
psql -c "SELECT pid, usename, query, query_start FROM pg_stat_activity WHERE state != 'idle';"

# Check connection pool in app
kubectl exec -it [pod] -n production -- \
  curl -s localhost:8000/metrics | grep db_pool_size
```

**Solutions**:
1. **Increase connection pool size**
   ```bash
   kubectl set env deployment/betting-api DB_POOL_SIZE=30 -n production
   kubectl rollout restart deployment/betting-api -n production
   ```

2. **Kill long-running queries**
   ```bash
   # Find query to kill
   SELECT pid FROM pg_stat_activity WHERE query_start < now() - interval '30 minutes';
   
   # Kill it
   SELECT pg_terminate_backend(pid);
   ```

3. **Increase database max connections**
   ```sql
   ALTER SYSTEM SET max_connections = 500;
   SELECT pg_reload_conf();
   ```

### 3. Slow API Response Times

**Symptoms**:
- Response time P95 > 1000ms
- Users report slow application
- "Slow query" logs

**Investigation**:
```bash
# Enable query logging
kubectl set env deployment/betting-api LOG_SQL_QUERIES=true -n production

# Find slow queries
kubectl logs deployment/betting-api -n production | grep "Query took" | sort -k3 -rn | head -20

# Check database query performance
psql -c "SELECT query, calls, total_time, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Check for missing indexes
psql -c "SELECT schemaname, tablename, attname FROM pg_stat_user_columns WHERE null_frac > 0.1;"
```

**Solutions**:
1. **Create missing indexes**
   ```sql
   -- If lots of queries on user_id and created_at
   CREATE INDEX CONCURRENTLY idx_bets_user_id_created_at ON bets(user_id, created_at DESC);
   
   -- Check index creation progress
   SELECT * FROM pg_stat_progress_create_index;
   ```

2. **Analyze table statistics**
   ```sql
   ANALYZE bets;
   ANALYZE positions;
   ANALYZE users;
   ```

3. **Enable query result caching** (Redis)
   ```bash
   kubectl set env deployment/betting-api CACHE_RESPONSES=true -n production
   kubectl set env deployment/betting-api CACHE_TTL=300 -n production
   ```

4. **Increase API replicas**
   ```bash
   kubectl scale deployment/betting-api --replicas=8 -n production
   ```

### 4. Redis Cache Failures

**Symptoms**:
- Cache hit rate drops below 50%
- Errors: "Redis connection refused"
- Increased database load

**Investigation**:
```bash
# Check Redis connectivity
redis-cli -h prod-cache.example.com ping

# Check memory usage
redis-cli -h prod-cache.example.com INFO memory

# Check connected clients
redis-cli -h prod-cache.example.com INFO clients

# Check eviction rate
redis-cli -h prod-cache.example.com INFO stats | grep evicted
```

**Solutions**:
1. **Restart Redis**
   ```bash
   # If using managed service, restart from provider dashboard
   # If self-hosted:
   systemctl restart redis-server
   ```

2. **Increase Redis memory**
   ```bash
   # Update cloud provider settings to increase maxmemory
   # Then restart: systemctl restart redis-server
   ```

3. **Change eviction policy** (from provider dashboard or redis.conf)
   ```
   maxmemory-policy allkeys-lru  # Keep most recently used keys
   ```

4. **Flush old cache data**
   ```bash
   redis-cli -h prod-cache.example.com FLUSHDB ASYNC
   ```

### 5. Database Disk Space Full

**Symptoms**:
- Errors: "No space left on device"
- Write operations failing
- Backup jobs failing

**Investigation**:
```bash
# Check disk usage
df -h /var/lib/postgresql

# Check largest tables
psql -c "
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables 
WHERE schemaname NOT IN ('pg_catalog','information_schema') 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC 
LIMIT 10;"

# Check for bloated tables
psql -c "SELECT schemaname, tablename, round(100*live_tuples/(live_tuples+dead_tuples)) FROM pg_stat_user_tables ORDER BY live_tuples+dead_tuples DESC LIMIT 10;"
```

**Solutions**:
1. **Delete old logs and data**
   ```sql
   -- Delete audit logs older than 90 days
   DELETE FROM audit_logs WHERE created_at < now() - interval '90 days';
   
   -- Delete old bets (settled and closed)
   DELETE FROM bets WHERE status = 'SETTLED' AND settled_at < now() - interval '1 year';
   
   -- Vacuum to reclaim space
   VACUUM FULL audit_logs;
   VACUUM FULL bets;
   ```

2. **Expand disk volume**
   ```bash
   # In cloud provider console, expand volume and restart database
   # Then run ANALYZE to update query planner
   ```

3. **Archive old data**
   ```bash
   # Dump and delete old data
   pg_dump betting_db -t bets --where="settled_at < now() - interval '1 year'" > archive_$(date +%s).sql
   DELETE FROM bets WHERE settled_at < now() - interval '1 year';
   ```

### 6. Authentication Token Expiration Issues

**Symptoms**:
- Users getting 401 Unauthorized
- Error: "token has expired"
- After several hours of inactivity

**Investigation**:
```bash
# Check token expiration setting
kubectl get env deployment/betting-api | grep TOKEN_EXPIRE

# Check auth logs
kubectl logs deployment/betting-api -n production | grep "token.*expired"
```

**Solutions**:
1. **Increase token expiration**
   ```bash
   kubectl set env deployment/betting-api ACCESS_TOKEN_EXPIRE_MINUTES=1440 -n production  # 24 hours
   kubectl rollout restart deployment/betting-api -n production
   ```

2. **Implement refresh token flow**
   - Frontend should call `/api/auth/refresh` before token expires
   - Add refresh token endpoint to API if not exists

3. **Enable token caching**
   ```bash
   kubectl set env deployment/betting-api CACHE_TOKENS=true -n production
   ```

### 7. Bet Settlement Failures

**Symptoms**:
- Bets stuck in "PENDING" or "PLACED" status
- Users unable to settle positions
- Settlement queue backing up

**Investigation**:
```bash
# Check settlement worker status
kubectl logs deployment/settlement-worker -n production | tail -100

# Count stuck bets
psql -c "SELECT status, COUNT(*) FROM bets GROUP BY status;"

# Check for errors in settlement service
psql -c "SELECT * FROM audit_logs WHERE event_type = 'BET_SETTLEMENT' AND status = 'FAILED' LIMIT 10;"
```

**Solutions**:
1. **Restart settlement worker**
   ```bash
   kubectl rollout restart deployment/settlement-worker -n production
   ```

2. **Clear stuck jobs from queue**
   ```bash
   # Using Celery/RQ to clear stuck tasks
   celery -A tasks purge  # WARNING: clears entire queue
   
   # Or manually mark bets as settled
   psql -c "
   UPDATE bets 
   SET status = 'SETTLED', settled_at = now() 
   WHERE status = 'PLACED' AND placed_at < now() - interval '24 hours';"
   ```

3. **Manually trigger settlement for specific bet**
   ```bash
   # Make API call to settle bet
   curl -X POST https://api.betting-framework.ai/api/settle \
     -H "Authorization: Bearer <token>" \
     -d '{"bet_id": "123"}'
   ```

---

## Scaling & Performance

### Auto-Scaling Configuration

```yaml
# Kubernetes HPA (Horizontal Pod Autoscaler)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: betting-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: betting-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
```

### Manual Scaling

```bash
# Scale up
kubectl scale deployment/betting-api --replicas=8 -n production

# Scale down
kubectl scale deployment/betting-api --replicas=3 -n production

# Monitor scaling
watch kubectl get hpa -n production
```

### Load Testing

```bash
# Run load test (before peak hours)
# Using Apache Bench
ab -n 10000 -c 100 https://api.betting-framework.ai/health

# Using wrk
wrk -t4 -c100 -d30s https://api.betting-framework.ai/health

# Monitor during test
watch -n1 'kubectl top pods -n production | grep betting-api'
```

### Database Optimization

```bash
# Run ANALYZE to update statistics
psql -c "ANALYZE;"

# Identify unused indexes
SELECT schemaname, tablename, indexname, idx_scan 
FROM pg_stat_user_indexes 
WHERE idx_scan = 0 
AND indexname NOT LIKE 'pg_%'
LIMIT 20;

# Drop unused indexes (after confirmation)
DROP INDEX CONCURRENTLY idx_unused_index;

# Reindex fragmented indexes
REINDEX TABLE bets;

# Check table bloat
SELECT schemaname, tablename, round(100 * (pg_total_relation_size(schemaname||'.'||tablename) - pg_total_relation_size(schemaname||'.'||tablename, 'main')) / pg_total_relation_size(schemaname||'.'||tablename))::text || '%' AS bloat_ratio 
FROM pg_tables 
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## Incident Response

### Severity Levels

| Level | Response Time | Examples |
|-------|---------------|----------|
| P1 (Critical) | Immediate (< 5 min) | Total outage, data loss, security breach |
| P2 (High) | 15 minutes | Major feature broken, error rate > 5% |
| P3 (Medium) | 30 minutes | Degraded performance, single component down |
| P4 (Low) | 4 hours | Minor issues, cosmetic bugs |

### Incident Declaration

1. **Declare incident in Slack**
   ```
   @channel INCIDENT DECLARED - Betting Framework API
   Severity: P2
   Impact: Login not working
   Status: Investigating
   ETA: 15 minutes
   ```

2. **Page on-call engineer**
   - Use PagerDuty or equivalent
   - Include incident description and severity

3. **Open war room**
   - Create Slack channel: #incident-2026-06-28-001
   - Add relevant team members
   - Schedule Zoom call if needed

### War Room Workflow

```
Time  | Activity                    | Owner
------|-----------------------------|---------
T+0   | Declare incident             | On-call
T+2   | Initial triage               | Team
T+5   | Root cause hypothesis        | Tech lead
T+10  | Implement fix                | Engineer
T+15  | Deploy fix / Verify resolved | DevOps
T+20  | Communicate resolution       | Product
T+30  | Begin post-mortem            | Team
```

### Post-Incident

1. **Write incident report** (within 24 hours)
   - What happened
   - Timeline
   - Root cause
   - Impact (downtime, data affected)
   - Resolution
   - Prevention measures

2. **Schedule post-mortem** (within 48 hours)
   - Review incident report
   - Discuss timeline
   - Identify action items
   - Assign owners for fixes

3. **Track improvements**
   - Create tickets for action items
   - Prioritize high-impact items
   - Track resolution progress

---

## Maintenance Windows

### Planned Maintenance Schedule

| Frequency | Window | Activities | Duration |
|-----------|--------|-----------|----------|
| Weekly | Tue 2-3 AM UTC | Security patches | 1 hour |
| Monthly | First Sat 2-4 AM UTC | Major updates, DB maintenance | 2 hours |
| Quarterly | End of quarter | Infrastructure upgrades | 4 hours |

### Pre-Maintenance Checklist

- [ ] Schedule announced 7 days prior
- [ ] No major sporting events scheduled during window
- [ ] Team members available and assigned
- [ ] Backup created
- [ ] Rollback plan documented
- [ ] Stakeholders notified
- [ ] Support team on standby

### Maintenance Procedure

```bash
# 1. Notify users (30 min before)
# Post to status page, send email

# 2. Enable maintenance mode
kubectl set env deployment/betting-api MAINTENANCE_MODE=true -n production

# 3. Perform maintenance (DB optimization, etc.)
psql -c "ANALYZE;"
psql -c "VACUUM ANALYZE;"

# 4. Restart services gracefully
kubectl rollout restart deployment/betting-api -n production
kubectl rollout status deployment/betting-api -n production

# 5. Run health checks
curl -s https://api.betting-framework.ai/health | jq .

# 6. Disable maintenance mode
kubectl set env deployment/betting-api MAINTENANCE_MODE=false -n production

# 7. Notify completion
# Post to status page, send email
```

### Database Maintenance

```bash
# Weekly: Analyze statistics
ANALYZE;

# Weekly: Vacuum bloated tables
VACUUM ANALYZE bets;
VACUUM ANALYZE positions;

# Monthly: Full vacuum
VACUUM FULL bets;
VACUUM FULL positions;

# Quarterly: Reindex
REINDEX TABLE bets;
REINDEX TABLE positions;
```

---

## On-Call Handoff

**Every Monday at 9 AM UTC**, outgoing on-call gives handoff to incoming:

1. **Review incidents** from past week
2. **Discuss known issues** that may re-occur
3. **Share tips** and workarounds
4. **Review alerts** configuration
5. **Check upcoming events** that might cause load

**Handoff template**:
```
Previous week incidents:
- [Date] API error rate spike (RESOLVED)
- [Date] Database connection pool issue (ONGOING - watch for recurrence)

Known issues to watch:
- Tennis API sometimes slow on match days
- Email delivery slow during peak hours

Alerts to tune:
- Consider increasing threshold for X
- Consider adding alert for Y

Upcoming events:
- Wimbledon starts [date] - expect 3-5x traffic
- NBA Finals [date] - expect spike in baseball betting
```
