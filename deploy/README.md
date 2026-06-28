# Strike CLV Tracking Deployment Guide

Production deployment scripts and systemd unit files for Strike CLV (Customer Lifetime Value) tracking system on VPS.

## Overview

This deployment package provides:

1. **Automated CLV Capture Jobs** - Three daily cron jobs for market open/close tracking
2. **Health Monitoring** - 5-minute interval health checks with alerting
3. **Log Management** - Production log tailing, filtering, and rotation
4. **Systemd Service Management** - Background service definitions for backend/frontend
5. **Multi-deployment Support** - Works with both systemd timers and traditional crontab

## Files

```
deploy/
├── cron-setup.sh          # Install/manage CLV cron jobs
├── clv-capture.sh         # Execute CLV capture API calls
├── monitoring.sh          # Health checks every 5 minutes
├── logs.sh               # Tail/filter production logs
├── systemd/
│   ├── strike-backend.service    # Backend service definition
│   └── strike-frontend.service   # Frontend service definition
└── README.md             # This file
```

## Quick Start

### Prerequisites

- Linux VPS (Ubuntu 20.04+ or similar)
- Python 3.9+ with virtual environment
- Node.js 18+ (for frontend)
- Systemd or cron support
- curl for API calls
- sudo access for installation

### 1. Deploy Service Files

```bash
# Copy systemd service files
sudo cp deploy/systemd/*.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Start services
sudo systemctl start strike-backend.service
sudo systemctl start strike-frontend.service

# Enable for auto-start on boot
sudo systemctl enable strike-backend.service
sudo systemctl enable strike-frontend.service

# Check status
sudo systemctl status strike-backend.service
sudo systemctl status strike-frontend.service
```

### 2. Install CLV Tracking Jobs

```bash
# Make scripts executable
chmod +x deploy/*.sh deploy/systemd/*

# Install cron jobs (systemd timers on modern systems, crontab fallback)
./deploy/cron-setup.sh install

# List installed jobs
./deploy/cron-setup.sh list

# View logs
./deploy/logs.sh capture    # Show CLV capture logs
./deploy/logs.sh -f all     # Follow all logs
./deploy/logs.sh errors     # Show recent errors
```

### 3. Configure Environment

Create `/etc/strike/backend.env`:

```bash
# API Configuration
BACKEND_URL=http://localhost:8000
CLV_API_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://user:pass@localhost/strike

# Logging
LOG_LEVEL=INFO

# Monitoring
ALERT_EMAIL=ops@example.com
ALERT_SLACK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## Usage

### CLV Capture Jobs

Three scheduled capture jobs run daily:

| Time | Job | Purpose |
|------|-----|---------|
| 1:00 PM UTC | `capture_open` | Capture CLV metrics at market open |
| 10:15 PM UTC | `capture_close` | Capture CLV metrics at market close |
| 10:30 PM UTC | `calculate_clv` | Calculate and aggregate CLV metrics |

Each job:
- Calls the appropriate backend API endpoint
- Retries up to 3 times on failure
- Logs results to `logs/clv-capture.log`
- Alerts on errors

#### Manual Trigger

```bash
# Run capture immediately
./deploy/clv-capture.sh open
./deploy/clv-capture.sh close
./deploy/clv-capture.sh calculate

# With custom backend URL
BACKEND_URL=https://api.example.com ./deploy/clv-capture.sh open

# With API authentication
CLV_API_KEY=token123 ./deploy/clv-capture.sh open

# With debug logging
DEBUG=1 ./deploy/clv-capture.sh open
```

### Health Monitoring

Monitoring runs every 5 minutes and checks:

- ✓ Backend API connectivity
- ✓ Cron/timer jobs are installed
- ✓ API endpoints are responding
- ✓ Recent log activity
- ✓ Error count in logs

```bash
# Run health check manually
./deploy/monitoring.sh

# With Slack alerts
ALERT_SLACK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL" \
  ./deploy/monitoring.sh

# With email alerts
ALERT_EMAIL="ops@example.com" ./deploy/monitoring.sh
```

### Log Management

```bash
# Show last 100 lines of all logs
./deploy/logs.sh

