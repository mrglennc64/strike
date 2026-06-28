# Quick Start Guide

## Option 1: Using Docker Compose (Easiest)

```bash
# Navigate to backend directory
cd backend

# Start PostgreSQL and API
docker-compose up

# API will be available at http://localhost:8000
# Swagger UI at http://localhost:8000/docs
```

## Option 2: Manual Setup

### Prerequisites
- Python 3.10+
- PostgreSQL 12+

### Setup Steps

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create PostgreSQL database
createdb betting_db

# 4. Configure environment
cp .env.example .env
# Edit .env with your database credentials

# 5. Run server
python main.py
```

API available at `http://localhost:8000`

## Quick API Test

### 1. Sign Up
```bash
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "password123"
  }'
```

### 2. Initialize Bankroll
```bash
curl -X POST http://localhost:8000/api/bankroll/initialize \
  -H "Content-Type: application/json" \
  -d '{
    "initial_amount": 10000
  }'
```

### 3. Submit Prediction
```bash
curl -X POST http://localhost:8000/api/predictions/ \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "GAME_1",
    "event_description": "Team A vs Team B",
    "outcome": "Team A wins",
    "predicted_probability": 0.62,
    "market_probability": 0.55,
    "market_odds": 1.82,
    "notes": "Strong matchup"
  }'
```

### 4. Calculate Kelly
```bash
curl -X POST http://localhost:8000/api/kelly/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "bankroll": 10000,
    "win_probability": 0.62,
    "odds": 1.82
  }'
```

### 5. Place Bet
```bash
curl -X POST http://localhost:8000/api/place-bet/ \
  -H "Content-Type: application/json" \
  -d '{
    "prediction_id": 1,
    "stake": 490,
    "kelly_fraction": 0.25
  }'
```

### 6. Check Positions
```bash
curl http://localhost:8000/api/positions/summary
```

## Using Interactive Swagger UI

Open http://localhost:8000/docs in your browser for interactive API testing.

## Key Endpoints Quick Reference

| Action | Endpoint | Method |
|--------|----------|--------|
| Sign up | `/api/auth/signup` | POST |
| Login | `/api/auth/login` | POST |
| Initialize bankroll | `/api/bankroll/initialize` | POST |
| Get bankroll | `/api/bankroll/current` | GET |
| Submit prediction | `/api/predictions/` | POST |
| Calculate Kelly | `/api/kelly/calculate` | POST |
| Place bet | `/api/place-bet/` | POST |
| Transition bet status | `/api/place-bet/{id}/transition` | POST |
| Get active positions | `/api/positions/active` | GET |
| Get position summary | `/api/positions/summary` | GET |
| Settle bet | `/api/settle/{id}` | POST |
| Get audit logs | `/api/audit-log/` | GET |

## Typical Workflow

1. **User Signs Up**: `/api/auth/signup`
2. **Set Bankroll**: `/api/bankroll/initialize`
3. **Submit Prediction**: `/api/predictions/` with odds and probabilities
4. **Calculate Stake**: `/api/kelly/calculate` or `/api/kelly/suggest-stake`
5. **Place Bet**: `/api/place-bet/` with prediction_id and stake
6. **Transition States**: Move through PENDING → SUBMITTED → CONFIRMED → LIVE
7. **Settle**: `/api/settle/{bet_id}` when outcome is known
8. **Monitor**: `/api/positions/summary` for P&L tracking

## Database Reset (Development)

```bash
# Drop all tables and restart
rm test.db  # If using SQLite

# Or with PostgreSQL:
dropdb betting_db
createdb betting_db
python main.py  # Will recreate tables
```

## Troubleshooting

### "Connection refused" on port 5432
- PostgreSQL not running
- For Docker: Run `docker-compose up`
- For manual: Run `postgres` service

### "ModuleNotFoundError"
- Virtual environment not activated
- Run `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

### Database errors
- Check `.env` DATABASE_URL matches your setup
- For Docker: Use `DATABASE_URL=postgresql://betting_user:betting_password@postgres:5432/betting_db`
- For local PostgreSQL: Update user/password in `.env`

## Next Steps

- Read full [README.md](README.md) for complete API documentation
- Run tests: `pytest test_api.py -v`
- Check [example_usage.py](example_usage.py) for programmatic client
- Explore risk limits in [config.py](config.py)
- Study state machine in [services/bet_state_machine.py](services/bet_state_machine.py)

## Environment Variables

Key settings in `.env`:

```
DATABASE_URL=postgresql://user:pass@localhost/betting_db
SECRET_KEY=your-secret-key
MAX_SINGLE_BET_FRACTION=0.05  # 5% of bankroll
MAX_DAILY_LOSS_FRACTION=0.10  # 10% daily loss
MAX_KELLY_FRACTION=0.25       # 25% Kelly max
DEBUG=False
```

See `.env.example` for all options.
