# Production Deployment Package Index
## Strike Betting Platform - strike.perfecthold.online

**Package Version**: 1.0.0  
**Created**: June 28, 2026  
**Status**: Ready for Production Deployment

---

## OVERVIEW

This deployment package contains everything needed to deploy Strike to production on a Linux VPS (strike.perfecthold.online) using Docker Compose.

**What's Included:**
1. Automated deployment script
2. Comprehensive deployment guides
3. Verification checklists
4. Monitoring and maintenance procedures
5. Cron job setup tools
6. Docker configuration files

**Deployment Time**: ~30 minutes (fully automated) or 1 hour (step-by-step)

---

## FILE LISTING & PURPOSES

### 🚀 START HERE

| File | Purpose | Read Time |
|------|---------|-----------|
| **DEPLOYMENT_QUICK_START.md** | Quick reference for deploying to VPS | 10 min |
| **deploy-vps.sh** | Automated deployment script (run on VPS) | N/A |

### 📖 DETAILED GUIDES

| File | Purpose | When to Use |
|------|---------|-------------|
| **PRODUCTION_DEPLOYMENT_VPS.md** | Complete step-by-step deployment guide with all details | Full manual deployment or reference |
| **DEPLOYMENT_VERIFICATION_CHECKLIST.md** | Detailed checklist for verifying each step | During/after deployment to verify success |
| **MONITORING_AND_MAINTENANCE.md** | Ongoing monitoring, maintenance, and incident response | After deployment, for daily/weekly/monthly ops |

### 🛠️ DEPLOYMENT SCRIPTS

| File | Location | Purpose | Runs On |
|------|----------|---------|---------|
| **deploy-vps.sh** | Project root | Automated end-to-end deployment | VPS (as root) |
| **docker-compose.prod.yml** | Project root | Production Docker configuration | VPS |
| **cron-setup.sh** | `deploy/` | Install CLV tracking cron jobs | VPS (as user) |
| **monitoring.sh** | `deploy/` | Health monitoring script | VPS (every 5 min) |
| **clv-capture.sh** | `deploy/` | CLV data capture script | VPS (scheduled) |

### 📋 CONFIGURATION FILES

| File | Purpose | Should Commit? |
|------|---------|---|
| `.env.example` | Template for production environment variables | YES |
| `.env` | ACTUAL production secrets (created on VPS) | **NO - NEVER** |
| `docker-compose.prod.yml` | Production service configuration | YES |
| `Dockerfile` (backend) | Backend container definition | YES |
| `Dockerfile` (frontend) | Frontend container definition | YES |

---

## DEPLOYMENT FLOW

### Quick Path (30 minutes - Automated)

```
┌─────────────────────────────────┐
│ 1. SSH into VPS                 │
│    ssh root@VPS_IP              │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│ 2. Run automated script          │
│    bash deploy-vps.sh            │
│    (installs everything)         │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│ 3. Verify deployment             │
│    Check service status          │
│    Test health endpoints         │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│ ✓ DEPLOYMENT COMPLETE            │
│   https://strike.perfecthold.online │
└─────────────────────────────────┘
```

### Detailed Path (1 hour - Manual)

Follow **PRODUCTION_DEPLOYMENT_VPS.md** steps 1-12 in order.

---

## HOW TO USE THIS PACKAGE

### 1. PRE-DEPLOYMENT (Do This First)

```bash
# Local machine - ensure all code is committed
git status  # Should be clean
git push origin main

# Verify SSH access
ssh root@strike.perfecthold.online "echo OK"

# Save these files in a safe location (not git)
# - DNS configuration
# - SSH private key
# - Production secrets (generate fresh ones)
```

### 2. DEPLOYMENT OPTIONS

#### Option A: Fully Automated (Recommended)

```bash
# SSH into VPS
ssh root@strike.perfecthold.online

# Run automated deployment
cd /tmp
curl -fsSL https://raw.githubusercontent.com/yourusername/strike/main/deploy-vps.sh -o deploy-vps.sh
bash deploy-vps.sh

# Follow prompts, saves secrets shown at end
```

#### Option B: Step-by-Step Manual

```bash
# SSH into VPS
ssh root@strike.perfecthold.online

# Follow PRODUCTION_DEPLOYMENT_VPS.md steps 1-12
# Takes about 1 hour
```

