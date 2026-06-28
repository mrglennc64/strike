# Production Monitoring & Maintenance Guide
## strike.perfecthold.online

---

## QUICK STATUS COMMANDS

```bash
# All-in-one status check
cd /opt/strike && \
  echo "=== Docker Services ===" && \
  docker-compose -f docker-compose.prod.yml ps && \
  echo "" && \
  echo "=== API Health ===" && \
  curl -s http://localhost:8000/health | jq . && \
  echo "" && \
  echo "=== Disk Usage ===" && \
  df -h /opt/strike && \
  echo "" && \
  echo "=== Memory Usage ===" && \
  free -h
```

---

## DAILY MONITORING (Automated via Cron)

### Health Check Script (every 5 minutes)

Location: `/opt/strike/deploy/monitoring.sh`

Checks:
- Docker services status
- API health endpoint
- Database connectivity
- Redis connectivity
- Disk space (alert if < 10% free)
- Memory usage (alert if > 80%)

View logs:
```bash
tail -f /opt/strike/logs/monitoring.log
```

### Manual Daily Checks

```bash
#!/bin/bash
# Daily monitoring script

APP_DIR="/opt/strike"
cd "$APP_DIR"

echo "=== DAILY HEALTH CHECK ==="
echo "Time: $(date)"
echo ""

# Check services
echo "1. Docker Services:"
docker-compose -f docker-compose.prod.yml ps

# Check health
echo ""
echo "2. API Health:"
curl -s http://localhost:8000/health

# Check errors in logs
echo ""
echo "3. Recent Errors:"
docker-compose -f docker-compose.prod.yml logs --tail=50 | grep -i "error" | tail -5 || echo "No errors found"

# Check disk
echo ""
echo "4. Disk Space:"
df -h /opt/strike | tail -1

# Check database
echo ""
echo "5. Database Status:"
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# Check cron jobs
echo ""
echo "6. Cron Jobs:"
crontab -l | grep -E "strike|clv" | head -3

echo ""
echo "=== END HEALTH CHECK ==="
```

---

## WEEKLY MAINTENANCE

### Database Backup Verification

```bash
#!/bin/bash
# Weekly backup verification

APP_DIR="/opt/strike"
BACKUP_DIR="$APP_DIR/backups"

echo "=== WEEKLY BACKUP CHECK ==="
echo "Time: $(date)"
echo ""

# Create backup
echo "Creating backup..."
docker-compose -f "$APP_DIR/docker-compose.prod.yml" exec postgres \
  pg_dump -U betting_user betting_db > "$BACKUP_DIR/db_$(date +%Y%m%d).sql"

# Verify size
echo "Backup files:"
ls -lh "$BACKUP_DIR" | grep -E "db_.*sql" | tail -5

# Check disk space after backup
echo ""
echo "Disk usage:"
du -sh "$BACKUP_DIR"
df -h /opt/strike

# Alert if backup is too small
LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/db_*.sql 2>/dev/null | head -1)
if [ -z "$LATEST_BACKUP" ]; then
  echo "ERROR: No backup found!"
  exit 1
fi

SIZE=$(stat -f%z "$LATEST_BACKUP" 2>/dev/null || stat -c%s "$LATEST_BACKUP")
if [ "$SIZE" -lt 1000 ]; then
  echo "WARNING: Backup size is suspiciously small ($SIZE bytes)"
  exit 1
fi

echo "✓ Backup successful"
```

### Security Review

```bash
#!/bin/bash
# Weekly security review

APP_DIR="/opt/strike"

echo "=== WEEKLY SECURITY CHECK ==="
echo "Time: $(date)"
echo ""

# Check .env permissions
echo "1. File permissions:"
ls -la "$APP_DIR/.env"

# Verify .env not in git
echo ""
echo "2. Git check:"
cd "$APP_DIR"
git check-ignore .env && echo "✓ .env properly ignored" || echo "⚠ .env might be tracked"

# Check for exposed secrets
echo ""
echo "3. Secret exposure scan:"
git log --all -S "POSTGRES_PASSWORD" --oneline | wc -l
git log --all -S "SECRET_KEY" --oneline | wc -l
echo "(Should be 0)"

# SSL certificate expiration
echo ""
echo "4. SSL Certificate:"
sudo certbot certificates | grep -E "Expiration|strike" || echo "No certificate"

# Failed login attempts
echo ""
echo "5. Failed authentication:"
docker-compose -f "$APP_DIR/docker-compose.prod.yml" logs --tail=100 | grep -i "unauthorized\|forbidden" | wc -l

echo ""
echo "=== END SECURITY CHECK ==="
```

