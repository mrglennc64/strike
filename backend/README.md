# Betting Framework Backend API

A complete FastAPI backend for managing sports betting with Kelly criterion sizing, risk management, and a state machine for bet lifecycle tracking.

## Features

- **JWT Authentication**: Login/signup with token-based auth
- **Bankroll Management**: Set initial capital and track balance/ROI
- **Prediction Submission**: Submit predictions with win probability and market odds
- **Kelly Calculator**: Calculate optimal bet sizing using Kelly criterion
- **Bet Placement**: Place bets with state machine (PENDING → SUBMITTED → CONFIRMED → LIVE → SETTLED)
- **Risk Limits Middleware**: Enforce position limits before bet execution
- **Position Tracking**: Monitor active and settled positions with P&L
- **Settlement**: Settle bets with actual outcome
- **Audit Logging**: Complete audit trail of all actions
- **PostgreSQL**: Persistent storage with SQLAlchemy ORM

## Architecture

```
backend/
├── main.py                      # FastAPI app entry point
├── config.py                    # Configuration from environment
├── database.py                  # SQLAlchemy setup
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── models/
│   ├── __init__.py
│   ├── user.py                  # User authentication
│   ├── bankroll.py              # Bankroll tracking
│   ├── prediction.py            # Prediction data
│   ├── bet.py                   # Bet with state machine
│   └── audit_log.py             # Audit trail
├── schemas/
│   ├── __init__.py
│   ├── auth.py                  # Auth request/response
│   ├── bankroll.py              # Bankroll validation
│   ├── prediction.py            # Prediction validation
│   ├── kelly.py                 # Kelly calculation schemas
│   ├── bet.py                   # Bet validation
│   └── audit.py                 # Audit log response
├── routes/
│   ├── __init__.py
│   ├── auth.py                  # /api/auth
│   ├── bankroll.py              # /api/bankroll
│   ├── predictions.py           # /api/predictions
│   ├── kelly.py                 # /api/kelly
│   ├── bets.py                  # /api/place-bet
│   ├── positions.py             # /api/positions
│   ├── settlement.py            # /api/settle
│   └── audit.py                 # /api/audit-log
├── services/
│   ├── __init__.py
│   ├── kelly_calculator.py      # Kelly criterion math
│   ├── bet_state_machine.py     # Bet state transitions
│   └── risk_manager.py          # Risk limit checks
└── middleware/
    ├── __init__.py
    └── risk_limits.py           # Risk enforcement middleware
```

## Setup

### Prerequisites
- Python 3.10+
- PostgreSQL 12+

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your database credentials
```

### 3. Create Database

```bash
createdb betting_db
# Or use pgAdmin/other PostgreSQL tools
```

### 4. Run Server

```bash
python main.py
# Or with uvicorn directly:
# uvicorn main:app --reload
```

Server starts at `http://localhost:8000`

API documentation: `http://localhost:8000/docs` (Swagger UI)

## API Endpoints

### Authentication (`/api/auth`)

**Sign Up**
```
POST /api/auth/signup
{
  "email": "user@example.com",
  "username": "john_doe",
  "password": "secure_password"
}
Response: UserResponse with user details
```

**Login**
```
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "secure_password"
}
Response: TokenResponse with access_token
```

**Get Current User**
```
GET /api/auth/me
Headers: Authorization: Bearer <token>
Response: UserResponse
```

### Bankroll (`/api/bankroll`)

**Initialize Bankroll**
```
POST /api/bankroll/initialize
{
  "initial_amount": 10000.0
}
Response: BankrollResponse
```

**Get Current Bankroll**
```
GET /api/bankroll/current
Response: BankrollResponse with balance, ROI, P&L
```

**Update Bankroll** (used after settlement)
```
PUT /api/bankroll/update
{
  "current_balance": 9950.0
}
Response: BankrollResponse
```

### Predictions (`/api/predictions`)

**Submit Prediction**
```
POST /api/predictions/
{
  "event_id": "MLB_2026_06_28_NYY_BOS",
  "event_description": "Yankees vs Red Sox, June 28 2026",
  "outcome": "Yankees ML",
  "predicted_probability": 0.62,
  "market_probability": 0.55,
  "market_odds": 1.82,
  "notes": "Strong bullpen matchup in favor of Yankees"
}
Response: PredictionResponse with edge calculation
```

**Get Prediction**
```
GET /api/predictions/{prediction_id}
Response: PredictionResponse
```

