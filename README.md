# Betting Framework - Generic Kelly Criterion for Any Prediction

A production-ready betting/trading framework that works with **any binary outcome prediction** (sports, crypto, elections, weather, etc.). Implements Kelly Criterion position sizing, multi-layer risk controls, and comprehensive audit logging.

## Key Features

- **Outcome-Agnostic**: Works with sports, crypto, equities, commodities, or any binary prediction
- **Kelly Criterion Sizing**: Automatic position sizing with fractional Kelly for risk management
- **Risk Controls**: Daily loss limits, exposure caps, correlation warnings
- **Bet State Machine**: Strict bet lifecycle with audit trail (PENDING → PLACED → MATCHED → SETTLED)
- **Real-time Dashboard**: Monitor bankroll, positions, and P&L
- **Full Audit Trail**: Every decision logged with reasoning and justification
- **API-First Architecture**: REST API + React frontend, easily integrable

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | FastAPI + SQLAlchemy + PostgreSQL |
| **Frontend** | React 18 + TypeScript + Tailwind |
| **Deployment** | Docker + Railway/Render + Vercel |
| **Testing** | pytest (35+ test cases) |
| **Auth** | JWT tokens |

## Quick Start (5 minutes)

### Local Development with Docker

```bash
# Clone repo
git clone https://github.com/yourusername/betting-framework.git
cd betting-framework

# Start all services
docker-compose up

# Services running:
# API: http://localhost:8000
# Frontend: http://localhost:3000
# Database: postgres://localhost:5432
```

Visit http://localhost:3000 and sign up!

### Manual Setup

**Backend:**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
# API running on http://localhost:8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
# Frontend running on http://localhost:3000
```

## API Endpoints

### Authentication

```
POST   /api/auth/signup          # Create account
POST   /api/auth/login           # Login
GET    /api/auth/me              # Current user
```

### Bankroll Management

```
POST   /api/bankroll/initialize  # Set initial capital ($10,000)
GET    /api/bankroll/current     # Get balance & ROI
```

### Predictions & Betting

```
POST   /api/predictions          # Submit prediction (62% vs 55% market)
POST   /api/kelly/calculate      # Calculate Kelly %, suggested stake
POST   /api/place-bet            # Place bet with auto Kelly sizing
```

### Portfolio

```
GET    /api/positions/active     # All open bets
GET    /api/positions/all        # All bets with filters
GET    /api/positions/summary    # Portfolio metrics (Sharpe, drawdown, win rate)
```

### Settlement

```
POST   /api/settle/{id}          # Settle bet with outcome
POST   /api/settle/{id}/void     # Void bet (return stake)
```

### Audit & Compliance

```
GET    /api/audit-log            # All actions with timestamps
GET    /api/audit-log/summary    # Compliance metrics
```

## Example Workflow

```bash
# 1. Sign up
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"trader1","password":"pass"}'

# 2. Login
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -d "username=user@example.com&password=pass" \
  | jq -r '.access_token')

# 3. Initialize bankroll ($10,000)
curl -X POST http://localhost:8000/api/bankroll/initialize \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"initial_amount":10000}'

# 4. Submit prediction
curl -X POST http://localhost:8000/api/predictions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id":"MLB_2026_06_27_NYY_BOS",
    "event_description":"Yankees vs Red Sox",
    "outcome":"yankees_win",
    "predicted_probability":0.65,
    "market_probability":0.55,
    "market_odds":1.85,
    "notes":"Strong pitcher matchup advantage"
  }'

# 5. Calculate Kelly
curl -X POST http://localhost:8000/api/kelly/calculate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"win_probability":0.65,"decimal_odds":1.85}'

# 6. Place $490 bet
curl -X POST http://localhost:8000/api/place-bet \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prediction_id":"<prediction_id>",
    "stake":490,
    "notes":"High confidence"
  }'

# 7. Settle bet (Yankees won, $908.65 return)
curl -X POST http://localhost:8000/api/settle/<bet_id> \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"actual_outcome":"yankees_win","actual_return":908.65}'

# 8. Check bankroll (+$418.65 profit!)
curl -X GET http://localhost:8000/api/bankroll/current \
  -H "Authorization: Bearer $TOKEN" | jq
