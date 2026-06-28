# Operations Guide - Production Betting Framework

**Last Updated**: 2026-06-28  
**Version**: 1.0.0  
**Ops Owner**: DevOps Team  
**On-Call Rotation**: Weekly (Mon-Sun)

---

## Table of Contents

1. [Daily Operations](#daily-operations)
2. [Weekly Maintenance](#weekly-maintenance)
3. [Monthly Audits](#monthly-audits)
4. [Quarterly Reviews](#quarterly-reviews)
5. [Annual Planning](#annual-planning)
6. [On-Call Procedures](#on-call-procedures)
7. [Incident Tracking](#incident-tracking)
8. [Documentation Maintenance](#documentation-maintenance)

---

## Daily Operations

### Morning Check (9:00 AM UTC)

Run this checklist every morning before business hours:

```bash
#!/bin/bash
# morning_check.sh

echo "=== BETTING FRAMEWORK MORNING CHECK ==="
echo "Time: $(date)"
echo ""

# 1. Health check
echo "1. Health Check..."
health=$(curl -s https://api.betting-framework.ai/health)
status=$(echo "$health" | jq -r '.status')
echo "  Status: $status"

if [ "$status" != "healthy" ]; then
    echo "  ⚠️  WARNING: System not fully healthy!"
    echo "$health" | jq .
fi

# 2. Check database
echo ""
echo "2. Database Status..."
db_status=$(echo "$health" | jq -r '.database.status')
echo "  Database: $db_status"

# 3. Check verticals
echo ""
echo "3. Verticals Status..."
echo "$health" | jq '.verticals'

# 4. Check recent errors
echo ""
echo "4. Recent Errors (last hour)..."
error_count=$(kubectl logs -n production deployment/betting-api --since=1h | grep -c "ERROR")
echo "  Errors in last hour: $error_count"

# 5. Performance metrics
echo ""
echo "5. Performance Metrics..."
# Note: Would integrate with your monitoring tool
# Example using curl to Datadog API
# curl -s "https://api.datadoghq.com/api/v1/query..." | jq .

# 6. Disk usage
echo ""
echo "6. Disk Usage..."
df -h / | tail -1

echo ""
echo "=== MORNING CHECK COMPLETE ==="
```

**Run daily**:
```bash
chmod +x morning_check.sh
./morning_check.sh > logs/morning_check_$(date +%Y%m%d).log
```

### Hourly Monitoring (During Business Hours)

| Time | Task | Owner |
|------|------|-------|
| Every hour | Check error rate dashboard | On-call |
| Every hour | Review alerts in Slack | On-call |
| Every 2 hours | Check database replication lag | On-call |
| Every 4 hours | Verify backup completion | DevOps |

### Evening Check (6:00 PM UTC)

1. **Review daily errors**
   ```bash
   kubectl logs -n production deployment/betting-api --since=24h | grep ERROR | tail -50
   ```

2. **Check settling system**
   ```bash
   psql -c "SELECT COUNT(*) FROM bets WHERE status IN ('PENDING', 'PLACED', 'MATCHED');"
   ```

3. **Verify backups completed**
   ```bash
   ls -lh backups/ | tail -5
   ```

4. **Document any issues**
   - Create ticket for any anomalies
   - Note in shared log for next team

### Daily Tasks Checklist

- [ ] Morning health check passed
- [ ] No critical alerts in last 24h
- [ ] Error rate < 0.5%
- [ ] Database replication lag < 1 sec
- [ ] All 5 verticals operational
- [ ] Cache hit rate > 90%
- [ ] Disk usage monitored
- [ ] Backups completed successfully
- [ ] No pending data loss issues
- [ ] Evening summary documented

---

## Weekly Maintenance

### Weekly Maintenance Window

**Schedule**: Tuesday 2:00 AM - 3:00 AM UTC  
**Owner**: DevOps Lead  
**Backup**: Senior DevOps Engineer

### Pre-Maintenance (Monday)

- [ ] Schedule maintenance notification (48h notice)
- [ ] Review pending updates
- [ ] Test updates in staging
- [ ] Prepare rollback plan
- [ ] Notify support team
- [ ] Check no major sporting events

### Maintenance Tasks

#### 1. Security Patches (0:00 - 0:15)

```bash
# Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# Update Python dependencies
pip install --upgrade -r requirements.txt
pip check  # Check for conflicts

# Run security scan
bandit -r backend/

# Check for vulnerabilities
safety check
```

#### 2. Database Optimization (0:15 - 0:30)

```bash
# Connect to database
psql -U prod_user -h prod-db.example.com -d betting_db

# Analyze statistics
ANALYZE;

# Vacuum tables
VACUUM ANALYZE bets;
VACUUM ANALYZE positions;
VACUUM ANALYZE users;
VACUUM ANALYZE audit_logs;

# Check table bloat
SELECT schemaname, tablename, 
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables 
WHERE schemaname NOT IN ('pg_catalog','information_schema') 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

#### 3. Index Optimization (0:30 - 0:45)

```bash
psql -U prod_user -h prod-db.example.com -d betting_db

# Reindex fragmented indexes
REINDEX TABLE CONCURRENTLY bets;
REINDEX TABLE CONCURRENTLY positions;

# Find and drop unused indexes
SELECT schemaname, tablename, indexname, idx_scan 
FROM pg_stat_user_indexes 
WHERE idx_scan = 0 AND indexname NOT LIKE 'pg_%' LIMIT 20;

-- Drop unused (if confirmed safe):
-- DROP INDEX CONCURRENTLY idx_unused_name;
```

#### 4. Log Cleanup (0:45 - 0:55)

```bash
# Archive old logs
tar -czf logs/archive_$(date +%Y%m%d).tar.gz logs/*.log

# Delete logs older than 7 days
find logs -name "*.log" -mtime +7 -delete

# Check disk usage
du -sh logs/
```

#### 5. System Restart (0:55 - 1:00)

```bash
# If needed, restart API gracefully
kubectl rollout restart deployment/betting-api -n production
kubectl rollout status deployment/betting-api -n production

# Verify health
curl -s https://api.betting-framework.ai/health | jq .
```

### Post-Maintenance (Tuesday)

- [ ] Verify all systems operational
- [ ] Review maintenance logs
- [ ] Check error rate hasn't increased
- [ ] Notify stakeholders of completion
- [ ] Document any issues found
- [ ] Update maintenance log entry

### Weekly Checklist

- [ ] Security patches applied
- [ ] Database optimized
- [ ] Indexes analyzed and cleaned
- [ ] Logs archived
- [ ] Backups verified
- [ ] No data inconsistencies
- [ ] All alerts still configured
- [ ] Documentation up-to-date

---

## Monthly Audits

### First Monday of Month (9:00 AM UTC)

#### 1. Access Audit (30 minutes)

**Verify**: All users with production access are still authorized

```bash
#!/bin/bash
# audit_access.sh

echo "=== PRODUCTION ACCESS AUDIT ==="

# 1. Check database users
echo "Database users:"
psql -U prod_user -h prod-db.example.com -d betting_db -c "SELECT usename FROM pg_user;"

# 2. Check Kubernetes RBAC
echo ""
echo "Kubernetes roles:"
kubectl get rolebindings -n production -o wide

# 3. Check SSH keys
echo ""
echo "SSH authorized keys:"
cat ~/.ssh/authorized_keys | wc -l

# 4. Check recent logins
echo ""
echo "Recent production logins:"
last -f /var/log/wtmp | head -20
```

**Action**: Remove any unauthorized access

#### 2. Data Integrity Check (45 minutes)

```sql
-- Run monthly integrity checks
BEGIN;

-- Check for orphaned records
SELECT COUNT(*) as orphaned_bets
FROM bets b
WHERE NOT EXISTS (SELECT 1 FROM users u WHERE u.id = b.user_id);

SELECT COUNT(*) as orphaned_positions
FROM positions p
WHERE NOT EXISTS (SELECT 1 FROM bets b WHERE b.id = p.bet_id);

-- Check for duplicate entries
SELECT user_id, COUNT(*) 
FROM users 
GROUP BY user_id 
HAVING COUNT(*) > 1;

-- Verify audit logs integrity
SELECT COUNT(*) as total_logs FROM audit_logs;
SELECT COUNT(DISTINCT user_id) as distinct_users FROM audit_logs;

-- Check for data gaps
SELECT 
  (SELECT MAX(created_at) FROM bets) as latest_bet,
  (SELECT MAX(created_at) FROM audit_logs) as latest_audit,
  (SELECT MAX(settled_at) FROM bets WHERE status='SETTLED') as latest_settlement;

ROLLBACK;  -- Don't commit, just verify
```

#### 3. Performance Baseline (30 minutes)

```bash
# Measure and record monthly baseline
echo "=== MONTHLY PERFORMANCE BASELINE ==="
echo "Date: $(date)" > performance_baseline_$(date +%Y%m).log

# API latency
kubectl top pods -n production >> performance_baseline_$(date +%Y%m).log

# Database performance
psql -c "SELECT 
  (SELECT COUNT(*) FROM pg_stat_statements) as total_queries,
  (SELECT MAX(mean_time) FROM pg_stat_statements) as slowest_query_ms,
  (SELECT AVG(mean_time) FROM pg_stat_statements) as avg_query_ms;" >> performance_baseline_$(date +%Y%m).log

# Cache statistics
redis-cli -h prod-cache.example.com INFO stats >> performance_baseline_$(date +%Y%m).log
```

#### 4. Security Audit (1 hour)

```bash
# 1. Check for exposed secrets
grep -r "password" backend/*.py | grep -v "hashed" | grep -v "#" || echo "No hardcoded passwords found"

# 2. Check SSL certificate expiration
echo "SSL Certificate expiration:"
openssl s_client -connect api.betting-framework.ai:443 -showcerts 2>/dev/null | \
  openssl x509 -noout -dates

# 3. Run security scanner
bandit -r backend/ > security_audit_$(date +%Y%m).log

# 4. Check for vulnerable dependencies
safety check > dependency_audit_$(date +%Y%m).log

# 5. Review auth logs for anomalies
kubectl logs -n production deployment/betting-api --since=720h | \
  grep "AUTH_FAILED\|UNAUTHORIZED" | wc -l
```

#### 5. Backup Verification (30 minutes)

```bash
# Verify recent backups exist and are valid
echo "=== BACKUP VERIFICATION ==="

# Check backups created in last 7 days
find backups/ -name "*.sql" -mtime -7

# Verify backup integrity (try restoring to test DB)
pg_restore --verbose backups/pre_deployment_latest.sql -d betting_test 2>&1 | head -20

# Check backup size isn't growing unexpectedly
du -sh backups/

# Verify offsite copies
aws s3 ls s3://betting-framework-backups/ | tail -5
```

#### 6. Capacity Planning (30 minutes)

```bash
# Monitor growth trends
echo "=== CAPACITY METRICS ==="

# Database size trend
psql -c "SELECT 
  pg_size_pretty(pg_database_size('betting_db')) as db_size;"

# User growth
psql -c "SELECT COUNT(*) FROM users;"
psql -c "SELECT COUNT(*) FROM users WHERE created_at > now() - interval '30 days';"

# Data volume
psql -c "SELECT COUNT(*) FROM bets;"
psql -c "SELECT COUNT(*) FROM positions;"
psql -c "SELECT COUNT(*) FROM audit_logs;"

# Disk capacity
df -h /
```

### Monthly Checklist

- [ ] Access audit completed
- [ ] Data integrity verified
- [ ] No orphaned records
- [ ] Performance baseline recorded
- [ ] Security audit completed
- [ ] No vulnerabilities found
- [ ] Backups verified
- [ ] Capacity growth within limits
- [ ] SLOs being met
- [ ] Monthly report generated

---

## Quarterly Reviews

### End of Quarter (Last Friday of Q)

#### 1. Performance Review (2 hours)

- **Uptime**: Measure actual vs SLO (99.5%)
- **Response Time**: Compare P95 latency trends
- **Error Rate**: Review error trends and top errors
- **Scaling Events**: How many times did we scale?
- **Incidents**: Review P1/P2 incidents and MTTR

#### 2. Capacity Planning (1 hour)

- **Disk**: Current usage and growth trend
- **Database**: Table sizes and growth trajectory
- **Memory**: Peak usage and trends
- **CPU**: Peak usage and scaling readiness
- **Network**: Bandwidth utilization

#### 3. Security Review (1 hour)

- **Vulnerability**: Any new issues found?
- **Access**: Audit user permissions quarterly
- **Encryption**: Verify TLS and data encryption
- **Backups**: Test restore procedures
- **Logs**: Review for security anomalies

#### 4. Cost Review (30 min)

- **Cloud Costs**: Month-over-month trend
- **Database**: Dedicated vs shared, optimization opportunities
- **Cache**: Memory allocation vs usage
- **Storage**: Backup costs vs available budget
- **Optimization**: Where can we reduce costs?

### Quarterly Checklist

- [ ] Q performance metrics compiled
- [ ] SLO compliance reviewed
- [ ] Top issues analyzed
- [ ] Capacity projections updated
- [ ] Cost analysis completed
- [ ] Security posture assessed
- [ ] Team feedback collected
- [ ] Q report generated

---

## Annual Planning

### Annual Review (January, 2-3 days)

#### 1. Year-Over-Year Metrics

```
Availability:
  2025: 99.2%
  2026: 99.5% (target met)
  
Response Time P95:
  2025: 450ms average
  2026: 350ms average (improved 22%)
  
Error Rate:
  2025: 0.8% average
  2026: 0.3% average (improved 63%)
  
Users:
  2025: 5,000
  2026: 12,000 (140% growth)
  
Revenue:
  2025: $50,000
  2026: $130,000 (160% growth)
```

#### 2. Infrastructure Roadmap

- **Current**: 2 API instances, single-region DB
- **Q3 2026**: 5 API instances, multi-region replication
- **Q4 2026**: Global CDN, edge caching
- **2027**: Kubernetes multi-cluster, full HA setup

#### 3. Technology Updates

- **Python 3.10 → 3.12**: Plan upgrade path
- **FastAPI 0.100 → latest**: No breaking changes expected
- **PostgreSQL 13 → 15**: Plan upgrade and testing
- **Redis 6 → 7**: Compatibility verified

#### 4. Team Planning

- **Hiring**: Need 2 more DevOps engineers
- **Training**: Kubernetes certification for team
- **Tools**: Consider new monitoring solution (Datadog vs New Relic)
- **Documentation**: Maintain and update runbooks

### Annual Checklist

- [ ] Year metrics compiled
- [ ] Roadmap approved by leadership
- [ ] Budget allocated for 2027
- [ ] Team plan created
- [ ] Technology upgrades scheduled
- [ ] Risk assessment completed
- [ ] Strategy document created

---

## On-Call Procedures

### On-Call Rotation

**Schedule**: Weekly rotation starting Monday 9:00 AM UTC

```
Week 1: Alice (alice@example.com, +1-555-0001)
Week 2: Bob (bob@example.com, +1-555-0002)
Week 3: Carol (carol@example.com, +1-555-0003)
Week 4: Dave (dave@example.com, +1-555-0004)
```

### On-Call Responsibilities

**Daily**:
- Monitor alerts in Slack #ops
- Respond to P1/P2 incidents within SLA
- Check morning/evening status
- Document any issues

**During Incident**:
- Join war room (Slack or Zoom)
- Coordinate with team
- Implement fixes
- Keep stakeholders updated
- Document timeline

**End of Week**:
- Hand off to next on-call
- Summary of issues handled
- Known issues to watch for
- Recommend improvements

### Escalation

| Level | Response Time | Action |
|-------|---------------|--------|
| L1: Alert | Acknowledged in 5 min | On-call reads alert, determines severity |
| L2: Diagnosis | 15 min | Root cause identified, fix underway |
| L3: Escalation | 30 min | Manager/tech lead paged if not resolved |
| L4: Executive | 1 hour | Director/VP notified if ongoing |

### On-Call Support

- **Slack**: #ops channel for questions
- **Phone**: Use PagerDuty for calls
- **Resources**: Runbook at /docs/PRODUCTION_RUNBOOK.md
- **Tools**: Access to all monitoring dashboards
- **Admin**: Can restart services, modify configs

---

## Incident Tracking

### Incident Log Template

```
INCIDENT REPORT
Date: 2026-06-28
Severity: P2 (High)
Duration: 45 minutes
Status: RESOLVED

SUMMARY:
API returned 500 errors for 45 minutes due to database connection pool exhaustion.

TIMELINE:
10:30 UTC - Alert: Error rate > 1%
10:32 UTC - On-call investigates
10:35 UTC - Root cause: DB connections at max
10:38 UTC - Solution: Increase connection pool size
10:45 UTC - Deploy fix, system normalizing
11:15 UTC - All errors cleared, system healthy

ROOT CAUSE:
Slow queries from recent analytics job held connections,
preventing new connections to be established.

IMPACT:
- Error rate: 2.3% for 45 minutes
- Affected users: ~1,200
- Data loss: None
- Revenue impact: $500 (blocked transactions)

RESOLUTION:
1. Increased max_connections from 100 to 150
2. Added query timeout (30s) to analytics job
3. Optimized slow query with new index

ACTION ITEMS:
- [ ] Add analytics job to slow query monitoring (assigned: Alice)
- [ ] Document connection pool tuning (assigned: Bob)
- [ ] Load test with 150+ concurrent connections (assigned: Carol)

PREVENTION:
- Implement query governor to prevent runaway queries
- Add proactive alert when connection usage > 70%
```

### Monthly Incident Review

**First Wednesday of month, 2 PM UTC**

1. Review all incidents from past month
2. Identify trends (same issues recurring?)
3. Discuss prevention measures
4. Update runbooks with lessons learned
5. Plan improvements for next quarter

---

## Documentation Maintenance

### Documentation Checklist (Monthly)

- [ ] API_REFERENCE.md: Add new endpoints
- [ ] PRODUCTION_RUNBOOK.md: Update common issues
- [ ] DEPLOYMENT_CHECKLIST.md: Reflect process changes
- [ ] MONITORING.md: Update alert thresholds
- [ ] OPERATIONS.md: Document new procedures
- [ ] Architecture diagram: Keep current

### Annual Documentation Refresh

- Rewrite major sections for clarity
- Update all code examples
- Review all commands for accuracy
- Verify all external links still work
- Collect feedback from team

---

## Operations Dashboard

Create a one-page daily ops dashboard:

```
BETTING FRAMEWORK OPERATIONS DASHBOARD
Date: 2026-06-28

SYSTEM HEALTH
┌─────────────────────────────────────────┐
│ API Response Time P95: 250ms (OK)       │
│ Error Rate: 0.2% (OK)                   │
│ Database Latency P95: 35ms (OK)         │
│ Cache Hit Rate: 94% (OK)                │
│ Disk Usage: 65% (OK)                    │
│ Memory Usage: 72% (OK)                  │
│ Replica Lag: 150ms (OK)                 │
└─────────────────────────────────────────┘

BUSINESS METRICS
│ Bets Placed (24h): 5,234 (+12% vs avg)  │
│ Settlement Success: 99.97% (OK)         │
│ Portfolio Value: $125,430 (+2.3% d/d)   │
│ Sharpe Ratio (7d): 1.85 (Strong)        │
│ Win Rate (30d): 56.7% (Good)            │

ALERTS
┌─────────────────────────────────────────┐
│ Active: 0 Critical                      │
│ Active: 1 Warning (High response time   │
│         on tennis predictions)          │
│ This Week: 2 P2 incidents (RESOLVED)    │
└─────────────────────────────────────────┘

UPCOMING
- Tue 2 AM: Weekly maintenance window
- Fri 3 PM: Quarterly review meeting
- Wimbledon starts: July 1 (expect 3x traffic)

NOTES
- Database growing 2GB/week
- Need to plan scaling for July
- Tennis API latency needs investigation
```

---

## Operations Contacts

| Role | Name | Slack | Phone | Email |
|------|------|-------|-------|-------|
| Operations Lead | | @ops-lead | | |
| DevOps Engineer 1 | | | | |
| DevOps Engineer 2 | | | | |
| Database Admin | | | | |
| Security Lead | | | | |
| On-Call (Week) | | | | |

**Escalation**:
- L1: On-call engineer
- L2: Operations lead
- L3: VP of Engineering
- L4: CTO/CEO

---

## Quick Reference

### Emergency Commands

```bash
# Restart API
kubectl rollout restart deployment/betting-api -n production

# View recent logs
kubectl logs -f deployment/betting-api -n production

# Check pod status
kubectl get pods -n production

# Scale deployment
kubectl scale deployment/betting-api --replicas=8 -n production

# Database backup
pg_dump betting_db > backup_$(date +%s).sql

# Restore database
pg_restore backup_$(date +%s).sql -d betting_db

# Check disk space
df -h /

# Clear cache (careful!)
redis-cli FLUSHDB ASYNC
```

### Useful Metrics Queries

```sql
-- Current active bets
SELECT COUNT(*) FROM bets WHERE status IN ('PENDING', 'PLACED', 'MATCHED');

-- Win rate (last 30 days)
SELECT COUNT(*) FILTER (WHERE actual_outcome = 'win') * 100.0 / COUNT(*) 
FROM bets WHERE settled_at > now() - interval '30 days' AND status = 'SETTLED';

-- Revenue (commissions)
SELECT SUM(stake * 0.05) FROM bets WHERE created_at > now() - interval '24 hours';

-- Database growth rate
SELECT pg_size_pretty(pg_database_size('betting_db'));

-- Active connections
SELECT COUNT(*) FROM pg_stat_activity WHERE state != 'idle';
```

---

**Last Review**: 2026-06-28  
**Next Review**: 2026-07-28  
**Owner**: DevOps Team  
**Approval**: ✓ Approved by VP Engineering
