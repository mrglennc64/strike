#!/bin/bash
#
# cron-setup.sh - Install and manage CLV capture cron jobs
#
# Sets up three daily cron jobs:
#   - 0 13 * * * → capture_open (1pm UTC)
#   - 15 22 * * * → capture_close (10pm UTC)
#   - 30 22 * * * → calculate_clv (10:30pm UTC)
#
# Supports both crontab and systemd timers (prefers systemd on modern systems)
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="${PROJECT_ROOT}/logs"
DEPLOY_USER="${DEPLOY_USER:-strike}"
USE_SYSTEMD="${USE_SYSTEMD:-auto}"
VENV_PATH="${VENV_PATH:-${PROJECT_ROOT}/.venv}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
  echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
  echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $*" >&2
}

# Determine if we should use systemd
should_use_systemd() {
  if [[ "$USE_SYSTEMD" == "false" ]]; then
    return 1
  fi

  if [[ "$USE_SYSTEMD" == "true" ]]; then
    return 0
  fi

  # Auto-detect: check if systemd is available
  command -v systemctl &>/dev/null && [[ -d /etc/systemd/system ]]
}

# Create log directory
setup_logs() {
  mkdir -p "$LOG_DIR"
  chmod 755 "$LOG_DIR"
  log_info "Log directory: $LOG_DIR"
}

# Validate backend is reachable
validate_backend() {
  local backend_url="${BACKEND_URL:-http://localhost:8000}"
  log_info "Validating backend connectivity to $backend_url..."

  if ! timeout 5 curl -s -f "$backend_url/health" >/dev/null 2>&1; then
    log_warn "Backend health check failed - jobs will still be installed but may fail until backend is running"
  else
    log_info "Backend health check passed"
  fi
}

# Install via systemd timers
install_systemd_timers() {
  log_info "Installing systemd timers..."

  # Check if running with sudo
  if [[ $EUID -ne 0 ]]; then
    log_error "systemd timer installation requires sudo"
    return 1
  fi

  local timer_dir="/etc/systemd/system"

  # Create timer unit files
  cat > "$timer_dir/strike-clv-capture-open.timer" <<'EOF'
[Unit]
Description=Strike CLV Capture Open Timer
After=network-online.target
Wants=network-online.target

[Timer]
# Run at 1pm UTC (13:00)
OnCalendar=*-*-* 13:00:00
Unit=strike-clv-capture-open.service

[Install]
WantedBy=timers.target
EOF

  cat > "$timer_dir/strike-clv-capture-close.timer" <<'EOF'
[Unit]
Description=Strike CLV Capture Close Timer
After=network-online.target
Wants=network-online.target

[Timer]
# Run at 10:15pm UTC (22:15)
OnCalendar=*-*-* 22:15:00
Unit=strike-clv-capture-close.service

[Install]
WantedBy=timers.target
EOF

  cat > "$timer_dir/strike-clv-calculate.timer" <<'EOF'
[Unit]
Description=Strike CLV Calculate Timer
After=network-online.target
Wants=network-online.target

[Timer]
# Run at 10:30pm UTC (22:30)
OnCalendar=*-*-* 22:30:00
Unit=strike-clv-calculate.service

[Install]
WantedBy=timers.target
EOF

  # Create service unit files
  cat > "$timer_dir/strike-clv-capture-open.service" <<EOF
[Unit]
Description=Strike CLV Capture Open
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=$DEPLOY_USER
WorkingDirectory=$PROJECT_ROOT
Environment="PATH=$VENV_PATH/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
ExecStart=$SCRIPT_DIR/clv-capture.sh open
StandardOutput=journal
StandardError=journal
SyslogIdentifier=strike-clv-capture-open

[Install]
WantedBy=multi-user.target
EOF

  cat > "$timer_dir/strike-clv-capture-close.service" <<EOF
[Unit]
Description=Strike CLV Capture Close
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=$DEPLOY_USER
WorkingDirectory=$PROJECT_ROOT
Environment="PATH=$VENV_PATH/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
ExecStart=$SCRIPT_DIR/clv-capture.sh close
StandardOutput=journal
StandardError=journal
SyslogIdentifier=strike-clv-capture-close

[Install]
WantedBy=multi-user.target
EOF

  cat > "$timer_dir/strike-clv-calculate.service" <<EOF
[Unit]
Description=Strike CLV Calculate
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=$DEPLOY_USER
WorkingDirectory=$PROJECT_ROOT
Environment="PATH=$VENV_PATH/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
ExecStart=$SCRIPT_DIR/clv-capture.sh calculate
StandardOutput=journal
StandardError=journal
SyslogIdentifier=strike-clv-calculate

[Install]
WantedBy=multi-user.target
EOF

  # Reload systemd and enable timers
  systemctl daemon-reload
  systemctl enable strike-clv-capture-open.timer
  systemctl enable strike-clv-capture-close.timer
  systemctl enable strike-clv-calculate.timer

  systemctl start strike-clv-capture-open.timer
  systemctl start strike-clv-capture-close.timer
  systemctl start strike-clv-calculate.timer

  log_info "systemd timers installed and started"
  systemctl list-timers strike-clv-*
}

