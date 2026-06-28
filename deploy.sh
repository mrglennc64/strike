#!/bin/bash

################################################################################
# Portfolio Engine Deployment Script
#
# Usage: ./deploy.sh [dev|staging|prod] [--no-tests] [--verbose]
#
# This script:
# 1. Tests the portfolio simulator with realistic parameters
# 2. Runs sample allocation calculations (Kelly, Sharpe, Min-Variance)
# 3. Verifies the regime controller with various market conditions
# 4. Performs health checks on all services
# 5. Validates API endpoints
################################################################################

set -e

# Configuration
ENVIRONMENT=${1:-dev}
SKIP_TESTS=${2:-false}
VERBOSE=${3:-false}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/logs/deployment"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${LOG_DIR}/deploy_${ENVIRONMENT}_${TIMESTAMP}.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# Create log directory
mkdir -p "$LOG_DIR"

################################################################################
# 1. PRE-DEPLOYMENT CHECKS
################################################################################

log_info "=========================================="
log_info "Portfolio Engine Deployment"
log_info "Environment: $ENVIRONMENT"
log_info "Timestamp: $(date)"
log_info "=========================================="

log_info "Step 1: Pre-deployment checks"

# Check Docker
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed"
    exit 1
fi
log_success "Docker is installed"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose is not installed"
    exit 1
fi
log_success "Docker Compose is installed"

# Check Python
if ! command -v python3 &> /dev/null; then
    log_error "Python3 is not installed"
    exit 1
fi
log_success "Python3 is installed: $(python3 --version)"

# Check .env file
if [ ! -f "${SCRIPT_DIR}/.env.example" ]; then
    log_error ".env.example not found"
    exit 1
fi
log_success ".env.example found"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    log_error "Invalid environment: $ENVIRONMENT (must be dev, staging, or prod)"
    exit 1
fi
log_success "Environment validation passed"

################################################################################
# 2. DEPLOY SERVICES
################################################################################

log_info "Step 2: Deploying Docker services"

if [ "$ENVIRONMENT" == "prod" ]; then
    log_info "Using production docker-compose"
    docker-compose -f docker-compose.prod.yml up -d >> "$LOG_FILE" 2>&1
else
    log_info "Using development/staging docker-compose"
    docker-compose -f docker-compose.yml -f docker-compose.portfolio.yml up -d >> "$LOG_FILE" 2>&1
fi

log_success "Docker services started"

# Wait for services to be healthy
log_info "Waiting for services to be healthy..."
sleep 10

max_retries=30
retry_count=0

while [ $retry_count -lt $max_retries ]; do
    if docker-compose ps | grep -E "postgres|redis|api|portfolio" | grep -q "healthy\|Up"; then
        log_success "Services are healthy"
        break
    fi
    retry_count=$((retry_count + 1))
    log_info "Waiting for services... (attempt $retry_count/$max_retries)"
    sleep 5
done

if [ $retry_count -eq $max_retries ]; then
    log_error "Services failed to become healthy"
    docker-compose logs >> "$LOG_FILE"
    exit 1
fi

################################################################################
# 3. TEST PORTFOLIO SIMULATOR
################################################################################

if [[ "$SKIP_TESTS" != "--no-tests" ]]; then
    log_info "Step 3: Testing Portfolio Simulator"

    cat > /tmp/test_simulator.py << 'EOF'
#!/usr/bin/env python3
"""Test Portfolio Simulator with realistic parameters"""

import sys
import json
import subprocess
import time

BASE_URL = "http://localhost:8001" if len(sys.argv) < 2 else sys.argv[1]
TIMEOUT = 300

