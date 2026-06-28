#!/bin/bash
#
# logs.sh - Tail and filter production logs
#
# Usage: logs.sh [options] [filter]
#
# Provides convenient log tailing with filtering by error level
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="${PROJECT_ROOT}/logs"
TAIL_LINES="${TAIL_LINES:-100}"
FOLLOW="${FOLLOW:-0}"
ERROR_LEVEL="${ERROR_LEVEL:-ALL}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Colorize log output
colorize_logs() {
  while IFS= read -r line; do
    if [[ "$line" =~ \[ERROR\] ]]; then
      echo -e "${RED}$line${NC}"
    elif [[ "$line" =~ \[WARN\] ]]; then
      echo -e "${YELLOW}$line${NC}"
    elif [[ "$line" =~ \[SUCCESS\]|\[OK\]|Success|Completed ]]; then
      echo -e "${GREEN}$line${NC}"
    elif [[ "$line" =~ \[DEBUG\] ]]; then
      echo -e "${BLUE}$line${NC}"
    elif [[ "$line" =~ \[INFO\] ]]; then
      echo -e "${CYAN}$line${NC}"
    else
      echo "$line"
    fi
  done
}

# Filter logs by error level
filter_by_level() {
  local level="$1"

  case "$level" in
    ERROR)
      grep "\[ERROR\]"
      ;;
    WARN)
      grep -E "\[WARN\]|\[ERROR\]"
      ;;
    INFO)
      grep -E "\[INFO\]|\[WARN\]|\[ERROR\]"
      ;;
    DEBUG)
      cat
      ;;
    ALL)
      cat
      ;;
    *)
      echo "Unknown error level: $level" >&2
      echo "Valid levels: ERROR, WARN, INFO, DEBUG, ALL" >&2
      return 1
      ;;
  esac
}

# Show CLV capture logs
show_clv_capture_logs() {
  local file="$LOG_DIR/clv-capture.log"

  if [[ ! -f "$file" ]]; then
    echo "Log file not found: $file" >&2
    return 1
  fi

  echo "=== CLV Capture Logs ==="
  echo "File: $file"
  echo ""

  if [[ $FOLLOW -eq 1 ]]; then
    tail -f -n "$TAIL_LINES" "$file" | filter_by_level "$ERROR_LEVEL" | colorize_logs
  else
    tail -n "$TAIL_LINES" "$file" | filter_by_level "$ERROR_LEVEL" | colorize_logs
  fi
}

# Show monitoring logs
show_monitoring_logs() {
  local file="$LOG_DIR/monitoring.log"

  if [[ ! -f "$file" ]]; then
    echo "Log file not found: $file" >&2
    return 1
  fi

  echo "=== Monitoring Logs ==="
  echo "File: $file"
  echo ""

  if [[ $FOLLOW -eq 1 ]]; then
    tail -f -n "$TAIL_LINES" "$file" | filter_by_level "$ERROR_LEVEL" | colorize_logs
  else
    tail -n "$TAIL_LINES" "$file" | filter_by_level "$ERROR_LEVEL" | colorize_logs
  fi
}