# Follow CLV capture logs in real-time
./deploy/logs.sh -f capture

# Show only errors
./deploy/logs.sh -l ERROR

# Show warnings and errors
./deploy/logs.sh -l WARN

# Search for specific pattern
./deploy/logs.sh search "timeout"

# Show log statistics
./deploy/logs.sh summary

# Rotate logs
./deploy/logs.sh rotate

# Clean logs older than 14 days
./deploy/logs.sh clean 14

# Show systemd journal entries
./deploy/logs.sh systemd
```

### Service Management

```bash
# View service status
systemctl status strike-backend.service
systemctl status strike-frontend.service

# View service logs
journalctl -u strike-backend.service -f     # Follow logs
journalctl -u strike-backend.service -n 100  # Last 100 lines

# Restart services
sudo systemctl restart strike-backend.service
sudo systemctl restart strike-frontend.service

# Stop services
sudo systemctl stop strike-backend.service
sudo systemctl stop strike-frontend.service

# Check service startup issues
systemctl status strike-backend.service
journalctl -u strike-backend.service -p err
```

### Cron Job Management

```bash
# List all installed cron jobs
./deploy/cron-setup.sh list

# Uninstall all CLV cron jobs
./deploy/cron-setup.sh uninstall

# Reinstall jobs
./deploy/cron-setup.sh install

# View raw crontab
crontab -l

# Manual crontab editing
crontab -e
```

## Configuration

### Environment Variables

#### cron-setup.sh

```bash
DEPLOY_USER=strike        # User to run jobs as
USE_SYSTEMD=auto          # Force systemd, cron, or auto-detect
VENV_PATH=/opt/strike/.venv  # Virtual environment path
BACKEND_URL=http://localhost:8000  # Backend URL
```

#### clv-capture.sh

```bash
BACKEND_URL=http://localhost:8000  # Backend API URL
CLV_API_KEY=token                  # Optional Bearer token
REQUEST_TIMEOUT=30                 # Request timeout in seconds
RETRY_COUNT=3                      # Number of retry attempts
RETRY_DELAY=5                      # Delay between retries in seconds
DEBUG=1                            # Enable debug logging
```

#### monitoring.sh

```bash
BACKEND_URL=http://localhost:8000  # Backend URL
ALERT_EMAIL=ops@example.com        # Email for alerts
ALERT_SLACK=https://hooks.slack.com/services/...  # Slack webhook
HEALTH_CHECK_TIMEOUT=10            # Timeout for health checks
MAX_LOG_AGE_MINUTES=30             # Alert if logs older than N minutes
```

#### logs.sh

```bash
TAIL_LINES=100                     # Number of lines to tail
ERROR_LEVEL=ALL                    # Filter level: ERROR|WARN|INFO|DEBUG|ALL
```

### Service Configuration

Edit service files to customize:

- **Port numbers**: Change `--port 8000` in backend service
- **Worker count**: Change `--workers 4` for CPU-intensive workloads
- **Memory limits**: Change `MemoryLimit=512M` for more/less memory
- **CPU quota**: Change `CPUQuota=50%` for more/less CPU
- **User/group**: Change `User=strike` for different user

Then reload:

```bash
sudo systemctl daemon-reload
sudo systemctl restart strike-backend.service
```

## Logging

### Log Locations

```
logs/
├── clv-capture.log       # CLV capture job results
├── monitoring.log        # Health check results
└── (rotated files)       # Archived logs
```

### Log Format

Each log entry includes:
- **Timestamp** - YYYY-MM-DD HH:MM:SS
- **Level** - INFO, WARN, ERROR, DEBUG
- **Message** - Descriptive message

Example:
```
[2026-06-28 13:00:15] [INFO] Attempt 1/3: POST /api/clv/capture?mode=open
[2026-06-28 13:00:17] [INFO] Success: HTTP 200
[2026-06-28 13:00:17] [INFO] CLV capture (open) completed in 2s
```

### Log Rotation

Logs are automatically rotated and compressed:

```bash
# Manual rotation
./deploy/logs.sh rotate

