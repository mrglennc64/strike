#!/bin/bash
#
# monitoring.sh - Health checks and alerting for CLV tracking jobs
#
# Runs every 5 minutes to:
#   - Check backend API health
#   - Verify cron/timer jobs are running
#   - Check for recent errors in logs
#   - Send alerts if critical issues detected
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="${PROJECT_ROOT}/logs"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
ALERT_EMAIL="${ALERT_EMAIL:-}"
ALERT_SLACK="${ALERT_SLACK:-}"
HEALTH_CHECK_TIMEOUT="${HEALTH_CHECK_TIMEOUT:-10}"
ERROR_LOG_LINES="${ERROR_LOG_LINES:-50}"
MAX_LOG_AGE_MINUTES="${MAX_LOG_AGE_MINUTES:-30}"

# Status file for tracking alerts
STATUS_FILE="/tmp/strike-clv-monitor-status.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging with timestamp
log_ts() {
  local level="$1"
  shift
  local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  local color="$NC"

  case "$level" in
    INFO)
      color="$GREEN"
      ;;
    WARN)
      color="$YELLOW"
      ;;
    ERROR)
      color="$RED"
      ;;
    DEBUG)
      color="$BLUE"
      ;;
  esac

  echo -e "${color}[${timestamp}] [${level}]${NC} $*"
}

log_info() {
  log_ts INFO "$@"
}

log_warn() {
  log_ts WARN "$@" >&2
}

log_error() {
  log_ts ERROR "$@" >&2
}

log_debug() {
  if [[ "${DEBUG:-0}" == "1" ]]; then
    log_ts DEBUG "$@"
  fi
}

# Check backend API health
check_backend_health() {
  log_debug "Checking backend health at $BACKEND_URL"

  local health_endpoint="${BACKEND_URL}/health"
  local response
  local http_code

  response=$(curl -s -w "\n%{http_code}" --connect-timeout "$HEALTH_CHECK_TIMEOUT" --max-time "$((HEALTH_CHECK_TIMEOUT * 2))" "$health_endpoint" 2>&1)
  http_code=$(echo "$response" | tail -n1)
  local response_body=$(echo "$response" | sed '$d')

  if [[ "$http_code" =~ ^[2][0-9]{2}$ ]]; then
    log_info "Backend health: OK (HTTP $http_code)"
    return 0
  else
    log_error "Backend health: FAILED (HTTP $http_code)"
    log_debug "Response: $response_body"
    return 1
  fi
}

# Check if cron/timer jobs are installed
check_jobs_installed() {
  log_debug "Checking if CLV jobs are installed"

  # Check for systemd timers
  if command -v systemctl &>/dev/null; then
    if systemctl list-timers strike-clv-* &>/dev/null; then
      log_info "Systemd timers: Found"
      return 0
    fi
  fi

  # Check for crontab entries
  if crontab -l 2>/dev/null | grep -q "strike.*clv\|clv-capture.sh"; then
    log_info "Crontab entries: Found"
    return 0
  fi

  log_error "No CLV jobs installed (neither systemd timers nor crontab)"
  return 1
}

# Check for recent log activity
check_log_activity() {
  log_debug "Checking log activity"

  if [[ ! -f "$LOG_DIR/clv-capture.log" ]]; then
    log_warn "Log file not found: $LOG_DIR/clv-capture.log"
    return 1
  fi

  # Check if log was modified recently
  local log_mtime=$(stat -f%m "$LOG_DIR/clv-capture.log" 2>/dev/null || stat -c%Y "$LOG_DIR/clv-capture.log" 2>/dev/null || echo 0)
  local current_time=$(date +%s)
  local age_seconds=$((current_time - log_mtime))
  local age_minutes=$((age_seconds / 60))

  log_debug "Log age: ${age_minutes} minutes"

  if [[ $age_minutes -lt $MAX_LOG_AGE_MINUTES ]]; then
    log_info "Recent log activity: Yes (${age_minutes}m old)"
    return 0
  else
    log_warn "Log activity: Stale (${age_minutes}m old, threshold: ${MAX_LOG_AGE_MINUTES}m)"
    return 1
  fi
}

# Check for errors in logs
check_for_errors() {
  log_debug "Checking for errors in logs"

  local error_count=0
  local error_sample=""

  if [[ -f "$LOG_DIR/clv-capture.log" ]]; then
    error_count=$(grep -c "ERROR\|FAILED\|Exception" "$LOG_DIR/clv-capture.log" 2>/dev/null || echo 0)
    error_sample=$(grep "ERROR\|FAILED\|Exception" "$LOG_DIR/clv-capture.log" 2>/dev/null | tail -n 3 || true)
  fi

  if [[ $error_count -gt 0 ]]; then
    log_error "Found $error_count errors in logs"
    log_debug "Recent errors:\n$error_sample"
    return 1
  else
    log_info "No errors found in logs"
    return 0
  fi
}