# Show all CLV-related logs
show_all_logs() {
  echo "=== All CLV Logs ==="
  echo ""

  if [[ $FOLLOW -eq 1 ]]; then
    # For follow mode, tail all log files
    tail -f -n "$TAIL_LINES" "$LOG_DIR"/*.log 2>/dev/null | filter_by_level "$ERROR_LEVEL" | colorize_logs
  else
    # Tail all log files and display
    for logfile in "$LOG_DIR"/*.log; do
      if [[ -f "$logfile" ]]; then
        echo "--- $(basename "$logfile") ---"
        tail -n 20 "$logfile" | filter_by_level "$ERROR_LEVEL" | colorize_logs
        echo ""
      fi
    done
  fi
}

# Show systemd journal logs (if using systemd)
show_systemd_logs() {
  if command -v journalctl &>/dev/null; then
    echo "=== Systemd Journal Logs (Strike CLV) ==="
    echo ""

    if [[ $FOLLOW -eq 1 ]]; then
      journalctl -u "strike-clv-*.service" -f --no-pager | colorize_logs
    else
      journalctl -u "strike-clv-*.service" -n "$TAIL_LINES" --no-pager | filter_by_level "$ERROR_LEVEL" | colorize_logs
    fi
  fi
}

# Show log summary/stats
show_log_summary() {
  echo "=== Log Summary ==="
  echo ""

  for logfile in "$LOG_DIR"/*.log; do
    if [[ -f "$logfile" ]]; then
      local filename=$(basename "$logfile")
      local total_lines=$(wc -l < "$logfile")
      local error_count=$(grep -c "\[ERROR\]" "$logfile" || echo 0)
      local warn_count=$(grep -c "\[WARN\]" "$logfile" || echo 0)
      local info_count=$(grep -c "\[INFO\]" "$logfile" || echo 0)
      local mtime=$(stat -f%m "$logfile" 2>/dev/null || stat -c%Y "$logfile" 2>/dev/null)
      local last_modified=$(date -d @"$mtime" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date -r "$mtime" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "unknown")

      echo "File: $filename"
      echo "  Total Lines:     $total_lines"
      echo "  Errors:          $error_count"
      echo "  Warnings:        $warn_count"
      echo "  Info:            $info_count"
      echo "  Last Modified:   $last_modified"
      echo ""
    fi
  done
}

# List available log files
list_log_files() {
  echo "=== Available Log Files ==="
  echo ""

  if [[ ! -d "$LOG_DIR" ]] || [[ ! "$(ls -A "$LOG_DIR")" ]]; then
    echo "No log files found in $LOG_DIR"
    return 1
  fi

  ls -lh "$LOG_DIR"/*.log 2>/dev/null || echo "No log files found"
}

# Search logs for pattern
search_logs() {
  local pattern="$1"

  if [[ -z "$pattern" ]]; then
    echo "Usage: logs.sh search <pattern>" >&2
    return 1
  fi

  echo "=== Search Results for: $pattern ==="
  echo ""

  local found=false
  for logfile in "$LOG_DIR"/*.log; do
    if [[ -f "$logfile" ]] && grep -q "$pattern" "$logfile"; then
      found=true
      echo "--- $(basename "$logfile") ---"
      grep -n "$pattern" "$logfile" | head -n 20 | colorize_logs
      echo ""
    fi
  done

  if [[ "$found" != "true" ]]; then
    echo "No matches found for: $pattern"
    return 1
  fi
}

# Show recent errors
show_recent_errors() {
  echo "=== Recent Errors ==="
  echo ""

  local found=false
  for logfile in "$LOG_DIR"/*.log; do
    if [[ -f "$logfile" ]] && grep -q "\[ERROR\]" "$logfile"; then
      found=true
      echo "--- $(basename "$logfile") ---"
      grep "\[ERROR\]" "$logfile" | tail -n 10 | colorize_logs
      echo ""
    fi
  done

  if [[ "$found" != "true" ]]; then
    echo "No errors found"
    return 0
  fi
}

# Rotate logs
rotate_logs() {
  echo "Rotating logs in $LOG_DIR..."

  for logfile in "$LOG_DIR"/*.log; do
    if [[ -f "$logfile" ]]; then
      local rotated="${logfile}.$(date +%Y%m%d-%H%M%S)"
      mv "$logfile" "$rotated"
      gzip "$rotated" 2>/dev/null || true
      echo "Rotated: $(basename "$logfile") → $(basename "$rotated").gz"
    fi
  done
}

# Clean old logs
clean_old_logs() {
  local days="${1:-7}"

  echo "Cleaning logs older than $days days in $LOG_DIR..."

  find "$LOG_DIR" -name "*.log*" -mtime "+$days" -delete

  echo "Done"
}

# Show help
show_help() {
  cat <<'EOF'
Usage: logs.sh [options] [command] [args]

Commands:
  capture          Show CLV capture logs
  monitoring       Show monitoring logs
  all              Show all CLV logs (default)
  systemd          Show systemd journal logs
  summary          Show log summary/statistics
  list             List available log files
  search <pattern> Search logs for pattern
  errors           Show recent errors
  rotate           Rotate log files
  clean [days]     Clean logs older than N days (default: 7)

Options:
  -f, --follow     Follow log file in real-time
  -n, --lines NUM  Number of lines to tail (default: 100)
  -l, --level LEV  Filter by error level: ERROR, WARN, INFO, DEBUG, ALL (default: ALL)
  -h, --help       Show this help message

Examples:
  logs.sh                    # Show all logs
  logs.sh -f capture         # Follow CLV capture logs
  logs.sh -l ERROR           # Show only errors
  logs.sh search "timeout"   # Search for "timeout" pattern
  logs.sh clean 14           # Clean logs older than 14 days

Error Levels:
  ERROR - Show only errors
  WARN  - Show warnings and errors
  INFO  - Show info, warnings, and errors
  DEBUG - Show all log levels
  ALL   - Show all entries

EOF
}

# Main execution
main() {
  # Parse options
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -f|--follow)
        FOLLOW=1
        shift
        ;;
      -n|--lines)
        TAIL_LINES="$2"
        shift 2
        ;;
      -l|--level)
        ERROR_LEVEL="$2"
        shift 2
        ;;
      -h|--help)
        show_help
        exit 0
        ;;
      *)
        break
        ;;
    esac
  done

  local command="${1:-all}"

  # Ensure log directory exists
  mkdir -p "$LOG_DIR"

  case "$command" in
    capture)
      show_clv_capture_logs
      ;;
    monitoring)
      show_monitoring_logs
      ;;
    all)
      show_all_logs
      ;;
    systemd)
      show_systemd_logs
      ;;
    summary)
      show_log_summary
      ;;
    list)
      list_log_files
      ;;
    search)
      search_logs "${2:-}"
      ;;
    errors)
      show_recent_errors
      ;;
    rotate)
      rotate_logs
      ;;
    clean)
      clean_old_logs "${2:-7}"
      ;;
    -h|--help|help)
      show_help
      ;;
    *)
      echo "Unknown command: $command" >&2
      show_help
      exit 1
      ;;
  esac
}

main "$@"