### 3. VERIFICATION

```bash
# Use DEPLOYMENT_VERIFICATION_CHECKLIST.md
# Check each item in the checklist
# All items should be ✓ PASS

# Quick test:
curl https://strike.perfecthold.online/api/health
```

### 4. ONGOING OPERATIONS

```bash
# Use MONITORING_AND_MAINTENANCE.md for:
# - Daily health checks
# - Weekly backups & security reviews
# - Monthly maintenance & updates
# - Quarterly disaster recovery tests
```

---

## WHAT EACH FILE DOES

### DEPLOYMENT_QUICK_START.md
- **Length**: 2-3 pages
- **Purpose**: Fast reference for anyone deploying
- **Contains**: 8-step deployment in ~30 minutes
- **When to use**: First-time deployments, emergency re-deployments

### PRODUCTION_DEPLOYMENT_VPS.md
- **Length**: 10+ pages
- **Purpose**: Complete reference with all details
- **Contains**: Every step with explanations, troubleshooting, commands
- **When to use**: First deployment, debugging issues, understanding the process

### DEPLOYMENT_VERIFICATION_CHECKLIST.md
- **Length**: 15+ pages
- **Purpose**: Verify each step works correctly
- **Contains**: 100+ checkboxes for testing each component
- **When to use**: After deployment, before going live, quarterly audits

### MONITORING_AND_MAINTENANCE.md
- **Length**: 10+ pages
- **Purpose**: Keep service running smoothly
- **Contains**: Daily, weekly, monthly, quarterly tasks with scripts
- **When to use**: Every day/week/month, incident response

### deploy-vps.sh
- **Type**: Bash script (executable)
- **Purpose**: Automates entire deployment
- **Runs as**: root on VPS
- **What it does**: 
  1. Installs Docker & dependencies
  2. Clones repository
  3. Creates .env file with secrets
  4. Builds Docker images
  5. Starts all services
  6. Configures Nginx
  7. Sets up SSL
  8. Installs cron jobs

---

## QUICK REFERENCE

### Service URLs (After Deployment)

```
Frontend:     https://strike.perfecthold.online
API:          https://strike.perfecthold.online/api
Health Check: https://strike.perfecthold.online/api/health
Swagger Docs: https://strike.perfecthold.online/api/docs
ReDoc Docs:   https://strike.perfecthold.online/api/redoc
```

### Database Credentials

```
User:     betting_user
Password: [Generated & stored in .env on VPS]
Database: betting_db
Port:     5432 (internal only)
```

### Required Ports

```
80   (HTTP, redirects to HTTPS)
443  (HTTPS, production traffic)
22   (SSH, admin access)
```

### Cron Jobs (After Deployment)

```
1:00 PM UTC    - CLV capture (open odds)
10:15 PM UTC   - CLV capture (close odds)
10:30 PM UTC   - CLV calculation
Every 5 mins   - Health monitoring
Daily 2 AM UTC - Database backup
```

---

## TROUBLESHOOTING BY SYMPTOM

### "Services won't start"
→ See: PRODUCTION_DEPLOYMENT_VPS.md > Troubleshooting > API won't start

### "Can't connect to database"
→ See: PRODUCTION_DEPLOYMENT_VPS.md > Troubleshooting > Database connection error

### "HTTPS not working"
→ See: MONITORING_AND_MAINTENANCE.md > Incident Response > SSL certificate issues

### "Out of disk space"
→ See: MONITORING_AND_MAINTENANCE.md > Incident Response > Disk Space Crisis

### "Service keeps restarting"
→ See: MONITORING_AND_MAINTENANCE.md > Check docker logs

---

## IMPORTANT SECURITY NOTES

### DO's ✓
- [ ] Generate NEW secrets for production (never reuse dev secrets)
- [ ] Store .env securely (not in git, not shared)
- [ ] Enable automatic backups (configured in deploy-vps.sh)
- [ ] Monitor SSL certificate expiration (30 days notice)
- [ ] Keep Docker images updated (monthly)
- [ ] Rotate secrets every 90 days

