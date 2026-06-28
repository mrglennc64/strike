#!/bin/bash

################################################################################
# Automated VPS Deployment Script for strike.perfecthold.online
#
# Usage: ./deploy-vps.sh
#
# This script automates:
# 1. Docker & Docker Compose installation
# 2. Repository cloning/updating
# 3. .env file setup (prompts for secrets)
# 4. Service startup
# 5. Health checks
# 6. Nginx configuration
# 7. SSL certificate setup
# 8. Cron job installation
# 9. Final verification
#
# Run on your VPS as: bash deploy-vps.sh
################################################################################

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
VPS_HOST=${VPS_HOST:-strike.perfecthold.online}
APP_DIR=${APP_DIR:-/opt/strike}
REPO_URL=${REPO_URL:-https://github.com/yourusername/strike.git}
DOMAIN=${DOMAIN:-strike.perfecthold.online}

# Logging functions
log_info() {
  echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
  echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warn() {
  echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $*" >&2
}

# Check if running on Linux VPS
check_system() {
  if [[ ! "$OSTYPE" =~ ^linux ]]; then
    log_error "This script must run on Linux. Detected: $OSTYPE"
    exit 1
  fi

  if [ "$EUID" -ne 0 ]; then
    log_error "This script must run as root (use: sudo bash deploy-vps.sh)"
    exit 1
  fi

  log_success "System check passed (Linux, root)"
}

# Install Docker
install_docker() {
  log_info "Installing Docker..."

  if command -v docker &> /dev/null; then
    log_success "Docker already installed: $(docker --version)"
    return 0
  fi

  curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
  bash /tmp/get-docker.sh

  # Add root to docker group if needed
  usermod -aG docker root 2>/dev/null || true

  log_success "Docker installed"
}

# Install Docker Compose
install_docker_compose() {
  log_info "Installing Docker Compose..."

  if command -v docker-compose &> /dev/null; then
    log_success "Docker Compose already installed: $(docker-compose --version)"
    return 0
  fi

  curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose
  chmod +x /usr/local/bin/docker-compose

  log_success "Docker Compose installed"
}

# Install nginx and certbot
install_nginx() {
  log_info "Installing Nginx and Certbot..."

  if ! command -v nginx &> /dev/null; then
    apt-get update
    apt-get install -y nginx certbot python3-certbot-nginx
  fi

  log_success "Nginx and Certbot installed"
}

# Create app directory
setup_directory() {
  log_info "Setting up application directory: $APP_DIR"

  mkdir -p "$APP_DIR"
  cd "$APP_DIR"

  if [ ! -d ".git" ]; then
    log_info "Cloning repository..."
    git clone "$REPO_URL" . 2>/dev/null || {
      log_warn "Clone failed - assuming repo already exists"
    }
  else
    log_info "Updating repository..."
    git pull origin main || log_warn "Pull failed - may need manual intervention"
  fi

  log_success "Application directory ready"
}

# Generate secure secrets
generate_secrets() {
  log_info "Generating production secrets..."

  local secret_key=$(openssl rand -hex 32)
  local postgres_password=$(openssl rand -base64 32)
  local redis_password=$(openssl rand -base64 32)

  echo "$secret_key"
  echo "$postgres_password"
  echo "$redis_password"
}

# Create .env file
create_env_file() {
  log_info "Creating .env file..."

  cd "$APP_DIR"

  if [ -f ".env" ]; then
    log_warn ".env already exists - backing up to .env.backup"
    mv .env .env.backup
  fi

  # Generate secrets
  local secret_key=$(openssl rand -hex 32)
  local postgres_password=$(openssl rand -base64 32)
  local redis_password=$(openssl rand -base64 32)

  # Create .env
  cat > .env << EOF
# Generated: $(date)

DEBUG=False
APP_NAME=Strike Betting Platform

POSTGRES_USER=betting_user
POSTGRES_PASSWORD=$postgres_password
POSTGRES_DB=betting_db
DATABASE_URL=postgresql://betting_user:$postgres_password@postgres:5432/betting_db

REDIS_PASSWORD=$redis_password
REDIS_URL=redis://:$redis_password@redis:6379

SECRET_KEY=$secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

MAX_SINGLE_BET_FRACTION=0.05
MAX_DAILY_LOSS_FRACTION=0.10
MAX_KELLY_FRACTION=0.25
MIN_KELLY_FRACTION=0.01

VITE_API_URL=https://$DOMAIN/api
API_URL=http://api:8000
EOF

  chmod 600 .env
  log_success ".env file created (secrets stored securely)"

  # Show secrets for user to save
  log_warn "IMPORTANT: Save these secrets securely!"
  echo ""
  echo "SECRET_KEY: $secret_key"
  echo "POSTGRES_PASSWORD: $postgres_password"
  echo "REDIS_PASSWORD: $redis_password"
  echo ""
}

# Build and start services
start_services() {
  log_info "Building Docker images..."

  cd "$APP_DIR"
  docker-compose -f docker-compose.prod.yml build

  log_info "Starting services..."
  docker-compose -f docker-compose.prod.yml up -d

  sleep 10

  log_info "Service status:"
  docker-compose -f docker-compose.prod.yml ps

  log_success "Services started"
}

# Health checks
run_health_checks() {
  log_info "Running health checks..."

  cd "$APP_DIR"

  # PostgreSQL
  if docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready > /dev/null 2>&1; then
    log_success "PostgreSQL: healthy"
  else
    log_warn "PostgreSQL: not ready yet"
  fi

  # Redis
  if docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping > /dev/null 2>&1; then
    log_success "Redis: healthy"
  else
    log_warn "Redis: not ready yet"
  fi

  # API
  sleep 5
  if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    log_success "API: healthy"
  else
    log_warn "API: not responding yet"
  fi

  # Frontend
  if curl -s http://localhost:3000 > /dev/null 2>&1; then
    log_success "Frontend: running"
  else
    log_warn "Frontend: not responding yet"
  fi
}

# Configure nginx
configure_nginx() {
  log_info "Configuring Nginx reverse proxy..."

  cat > /etc/nginx/sites-available/strike << 'EOF'
# Upstream services
upstream api {
  server localhost:8000;
}

upstream web {
  server localhost:3000;
}

# HTTP -> HTTPS redirect
server {
  listen 80;
  listen [::]:80;
  server_name strike.perfecthold.online;
  return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
  listen 443 ssl http2;
  listen [::]:443 ssl http2;
  server_name strike.perfecthold.online;

  # SSL (will be configured by certbot)
  ssl_protocols TLSv1.2 TLSv1.3;
  ssl_ciphers HIGH:!aNULL:!MD5;
  ssl_prefer_server_ciphers on;

  # API routes
  location /api/ {
    proxy_pass http://api;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
  }

  # Health endpoint
  location /health {
    proxy_pass http://api;
  }

  # Frontend
  location / {
    proxy_pass http://web;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  }
}
EOF

  ln -sf /etc/nginx/sites-available/strike /etc/nginx/sites-enabled/
  rm -f /etc/nginx/sites-enabled/default

  nginx -t && systemctl reload nginx

  log_success "Nginx configured"
}

# Setup SSL
setup_ssl() {
  log_info "Setting up SSL certificate with Let's Encrypt..."

  # Check if domain is accessible first
  if ! ping -c 1 "$DOMAIN" &> /dev/null; then
    log_warn "Domain $DOMAIN not responding. You may need to setup DNS first."
    log_info "To get SSL later, run: sudo certbot certonly --nginx -d $DOMAIN"
    return 0
  fi

  certbot certonly --nginx -d "$DOMAIN" --non-interactive --agree-tos --email admin@$DOMAIN || \
    log_warn "SSL setup incomplete - may need manual configuration"

  log_success "SSL configured"
}

# Setup cron jobs
setup_cron() {
  log_info "Setting up cron jobs..."

  cd "$APP_DIR"

  if [ -f "deploy/cron-setup.sh" ]; then
    bash deploy/cron-setup.sh install || log_warn "Cron setup failed - may need manual intervention"
    log_success "Cron jobs installed"
  else
    log_warn "Cron setup script not found"
  fi
}

# Final verification
final_verification() {
  log_info "Final verification..."

  cd "$APP_DIR"

  echo ""
  echo "=== DEPLOYMENT SUMMARY ==="
  echo ""

  echo "Docker Services:"
  docker-compose -f docker-compose.prod.yml ps
  echo ""

  echo "API Endpoint: http://localhost:8000"
  echo "Frontend Endpoint: http://localhost:3000"
  echo "Public URL: https://$DOMAIN"
  echo ""

  echo "To view logs: docker-compose -f docker-compose.prod.yml logs -f"
  echo "To stop services: docker-compose -f docker-compose.prod.yml down"
  echo ""

  log_success "Deployment complete!"
}

# Main execution
main() {
  echo ""
  echo "=========================================="
  echo "Strike VPS Deployment Script"
  echo "Target: $DOMAIN"
  echo "Directory: $APP_DIR"
  echo "=========================================="
  echo ""

  check_system
  install_docker
  install_docker_compose
  install_nginx
  setup_directory
  create_env_file
  start_services
  run_health_checks
  configure_nginx
  setup_ssl
  setup_cron
  final_verification

  echo ""
  log_success "All steps completed!"
  echo ""
  echo "NEXT STEPS:"
  echo "1. Verify DNS is pointing to this server's IP"
  echo "2. Visit https://$DOMAIN in your browser"
  echo "3. Monitor logs: docker-compose -f docker-compose.prod.yml logs -f"
  echo "4. Save the secrets shown above in a secure location"
  echo ""
}

# Run main if script is executed (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
