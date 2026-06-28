# Betting Framework - Quick Start Guide

Get the betting framework running in **5 minutes**.

## Option 1: Docker Compose (Easiest - 3 commands)

```bash
# 1. Clone and navigate
git clone https://github.com/yourusername/betting-framework.git
cd betting-framework

# 2. Start all services (API, Frontend, Database)
docker-compose up

# 3. Open browser
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

**Done!** Create account and start trading.

---

## Option 2: Manual Setup (Development)

### Backend (Python 3.11+)

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
python main.py
```

API running on **http://localhost:8000**

### Frontend (Node.js 18+)

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend running on **http://localhost:3000**

---

## First Steps

### 1. Sign Up

Visit http://localhost:3000

- Email: `trader@example.com`
- Username: `trader1`
- Password: `password123`

### 2. Initialize Bankroll

Click "Dashboard" → "Initialize Bankroll" → Enter `$10,000`

### 3. Submit Prediction

Go to "Predictions":

```json
{
  "Event": "Yankees vs Red Sox",
  "Your Prediction": "Yankees Win (65%)",
  "Market Odds": 1.85,
  "Expected Value": "+7%"
}
```

### 4. Place Bet

Click "Place Bet":

- Predicted Probability: 0.65
- Odds: 1.85
- Stake: 500 (or let Kelly calculate: $375)

### 5. Settle Bet

After outcome:

- Go to "Positions"
- Click "Settle"
- Enter actual outcome: "Won"
- Enter return: $908.65
- See P&L: **+$408.65 profit**

---

## API Quick Reference

### Start API Server

```bash
cd backend
python main.py
```

### Health Check

```bash
curl http://localhost:8000/health
```

### Full API Docs

```
http://localhost:8000/docs          # Swagger UI (try-it-out)
http://localhost:8000/redoc         # ReDoc (beautiful)
http://localhost:8000/openapi.json  # OpenAPI spec
```

### Example API Call (cURL)

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=trader@example.com&password=password123"

# Get token from response
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Submit prediction
curl -X POST http://localhost:8000/api/predictions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "TEST_001",
    "event_description": "Test Event",
    "outcome": "win",
    "predicted_probability": 0.65,
    "market_probability": 0.55,
    "market_odds": 1.85,
    "notes": "Test prediction"
  }'
```

---

## Testing

```bash
cd backend
pytest test_api.py -v

# Single test class
pytest test_api.py::TestKelly -v

# Coverage
pytest --cov=. test_api.py --cov-report=html
```

---

## Common Issues

### Port Already in Use

```bash
# Kill process on port 8000 (API)
lsof -ti:8000 | xargs kill -9

# Kill process on port 3000 (Frontend)
lsof -ti:3000 | xargs kill -9

# Or use different ports
docker-compose -f docker-compose.override.yml up
```

### Database Connection Failed

```bash
# Reset database (remove volume)
docker-compose down -v
docker-compose up

# Or manually with postgres running
cd backend
python
>>> from database import Base, engine
>>> Base.metadata.create_all(bind=engine)
```

### Frontend Can't Connect to API

```bash
# Edit frontend/.env
VITE_API_URL=http://localhost:8000

# Rebuild frontend
cd frontend
npm run build
```

### Tests Failing

```bash
# Ensure database is running
docker-compose up postgres -d

# Install dependencies
cd backend
pip install -r requirements.txt

# Run with output
pytest test_api.py -v -s
```

---

## Project Structure

```
betting-framework/
├── backend/                     # FastAPI backend
│   ├── main.py                 # Start: python main.py
│   ├── config.py               # Configuration
│   ├── database.py             # Database models
│   ├── requirements.txt         # pip install -r
│   ├── models/                 # SQLAlchemy ORM
│   ├── routes/                 # API endpoints
│   ├── services/               # Kelly, Risk, State Machine
│   └── test_api.py             # Run: pytest
│
├── frontend/                    # React TypeScript
│   ├── src/main.tsx            # Start: npm run dev
│   ├── package.json            # npm install
│   ├── vite.config.ts          # Build: npm run build
│   └── index.html              # Entry HTML
│
├── docker-compose.yml          # Start all: docker-compose up
├── .github/workflows/          # CI/CD pipelines
├── DEPLOYMENT.md               # Production guide
├── ARCHITECTURE.md             # System design
└── README.md                   # Full documentation
```

---

## Environment Variables

### Backend (.env)

```env
DATABASE_URL=postgresql://user:password@postgres:5432/betting_db
SECRET_KEY=your-secret-key-32-chars-minimum
DEBUG=False
```

### Frontend (.env)

```env
VITE_API_URL=http://localhost:8000
```

---

## Useful Commands

```bash
# Docker
docker-compose up                    # Start everything
docker-compose down                  # Stop everything
docker-compose logs -f api          # View API logs
docker-compose logs -f frontend     # View frontend logs
docker-compose ps                    # Check services

# Backend
cd backend
python main.py                       # Run API
pytest test_api.py -v               # Run tests
python example_client.py             # Run example

# Frontend
cd frontend
npm run dev                          # Dev server
npm run build                        # Production build
npm run type-check                   # TypeScript check
npm run lint                         # Linting

# Database
psql postgresql://localhost:5432/betting_db
SELECT * FROM bets;
SELECT * FROM audit_logs ORDER BY timestamp DESC;

# Git
git status
git add .
git commit -m "Feature: ..."
git push origin main
```

---

## Next Steps

1. **Run locally** with Docker Compose
2. **Explore API** at http://localhost:8000/docs
3. **Read** [ARCHITECTURE.md](./ARCHITECTURE.md) for system design
4. **Deploy** using [DEPLOYMENT.md](./DEPLOYMENT.md)
5. **Customize** for your prediction source

---

## Support

- **API Docs**: http://localhost:8000/docs
- **Backend README**: backend/README.md
- **Architecture**: ARCHITECTURE.md
- **Deployment**: DEPLOYMENT.md

---

**Created**: June 28, 2026  
**Version**: 1.0.0