### DON'Ts ✗
- [ ] Never commit .env to git
- [ ] Never share production secrets in Slack/email
- [ ] Never use same password for multiple services
- [ ] Never leave DEBUG=True in production
- [ ] Never skip SSL certificate renewal
- [ ] Never expose Docker API to internet

---

## SUCCESS CRITERIA

You'll know deployment succeeded when:

- [ ] All 4 Docker services showing "Up (healthy)"
- [ ] API responds: `curl https://strike.perfecthold.online/api/health`
- [ ] Frontend loads: `https://strike.perfecthold.online`
- [ ] SSL certificate valid (padlock in browser)
- [ ] Nginx proxying correctly
- [ ] Database backups running
- [ ] Cron jobs scheduled
- [ ] No error logs in docker output

---

## ESTIMATED TIMINGS

| Task | Automated | Manual |
|------|-----------|--------|
| System setup (Docker, nginx) | 5 min | 10 min |
| Repository clone & .env setup | 2 min | 5 min |
| Build Docker images | 10 min | 10 min |
| Start services | 1 min | 1 min |
| Health checks | 2 min | 5 min |
| Nginx & SSL setup | 3 min | 10 min |
| Cron job setup | 1 min | 5 min |
| Verification | 5 min | 10 min |
| **TOTAL** | **~30 min** | **~60 min** |

---

## WHAT TO SAVE AFTER DEPLOYMENT

Store these securely (password manager, secure backup):

1. **Database Password** - From .env `POSTGRES_PASSWORD`
2. **Redis Password** - From .env `REDIS_PASSWORD`
3. **Secret Key** - From .env `SECRET_KEY`
4. **SSH Private Key** - For VPS access
5. **Domain Name** - strike.perfecthold.online
6. **VPS IP Address** - For direct access if DNS fails
7. **Let's Encrypt Email** - For certificate renewal alerts

**NEVER store these in:**
- Public git repositories
- Slack messages
- Email (unencrypted)
- Browser bookmarks with passwords

---

## AUTOMATION FEATURES

This deployment includes automatic:

✓ Health checks (every 5 minutes)  
✓ Database backups (daily at 2 AM UTC)  
✓ Log rotation (keep 30 days)  
✓ SSL renewal (30 days before expiration)  
✓ Service restart if crashed  
✓ CLV tracking (3 times daily)  
✓ Monitoring alerts (if service down)  

---

## SUPPORT & HELP

### For Deployment Issues

1. Check relevant guide (PRODUCTION_DEPLOYMENT_VPS.md)
2. Review DEPLOYMENT_VERIFICATION_CHECKLIST.md
3. View logs: `docker-compose -f docker-compose.prod.yml logs -f`
4. Check specific service:
   - API: `docker-compose -f docker-compose.prod.yml logs api`
   - Frontend: `docker-compose -f docker-compose.prod.yml logs frontend`
   - Database: `docker-compose -f docker-compose.prod.yml logs postgres`

### For Ongoing Operations

1. Use MONITORING_AND_MAINTENANCE.md for daily/weekly/monthly tasks
2. Keep backups healthy: `ls -lh /opt/strike/backups/ | tail -5`
3. Monitor disk space: `df -h /opt/strike`
4. Check service health: `curl https://strike.perfecthold.online/api/health`

---

## REVISION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-06-28 | Initial production deployment package |

---

## NEXT STEPS AFTER DEPLOYMENT

1. **Day 1**: Verify all health checks pass, test user login flow
2. **Day 2-7**: Monitor logs for errors, ensure backups working
3. **Week 2**: Performance baseline, user feedback review
4. **Month 1**: Full disaster recovery test, security audit
5. **Ongoing**: Daily monitoring, weekly maintenance, monthly updates

---

**You now have everything needed to deploy to production!**

Start with: **DEPLOYMENT_QUICK_START.md**

---

**Questions?** Open the file corresponding to your situation:
- Deploying? → DEPLOYMENT_QUICK_START.md or PRODUCTION_DEPLOYMENT_VPS.md
- Verifying? → DEPLOYMENT_VERIFICATION_CHECKLIST.md
- Operating? → MONITORING_AND_MAINTENANCE.md
- Quick reference? → This file (DEPLOYMENT_PACKAGE_INDEX.md)

**Good luck with your deployment! 🚀**