**List Predictions**
```
GET /api/predictions/?skip=0&limit=100&has_edge=true
Response: List[PredictionResponse]
```

### Kelly Calculator (`/api/kelly`)

**Calculate Kelly Fraction**
```
POST /api/kelly/calculate
{
  "bankroll": 10000.0,
  "win_probability": 0.62,
  "odds": 1.82
}
Response: KellyResponse with kelly_fraction and suggested_stake
```

**Suggest Stake** (uses user's actual bankroll)
```
POST /api/kelly/suggest-stake?win_probability=0.62&odds=1.82&kelly_multiplier=0.25
Response: dict with suggested_stake and details
```

### Place Bet (`/api/place-bet`)

**Create Bet**
```
POST /api/place-bet/
{
  "prediction_id": 1,
  "stake": 500.0,
  "kelly_fraction": 0.25
}
Response: BetResponse in PENDING state
```

**Transition Bet Status**
```
POST /api/place-bet/{bet_id}/transition
{
  "status": "SUBMITTED",
  "notes": "Sent to sportsbook"
}
Response: BetResponse with new status and timestamp
```

Valid transitions:
- PENDING → SUBMITTED, CANCELLED
- SUBMITTED → CONFIRMED, CANCELLED
- CONFIRMED → LIVE, CANCELLED
- LIVE → SETTLED, VOID
- SETTLED, CANCELLED, VOID (terminal)

**Get Bet**
```
GET /api/place-bet/{bet_id}
Response: BetResponse
```

### Positions (`/api/positions`)

**Get Active Positions**
```
GET /api/positions/active?skip=0&limit=100
Response: List[BetResponse] for LIVE bets only
```

**Get All Bets**
```
GET /api/positions/all?skip=0&limit=100&status_filter=LIVE
Response: List[BetResponse] with optional status filter
```

**Get Positions Summary**
```
GET /api/positions/summary
Response: {
  "active_bets": 5,
  "active_exposure": 2500.0,
  "active_potential_return": 4150.0,
  "today": {
    "settled_bets": 8,
    "wins": 5,
    "losses": 3,
    "win_rate": 62.5,
    "pnl": 450.0
  },
  "all_time": {
    "settled_bets": 145,
    "wins": 87,
    "losses": 58,
    "win_rate": 60.0,
    "pnl": 3450.0
  }
}
```

### Settlement (`/api/settle`)

**Settle Bet**
```
POST /api/settle/{bet_id}
{
  "actual_outcome": "Yankees won 5-2",
  "is_winner": true,
  "actual_return": 910.0
}
Response: BetResponse in SETTLED state with P&L calculated
```

**Void Bet**
```
POST /api/settle/{bet_id}/void?reason="Event cancelled"
Response: BetResponse in VOID state, stake returned to bankroll
```

### Audit Log (`/api/audit-log`)

**List Audit Logs**
```
GET /api/audit-log/?skip=0&limit=100&days=30&action_filter=PLACE_BET
Response: List[AuditLogResponse] sorted by timestamp (newest first)
```

**Get Logs by Action**
```
GET /api/audit-log/action/SETTLE_BET
Response: List[AuditLogResponse]
```

**Get Logs by Entity**
```
GET /api/audit-log/entity/bet/123
Response: List[AuditLogResponse] for bet #123
```

**Get Audit Summary**
```
GET /api/audit-log/summary?days=30
Response: {
  "period_days": 30,
  "total_logs": 157,
  "by_action": {...},
  "by_entity_type": {...},
  "by_status": {...}
}
```

## Risk Management

Risk limits are enforced via middleware before bet execution:

### Configuration (config.py)
```python
MAX_SINGLE_BET_FRACTION = 0.05  # 5% of bankroll per bet
MAX_DAILY_LOSS_FRACTION = 0.10  # 10% daily loss limit
MAX_KELLY_FRACTION = 0.25       # Max 25% Kelly fraction
MIN_KELLY_FRACTION = 0.01       # Min 1% Kelly fraction
```

### Enforcement
Middleware (`middleware/risk_limits.py`) intercepts `/api/place-bet` and `/api/predictions` requests:
1. Checks if proposed stake > single bet limit
2. Checks if daily loss > daily loss limit
3. Checks if bankroll has sufficient funds

Failed checks return 429 status with detailed error messages.

## State Machine

Bet lifecycle follows strict state machine:

```
PENDING (initial)
  ├─→ SUBMITTED
  │     └─→ CONFIRMED
  │           └─→ LIVE
  │                 ├─→ SETTLED (terminal)
  │                 └─→ VOID (terminal)
  └─→ CANCELLED (terminal)
```

Transitions include timestamp tracking:
- `submitted_at`: When transitioned to SUBMITTED
- `confirmed_at`: When transitioned to CONFIRMED
- `live_at`: When transitioned to LIVE
- `settled_at`: When transitioned to SETTLED/VOID

## Kelly Criterion

Formula: `f* = (bp - q) / b`

Where:
- `b` = odds - 1 (fractional odds)
- `p` = win probability
- `q` = loss probability (1 - p)
- `f*` = Kelly fraction

The calculator:
1. Ensures probabilities sum to 1
2. Calculates raw Kelly fraction
3. Clamps to limits (MIN_KELLY to MAX_KELLY)
4. Applies fractional Kelly multiplier (default 25%)
5. Calculates suggested stake

Example:
```
Win probability: 62%
Odds: 1.82
Raw Kelly: 0.196 (19.6%)
25% Kelly: 0.049 (4.9%)
Bankroll: $10,000
Suggested stake: $490
Potential return: $891.80
Expected value: +$31.80
```

## Database Schema

### Users
- id, email, username, hashed_password, is_active, created_at, updated_at

### Bankrolls
- id, user_id, initial_amount, current_balance, total_wagered, total_returns, profit_loss, created_at, updated_at

### Predictions
- id, user_id, event_id, event_description, outcome, predicted_probability, market_probability, market_odds, edge_percentage, notes, created_at

### Bets
- id, user_id, prediction_id, status, stake, odds, potential_return, kelly_fraction_used, kelly_stake, is_settled, actual_outcome, is_winner, actual_return, pnl, created_at, submitted_at, confirmed_at, live_at, settled_at, notes

### AuditLogs
- id, user_id, action, entity_type, entity_id, status, details, ip_address, timestamp

## Testing

Run tests (requires pytest):
```bash
pytest
```

Example test file structure:
```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_signup():
    response = client.post("/api/auth/signup", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "password123"
    })
    assert response.status_code == 200
```

## Security Notes

1. **JWT Tokens**: Change SECRET_KEY in production
2. **CORS**: Update allowed origins in main.py
3. **Password Hashing**: Uses bcrypt (passlib)
4. **Database**: Use SSL connections in production
5. **Rate Limiting**: Consider adding rate limiter middleware
6. **Input Validation**: All inputs validated with Pydantic

## Performance Considerations

1. **Database Indexing**: Models include indexes on frequently queried fields
2. **Connection Pooling**: SQLAlchemy uses connection pooling
3. **Pagination**: List endpoints support skip/limit
4. **Caching**: Consider Redis for frequently accessed predictions
5. **Batch Operations**: Settlement can be batched

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Settings

```bash
# Use environment variables
export DATABASE_URL=postgresql://prod_user:prod_pass@prod_host:5432/betting_db
export SECRET_KEY=<strong-random-key>
export DEBUG=False

# Run with gunicorn + uvicorn workers
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

## Example Workflow

1. **User Signs Up**
   ```bash
   POST /api/auth/signup
   ```

2. **Initialize Bankroll**
   ```bash
   POST /api/bankroll/initialize
   {"initial_amount": 10000}
   ```

3. **Submit Prediction**
   ```bash
   POST /api/predictions/
   {
     "event_id": "MLB_2026_06_28",
     "predicted_probability": 0.62,
     "market_probability": 0.55,
     "market_odds": 1.82
   }
   ```

4. **Calculate Kelly**
   ```bash
   POST /api/kelly/calculate
   {
     "bankroll": 10000,
     "win_probability": 0.62,
     "odds": 1.82
   }
   ```

5. **Place Bet**
   ```bash
   POST /api/place-bet/
   {
     "prediction_id": 1,
     "stake": 490
   }
   ```

6. **Transition to Live**
   ```bash
   POST /api/place-bet/1/transition
   {"status": "SUBMITTED"}
   POST /api/place-bet/1/transition
   {"status": "CONFIRMED"}
   POST /api/place-bet/1/transition
   {"status": "LIVE"}
   ```

7. **Settle Bet**
   ```bash
   POST /api/settle/1
   {
     "actual_outcome": "Event occurred",
     "is_winner": true,
     "actual_return": 891.80
   }
   ```

8. **Check Results**
   ```bash
   GET /api/positions/summary
   GET /api/bankroll/current
   GET /api/audit-log/?limit=10
   ```

## License

Proprietary - Internal Use Only