### Log Review

```bash
#!/bin/bash
# Weekly log analysis

APP_DIR="/opt/strike"

echo "=== WEEKLY LOG ANALYSIS ==="
echo ""

# Error count
echo "Error count (last 7 days):"
docker-compose -f "$APP_DIR/docker-compose.prod.yml" logs --tail=10000 | grep -i "error" | wc -l

# Warning count
echo "Warning count (last 7 days):"
docker-compose -f "$APP_DIR/docker-compose.prod.yml" logs --tail=10000 | grep -i "warning" | wc -l

# Performance issues
echo ""
echo "Slow queries or timeouts:"
docker-compose -f "$APP_DIR/docker-compose.prod.yml" logs --tail=10000 | grep -i "timeout\|slow" | wc -l

# Database issues
echo ""
echo "Database errors:"
docker-compose -f "$APP_DIR/docker-compose.prod.yml" logs --tail=10000 postgres | grep -i "error\|fatal" | tail -3

echo ""
echo "=== END LOG ANALYSIS ==="
```

---

## MONTHLY MAINTENANCE

### Docker Image Updates

```bash
#!/bin/bash
# Monthly Docker update

APP_DIR="/opt/strike"

echo "=== MONTHLY DOCKER UPDATE ==="
cd "$APP_DIR"

# Pull latest images
echo "Pulling latest images..."
docker-compose -f docker-compose.prod.yml pull

# Show available updates
echo ""
echo "Available updates:"
docker images | grep -E "postgres|redis|alpine" | awk '{print $1":"$2}'

# Update base images (careful with this)
echo ""
echo "Updating services..."
docker-compose -f docker-compose.prod.yml up -d

# Verify services are healthy
sleep 10
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "=== END DOCKER UPDATE ==="
```

### System Security Updates

```bash
#!/bin/bash
# Monthly security patches

echo "=== MONTHLY SECURITY UPDATES ==="
echo "Time: $(date)"

# List available updates
echo "Available updates:"
apt list --upgradable

# Apply security updates only (non-interactive)
echo ""
echo "Installing security updates..."
apt-get update
apt-get upgrade -y

# Check for Docker updates
echo ""
echo "Checking Docker..."
docker --version
docker-compose --version

# Check SSL certificate renewal
echo ""
echo "SSL certificate status:"
sudo certbot renew --dry-run

echo ""
echo "=== END SECURITY UPDATES ==="
```

### Database Optimization

```bash
#!/bin/bash
# Monthly database maintenance

APP_DIR="/opt/strike"

echo "=== MONTHLY DATABASE MAINTENANCE ==="
cd "$APP_DIR"

# Analyze tables
echo "Analyzing database..."
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U betting_user -d betting_db -c "ANALYZE;"

# Vacuum tables
echo "Vacuuming database..."
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U betting_user -d betting_db -c "VACUUM;"

# Check disk usage
echo ""
echo "Database size:"
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U betting_user -d betting_db -c "SELECT pg_size_pretty(pg_database_size('betting_db'));"

# Show table sizes
echo ""
echo "Table sizes:"
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U betting_user -d betting_db -c "SELECT tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables WHERE schemaname != 'pg_catalog' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"

echo ""
echo "=== END DATABASE MAINTENANCE ==="
```

### Backup Rotation

```bash
#!/bin/bash
# Monthly backup cleanup (keep last 30 days)

APP_DIR="/opt/strike"
BACKUP_DIR="$APP_DIR/backups"

echo "=== MONTHLY BACKUP ROTATION ==="
echo "Keeping last 30 days of backups..."

# Delete backups older than 30 days
find "$BACKUP_DIR" -name "db_*.sql" -mtime +30 -delete

echo "Remaining backups:"
ls -lh "$BACKUP_DIR" | grep "db_" | wc -l

echo "Total backup size:"
du -sh "$BACKUP_DIR"

echo ""
echo "=== END BACKUP ROTATION ==="
```