# Install via crontab
install_crontab() {
  log_info "Installing crontab entries..."

  local cron_file="/tmp/strike_cron_$$.txt"
  local cron_cmd_base="cd $PROJECT_ROOT && $SCRIPT_DIR/clv-capture.sh"

  # Get existing crontab or create new
  crontab -l > "$cron_file" 2>/dev/null || true

  # Remove any existing strike CLV entries
  grep -v "strike.*clv" "$cron_file" > "${cron_file}.tmp" || true
  mv "${cron_file}.tmp" "$cron_file"

  # Add new entries with error handling and logging
  cat >> "$cron_file" <<EOF

# Strike CLV Tracking Cron Jobs
# Open capture at 1pm UTC
0 13 * * * $cron_cmd_base open >> $LOG_DIR/clv-capture.log 2>&1

# Close capture at 10:15pm UTC
15 22 * * * $cron_cmd_base close >> $LOG_DIR/clv-capture.log 2>&1

# Calculate CLV at 10:30pm UTC
30 22 * * * $cron_cmd_base calculate >> $LOG_DIR/clv-capture.log 2>&1

EOF

  # Install the crontab
  crontab "$cron_file"
  rm "$cron_file"

  log_info "crontab entries installed"
  log_info "Current crontab entries:"
  crontab -l | grep -E "strike.*clv|0 13|15 22|30 22" || true
}

# Install monitoring cron job (5-minute health check)
install_monitoring() {
  log_info "Installing monitoring cron job..."

  local cron_file="/tmp/strike_monitor_$$.txt"
  local monitor_cmd="$SCRIPT_DIR/monitoring.sh"

  # Get existing crontab or create new
  crontab -l > "$cron_file" 2>/dev/null || true

  # Remove any existing monitoring entries
  grep -v "strike.*monitoring\|monitoring.sh" "$cron_file" > "${cron_file}.tmp" || true
  mv "${cron_file}.tmp" "$cron_file"

  # Add monitoring every 5 minutes
  cat >> "$cron_file" <<EOF

# Strike CLV Monitoring (health check every 5 minutes)
*/5 * * * * $monitor_cmd >> $LOG_DIR/monitoring.log 2>&1

EOF

  crontab "$cron_file"
  rm "$cron_file"

  log_info "Monitoring cron job installed"
}

# List current jobs
list_jobs() {
  log_info "Listing installed CLV tracking jobs..."

  if should_use_systemd; then
    echo ""
    echo "=== Systemd Timers ==="
    systemctl list-timers strike-clv-* --all || true
    echo ""
    echo "=== Systemd Services Status ==="
    systemctl status strike-clv-capture-open.service || true
    systemctl status strike-clv-capture-close.service || true
    systemctl status strike-clv-calculate.service || true
  else
    echo ""
    echo "=== Crontab Entries ==="
    crontab -l | grep -E "strike|clv" || echo "No CLV entries found"
  fi
}

# Uninstall all jobs
uninstall() {
  log_warn "Uninstalling CLV tracking jobs..."

  if should_use_systemd; then
    systemctl stop strike-clv-capture-open.timer 2>/dev/null || true
    systemctl stop strike-clv-capture-close.timer 2>/dev/null || true
    systemctl stop strike-clv-calculate.timer 2>/dev/null || true

    systemctl disable strike-clv-capture-open.timer 2>/dev/null || true
    systemctl disable strike-clv-capture-close.timer 2>/dev/null || true
    systemctl disable strike-clv-calculate.timer 2>/dev/null || true

    rm -f /etc/systemd/system/strike-clv-*.{timer,service}
    systemctl daemon-reload

    log_info "systemd timers removed"
  else
    local cron_file="/tmp/strike_cron_$$.txt"
    crontab -l > "$cron_file" 2>/dev/null || true
    grep -v "strike.*clv\|monitoring.sh" "$cron_file" > "${cron_file}.tmp" || true

    if [[ -s "${cron_file}.tmp" ]]; then
      crontab "${cron_file}.tmp"
    else
      crontab -r 2>/dev/null || true
    fi
    rm -f "$cron_file" "${cron_file}.tmp"

    log_info "crontab entries removed"
  fi
}

# Main execution
main() {
  local command="${1:-install}"

  case "$command" in
    install)
      log_info "Installing CLV tracking cron jobs..."
      setup_logs
      validate_backend

      if should_use_systemd; then
        install_systemd_timers
      else
        install_crontab
      fi
      install_monitoring
      list_jobs
      ;;

    list)
      list_jobs
      ;;

    uninstall)
      uninstall
      ;;

    *)
      echo "Usage: $0 {install|list|uninstall}"
      echo ""
      echo "Commands:"
      echo "  install   - Install CLV tracking cron jobs (default)"
      echo "  list      - List installed jobs"
      echo "  uninstall - Remove all CLV tracking jobs"
      echo ""
      echo "Environment variables:"
      echo "  DEPLOY_USER   - User to run jobs as (default: strike)"
      echo "  USE_SYSTEMD   - Force systemd (true/false) or auto-detect (default: auto)"
      echo "  VENV_PATH     - Virtual environment path"
      echo "  BACKEND_URL   - Backend URL for health checks (default: http://localhost:8000)"
      exit 1
      ;;
  esac
}

main "$@"