# Check backend endpoint availability
check_api_endpoints() {
  log_debug "Checking API endpoints"

  local endpoints=(
    "/api/clv/capture"
    "/api/clv/calculate"
  )

  local all_ok=true

  for endpoint in "${endpoints[@]}"; do
    local url="${BACKEND_URL}${endpoint}"
    local http_code=$(curl -s -o /dev/null -w "%{http_code}" \
      --connect-timeout 5 --max-time 10 \
      -X OPTIONS "$url" 2>/dev/null || echo "000")

    if [[ "$http_code" =~ ^[2][0-9]{2}$ ]] || [[ "$http_code" == "405" ]]; then
      # 405 Method Not Allowed is OK for OPTIONS request - means endpoint exists
      log_debug "Endpoint $endpoint: OK"
    else
      log_error "Endpoint $endpoint: Unreachable (HTTP $http_code)"
      all_ok=false
    fi
  done

  [[ "$all_ok" == "true" ]]
}

# Send email alert
send_email_alert() {
  local subject="$1"
  local message="$2"

  if [[ -z "$ALERT_EMAIL" ]]; then
    log_debug "Email alerts not configured"
    return 0
  fi

  log_info "Sending email alert to $ALERT_EMAIL"

  if command -v mail &>/dev/null; then
    echo "$message" | mail -s "$subject" "$ALERT_EMAIL"
  elif command -v sendmail &>/dev/null; then
    {
      echo "To: $ALERT_EMAIL"
      echo "Subject: $subject"
      echo ""
      echo "$message"
    } | sendmail "$ALERT_EMAIL"
  else
    log_warn "No email client available (install mailutils)"
  fi
}

# Send Slack alert
send_slack_alert() {
  local message="$1"
  local severity="${2:-warning}"

  if [[ -z "$ALERT_SLACK" ]]; then
    log_debug "Slack alerts not configured"
    return 0
  fi

  log_info "Sending Slack alert"

  local color="warning"
  [[ "$severity" == "error" ]] && color="danger"
  [[ "$severity" == "info" ]] && color="good"

  local payload=$(cat <<EOF
{
  "attachments": [
    {
      "color": "$color",
      "title": "Strike CLV Monitoring Alert",
      "text": "$message",
      "footer": "Strike CLV Tracker",
      "ts": $(date +%s)
    }
  ]
}
EOF
)

  curl -X POST -H 'Content-type: application/json' \
    --data "$payload" \
    "$ALERT_SLACK" 2>/dev/null || log_warn "Failed to send Slack alert"
}

# Generate status report
generate_status_report() {
  local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  local hostname=$(hostname)
  local uptime=$(uptime)

  echo "=== Strike CLV Health Check ==="
  echo "Timestamp: $timestamp"
  echo "Hostname: $hostname"
  echo "Uptime: $uptime"
  echo ""
  echo "Log Directory: $LOG_DIR"
  echo "Backend URL: $BACKEND_URL"
  echo ""

  if [[ -f "$LOG_DIR/clv-capture.log" ]]; then
    echo "Recent CLV Capture Entries:"
    tail -n 10 "$LOG_DIR/clv-capture.log" | sed 's/^/  /'
  fi
}

# Main monitoring logic
run_monitoring() {
  log_info "Starting CLV health check"

  local all_healthy=true
  local alert_message=""

  # Check 1: Backend health
  if ! check_backend_health; then
    all_healthy=false
    alert_message+="- Backend API unreachable at $BACKEND_URL\n"
  fi

  # Check 2: Jobs installed
  if ! check_jobs_installed; then
    all_healthy=false
    alert_message+="- No CLV tracking jobs installed\n"
  fi

  # Check 3: API endpoints
  if ! check_api_endpoints; then
    all_healthy=false
    alert_message+="- One or more CLV API endpoints unreachable\n"
  fi

  # Check 4: Log activity
  if ! check_log_activity; then
    all_healthy=false
    alert_message+="- No recent log activity (threshold: ${MAX_LOG_AGE_MINUTES}m)\n"
  fi

  # Check 5: Errors
  if ! check_for_errors; then
    all_healthy=false
    alert_message+="- Errors detected in logs\n"
  fi

  # Send alerts if issues found
  if [[ "$all_healthy" != "true" ]]; then
    log_error "Health check FAILED"
    alert_message="CLV Tracking Health Check Failed:\n\n$alert_message\n\n$(generate_status_report)"

    send_email_alert "Strike CLV Health Check FAILED" "$alert_message"
    send_slack_alert "CLV Tracking Health Check Failed" "error"

    return 1
  else
    log_info "Health check PASSED"
    return 0
  fi
}

# Main execution
main() {
  local log_file="$LOG_DIR/monitoring.log"

  mkdir -p "$LOG_DIR"

  {
    log_info "========================================="
    log_info "CLV Health Check Run"
    log_info "========================================="

    run_monitoring
    exit_code=$?

    log_info "========================================="
    if [[ $exit_code -eq 0 ]]; then
      log_info "Health check passed"
    else
      log_error "Health check failed"
    fi
    log_info "========================================="

    exit "$exit_code"
  } 2>&1 | tee -a "$log_file"
}

main "$@"