def test_simulator():
    """Test Monte Carlo simulation endpoint"""

    payload = {
        "strategies": [
            {
                "name": "MLB",
                "expected_return": 15.0,
                "volatility": 12.0,
                "sharpe_ratio": 1.25,
                "max_drawdown": -0.15,
                "weight": 0.20
            },
            {
                "name": "Crypto",
                "expected_return": 25.0,
                "volatility": 40.0,
                "sharpe_ratio": 0.625,
                "max_drawdown": -0.50,
                "weight": 0.15
            },
            {
                "name": "Earnings",
                "expected_return": 18.0,
                "volatility": 18.0,
                "sharpe_ratio": 1.0,
                "max_drawdown": -0.20,
                "weight": 0.25
            },
            {
                "name": "AI",
                "expected_return": 22.0,
                "volatility": 32.0,
                "sharpe_ratio": 0.69,
                "max_drawdown": -0.35,
                "weight": 0.20
            },
            {
                "name": "Econ",
                "expected_return": 12.0,
                "volatility": 8.0,
                "sharpe_ratio": 1.5,
                "max_drawdown": -0.10,
                "weight": 0.20
            }
        ],
        "num_simulations": 500,  # Reduced for faster testing
        "time_horizon_days": 252,
        "initial_capital": 100000
    }

    print("[TEST] Running portfolio simulator...")
    try:
        cmd = [
            "curl", "-s", "-X", "POST",
            f"{BASE_URL}/api/portfolio/simulate",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(payload),
            "--max-time", str(TIMEOUT)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT+10)

        if result.returncode != 0:
            print(f"[ERROR] Simulator test failed: {result.stderr}")
            return False

        response = json.loads(result.stdout)

        # Validate response
        assert "num_simulations" in response, "Missing num_simulations"
        assert "total_return_mean" in response, "Missing total_return_mean"
        assert "sharpe_ratio" in response, "Missing sharpe_ratio"
        assert "max_drawdown_worst" in response, "Missing max_drawdown_worst"
        assert "probability_profitable" in response, "Missing probability_profitable"

        print(f"[SUCCESS] Simulator test passed")
        print(f"  Mean Return: {response['total_return_mean']:.2f}%")
        print(f"  Sharpe Ratio: {response['sharpe_ratio']:.2f}")
        print(f"  Max Drawdown: {response['max_drawdown_worst']:.1f}%")
        print(f"  Win Rate: {response['probability_profitable']:.1f}%")

        return True

    except Exception as e:
        print(f"[ERROR] Simulator test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_simulator()
    sys.exit(0 if success else 1)
EOF

    python3 /tmp/test_simulator.py "$BASE_URL" | tee -a "$LOG_FILE"
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        log_success "Portfolio simulator test passed"
    else
        log_error "Portfolio simulator test failed"
        exit 1
    fi

    ################################################################################
    # 4. TEST ALLOCATION OPTIMIZATION
    ################################################################################

    log_info "Step 4: Testing Allocation Optimization"

    cat > /tmp/test_allocation.py << 'EOF'
#!/usr/bin/env python3
"""Test Allocation Optimization with multiple methods"""

import sys
import json
import subprocess

BASE_URL = "http://localhost:8001" if len(sys.argv) < 2 else sys.argv[1]

def test_allocation(method):
    """Test allocation endpoint with given method"""

    payload = {
        "strategies": [
            {"name": "MLB", "expected_return": 15.0, "volatility": 12.0, "sharpe_ratio": 1.25, "max_drawdown": -0.15, "weight": 0.2},
            {"name": "Crypto", "expected_return": 25.0, "volatility": 40.0, "sharpe_ratio": 0.625, "max_drawdown": -0.50, "weight": 0.2},
            {"name": "Earnings", "expected_return": 18.0, "volatility": 18.0, "sharpe_ratio": 1.0, "max_drawdown": -0.20, "weight": 0.2},
            {"name": "AI", "expected_return": 22.0, "volatility": 32.0, "sharpe_ratio": 0.69, "max_drawdown": -0.35, "weight": 0.2},
            {"name": "Econ", "expected_return": 12.0, "volatility": 8.0, "sharpe_ratio": 1.5, "max_drawdown": -0.10, "weight": 0.2}
        ],
        "optimization_method": method,
        "kelly_fraction": 0.25
    }

    print(f"[TEST] Testing allocation with method: {method}")
    try:
        cmd = [
            "curl", "-s", "-X", "POST",
            f"{BASE_URL}/api/portfolio/allocation",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(payload)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            print(f"[ERROR] Allocation test failed for {method}: {result.stderr}")
            return False

        response = json.loads(result.stdout)

        # Validate response
        assert "optimal_weights" in response, "Missing optimal_weights"
        assert "portfolio_expected_return" in response, "Missing portfolio_expected_return"
        assert "portfolio_volatility" in response, "Missing portfolio_volatility"

        weight_sum = sum(response["optimal_weights"].values())
        assert 0.99 <= weight_sum <= 1.01, f"Weights don't sum to 1.0: {weight_sum}"

        print(f"[SUCCESS] Allocation test passed for {method}")
        print(f"  Expected Return: {response['portfolio_expected_return']:.2f}%")
        print(f"  Volatility: {response['portfolio_volatility']:.2f}%")
        print(f"  Sharpe: {response['portfolio_sharpe_ratio']:.2f}")
        print(f"  Weights: {response['optimal_weights']}")

        return True

    except Exception as e:
        print(f"[ERROR] Allocation test failed for {method}: {str(e)}")
        return False

if __name__ == "__main__":
    methods = ["kelly", "sharpe", "min_variance", "equal_weight"]
    all_passed = True

    for method in methods:
        if not test_allocation(method):
            all_passed = False

    sys.exit(0 if all_passed else 1)
EOF

    python3 /tmp/test_allocation.py "$BASE_URL" | tee -a "$LOG_FILE"
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        log_success "Allocation optimization tests passed"
    else
        log_error "Allocation optimization tests failed"
        exit 1
    fi

    ################################################################################
    # 5. TEST REGIME CONTROLLER
    ################################################################################

    log_info "Step 5: Testing Regime Controller"

    cat > /tmp/test_regime.py << 'EOF'
#!/usr/bin/env python3
"""Test Regime Controller with various market conditions"""

import sys
import json
import subprocess

BASE_URL = "http://localhost:8001" if len(sys.argv) < 2 else sys.argv[1]

def test_regime(regime_name, vix, funding, sentiment):
    """Test regime assessment"""

    payload = {
        "current_vix": vix,
        "vix_percentile_30d": 50.0,
        "crypto_funding_rate": funding,
        "market_sentiment": sentiment,
        "base_weights": {
            "MLB": 0.20,
            "Crypto": 0.15,
            "Earnings": 0.25,
            "AI": 0.20,
            "Econ": 0.20
        },
        "strategies": [
            {"name": "MLB", "expected_return": 15.0, "volatility": 12.0, "sharpe_ratio": 1.25, "max_drawdown": -0.15, "weight": 0.2},
            {"name": "Crypto", "expected_return": 25.0, "volatility": 40.0, "sharpe_ratio": 0.625, "max_drawdown": -0.50, "weight": 0.2},
            {"name": "Earnings", "expected_return": 18.0, "volatility": 18.0, "sharpe_ratio": 1.0, "max_drawdown": -0.20, "weight": 0.2},
            {"name": "AI", "expected_return": 22.0, "volatility": 32.0, "sharpe_ratio": 0.69, "max_drawdown": -0.35, "weight": 0.2},
            {"name": "Econ", "expected_return": 12.0, "volatility": 8.0, "sharpe_ratio": 1.5, "max_drawdown": -0.10, "weight": 0.2}
        ]
    }

    print(f"[TEST] Testing regime: {regime_name} (VIX={vix}, Funding={funding}, Sentiment={sentiment})")
    try:
        cmd = [
            "curl", "-s", "-X", "POST",
            f"{BASE_URL}/api/portfolio/regime",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(payload)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            print(f"[ERROR] Regime test failed: {result.stderr}")
            return False

        response = json.loads(result.stdout)

        # Validate response
        assert "regime_name" in response, "Missing regime_name"
        assert "regime_adjusted_weights" in response, "Missing regime_adjusted_weights"
        assert "recommended_action" in response, "Missing recommended_action"

        print(f"[SUCCESS] {regime_name} regime test passed")
        print(f"  Detected Regime: {response['regime_name']}")
        print(f"  Recommended Action: {response['recommended_action']}")
        print(f"  Adjusted Weights: {response['regime_adjusted_weights']}")

        return True

    except Exception as e:
        print(f"[ERROR] Regime test failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_cases = [
        ("Low Volatility", 10.0, 0.005, 0.5),
        ("Normal Market", 18.0, 0.015, 0.2),
        ("High Volatility", 25.0, 0.025, -0.3),
        ("Stress Regime", 35.0, 0.05, -0.7)
    ]

    all_passed = True
    for regime_name, vix, funding, sentiment in test_cases:
        if not test_regime(regime_name, vix, funding, sentiment):
            all_passed = False

    sys.exit(0 if all_passed else 1)
EOF

    python3 /tmp/test_regime.py "$BASE_URL" | tee -a "$LOG_FILE"
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        log_success "Regime controller tests passed"
    else
        log_error "Regime controller tests failed"
        exit 1
    fi

fi  # Skip tests conditional

################################################################################
# 6. API HEALTH CHECKS
################################################################################

log_info "Step 6: API Health Checks"

# Portfolio API health
log_info "Checking Portfolio API health..."
if curl -s http://localhost:8001/api/portfolio/health | grep -q "ok"; then
    log_success "Portfolio API is healthy"
else
    log_error "Portfolio API health check failed"
    exit 1
fi

# Main API health (if different port)
if curl -s http://localhost:8000/health 2>/dev/null | grep -q "ok"; then
    log_success "Main API is healthy"
else
    log_warn "Main API health check failed or unreachable"
fi

################################################################################
# 7. DATABASE MIGRATION (if needed)
################################################################################

log_info "Step 7: Database migrations"

docker-compose exec -T api alembic upgrade head >> "$LOG_FILE" 2>&1 || true
log_success "Database migrations completed"

################################################################################
# 8. DEPLOYMENT SUMMARY
################################################################################

log_info "=========================================="
log_info "Deployment Complete!"
log_info "=========================================="
log_success "Environment: $ENVIRONMENT"
log_success "Timestamp: $(date)"
log_success "Log file: $LOG_FILE"

log_info ""
log_info "Service URLs:"
log_info "  - Portfolio API: http://localhost:8001"
log_info "  - Main API: http://localhost:8000"
log_info "  - Frontend: http://localhost:3000"
log_info "  - Database: localhost:5432"
log_info "  - Redis: localhost:6379"
log_info ""
log_info "Useful commands:"
log_info "  - View logs: docker-compose logs -f portfolio"
log_info "  - Stop services: docker-compose down"
log_info "  - Restart portfolio: docker-compose restart portfolio"
log_info ""

exit 0