---

## QUARTERLY REVIEW

### Full Disaster Recovery Test

```bash
#!/bin/bash
# Quarterly DR test

APP_DIR="/opt/strike"
BACKUP_DIR="$APP_DIR/backups"
TEST_DIR="/tmp/strike-dr-test"

echo "=== QUARTERLY DISASTER RECOVERY TEST ==="
echo "Time: $(date)"
echo ""

# Get latest backup
LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/db_*.sql 2>/dev/null | head -1)
if [ -z "$LATEST_BACKUP" ]; then
  echo "ERROR: No backup found!"
  exit 1
fi

echo "Testing restore from: $LATEST_BACKUP"
echo "Backup size: $(ls -lh "$LATEST_BACKUP" | awk '{print $5}')"
echo ""

# Note: This is a dry-run test, don't actually restore to production
echo "DR Test Plan:"
echo "1. Create test database"
echo "2. Restore from backup"
echo "3. Verify data integrity"
echo "4. Check application compatibility"
echo "5. Clean up test environment"
echo ""

echo "Manual steps to test restore:"
echo ""
echo "# Connect to test database"
echo "docker run -d --name postgres-test postgres:15-alpine"
echo ""
echo "# Wait for startup"
echo "sleep 10"
echo ""
echo "# Restore backup"
echo "cat $LATEST_BACKUP | docker exec -i postgres-test psql -U postgres -c 'CREATE DATABASE betting_db;'"
echo ""
echo "# Verify"
echo "docker exec postgres-test psql -U postgres -d betting_db -c '\dt'"
echo ""
echo "# Clean up"
echo "docker stop postgres-test && docker rm postgres-test"
echo ""

echo "=== END DR TEST ==="
```

### Performance Analysis

```bash
#!/bin/bash
# Quarterly performance review

APP_DIR="/opt/strike"

echo "=== QUARTERLY PERFORMANCE ANALYSIS ==="
echo "Time: $(date)"
echo ""

# Analyze Docker resource usage trends
echo "1. Current resource usage:"
docker stats --no-stream | grep -E "betting-framework"

# Check database query performance
echo ""
echo "2. Slow queries (if logging enabled):"
docker-compose -f "$APP_DIR/docker-compose.prod.yml" exec postgres \
  psql -U betting_user -d betting_db -c "SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;" 2>/dev/null || echo "pg_stat_statements not enabled"

# Analyze API response times (from access logs)
echo ""
echo "3. Recent API response times:"
docker-compose -f "$APP_DIR/docker-compose.prod.yml" logs api --tail=1000 | grep -oE "took [0-9.]+ ms" | tail -10

# Check Redis performance
echo ""
echo "4. Redis info:"
docker-compose -f "$APP_DIR/docker-compose.prod.yml" exec redis redis-cli info stats | head -10

echo ""
echo "Recommendations:"
echo "- Monitor API response times (should be < 500ms)"
echo "- Check database query performance"
echo "- Review cache hit rates"
echo "- Analyze error rates"

echo ""
echo "=== END PERFORMANCE ANALYSIS ==="
```

---

## MONITORING SETUP

### Enable Sentry for Error Tracking (Optional)

```bash
# Create Sentry account at https://sentry.io
# Add to .env:
SENTRY_DSN=https://your-key@sentry.io/project-id

# Restart services
docker-compose -f docker-compose.prod.yml restart api
```

### Enable CloudWatch Logs (Optional, AWS only)

```bash
# Configure Docker daemon to send logs to CloudWatch
# Edit /etc/docker/daemon.json:
{
  "log-driver": "awslogs",
  "log-opts": {
    "awslogs-group": "/aws/docker/strike",
    "awslogs-region": "us-east-1"
  }
}
```

### Setup Uptime Monitoring

```bash
# External uptime monitoring (use UptimeRobot, Pingdom, etc.)
# Monitor: https://strike.perfecthold.online/api/health
# Frequency: Every 5 minutes
# Alert threshold: 2 consecutive failures
```