```

## Project Structure

```
betting-framework/
├── backend/                    # FastAPI backend
│   ├── main.py               # Entry point
│   ├── config.py             # Configuration
│   ├── database.py           # SQLAlchemy setup
│   ├── requirements.txt       # Dependencies
│   ├── Dockerfile            # Docker image
│   ├── models/               # ORM models (User, Bankroll, Bet, etc)
│   ├── schemas/              # Pydantic request/response validation
│   ├── routes/               # API route handlers
│   ├── services/             # Business logic (Kelly, Risk, State Machine)
│   ├── middleware/           # Risk limits middleware
│   ├── test_api.py           # 35+ test cases
│   └── example_client.py     # Python client example
│
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── main.tsx          # Entry point
│   │   ├── App.tsx           # Main app + routing
│   │   ├── api/
│   │   │   └── client.ts     # API client
│   │   ├── store/
│   │   │   └── auth.ts       # Zustand auth store
│   │   ├── pages/            # Page components
│   │   ├── components/       # UI components
│   │   └── index.css         # Tailwind styles
│   ├── package.json          # Dependencies
│   ├── vite.config.ts        # Vite config
│   ├── Dockerfile            # Docker image
│   └── tsconfig.json         # TypeScript config
│
├── docker-compose.yml        # Local dev stack
├── docker-compose.prod.yml   # Production stack
├── .github/
│   └── workflows/
│       ├── ci-backend.yml    # Backend tests
│       ├── ci-frontend.yml   # Frontend tests
│       ├── deploy-backend.yml # Deploy to Railway
│       └── deploy-frontend.yml # Deploy to Vercel
├── DEPLOYMENT.md             # Complete deployment guide
├── ARCHITECTURE.md           # System architecture
└── README.md                 # This file
```

## Kelly Criterion Explanation

The Kelly Criterion calculates optimal position sizing to maximize long-term growth while minimizing ruin probability.

**Formula:** `f* = (b×p - q) / b`

Where:
- `b` = odds - 1 (net profit per unit)
- `p` = predicted probability
- `q` = 1 - p (loss probability)

**Example:**

```
Prediction: 65% win probability
Odds: 1.85

f* = (0.85 × 0.65 - 0.35) / 0.85
f* = 0.56 - 0.41 = 0.15 = 15% of bankroll

Bankroll: $10,000
Recommended Kelly: $1,500

Apply 25% fractional Kelly for safety:
Final stake: $1,500 × 0.25 = $375
```

If bet wins at 1.85 odds:
- Return: $375 × 1.85 = $694
- Profit: $694 - $375 = $319

## Risk Controls

The framework enforces multiple risk layers:

| Control | Default | Purpose |
|---------|---------|---------|
| **Daily Loss Limit** | 10% of bankroll | Prevent catastrophic losses |
| **Max Single Bet** | 5% of bankroll | Reduce variance |
| **Max Exposure** | 10% of bankroll | Total at-risk capital |
| **Correlation Check** | 0.70 threshold | Prevent correlated bets |
| **Kelly Clamp** | 0.01-0.25 | Full Kelly is too aggressive |
| **Fractional Kelly** | 25% | Safety multiplier |

All limits are **enforced before bet execution** via middleware.

## Testing

Run comprehensive test suite:

```bash
cd backend
pytest test_api.py -v

# Run specific test
pytest test_api.py::TestKelly -v

# Coverage report
pytest --cov=. test_api.py
```

**Test Coverage:**
- ✓ Authentication (signup, login, JWT)
- ✓ Bankroll management (CRUD, calculations)
- ✓ Predictions (submit, calculate edge)
- ✓ Kelly sizing (edge cases, validation)
- ✓ Bet placement (state machine, transitions)
- ✓ Settlement (wins, losses, voids)
- ✓ Risk limits (daily loss, exposure, correlation)
- ✓ Audit logging (complete trail)

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for complete deployment instructions.

**Quick deployment (Railway):**

```bash
# 1. Create Railway project
railway init
railway link

# 2. Add PostgreSQL
railway add

# 3. Set environment variables
railway variables

# 4. Deploy
railway up
```

**Recommended domain: betting-framework.ai** ($10-15/year)

**Cost estimate: $40-50/month for production**
- Vercel Frontend: $20 (free tier for most apps)
- Railway Backend + DB: $20-30

## Configuration

Edit environment variables in `.env`:

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/betting_db

# Security
SECRET_KEY=your-long-random-secret-key
DEBUG=False

# Risk Management
MAX_SINGLE_BET_FRACTION=0.05          # 5% of bankroll
MAX_DAILY_LOSS_FRACTION=0.10          # 10% of initial
MAX_KELLY_FRACTION=0.25               # Full Kelly is aggressive
MIN_KELLY_FRACTION=0.01

# Frontend
VITE_API_URL=http://localhost:8000
```

