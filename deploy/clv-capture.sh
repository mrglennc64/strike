#!/bin/bash
#
# clv-capture.sh - Execute CLV capture API calls
#
# Usage: clv-capture.sh {open|close|calculate}
#
# Calls backend endpoints to capture CLV data:
#   - open: POST /api/clv/capture?mode=open
#   - close: POST /api/clv/capture?mode=close
#   - calculate: POST /api/clv/calculate
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="${PROJECT_ROOT}/logs"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
API_KEY="${CLV_API_KEY:-}"
REQUEST_TIMEOUT="${REQUEST_TIMEOUT:-30}"
RETRY_COUNT="${RETRY_COUNT:-3}"
RETRY_DELAY="${RETRY_DELAY:-5}"

# Create logs directory
mkdir -p "$LOG_DIR"

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

# Make API request with retry logic
call_api() {
  local method="$1"
  local endpoint="$2"
  local mode="${3:-}"
  local url="${BACKEND_URL}${endpoint}"
  local attempt=1

  [[ -n "$mode" ]] && url="${url}?mode=${mode}"

  log_debug "API Call: $method $url"

  while [[ $attempt -le $RETRY_COUNT ]]; do
    log_info "Attempt $attempt/$RETRY_COUNT: $method ${endpoint}${mode:+?mode=$mode}"

    local response
    local http_code
    local curl_args=(
      -s
      -w "\n%{http_code}"
      -X "$method"
      -H "Content-Type: application/json"
      --connect-timeout "$REQUEST_TIMEOUT"
      --max-time "$((REQUEST_TIMEOUT * 2))"
    )

    # Add API key if provided
    if [[ -n "$API_KEY" ]]; then
      curl_args+=(-H "Authorization: Bearer $API_KEY")
    fi

    curl_args+=("$url")

    response=$(curl "${curl_args[@]}" 2>&1)
    http_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | sed '$d')

    log_debug "HTTP Code: $http_code"
    log_debug "Response: $response_body"

    if [[ "$http_code" =~ ^[2][0-9]{2}$ ]]; then
      log_info "Success: HTTP $http_code"
      echo "$response_body"
      return 0
    fi

    # Don't retry on 4xx errors (client errors)
    if [[ "$http_code" =~ ^[4][0-9]{2}$ ]]; then
      log_error "Client error (HTTP $http_code): $response_body"
      return 1
    fi

    # Retry on 5xx or connection errors
    if [[ $attempt -lt $RETRY_COUNT ]]; then
      log_warn "Server error (HTTP $http_code), retrying in ${RETRY_DELAY}s..."
      sleep "$RETRY_DELAY"
      attempt=$((attempt + 1))
    else
      log_error "Failed after $RETRY_COUNT attempts (HTTP $http_code): $response_body"
      return 1
    fi
  done

  return 1
}

# Capture open (1pm UTC)
capture_open() {
  log_info "Starting CLV capture (open mode)"
  local start_time=$(date +%s)

  if call_api POST "/api/clv/capture" "open"; then
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    log_info "CLV capture (open) completed in ${duration}s"
    return 0
  else
    log_error "CLV capture (open) failed"
    return 1
  fi
}

# Capture close (10:15pm UTC)
capture_close() {
  log_info "Starting CLV capture (close mode)"
  local start_time=$(date +%s)

  if call_api POST "/api/clv/capture" "close"; then
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    log_info "CLV capture (close) completed in ${duration}s"
    return 0
  else
    log_error "CLV capture (close) failed"
    return 1
  fi
}

# Calculate CLV (10:30pm UTC)
calculate_clv() {
  log_info "Starting CLV calculation"
  local start_time=$(date +%s)

  if call_api POST "/api/clv/calculate"; then
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    log_info "CLV calculation completed in ${duration}s"
    return 0
  else
    log_error "CLV calculation failed"
    return 1
  fi
}

# Verify backend is healthy
check_backend_health() {
  log_info "Checking backend health at $BACKEND_URL"

  if ! timeout 10 curl -s -f --connect-timeout 5 "$BACKEND_URL/health" >/dev/null 2>&1; then
    log_error "Backend health check failed at $BACKEND_URL"
    log_warn "Proceeding anyway - may fail during API calls"
    return 1
  fi

  log_info "Backend health check passed"
  return 0
}

# Main execution
main() {
  local mode="${1:-}"

  if [[ -z "$mode" ]]; then
    echo "Usage: $0 {open|close|calculate}"
    echo ""
    echo "Modes:"
    echo "  open      - Capture CLV at market open (1pm UTC)"
    echo "  close     - Capture CLV at market close (10:15pm UTC)"
    echo "  calculate - Calculate CLV metrics (10:30pm UTC)"
    echo ""
    echo "Environment variables:"
    echo "  BACKEND_URL      - Backend API URL (default: http://localhost:8000)"
    echo "  CLV_API_KEY      - Optional Bearer token for authentication"
    echo "  REQUEST_TIMEOUT  - Request timeout in seconds (default: 30)"
    echo "  RETRY_COUNT      - Number of retry attempts (default: 3)"
    echo "  RETRY_DELAY      - Delay between retries in seconds (default: 5)"
    echo "  DEBUG            - Enable debug logging (set to 1)"
    exit 1
  fi

  local log_file="$LOG_DIR/clv-capture.log"
  {
    log_info "========================================="
    log_info "CLV Capture Job Started"
    log_info "Mode: $mode"
    log_info "Backend: $BACKEND_URL"
    log_info "========================================="

    check_backend_health

    case "$mode" in
      open)
        capture_open
        exit_code=$?
        ;;

      close)
        capture_close
        exit_code=$?
        ;;

      calculate)
        calculate_clv
        exit_code=$?
        ;;

      *)
        log_error "Unknown mode: $mode"
        exit_code=1
        ;;
    esac

    log_info "========================================="
    if [[ $exit_code -eq 0 ]]; then
      log_info "CLV Capture Job Completed Successfully"
    else
      log_error "CLV Capture Job Failed (exit code: $exit_code)"
    fi
    log_info "========================================="

    exit "$exit_code"
  } 2>&1 | tee -a "$log_file"
}

main "$@"