# Auto-rotate with cron (add to crontab)
0 0 * * * /path/to/deploy/logs.sh rotate
```

## Troubleshooting

### Backend Not Starting

```bash
# Check service status
sudo systemctl status strike-backend.service

# View detailed logs
sudo journalctl -u strike-backend.service -p err -n 50

# Check if port is in use
sudo lsof -i :8000

# Check environment files
cat /etc/strike/backend.env
cat /opt/strike/.env
```

### CLV Capture Jobs Not Running

```bash
# Check if jobs are installed
./deploy/cron-setup.sh list

# Check cron/timer status
crontab -l                                      # crontab
systemctl list-timers strike-clv-*              # systemd

# Check job logs
./deploy/logs.sh capture

# Test job manually
DEBUG=1 ./deploy/clv-capture.sh open

# Check backend connectivity
curl -v http://localhost:8000/health
```

### Health Checks Failing

```bash
# Run health check manually
./deploy/monitoring.sh

# Check backend health endpoint
curl -v http://localhost:8000/health

# Verify API endpoints
curl -v http://localhost:8000/api/clv/capture
curl -v http://localhost:8000/api/clv/calculate

# Check monitoring logs
./deploy/logs.sh monitoring
```

### High Memory Usage

```bash
# Check service resource usage
systemctl status strike-backend.service

# Reduce memory limit in service file
sudo nano /etc/systemd/system/strike-backend.service
# Change: MemoryLimit=256M

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart strike-backend.service
```

### Logs Growing Too Fast

```bash
# Check log size
du -sh logs/

# Reduce log retention
./deploy/logs.sh clean 3        # Keep only 3 days

# Reduce log verbosity
# In /etc/strike/backend.env:
LOG_LEVEL=WARNING               # Only warnings and errors
```

## Production Checklist

Before deploying to production:

- [ ] Set `LOG_LEVEL=WARNING` (reduce log volume)
- [ ] Configure `ALERT_EMAIL` and/or `ALERT_SLACK`
- [ ] Test health monitoring: `./deploy/monitoring.sh`
- [ ] Test CLV capture manually: `./deploy/clv-capture.sh open`
- [ ] Verify cron/timer installation: `./deploy/cron-setup.sh list`
- [ ] Configure log rotation: `./deploy/logs.sh rotate` (cron)
- [ ] Set resource limits appropriately in service files
- [ ] Enable security features (ProtectSystem, NoNewPrivileges, etc.)
- [ ] Set up log shipping (optional): configure rsyslog or ELK stack
- [ ] Test service restart: `sudo systemctl restart strike-backend.service`
- [ ] Verify auto-start on boot: `sudo systemctl reboot && systemctl is-active strike-backend.service`

## Advanced Setup

### Log Aggregation (ELK Stack)

Forward logs to Elasticsearch:

```bash
# Install Filebeat
sudo apt-get install filebeat

# Configure /etc/filebeat/filebeat.yml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /opt/strike/logs/*.log

output.elasticsearch:
  hosts: ["elasticsearch:9200"]

# Start Filebeat
sudo systemctl start filebeat
```

### Metrics Collection (Prometheus)

Export metrics for Prometheus:

```bash
# Add to backend service ExecStart:
--metrics-port 9090

# Create Prometheus scrape config:
scrape_configs:
  - job_name: 'strike-backend'
    static_configs:
      - targets: ['localhost:9090']
```

### Load Balancing

For multiple backend instances:

```bash
# Install nginx
sudo apt-get install nginx

# Configure /etc/nginx/sites-enabled/strike:
upstream strike_backend {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}

server {
    listen 80;
    location / {
        proxy_pass http://strike_backend;
    }
}
```

## Support

For issues:

1. Check logs: `./deploy/logs.sh errors`
2. Run health check: `./deploy/monitoring.sh`
3. Review service status: `systemctl status strike-backend.service`
4. Check system resources: `top`, `free -h`, `df -h`

## License

Proprietary - Internal Use Only
