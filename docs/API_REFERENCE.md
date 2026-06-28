# API Reference - Betting Framework

**Version**: 1.0.0  
**Base URL**: `https://api.betting-framework.ai`  
**Authentication**: JWT Bearer Token  
**Rate Limit**: 100 requests per minute per user

---

## Table of Contents

1. [Authentication](#authentication)
2. [Bankroll Management](#bankroll-management)
3. [Predictions](#predictions)
4. [Kelly Calculator](#kelly-calculator)
5. [Betting](#betting)
6. [Positions](#positions)
7. [Settlement](#settlement)
8. [Audit & Logs](#audit--logs)
9. [Portfolio](#portfolio)
10. [Verticals](#verticals)
11. [CLV Tracking](#clv-tracking)
12. [Health & Monitoring](#health--monitoring)

---

## Authentication

### POST /api/auth/signup

Create a new user account.

**Request**:
```json
{
  "email": "user@example.com",
  "username": "john_doe",
  "password": "SecurePassword123!"
}
```

**Response** (201):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "username": "john_doe",
  "created_at": "2026-06-28T10:30:00Z",
  "is_active": true
}
```

**Errors**:
- `400 Bad Request`: Email or username already registered
- `422 Unprocessable Entity`: Invalid input format

---

### POST /api/auth/login

Authenticate user and get JWT token.

**Request**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response** (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Headers Required**:
```
None (authentication endpoint)
```

**Errors**:
- `401 Unauthorized`: Invalid email or password
- `404 Not Found`: User not found

---

### POST /api/auth/refresh

Refresh JWT token (if using refresh token flow).

**Request**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Errors**:
- `401 Unauthorized`: Invalid or expired refresh token

---

## Bankroll Management

### GET /api/bankroll

Get all bankrolls for authenticated user.

**Headers**:
```
Authorization: Bearer <jwt_token>
```

**Response** (200):
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "Main Account",
    "currency": "USD",
    "initial_amount": 10000.00,
    "current_balance": 9500.00,
    "status": "active",
    "daily_loss_limit": 1000.00,
    "max_single_bet_size": 500.00,
    "max_exposure_ratio": 0.30,
    "total_bets_placed": 150,
    "total_wins": 85,
    "total_losses": 65,
    "roi": 0.05,
    "created_at": "2026-01-01T00:00:00Z",
    "last_settlement": "2026-06-28T12:00:00Z"
  }
]
```

---

### POST /api/bankroll

Create new bankroll.

**Request**:
```json
{
  "name": "Risk-Aggressive Portfolio",
  "currency": "USD",
  "initial_amount": 50000.00,
  "daily_loss_limit": 5000.00,
  "max_single_bet_size": 2500.00,
  "max_exposure_ratio": 0.50,
  "kelly_fraction": 0.25
}
```

**Response** (201):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "name": "Risk-Aggressive Portfolio",
  "currency": "USD",
  "initial_amount": 50000.00,
  "current_balance": 50000.00,
  "status": "active",
  "created_at": "2026-06-28T10:30:00Z"
}
```

---

### PUT /api/bankroll/{bankroll_id}

Update bankroll settings.

**Request**:
```json
{
  "daily_loss_limit": 2000.00,
  "max_single_bet_size": 1000.00,
  "status": "active"
}
```

**Response** (200):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Main Account",
  "daily_loss_limit": 2000.00,
  "max_single_bet_size": 1000.00,
  "updated_at": "2026-06-28T10:35:00Z"
}
```

---

### DELETE /api/bankroll/{bankroll_id}

Delete/close bankroll.

**Response** (204): No Content

**Errors**:
- `400 Bad Request`: Cannot delete bankroll with open positions
- `404 Not Found`: Bankroll not found

---

## Predictions

### POST /api/predictions

Submit a prediction (required before placing bet).

**Request**:
```json
{
  "bankroll_id": "550e8400-e29b-41d4-a716-446655440001",
  "event_id": "mlb_2026_06_28_NYY_BOS",
  "event_name": "Yankees vs Red Sox",
  "event_type": "sports",
  "market_type": "moneyline",
  "predicted_outcome": "home_win",
  "predicted_probability": 0.58,
  "confidence_score": 0.82,
  "signal_source": "strikeout_edge_model_v2",
  "reasoning": "Strong strikeout rate differential favors Yankees pitcher",
  "model_version": "2.1.0",
  "market_odds": 1.90
}
```

**Response** (201):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440100",
  "event_id": "mlb_2026_06_28_NYY_BOS",
  "predicted_probability": 0.58,
  "confidence_score": 0.82,
  "market_odds": 1.90,
  "expected_value": 0.102,
  "kelly_fraction": 0.0289,
  "created_at": "2026-06-28T10:30:00Z"
}
```

---

### GET /api/predictions/{prediction_id}

Get prediction details.

**Response** (200):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440100",
  "event_name": "Yankees vs Red Sox",
  "predicted_probability": 0.58,
  "confidence_score": 0.82,
  "market_odds": 1.90,
  "expected_value": 0.102,
  "kelly_fraction": 0.0289,
  "created_at": "2026-06-28T10:30:00Z"
}
```

---

### GET /api/predictions

Get all predictions for user.

**Query Parameters**:
- `limit`: Number of predictions to return (default: 50, max: 500)
- `offset`: Pagination offset (default: 0)
- `status`: Filter by status (pending, matched, settled)
- `event_type`: Filter by type (sports, crypto, equities)

**Response** (200):
```json
{
  "predictions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440100",
      "event_name": "Yankees vs Red Sox",
      "predicted_probability": 0.58,
      "created_at": "2026-06-28T10:30:00Z"
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

---

## Kelly Calculator

### POST /api/kelly/calculate

Calculate Kelly fraction for a prediction.

**Request**:
```json
{
  "predicted_probability": 0.58,
  "decimal_odds": 1.90,
  "kelly_fraction_multiplier": 0.25
}
```

**Response** (200):
```json
{
  "win_probability": 0.58,
  "loss_probability": 0.42,
  "decimal_odds": 1.90,
  "kelly_fraction": 0.1155,
  "fractional_kelly": 0.0289,
  "expected_value": 0.102,
  "bet_size_for_bankroll_1000": 28.9,
  "ruin_probability": 0.00001,
  "confidence_interval": {
    "lower": 0.0115,
    "upper": 0.2319
  }
}
```

**Error Cases**:
- `400 Bad Request`: Invalid probability or odds
  ```json
  {
    "detail": "Probability must be between 0 and 1"
  }
  ```

---

### POST /api/kelly/optimal-bet

Calculate optimal bet size for given bankroll.

**Request**:
```json
{
  "bankroll": 10000.00,
  "predicted_probability": 0.58,
  "decimal_odds": 1.90,
  "kelly_multiplier": 0.25
}
```

**Response** (200):
```json
{
  "bankroll": 10000.00,
  "kelly_fraction": 0.1155,
  "fractional_kelly": 0.0289,
  "recommended_bet_size": 289.00,
  "potential_return": 548.10,
  "potential_loss": 289.00,
  "expected_value": 93.06
}
```

---

## Betting

### POST /api/place-bet

Place a new bet (requires valid prediction).

**Request**:
```json
{
  "prediction_id": "550e8400-e29b-41d4-a716-446655440100",
  "bankroll_id": "550e8400-e29b-41d4-a716-446655440001",
  "stake": 289.00,
  "kelly_fraction": 0.25
}
```

**Response** (201):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440200",
  "prediction_id": "550e8400-e29b-41d4-a716-446655440100",
  "bankroll_id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "PENDING",
  "stake": 289.00,
  "odds": 1.90,
  "potential_return": 548.10,
  "kelly_fraction_used": 0.25,
  "kelly_stake": 289.00,
  "created_at": "2026-06-28T10:30:00Z"
}
```

**Errors**:
- `429 Too Many Requests`: Risk limits exceeded (headers contain details)
- `400 Bad Request`: Invalid prediction or bankroll
- `403 Forbidden`: Insufficient bankroll balance

---

### GET /api/bets/{bet_id}

Get bet details.

**Response** (200):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440200",
  "prediction_id": "550e8400-e29b-41d4-a716-446655440100",
  "status": "PLACED",
  "stake": 289.00,
  "odds": 1.90,
  "potential_return": 548.10,
  "state_history": [
    {
      "from_status": "PENDING",
      "to_status": "PLACED",
      "timestamp": "2026-06-28T10:31:00Z",
      "reason": "Bet accepted by bookmaker"
    }
  ],
  "created_at": "2026-06-28T10:30:00Z",
  "placed_at": "2026-06-28T10:31:00Z"
}
```

---

### POST /api/bets/{bet_id}/transition

Transition bet status (state machine).

**Request**:
```json
{
  "status": "MATCHED",
  "reason": "Bet matched at odds 1.88"
}
```

**Response** (200):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440200",
  "status": "MATCHED",
  "matched_at": "2026-06-28T10:32:00Z"
}
```

**Valid Transitions**:
- PENDING → PLACED (bookmaker accepts)
- PLACED → MATCHED (odds confirmed)
- MATCHED → SETTLED (outcome determined)
- Any state → VOIDED (if cancelled)

---

### GET /api/bets

Get all bets for user.

**Query Parameters**:
- `bankroll_id`: Filter by bankroll
- `status`: Filter by status (PENDING, PLACED, MATCHED, SETTLED)
- `limit`: Results per page (default: 50)
- `offset`: Pagination offset

**Response** (200):
```json
{
  "bets": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440200",
      "status": "SETTLED",
      "stake": 289.00,
      "potential_return": 548.10,
      "actual_outcome": "win",
      "pnl": 259.10,
      "roi_pct": 0.896
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

---

## Positions

### GET /api/positions

Get all open positions for user.

**Response** (200):
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440300",
    "bet_id": "550e8400-e29b-41d4-a716-446655440200",
    "bankroll_id": "550e8400-e29b-41d4-a716-446655440001",
    "quantity": 1,
    "entry_price": 289.00,
    "current_price": 350.00,
    "entry_value": 289.00,
    "current_value": 350.00,
    "unrealized_pnl": 61.00,
    "unrealized_pnl_pct": 0.2111,
    "exposure_ratio": 0.035,
    "status": "OPEN",
    "opened_at": "2026-06-28T10:30:00Z",
    "days_held": 1
  }
]
```

---

### POST /api/positions/{position_id}/close

Close a position.

**Request**:
```json
{
  "exit_price": 350.00,
  "reason": "Taking profit"
}
```

**Response** (200):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440300",
  "status": "CLOSED",
  "exit_price": 350.00,
  "realized_pnl": 61.00,
  "realized_pnl_pct": 0.2111,
  "closed_at": "2026-06-28T11:30:00Z"
}
```

---

### POST /api/positions/{position_id}/hedge

Create hedge position.

**Request**:
```json
{
  "hedge_ratio": 0.50,
  "hedge_price": 320.00
}
```

**Response** (201):
```json
{
  "original_position_id": "550e8400-e29b-41d4-a716-446655440300",
  "hedge_position_id": "550e8400-e29b-41d4-a716-446655440301",
  "hedge_ratio": 0.50,
  "created_at": "2026-06-28T11:30:00Z"
}
```

---

## Settlement

### POST /api/settle

Settle completed bets.

**Request**:
```json
{
  "bet_ids": ["550e8400-e29b-41d4-a716-446655440200"],
  "outcomes": ["win"]
}
```

**Response** (200):
```json
{
  "settled_bets": 1,
  "total_pnl": 259.10,
  "successful_settlements": 1,
  "failed_settlements": 0,
  "settlements": [
    {
      "bet_id": "550e8400-e29b-41d4-a716-446655440200",
      "status": "SETTLED",
      "outcome": "win",
      "pnl": 259.10,
      "settled_at": "2026-06-28T16:00:00Z"
    }
  ]
}
```

---

### GET /api/settle/history

Get settlement history.

**Query Parameters**:
- `bankroll_id`: Filter by bankroll
- `start_date`: ISO format date
- `end_date`: ISO format date
- `limit`: Results per page

**Response** (200):
```json
{
  "settlements": [
    {
      "settled_at": "2026-06-28T16:00:00Z",
      "bet_id": "550e8400-e29b-41d4-a716-446655440200",
      "outcome": "win",
      "pnl": 259.10,
      "bankroll_balance_after": 9759.10
    }
  ],
  "total": 150,
  "total_pnl": 3850.50
}
```

---

## Audit & Logs

### GET /api/audit-log

Get audit logs for user.

**Query Parameters**:
- `event_type`: Filter by event type (bet_placed, risk_limit_breach, etc.)
- `resource_type`: Filter by resource (Bet, Position, RiskControl)
- `start_date`: ISO format date
- `end_date`: ISO format date
- `limit`: Results per page (max: 1000)

**Response** (200):
```json
{
  "logs": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440400",
      "event_type": "bet_placed",
      "resource_type": "Bet",
      "resource_id": "550e8400-e29b-41d4-a716-446655440200",
      "decision": "approved",
      "reason": "Within risk limits",
      "justification": {
        "daily_loss_used": 0.289,
        "daily_loss_limit": 1.0,
        "kelly_fraction": 0.0289,
        "expected_value": 0.102
      },
      "ip_address": "203.0.113.45",
      "created_at": "2026-06-28T10:30:00Z"
    }
  ],
  "total": 5000,
  "limit": 50,
  "offset": 0
}
```

---

## Portfolio

### GET /api/portfolio/health

Get portfolio health metrics.

**Response** (200):
```json
{
  "portfolio_value": 12350.50,
  "initial_capital": 10000.00,
  "return_amount": 2350.50,
  "return_percentage": 0.2351,
  "sharpe_ratio": 1.85,
  "max_drawdown": -0.15,
  "win_rate": 0.5667,
  "profit_factor": 2.45,
  "kelly_compliance": 0.98,
  "portfolio_health_score": 0.82,
  "active_positions": 12,
  "settled_bets": 150
}
```

---

### POST /api/portfolio/simulate

Simulate portfolio under different scenarios.

**Request**:
```json
{
  "scenario": "bear_market",
  "volatility_multiplier": 1.5,
  "correlation_change": 0.2
}
```

**Response** (200):
```json
{
  "scenario": "bear_market",
  "projected_portfolio_value": 10500.00,
  "projected_return": 0.05,
  "stress_test_results": {
    "max_loss": -2000.00,
    "ruin_probability": 0.001,
    "recovery_time_months": 3
  }
}
```

---

### GET /api/portfolio/allocation

Get current portfolio allocation across verticals.

**Response** (200):
```json
{
  "allocations": [
    {
      "vertical": "mlb",
      "allocation_percentage": 0.35,
      "current_exposure": 4322.67,
      "position_count": 45
    },
    {
      "vertical": "tennis",
      "allocation_percentage": 0.25,
      "current_exposure": 3087.63,
      "position_count": 32
    },
    {
      "vertical": "cricket",
      "allocation_percentage": 0.20,
      "current_exposure": 2470.10,
      "position_count": 28
    },
    {
      "vertical": "horse",
      "allocation_percentage": 0.12,
      "current_exposure": 1482.06,
      "position_count": 18
    },
    {
      "vertical": "hockey",
      "allocation_percentage": 0.08,
      "current_exposure": 988.04,
      "position_count": 12
    }
  ],
  "total_exposure": 12350.50,
  "diversification_score": 0.88
}
```

---

## Verticals

### GET /api/verticals

Get all available prediction verticals.

**Response** (200):
```json
{
  "verticals": [
    {
      "id": "mlb",
      "name": "MLB Strikeout Edge",
      "description": "Strikeout prediction model using pitch sequencing and pitcher stats",
      "status": "operational",
      "model_version": "2.1.0",
      "last_updated": "2026-06-28T08:00:00Z",
      "edge_type": "strikeout_rate_differential"
    },
    {
      "id": "tennis",
      "name": "Tennis Elo+Markov",
      "description": "Tennis match outcome prediction using Elo and Markov chains",
      "status": "operational",
      "model_version": "1.5.2",
      "last_updated": "2026-06-27T20:00:00Z",
      "edge_type": "elo_markov_transition"
    },
    {
      "id": "cricket",
      "name": "Cricket LBW Edge",
      "description": "Umpire LBW decision prediction - proprietary niche",
      "status": "operational",
      "model_version": "1.0.0",
      "last_updated": "2026-06-28T12:00:00Z",
      "edge_type": "umpire_decision_prediction"
    },
    {
      "id": "horse",
      "name": "Horse Racing Benter",
      "description": "Horse racing prediction using sectional times and form",
      "status": "operational",
      "model_version": "1.2.0",
      "last_updated": "2026-06-26T18:00:00Z",
      "edge_type": "sectional_time_analysis"
    },
    {
      "id": "hockey",
      "name": "NHL Shots-on-Goal",
      "description": "Hockey win prediction using SOG differentials",
      "status": "operational",
      "model_version": "2.0.0",
      "last_updated": "2026-06-28T10:30:00Z",
      "edge_type": "sog_differential"
    }
  ]
}
```

---

### GET /api/verticals/{vertical_id}

Get predictions for specific vertical.

**Query Parameters**:
- `limit`: Results per page (default: 50)
- `offset`: Pagination offset
- `event_status`: open, settled
- `sort_by`: confidence, odds, expected_value

**Response** (200):
```json
{
  "vertical": "mlb",
  "predictions": [
    {
      "event_id": "mlb_2026_06_28_NYY_BOS",
      "event_name": "Yankees vs Red Sox",
      "predicted_probability": 0.58,
      "confidence_score": 0.82,
      "market_odds": 1.90,
      "expected_value": 0.102,
      "kelly_fraction": 0.0289,
      "status": "open"
    }
  ]
}
```

---

### POST /api/verticals/{vertical_id}/predict

Get prediction from specific vertical model.

**Request**:
```json
{
  "event_id": "mlb_2026_06_28_NYY_BOS",
  "pitcher_id": "123456",
  "batter_id": "789012",
  "historical_data": {
    "pitcher_k_rate": 0.28,
    "batter_k_rate": 0.18
  }
}
```

**Response** (200):
```json
{
  "vertical": "mlb",
  "event_id": "mlb_2026_06_28_NYY_BOS",
  "predicted_outcome": "above_strikeout_line",
  "predicted_probability": 0.58,
  "confidence_score": 0.82,
  "edge_explanation": "Pitcher K-rate is 10% above batter average, favors strikeout",
  "recommended_action": "place_bet"
}
```

---

## CLV Tracking

### POST /api/clv/capture

Record closed line value capture for backtest analysis.

**Request**:
```json
{
  "bet_id": "550e8400-e29b-41d4-a716-446655440200",
  "opening_line": 1.90,
  "closing_line": 1.85,
  "actual_odds_wagered": 1.88,
  "outcome": "win"
}
```

**Response** (201):
```json
{
  "clv_value": 0.0263,
  "clv_percentage": 1.56,
  "opening_line": 1.90,
  "closing_line": 1.85,
  "actual_odds": 1.88,
  "captured_at": "2026-06-28T16:00:00Z"
}
```

---

### GET /api/clv/analysis

Get CLV analysis for period.

**Query Parameters**:
- `start_date`: ISO format date
- `end_date`: ISO format date
- `vertical`: Filter by vertical (mlb, tennis, etc.)

**Response** (200):
```json
{
  "period": {
    "start": "2026-06-01",
    "end": "2026-06-28"
  },
  "total_clv": 0.3850,
  "average_clv_per_bet": 0.00257,
  "total_bets_analyzed": 150,
  "clv_win_rate": 0.667,
  "roi_with_clv": 0.2451,
  "roi_without_clv": 0.2050,
  "clv_contribution": 0.0401,
  "vertical_breakdown": {
    "mlb": {
      "total_clv": 0.1850,
      "average_clv": 0.00308,
      "bets": 60
    }
  }
}
```

---

### GET /api/clv/leaderboard

Get CLV leaderboard for comparison.

**Query Parameters**:
- `period`: week, month, all_time
- `min_bets`: Minimum bets to qualify (default: 30)

**Response** (200):
```json
{
  "leaderboard": [
    {
      "rank": 1,
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "sharp_bettor",
      "total_clv": 0.4250,
      "average_clv_per_bet": 0.00289,
      "bets_tracked": 147,
      "roi": 0.3150
    },
    {
      "rank": 2,
      "user_id": "550e8400-e29b-41d4-a716-446655440001",
      "username": "data_analyst",
      "total_clv": 0.3850,
      "average_clv_per_bet": 0.00257,
      "bets_tracked": 150,
      "roi": 0.2451
    }
  ],
  "user_rank": 2,
  "period": "all_time"
}
```

---

## Health & Monitoring

### GET /health

Full health check with component status.

**Response** (200):
```json
{
  "status": "healthy",
  "timestamp": "2026-06-28T10:30:00Z",
  "version": "1.0.0",
  "environment": "production",
  "database": {
    "status": "ok",
    "type": "PostgreSQL",
    "latency_ms": 12.34
  },
  "apis": {
    "odds_api": "configured",
    "polymarket_api": "configured"
  },
  "portfolio_engine": "ok",
  "verticals": {
    "mlb": {
      "status": "operational",
      "type": "Strikeout Edge"
    },
    "tennis": {
      "status": "operational",
      "type": "Elo+Markov"
    },
    "cricket": {
      "status": "operational",
      "type": "LBW Edge"
    },
    "horse": {
      "status": "operational",
      "type": "Benter Model"
    },
    "hockey": {
      "status": "operational",
      "type": "SOG Model"
    }
  },
  "all_verticals_operational": true
}
```

---

### GET /health/database

Database-only health check.

**Response** (200):
```json
{
  "status": "ok",
  "database": "connected",
  "latency_ms": 12.34
}
```

---

### GET /health/ready

Kubernetes readiness probe.

**Response** (200):
```json
{
  "ready": true
}
```

---

### GET /health/live

Kubernetes liveness probe.

**Response** (200):
```json
{
  "live": true
}
```

---

## Error Handling

### Standard Error Response

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong",
  "status_code": 400,
  "error_code": "INVALID_INPUT",
  "timestamp": "2026-06-28T10:30:00Z",
  "path": "/api/endpoint",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Common Error Codes

| Code | Status | Meaning |
|------|--------|---------|
| INVALID_INPUT | 400 | Request validation failed |
| UNAUTHORIZED | 401 | Missing or invalid JWT token |
| FORBIDDEN | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found |
| CONFLICT | 409 | Resource already exists |
| RATE_LIMIT | 429 | Rate limit exceeded |
| RISK_LIMIT_BREACH | 429 | Risk management limit exceeded |
| INTERNAL_ERROR | 500 | Server error |
| SERVICE_UNAVAILABLE | 503 | Dependency unavailable |

---

## Rate Limiting

All endpoints are rate limited to **100 requests per minute per user**.

**Rate limit headers**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1656319800
```

When limit exceeded (429):
```json
{
  "detail": "Rate limit exceeded",
  "retry_after": 12
}
```

---

## Pagination

List endpoints support pagination:

**Query Parameters**:
- `limit`: Items per page (default: 50, max: 500)
- `offset`: Starting position (default: 0)

**Response Format**:
```json
{
  "items": [...],
  "total": 1500,
  "limit": 50,
  "offset": 0,
  "has_more": true
}
```

---

## Webhooks (Optional)

For real-time event notifications, subscribe to webhooks:

**Available Events**:
- `bet.placed`
- `bet.settled`
- `position.opened`
- `position.closed`
- `risk_limit.breach`
- `settlement.failed`

**Example Webhook Payload**:
```json
{
  "event": "bet.settled",
  "timestamp": "2026-06-28T16:00:00Z",
  "data": {
    "bet_id": "550e8400-e29b-41d4-a716-446655440200",
    "outcome": "win",
    "pnl": 259.10
  }
}
```

Register webhook: `POST /api/webhooks` with your endpoint URL.