---

## ALERTING RULES

### Critical Alerts (Immediate Action)

- [ ] Any service down for > 5 minutes
- [ ] Disk space < 5% free
- [ ] Database unreachable
- [ ] API response time > 5 seconds
- [ ] SSL certificate expires in < 7 days
- [ ] Unauthorized access attempts (> 10 in 5 min)

### Warning Alerts (Review Within 24 hours)

- [ ] Error rate > 1% of requests
- [ ] Memory usage > 80%
- [ ] Slow queries detected
- [ ] Backup failed
- [ ] Cron job failed

### Info Alerts (Log for Review)

- [ ] Service restarted
- [ ] New deployment completed
- [ ] Database maintenance job ran
- [ ] Regular health check passed

---

## AUTOMATED MONITORING SETUP

Create a monitoring cron job:

```bash
# Add to crontab for monitoring alerts
(crontab -l 2>/dev/null; echo "*/5 * * * * bash /opt/strike/deploy/monitoring.sh >> /opt/strike/logs/monitoring.log 2>&1") | crontab -
```

---

## USEFUL MONITORING COMMANDS

```bash
# Real-time resource monitoring
docker stats betting-framework-api betting-framework-web

# View logs for specific time period
docker-compose -f docker-compose.prod.yml logs --since 1h

# Filter logs by service
docker-compose -f docker-compose.prod.yml logs api | grep ERROR

# Database statistics
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U betting_user betting_db -c "SELECT schemaname, tablename, n_live_tup FROM pg_stat_user_tables ORDER BY n_live_tup DESC;"

# Check connections
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U betting_user -c "SELECT count(*) FROM pg_stat_activity;"

# Redis statistics
docker-compose -f docker-compose.prod.yml exec redis redis-cli info

# Check disk IO
iostat -x 1 5 # (if installed)
```

---

## SCHEDULED MAINTENANCE WINDOWS

Recommend scheduling maintenance during low-traffic hours:

- **Weekly**: Sunday 2-3 AM UTC (database backups, log rotation)
- **Monthly**: First Sunday 2-4 AM UTC (security updates, Docker updates)
- **Quarterly**: First Sunday of quarter, 2-6 AM UTC (full DR test, performance review)

### Maintenance Mode

During maintenance, you can:

```bash
# Stop accepting traffic
docker-compose -f docker-compose.prod.yml pause api

# Perform maintenance tasks
# ...

# Resume traffic
docker-compose -f docker-compose.prod.yml unpause api
```

---

## INCIDENT RESPONSE

### Service Down

1. Check service status: `docker-compose -f docker-compose.prod.yml ps`
2. View logs: `docker-compose -f docker-compose.prod.yml logs -f`
3. Restart service: `docker-compose -f docker-compose.prod.yml restart <service>`
4. If still down: `docker-compose -f docker-compose.prod.yml down && docker-compose -f docker-compose.prod.yml up -d`
5. Check health: `curl http://localhost:8000/health`
6. Document incident and root cause

### Database Performance Degradation

1. Check database size: `docker-compose -f docker-compose.prod.yml exec postgres pg_size_pretty(pg_database_size('betting_db'))`
2. Run VACUUM: `docker-compose -f docker-compose.prod.yml exec postgres psql -U betting_user betting_db -c "VACUUM;"`
3. Run ANALYZE: `docker-compose -f docker-compose.prod.yml exec postgres psql -U betting_user betting_db -c "ANALYZE;"`
4. Check slow queries: `docker-compose -f docker-compose.prod.yml exec postgres psql -U betting_user betting_db -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"`
5. Review indexes: `docker-compose -f docker-compose.prod.yml exec postgres psql -U betting_user betting_db -c "\di"`

### Disk Space Crisis

1. Check usage: `df -h`
2. Find large files: `du -sh /opt/strike/* | sort -rh | head -10`
3. Clean old backups: `find /opt/strike/backups -mtime +60 -delete`
4. Clean old logs: `find /opt/strike/logs -mtime +30 -delete`
5. Docker cleanup: `docker system prune -a` (use with caution)

---

**Maintenance Owner**: _______________  
**Last Review**: _______________  
**Next Review**: _______________