## Documentation

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Complete system design (Kelly, Risk, State Machine)
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Deployment guide (Railway, Render, AWS, self-hosted)
- **[backend/README.md](./backend/README.md)** - Backend API documentation
- **[backend/QUICKSTART.md](./backend/QUICKSTART.md)** - Backend quick start

## Features by Module

### Kelly Criterion Module

```python
from services.kelly_calculator import KellyCriterion

# Calculate Kelly percentage
kelly_pct = KellyCriterion.kelly_percentage(
    probability=0.65,
    odds=1.85
)  # Returns: 0.15 (15%)

# Apply fractional Kelly for safety
safe_kelly = KellyCriterion.fractional_kelly(kelly_pct, fraction=0.25)
# Returns: 0.0375 (3.75%)

# Convert to currency amount
bet_size = KellyCriterion.optimal_bet_size(
    kelly_pct=kelly_pct,
    bankroll=10000,
    fractional=0.25
)  # Returns: $375
```

### Risk Manager Module

```python
from services.risk_manager import RiskManager

rm = RiskManager()

# Check all risk limits before bet
result = rm.check_all_limits(
    bankroll=bankroll,
    proposed_bet=bet,
    existing_positions=positions
)

if result.passed:
    print("Bet approved, execute placement")
else:
    print(f"Bet blocked: {result.block_reason}")
    print(f"Warnings: {result.warnings}")
```

### Bet State Machine

```python
from services.bet_state_machine import BetStateMachine

sm = BetStateMachine()

# Transition through states
await sm.transition(
    bet=bet,
    new_state="SUBMITTED",
    reason="User placed bet"
)

# Terminal states: SETTLED, CLOSED, VOIDED, REJECTED
```

## Use Cases

This framework works for:

1. **Sports Betting** (NFL, MLB, soccer, tennis)
2. **Crypto Trading** (price predictions, liquidation events)
3. **Election Forecasting** (candidate win probability)
4. **Weather Betting** (temperature, precipitation)
5. **Stock Options** (directional bets on equities)
6. **Commodity Futures** (oil, gold, wheat)

## Example: Crypto Price Prediction

```python
# Prediction: ETH will be > $2,500 in 24 hours
prediction = {
    "event_id": "ETH_2026_06_28_2500",
    "event_description": "Ethereum > $2,500 by June 28, 2026",
    "outcome": "above_target",
    "predicted_probability": 0.72,  # Your model says 72%
    "market_probability": 0.65,      # Market (implied odds)
    "market_odds": 1.54,             # Decimal odds
    "notes": "Strong technical setup, volume spike"
}

# Edge: 0.72 > 0.65 = Positive edge detected
# Kelly: f* = (0.54 × 0.72 - 0.28) / 0.54 = 0.21 = 21%
# Stake (25% fractional Kelly): 0.21 × 0.25 × $10,000 = $525

# If correct: $525 × 1.54 = $809 (+$284 profit)
# ROI: +54% on single bet
```

## API Documentation (Auto-Generated)

Visit http://localhost:8000/docs for interactive Swagger UI with try-it-out functionality.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/cool-feature`)
3. Write tests for new features
4. Commit changes (`git commit -am 'Add cool feature'`)
5. Push to branch (`git push origin feature/cool-feature`)
6. Create Pull Request
7. GitHub Actions will run tests automatically

## License

MIT License - see LICENSE file for details

## Support

For issues:
1. Check [DEPLOYMENT.md](./DEPLOYMENT.md) for deployment troubleshooting
2. Review test cases in `backend/test_api.py`
3. Check example client in `backend/example_client.py`
4. Open GitHub issue with details

## Roadmap

**Phase 1 (MVP) - Complete**
- ✓ User auth + bankroll management
- ✓ Prediction submission
- ✓ Kelly Criterion calculator
- ✓ Bet placement with state machine
- ✓ Risk limits enforcement
- ✓ Full audit logging

**Phase 2 (Q3 2026)**
- [ ] Parlay builder (combine multiple bets)
- [ ] Hedging module (auto-hedge large moves)
- [ ] Portfolio analytics (Sharpe, Sortino, drawdown)
- [ ] Backtesting engine

**Phase 3 (Q4 2026)**
- [ ] Third-party integrations (Pinnacle API, Betfair, dYdX)
- [ ] Multi-currency support
- [ ] Arbitrage detection
- [ ] Advanced correlation analysis

---

**Status**: ✓ Production Ready

**Version**: 1.0.0

**Last Updated**: June 28, 2026

**Author**: Betting Framework Team
