# Generic Betting/Trading Framework Architecture

## Overview

A modular, production-ready betting/trading engine designed for binary outcome prediction across any market (sports, crypto, equities, commodities). Implements Kelly Criterion position sizing, multi-layer risk controls, and event-driven state management with full audit trail.

**Core Philosophy:**
- **Outcome-agnostic**: Works with any prediction source (models, oracles, signals)
- **Risk-first**: Position sizing and limits enforced before execution
- **Auditable**: Every decision logged with reasoning and timestamps
- **Scalable**: Distributed workers, async processing, real-time monitoring

---

## System Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
├──────────────────────────┬──────────────────────────────────────┤
│  React Dashboard         │  Third-party APIs (Webhooks)         │
│  - Bankroll tracking     │  - Odds feeds (pinnaacle, betfair)   │
│  - Live positions        │  - Oracle triggers (Chainlink, etc)  │
│  - Manual risk overrides │  - Trading signals (external models) │
└──────────────────────────┴──────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY / AUTH                          │
├─────────────────────────────────────────────────────────────────┤
│  JWT/API Key validation, rate limiting, request queuing         │
└──────────────────────────────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND (Core Engine)                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌────────────────────────┐  ┌──────────────────────────────────┐   │
│  │   Prediction Handler   │  │   Position Manager              │   │
│  │  - Parse predictions   │  │  - Track active positions       │   │
│  │  - Validate inputs     │  │  - Calculate exposure           │   │
│  │  - Enrich with context │  │  - Settle on outcome            │   │
│  └────────────────────────┘  └──────────────────────────────────┘   │
│                                                                        │
│  ┌────────────────────────┐  ┌──────────────────────────────────┐   │
│  │   Kelly Sizing Module  │  │   Risk Controls Module           │   │
│  │  - Expected value calc │  │  - Daily loss limits             │   │
│  │  - Optimal sizing      │  │  - Sector/corr exposure limits  │   │
│  │  - Fractional Kelly    │  │  - Max position sizing          │   │
│  │  - Ruin probability    │  │  - Portfolio stress tests       │   │
│  └────────────────────────┘  └──────────────────────────────────┘   │
│                                                                        │
│  ┌────────────────────────┐  ┌──────────────────────────────────┐   │
│  │   Bet State Machine    │  │   Audit & Compliance            │   │
│  │  - PENDING → PLACED    │  │  - Log all decisions            │   │
│  │  - PLACED → MATCHED    │  │  - Record justification         │   │
│  │  - MATCHED → SETTLED   │  │  - Trace risk limit breaches    │   │
│  │  - Error handling      │  │  - Regulatory reporting         │   │
│  └────────────────────────┘  └──────────────────────────────────┘   │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│         SERVICES & WORKERS (Async Task Processing)                   │
├──────────────────────────────────────────────────────────────────────┤
│  - Bet Placement Worker (connect to bookmakers/exchanges)            │
│  - Settlement Worker (monitor odds, close positions)                │
│  - Bankroll Reconciliation (nightly PnL settlement)                 │
│  - Risk Alert Worker (monitor limits, trigger hedges)              │
│  - Data Sync Worker (update positions from external feeds)         │
└──────────────────────────────────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                                       │
├──────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  PostgreSQL (Primary Store)                                  │   │
│  │  - Users, Bankrolls, Predictions, Positions, Bets           │   │
│  │  - Audit logs, Risk limits, Event history                   │   │
│  │  - Accounts, Bookmaker credentials (encrypted)              │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Redis (Cache & Message Queue)                              │   │
│  │  - Active positions (fast reads)                             │   │
│  │  - Bankroll state (atomic updates)                          │   │
│  │  - Job queue (Celery/RQ for workers)                        │   │
│  │  - Rate limiting (per-user counters)                        │   │
│  │  - Pub/Sub for real-time updates                            │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Time-series DB (InfluxDB/TimescaleDB)                      │   │
│  │  - Bankroll snapshots (for charting)                        │   │
│  │  - Position metrics (Sharpe, drawdown)                      │   │
│  │  - Risk limit breach events                                 │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Data Models

### Core Entities

#### User
```python
class User(Base):
    id: UUID
    email: str (unique)
    username: str
    password_hash: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    # Preferences
    kelly_fraction: float = 0.25  # Conservative fractional Kelly
    risk_profile: Literal["aggressive", "moderate", "conservative"]
    timezone: str
    
    # Relationships
    bankrolls: List[Bankroll]
    positions: List[Position]
    audit_logs: List[AuditLog]
```

#### Bankroll
```python
class Bankroll(Base):
    id: UUID
    user_id: UUID (FK)
    name: str  # "Main account", "Crypto portfolio", etc
    currency: str  # USD, EUR, BTC, etc
    initial_amount: Decimal
    current_balance: Decimal
    
    # Status tracking
    status: Literal["active", "suspended", "closed"]
    created_at: datetime
    last_settlement: datetime
    
    # Risk limits (can be overridden per-bankroll)
    daily_loss_limit: Decimal = None
    max_single_bet_size: Decimal = None
    max_exposure_ratio: float = 0.10  # % of bankroll
    
    # Audit
    total_bets_placed: int
    total_wins: int
    total_losses: int
    roi: float
    
    # Relationships
    positions: List[Position]
    risk_alerts: List[RiskAlert]
```

#### Bet (Prediction Input)
```python
class Bet(Base):
    id: UUID
    bankroll_id: UUID (FK)
    
    # Prediction details
    event_id: str  # Bookmaker event ID or unique identifier
    event_name: str  # "Team A vs Team B", "ETH/USDT > 2000", etc
    event_type: str  # "sports", "crypto", "equities", "commodities"
    market_type: str  # "moneyline", "spread", "over_under", "binary_option"
    
    # User prediction
    predicted_outcome: str  # "win", "loss", "over", "under", "call", "put"
    predicted_probability: float  # 0.0-1.0
    confidence_score: float  # Model confidence
    
    # Prediction metadata
    signal_source: str  # "model_v2", "external_api", "manual"
    reasoning: str  # Why this prediction
    model_version: str
    
    # Sizing
    recommended_kelly_size: Decimal
    final_bet_size: Decimal
    odds: float  # Decimal odds (1.5, 2.0, etc)
    
    # Status
    state: Literal["PENDING", "PLACED", "MATCHED", "SETTLED", "VOIDED", "ERROR"]
    state_history: List[BetStateTransition]
    
    # Outcome
    actual_outcome: str = None
    pnl: Decimal = None  # P&L if settled
    roi_pct: float = None
    
    # Timestamps
    created_at: datetime
    placed_at: datetime = None
    matched_at: datetime = None
    settled_at: datetime = None
    expires_at: datetime = None  # For time-limited bets
```

#### Position
```python
class Position(Base):
    id: UUID
    bankroll_id: UUID (FK)
    bet_id: UUID (FK)
    
    # Position details
    quantity: Decimal  # Units owned (fractional shares, contracts, etc)
    entry_price: Decimal
    current_price: Decimal
    
    # P&L tracking
    entry_value: Decimal  # quantity * entry_price
    current_value: Decimal  # quantity * current_price
    unrealized_pnl: Decimal
    unrealized_pnl_pct: float
    
    # Risk metrics
    exposure_ratio: float  # % of bankroll at risk
    max_loss: Decimal  # Stop loss level
    max_gain: Decimal  # Take profit level
    
    # Status
    status: Literal["OPEN", "PARTIALLY_CLOSED", "CLOSED", "HEDGED"]
    hedge_ratio: float = 0.0  # % hedged
    
    # Tracking
    opened_at: datetime
    closed_at: datetime = None
    days_held: int
    
    # Relationships
    hedge_positions: List[Position]  # Self-reference for hedges
```

#### RiskAlert
```python
class RiskAlert(Base):
    id: UUID
    bankroll_id: UUID (FK)
    
    # Alert details
    alert_type: Literal[
        "daily_loss_limit_breach",
        "max_exposure_breach",
        "correlation_warning",
        "volatility_spike",
        "liquidity_warning"
    ]
    severity: Literal["info", "warning", "critical"]
    
    # Context
    current_value: Decimal
    threshold_value: Decimal
    breach_pct: float  # How much over limit
    
    # Resolution
    status: Literal["active", "acknowledged", "resolved"]
    action_taken: str = None  # What was done (e.g., "position_reduced")
    
    created_at: datetime
    resolved_at: datetime = None
```

#### AuditLog
```python
class AuditLog(Base):
    id: UUID
    user_id: UUID (FK)
    bankroll_id: UUID (FK)
    
    # Event tracking
    event_type: str  # "bet_placed", "risk_limit_breach", "kelly_override", etc
    resource_type: str  # "Bet", "Position", "RiskControl", etc
    resource_id: UUID
    
    # Decision details
    decision: str  # "approved", "rejected", "overridden"
    reason: str  # Why the decision was made
    justification: dict  # JSON: risk metrics, model scores, etc
    
    # System context
    ip_address: str
    user_agent: str
    api_version: str
    
    created_at: datetime
    
    # Before/after state
    before_state: dict
    after_state: dict
```

#### BetStateTransition
```python
class BetStateTransition(Base):
    id: UUID
    bet_id: UUID (FK)
    
    from_state: str
    to_state: str
    
    # Transition details
    reason: str  # Why state changed
    data: dict  # Context (odds changed, outcome known, etc)
    
    created_at: datetime
    created_by: str  # "system", "user", "external_feed"
```

---

## API Endpoints

### Authentication
```
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/refresh
POST   /api/auth/logout
GET    /api/auth/me
```

### Predictions & Placement
```
POST   /api/predict
  Request:
    {
      "bankroll_id": "uuid",
      "event_id": "MLB_2026_06_27_NYY_BOS_K",
      "event_name": "Yankees vs Red Sox",
      "event_type": "sports",
      "market_type": "moneyline",
      "predicted_outcome": "yankees_win",
      "predicted_probability": 0.65,
      "confidence_score": 0.82,
      "signal_source": "model_v2",
      "reasoning": "Strength of schedule, pitcher matchup advantage",
      "odds": 1.85
    }
  Response:
    {
      "prediction_id": "uuid",
      "predicted_outcome": "yankees_win",
      "predicted_probability": 0.65,
      "edge": 0.07,  # (0.65 * 1.85) - 1
      "kelly_size": 0.045,  # Before fractional Kelly
      "recommended_size": 0.011,  # After 25% fractional Kelly
      "sizing_rationale": "Positive edge, within risk limits",
      "risk_check": {
        "passes": true,
        "daily_loss_available": 250.50,
        "max_exposure_available": 12500.00,
        "correlation_warning": null
      }
    }

POST   /api/place-bet
  Request:
    {
      "prediction_id": "uuid",
      "bet_size": 50.00,  # Override if < recommended
      "bookmaker": "pinnacle",
      "force_override": false,  # Skip risk checks if true (audit logged)
      "notes": "High confidence model signal"
    }
  Response:
    {
      "bet_id": "uuid",
      "state": "PENDING",
      "size_placed": 50.00,
      "odds": 1.85,
      "potential_return": 92.50,
      "max_loss": -50.00,
      "state_history": [
        {
          "from_state": null,
          "to_state": "PENDING",
          "reason": "Created",
          "timestamp": "2026-06-27T14:32:10Z"
        }
      ],
      "audit_trail": {
        "approved_by": "user_id",
        "risk_checks": { ... },
        "kelly_rationale": "..."
      }
    }

POST   /api/bets/{bet_id}/cancel
  Only allowed if state == "PENDING"
```

### Positions & Portfolio
```
GET    /api/positions
  Response:
    {
      "total_positions": 42,
      "total_exposure": 5234.50,
      "total_unrealized_pnl": 324.10,
      "portfolio_metrics": {
        "sharpe_ratio": 1.23,
        "max_drawdown": -0.08,
        "win_rate": 0.58,
        "profit_factor": 1.34
      },
      "positions": [
        {
          "position_id": "uuid",
          "bet_id": "uuid",
          "event_name": "...",
          "quantity": 50.0,
          "entry_price": 1.85,
          "current_price": 2.10,
          "unrealized_pnl": 12.50,
          "unrealized_pnl_pct": 0.025,
          "exposure_ratio": 0.004,
          "status": "OPEN",
          "opened_at": "2026-06-27T14:32:10Z",
          "days_held": 1
        }
      ]
    }

GET    /api/positions/{position_id}
  Response: Full position object + related bets

PUT    /api/positions/{position_id}
  Request:
    {
      "action": "close_partial",
      "quantity_to_close": 25.0,
      "reason": "Profit taking"
    }
  Response: Updated position with audit trail

POST   /api/positions/{position_id}/hedge
  Request:
    {
      "hedge_ratio": 0.5,
      "hedge_type": "inverse",
      "market": "pinnacle"
    }
  Response: New hedge position created

GET    /api/bankrolls/{bankroll_id}
  Response:
    {
      "bankroll_id": "uuid",
      "name": "Main account",
      "currency": "USD",
      "initial_amount": 10000.00,
      "current_balance": 10324.10,
      "roi": 0.0324,
      "roi_pct": 3.24,
      "status": "active",
      "created_at": "2026-01-01T00:00:00Z",
      "metrics": {
        "total_bets": 145,
        "total_wins": 84,
        "total_losses": 61,
        "win_rate": 0.579,
        "avg_win": 15.40,
        "avg_loss": -12.10,
        "profit_factor": 1.24,
        "sharpe_ratio": 1.08,
        "max_drawdown": -0.067
      },
      "risk_limits": {
        "daily_loss_limit": -250.00,
        "max_single_bet_size": 100.00,
        "max_exposure_ratio": 0.10,
        "current_daily_loss": -45.30,
        "current_exposure_ratio": 0.052
      }
    }
```

### Risk & Limits
```
GET    /api/risk/status
  Response:
    {
      "bankroll_id": "uuid",
      "daily_loss_status": {
        "limit": -250.00,
        "current": -45.30,
        "remaining": -204.70,
        "breach": false
      },
      "exposure_status": {
        "limit": 0.10,
        "current": 0.052,
        "remaining": 0.048,
        "breach": false
      },
      "correlation_status": {
        "warning_threshold": 0.70,
        "max_correlation": 0.54,
        "correlated_positions": [],
        "warning": false
      },
      "volatility_status": {
        "current_vol": 0.12,
        "typical_vol": 0.10,
        "spike_detected": false
      },
      "alerts": []
    }

PUT    /api/risk/limits/{bankroll_id}
  Request:
    {
      "daily_loss_limit": -300.00,
      "max_single_bet_size": 150.00,
      "max_exposure_ratio": 0.15
    }

GET    /api/risk/alerts
  Response:
    {
      "active_alerts": [
        {
          "alert_id": "uuid",
          "type": "daily_loss_limit_breach",
          "severity": "warning",
          "current_value": -245.50,
          "threshold": -250.00,
          "breach_pct": 0.018,
          "created_at": "2026-06-27T14:32:10Z"
        }
      ]
    }

POST   /api/risk/alerts/{alert_id}/acknowledge
POST   /api/risk/limits/stress-test
  Request:
    {
      "scenario": "nasdaq_drop_5pct",  # Predefined or custom
      "affected_positions": ["pos_id_1", "pos_id_2"]
    }
```

### Audit & Compliance
```
GET    /api/audit/logs
  Query params:
    ?start_date=2026-06-01&end_date=2026-06-27
    &event_type=kelly_override
    &user_id=uuid
    &limit=100
  Response:
    {
      "total_logs": 2345,
      "logs": [
        {
          "log_id": "uuid",
          "event_type": "bet_placed",
          "resource_type": "Bet",
          "resource_id": "uuid",
          "decision": "approved",
          "reason": "Within kelly sizing",
          "user_id": "uuid",
          "bankroll_id": "uuid",
          "justification": {
            "kelly_size": 0.045,
            "fractional_kelly": 0.011,
            "bet_size": 0.012,
            "edge": 0.07,
            "risk_checks": {
              "daily_loss": true,
              "exposure": true,
              "correlation": true
            }
          },
          "before_state": {...},
          "after_state": {...},
          "created_at": "2026-06-27T14:32:10Z"
        }
      ]
    }

GET    /api/audit/logs/{log_id}

GET    /api/audit/export
  Query params:
    ?start_date=2026-01-01&end_date=2026-06-27
    &format=csv|json
  Returns: Full audit export for compliance/reconciliation

GET    /api/audit/dashboard
  Response: High-level compliance metrics
    {
      "total_events": 2345,
      "kelly_overrides": 12,
      "risk_breaches": 3,
      "manual_overrides": 7,
      "force_placements": 1,
      "compliance_score": 0.98
    }
```

---

## Kelly Criterion Module

### Core Algorithm

```python
class KellyCriterion:
    """
    Implements Kelly Criterion for optimal position sizing.
    
    Kelly% = (edge * odds - (1 - edge)) / (odds - 1)
    
    Where:
    - edge = predicted_probability - (1 / odds)
    - Kelly% = fraction of bankroll to wager
    """
    
    @staticmethod
    def expected_value(probability: float, odds: float) -> float:
        """
        Calculate expected value per unit wagered.
        EV = (probability * odds) - 1
        """
        return (probability * odds) - 1
    
    @staticmethod
    def kelly_percentage(
        probability: float,
        odds: float,
        min_kelly: float = 0.0,
        max_kelly: float = 1.0
    ) -> float:
        """
        Calculate optimal Kelly sizing.
        Clipped to [min_kelly, max_kelly] for safety.
        """
        if probability <= 0 or odds <= 1:
            return 0.0
        
        # Kelly formula
        win_prob = probability
        lose_prob = 1 - probability
        win_payout = odds - 1  # Net profit per unit
        lose_loss = 1  # Loss per unit
        
        kelly_pct = (win_prob * win_payout - lose_prob * lose_loss) / win_payout
        
        # Clip to safe bounds
        return max(min_kelly, min(kelly_pct, max_kelly))
    
    @staticmethod
    def fractional_kelly(kelly_pct: float, fraction: float = 0.25) -> float:
        """
        Apply fractional Kelly for risk reduction.
        Typical: 25% Kelly (0.25x) balances growth vs stability.
        """
        return kelly_pct * fraction
    
    @staticmethod
    def ruin_probability(
        kelly_pct: float,
        num_bets: int,
        win_probability: float
    ) -> float:
        """
        Gamblers' ruin: probability of losing entire bankroll.
        Uses risk of ruin formula.
        """
        if kelly_pct <= 0 or kelly_pct >= 1:
            return 1.0
        
        # Simplified RoR for multiple bets
        odds_ratio = (1 - win_probability) / win_probability if win_probability > 0 else 1.0
        loss_factor = (1 - kelly_pct) ** num_bets
        
        return min(1.0, loss_factor)
    
    @staticmethod
    def optimal_bet_size(
        kelly_pct: float,
        bankroll: Decimal,
        fractional: float = 0.25
    ) -> Decimal:
        """
        Convert Kelly % to actual currency bet size.
        """
        fractional_pct = kelly_pct * fractional
        return bankroll * Decimal(str(fractional_pct))
```

### Sizing Workflow

```python
class BetSizer:
    """
    End-to-end sizing with risk checks.
    """
    
    def size_bet(
        self,
        bankroll: Bankroll,
        prediction: Prediction,
        kelly_config: KellyConfig
    ) -> BetSizingResult:
        """
        1. Calculate raw Kelly
        2. Apply fractional Kelly
        3. Check risk limits
        4. Return recommended size + rationale
        """
        
        # Step 1: Raw Kelly
        kelly_pct = KellyCriterion.kelly_percentage(
            probability=prediction.predicted_probability,
            odds=prediction.odds
        )
        
        # Step 2: Fractional Kelly (e.g., 25%)
        fractional_kelly = KellyCriterion.fractional_kelly(
            kelly_pct=kelly_pct,
            fraction=kelly_config.kelly_fraction
        )
        
        # Step 3: Convert to currency
        recommended_size = KellyCriterion.optimal_bet_size(
            kelly_pct=kelly_pct,
            bankroll=bankroll.current_balance,
            fractional=kelly_config.kelly_fraction
        )
        
        # Step 4: Cap by individual bet limits
        capped_size = min(
            recommended_size,
            bankroll.max_single_bet_size or recommended_size
        )
        
        # Step 5: Ruin probability check
        ror = KellyCriterion.ruin_probability(
            kelly_pct=fractional_kelly,
            num_bets=100,  # Typical horizon
            win_probability=prediction.predicted_probability
        )
        
        return BetSizingResult(
            recommended_size=capped_size,
            kelly_pct=kelly_pct,
            fractional_kelly=fractional_kelly,
            ruin_probability=ror,
            rationale={
                "edge": prediction.edge,
                "ev": KellyCriterion.expected_value(
                    prediction.predicted_probability,
                    prediction.odds
                ),
                "kelly_fraction_applied": kelly_config.kelly_fraction,
                "individual_bet_cap_applied": capped_size != recommended_size
            }
        )
```

---

## Risk Controls Module

### Multi-Layer Risk Framework

```python
class RiskController:
    """
    Enforces risk limits before bet placement.
    Prevents pathological losses, correlation blowups, and margin calls.
    """
    
    def check_all_limits(
        self,
        bankroll: Bankroll,
        proposed_bet: Bet,
        existing_positions: List[Position]
    ) -> RiskCheckResult:
        """
        Run all risk checks in order. Any failure blocks bet.
        """
        checks = [
            self.check_daily_loss_limit(bankroll),
            self.check_single_bet_size(bankroll, proposed_bet),
            self.check_total_exposure(bankroll, proposed_bet, existing_positions),
            self.check_correlation(proposed_bet, existing_positions),
            self.check_liquidity(proposed_bet),
        ]
        
        passed = all(c.passed for c in checks)
        
        return RiskCheckResult(
            passed=passed,
            checks=checks,
            block_bet=not passed,
            warnings=[c for c in checks if c.severity == "warning"]
        )
    
    def check_daily_loss_limit(self, bankroll: Bankroll) -> RiskCheck:
        """
        Prevent daily losses exceeding limit.
        Resets at UTC midnight.
        """
        today_pnl = self.calculate_daily_pnl(bankroll)
        limit = bankroll.daily_loss_limit or -0.05 * bankroll.current_balance
        
        passed = today_pnl > limit
        
        return RiskCheck(
            name="daily_loss_limit",
            passed=passed,
            current_value=today_pnl,
            threshold=limit,
            severity="critical" if not passed else "info",
            message=f"Daily loss: {today_pnl} / {limit}"
        )
    
    def check_single_bet_size(self, bankroll: Bankroll, bet: Bet) -> RiskCheck:
        """
        Prevent single bet from exceeding max % of bankroll.
        """
        max_size = bankroll.max_single_bet_size or (0.05 * bankroll.current_balance)
        
        passed = bet.final_bet_size <= max_size
        
        return RiskCheck(
            name="single_bet_size",
            passed=passed,
            current_value=bet.final_bet_size,
            threshold=max_size,
            severity="critical" if not passed else "info"
        )
    
    def check_total_exposure(
        self,
        bankroll: Bankroll,
        proposed_bet: Bet,
        existing_positions: List[Position]
    ) -> RiskCheck:
        """
        Cap total at-risk capital (% of bankroll in open positions).
        """
        current_exposure = sum(
            p.unrealized_pnl * -1 for p in existing_positions if p.status == "OPEN"
        )
        proposed_exposure = proposed_bet.final_bet_size
        total_exposure = current_exposure + proposed_exposure
        
        max_exposure = bankroll.current_balance * bankroll.max_exposure_ratio
        
        passed = total_exposure <= max_exposure
        
        return RiskCheck(
            name="total_exposure",
            passed=passed,
            current_value=total_exposure,
            threshold=max_exposure,
            severity="warning" if not passed else "info"
        )
    
    def check_correlation(
        self,
        proposed_bet: Bet,
        existing_positions: List[Position]
    ) -> RiskCheck:
        """
        Warn if new position highly correlated with existing ones.
        Prevents "all eggs in one basket" scenarios.
        """
        correlations = [
            self.estimate_correlation(proposed_bet, pos) 
            for pos in existing_positions
        ]
        
        max_corr = max(correlations) if correlations else 0.0
        warning_threshold = 0.70
        
        return RiskCheck(
            name="correlation",
            passed=max_corr <= warning_threshold,
            current_value=max_corr,
            threshold=warning_threshold,
            severity="warning",
            data={"max_corr_position": max_corr}
        )
    
    def check_liquidity(self, bet: Bet) -> RiskCheck:
        """
        Verify bet can be closed at reasonable slippage.
        """
        # Simplified: just check odds not too wide
        passed = bet.odds > 1.01  # Reasonable liquidity threshold
        
        return RiskCheck(
            name="liquidity",
            passed=passed,
            severity="warning" if not passed else "info"
        )
    
    def estimate_correlation(self, bet: Bet, position: Position) -> float:
        """
        Estimate correlation between new bet and existing position.
        Uses event metadata + historical data.
        """
        # Simplified: would use correlation matrix from model
        if bet.event_type != position.event_type:
            return 0.2  # Different asset classes
        
        # Same event type: higher correlation
        return 0.5  # Placeholder
```

### Risk Alert Triggering

```python
class RiskAlertEngine:
    """
    Monitors positions and triggers alerts when thresholds breached.
    """
    
    def evaluate_alerts(self, bankroll: Bankroll) -> List[RiskAlert]:
        """
        Run continuous monitoring after position updates.
        """
        alerts = []
        
        # Daily loss monitoring
        if self.check_daily_loss_breach(bankroll):
            alerts.append(RiskAlert(
                bankroll_id=bankroll.id,
                alert_type="daily_loss_limit_breach",
                severity="critical"
            ))
        
        # Exposure monitoring
        if self.check_exposure_breach(bankroll):
            alerts.append(RiskAlert(
                bankroll_id=bankroll.id,
                alert_type="max_exposure_breach",
                severity="warning"
            ))
        
        # Volatility spike
        if self.check_volatility_spike(bankroll):
            alerts.append(RiskAlert(
                bankroll_id=bankroll.id,
                alert_type="volatility_spike",
                severity="info"
            ))
        
        return alerts
```

---

## Bet State Machine

### States and Transitions

```
                    ┌─────────────┐
                    │   PENDING   │  (Prediction + sizing done, awaiting placement)
                    └──────┬──────┘
                           │ /place-bet
                           ▼
                    ┌─────────────┐
                    │   PLACED    │  (Sent to bookmaker, awaiting acceptance)
                    └──────┬──────┘
                           │ bookmaker confirms
                           ▼
                    ┌─────────────┐
                    │   MATCHED   │  (Accepted, position now open)
                    └──────┬──────┘
                    ┌──────┴──────┐
                    │             │
            outcome known    manual close
                    │             │
                    ▼             ▼
              ┌─────────┐   ┌──────────┐
              │SETTLED  │   │  CLOSED  │
              └─────────┘   └──────────┘
        
        Error paths:
        - PENDING → VOIDED (cancelled before placement)
        - PLACED → REJECTED (bookmaker rejects)
        - PLACED → TIMEOUT (unmatched after N hours)
        - Any state → ERROR (system failure)
```

### State Machine Implementation

```python
class BetStateMachine:
    """
    Enforces valid state transitions.
    All transitions logged with reasoning.
    """
    
    # Valid transitions
    TRANSITIONS = {
        BetState.PENDING: [BetState.PLACED, BetState.VOIDED, BetState.ERROR],
        BetState.PLACED: [BetState.MATCHED, BetState.REJECTED, BetState.TIMEOUT, BetState.ERROR],
        BetState.MATCHED: [BetState.SETTLED, BetState.CLOSED, BetState.ERROR],
        BetState.SETTLED: [],  # Terminal
        BetState.CLOSED: [],   # Terminal
        BetState.VOIDED: [],   # Terminal
        BetState.REJECTED: [], # Terminal
        BetState.ERROR: [],    # Terminal
    }
    
    async def transition(
        self,
        bet: Bet,
        new_state: BetState,
        reason: str,
        data: dict = None
    ) -> BetStateTransition:
        """
        Attempt state transition. Raise exception if invalid.
        """
        current_state = bet.state
        
        if new_state not in self.TRANSITIONS[current_state]:
            raise InvalidStateTransition(
                f"{current_state} -> {new_state} not allowed"
            )
        
        # Create transition record
        transition = BetStateTransition(
            bet_id=bet.id,
            from_state=current_state,
            to_state=new_state,
            reason=reason,
            data=data or {}
        )
        
        # Update bet
        bet.state = new_state
        if new_state == BetState.PLACED:
            bet.placed_at = utcnow()
        elif new_state == BetState.MATCHED:
            bet.matched_at = utcnow()
        elif new_state in [BetState.SETTLED, BetState.CLOSED]:
            bet.settled_at = utcnow()
        
        # Persist
        await self.db.add(transition)
        await self.db.commit()
        
        # Log
        await self.audit_log.record(
            event_type=f"bet_state_{new_state}",
            resource_type="Bet",
            resource_id=bet.id,
            reason=reason,
            data=transition.dict()
        )
        
        return transition
    
    async def settle_bet(
        self,
        bet: Bet,
        actual_outcome: str,
        final_price: float = None
    ) -> None:
        """
        Settle a matched bet with outcome.
        Calculates P&L and updates bankroll.
        """
        if actual_outcome not in [bet.predicted_outcome, "opposite", "void"]:
            raise ValueError(f"Invalid outcome: {actual_outcome}")
        
        # Calculate P&L
        if actual_outcome == "void":
            pnl = Decimal(0)
        elif actual_outcome == bet.predicted_outcome:
            # Win: bet_size * (odds - 1)
            pnl = bet.final_bet_size * (Decimal(str(bet.odds)) - Decimal(1))
        else:
            # Loss: -bet_size
            pnl = -bet.final_bet_size
        
        bet.actual_outcome = actual_outcome
        bet.pnl = pnl
        bet.roi_pct = float(pnl / bet.final_bet_size)
        
        # Transition to settled
        await self.transition(
            bet=bet,
            new_state=BetState.SETTLED,
            reason=f"Outcome: {actual_outcome}",
            data={"pnl": float(pnl), "outcome": actual_outcome}
        )
        
        # Update bankroll
        await self.update_bankroll(bet.bankroll_id, pnl)
        
        # Trigger risk re-evaluation
        await self.risk_alert_engine.evaluate_alerts(bet.bankroll)
```

---

## Tech Stack Recommendation

### Backend

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Framework** | FastAPI | Async-first, type-safe, auto-docs (OpenAPI), WebSocket support |
| **Language** | Python 3.11+ | Rich scientific ecosystem, fast dev, async/await maturity |
| **Task Queue** | Celery + Redis | Distributed async tasks (bet placement, settlement) |
| **ORM** | SQLAlchemy 2.0 | Type hints, async support, schema flexibility |
| **Validation** | Pydantic v2 | Runtime validation, JSON schema generation |
| **Auth** | FastAPI-JWT-Extended | JWT tokens, refresh flows, role-based access |
| **Encryption** | cryptography | Encrypt sensitive fields (API keys, passwords) |

### Database

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Primary Store** | PostgreSQL 15+ | ACID, JSON support, triggers for audit, spatial types for correlation |
| **Session Mgmt** | Redis | Distributed session store, cache invalidation |
| **Job Queue** | Redis Streams / RabbitMQ | Reliable async tasks (fallback: RabbitMQ) |
| **Time-Series** | TimescaleDB or InfluxDB | Bankroll snapshots, volatility tracking (optional but recommended) |

### Frontend

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Framework** | React 18+ | Component reusability, hooks, large ecosystem |
| **State Mgmt** | Zustand or Jotai | Lightweight, simpler than Redux for this use case |
| **Real-time** | WebSocket (FastAPI) | Live position updates, risk alerts |
| **Charting** | Recharts or Chart.js | Bankroll curves, position P&L, correlation heatmaps |
| **Tables** | TanStack Table | Server-side pagination for large position/audit logs |
| **Styling** | Tailwind CSS | Utility-first, dark mode support for trading dashboards |

### DevOps

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Containerization** | Docker + Docker Compose | Consistent dev/prod, orchestrate services |
| **Orchestration** | Kubernetes (optional) | Multi-region, auto-scaling if handling 1000+ users |
| **CI/CD** | GitHub Actions or GitLab CI | Code quality gates, test on PR, deploy on merge |
| **Monitoring** | Prometheus + Grafana | Metrics: API latency, worker queue depth, PnL curves |
| **Logging** | ELK Stack (Elasticsearch + Logstash + Kibana) | Centralized logs, audit trail search |
| **Secrets** | HashiCorp Vault or AWS Secrets Manager | Secure bookmaker API keys, encryption keys |

---

## Deployment Architecture

### Development Environment

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://user:pass@postgres:5432/betting_db
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: password
      POSTGRES_DB: betting_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./schema.sql:/docker-entrypoint-initdb.d/schema.sql

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  worker:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://user:pass@postgres:5432/betting_db
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis
    command: celery -A app.workers worker --loglevel=info

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      REACT_APP_API_URL: http://localhost:8000

volumes:
  postgres_data:
```

### Production Environment (AWS Example)

```
User → CloudFront (CDN)
  ↓
ALB (Application Load Balancer)
  ↓
ECS Fargate (FastAPI instances, auto-scaling)
  ↓
RDS PostgreSQL (Multi-AZ, automated backups)
  ↓
ElastiCache Redis (Cluster mode)
  ↓
SQS / SNS (for critical alerts)
  ↓
S3 (audit log exports)
```

---

## Security Considerations

### Authentication & Authorization
- JWT with 15-min access + 7-day refresh tokens
- Role-based access control (RBAC): User, Admin, Auditor
- IP whitelisting for high-risk operations (risk overrides)
- API key for programmatic access (webhooks from external models)

### Data Protection
- Encrypt at rest: PostgreSQL native encryption + per-row encryption for API keys
- Encrypt in transit: TLS 1.3 for all endpoints
- PII handling: Minimal user data (email only), use pseudonymous IDs internally

### Audit & Compliance
- Immutable audit log (cannot modify once written)
- Every action logged: user, timestamp, IP, resource, before/after state
- Retention: 7-year audit trail (regulatory requirement)
- Export: Audit trail exportable to CSV/JSON for compliance officers

### Bet Integrity
- Timestamp orders bets by microsecond
- Sign bets with HMAC-SHA256 to prevent tampering
- Store bookmaker response (odds, confirmation) as proof
- Detect double-placement: check for duplicate event_id + user_id within 5 seconds

---

## Monitoring & Observability

### Key Metrics

```python
# Prometheus metrics to track
metrics = {
    "api_request_duration_seconds": Histogram(["endpoint", "method"]),
    "api_request_total": Counter(["endpoint", "method", "status"]),
    "active_positions_total": Gauge(["bankroll_id"]),
    "bankroll_balance": Gauge(["bankroll_id", "currency"]),
    "daily_pnl": Gauge(["bankroll_id"]),
    "kelly_override_total": Counter(["reason"]),
    "risk_check_passed_ratio": Gauge(["check_type"]),
    "bet_placement_latency": Histogram(["bookmaker"]),
    "settlement_latency": Histogram(["event_type"]),
    "celery_worker_queue_depth": Gauge(["queue_name"]),
    "database_query_duration": Histogram(["query_type"]),
}
```

### Dashboard (Grafana)

1. **Trading Dashboard** (Trader View)
   - Active positions (count, exposure, P&L)
   - Bankroll curve (daily, weekly, monthly)
   - Win rate, profit factor, Sharpe ratio
   - Recent trades + outcomes

2. **Risk Dashboard** (Risk Manager View)
   - Daily loss against limit
   - Exposure against limit
   - Correlation heatmap (top positions)
   - Risk alerts (active + recent)

3. **Ops Dashboard** (System Administrator View)
   - API latency p50/p95/p99
   - Worker queue depth (placement, settlement)
   - Database connection pool health
   - Redis memory usage
   - Error rates (API, workers)

---

## API Rate Limiting

```python
# Per-user limits (JWT subject)
RATE_LIMITS = {
    "POST /api/predict": RateLimit(requests=10, window=60),           # 10/min
    "POST /api/place-bet": RateLimit(requests=5, window=60),          # 5/min
    "GET /api/positions": RateLimit(requests=60, window=60),          # 60/min
    "GET /api/audit/logs": RateLimit(requests=10, window=60),         # 10/min (audit ops)
    "PUT /api/risk/limits": RateLimit(requests=2, window=60),         # 2/min (risk overrides)
}
```

---

## Testing Strategy

### Unit Tests
- Kelly sizing edge cases (0% probability, odds < 1)
- State machine transitions (invalid paths)
- Risk checks (boundary conditions)
- P&L calculations (wins, losses, voided)

### Integration Tests
- End-to-end bet flow: predict → place → match → settle
- Concurrent bets (race conditions on bankroll balance)
- Risk limit enforcement (daily loss, exposure)
- Audit log completeness

### Load Tests
- 1000 concurrent users submitting predictions
- 100 concurrent bet placements
- Worker throughput (settlement rate)
- Database query performance (position queries with 100k+ records)

---

## Roadmap & Future Enhancements

### Phase 1 (MVP)
- ✓ User auth + bankroll CRUD
- ✓ Prediction → sizing → placement flow
- ✓ Kelly sizing + risk limits
- ✓ Audit logging

### Phase 2
- [ ] Parlay builder (combine multiple bets)
- [ ] Hedging module (auto-hedge large moves)
- [ ] ML calibration (adjust kelly_fraction per model)
- [ ] Third-party integrations (Pinnacle API, Betfair, dYdX)

### Phase 3
- [ ] Portfolio analytics (Sharpe, drawdown, factor attribution)
- [ ] Backtesting engine (replay historical signals)
- [ ] Multi-currency support (hedging currency risk)
- [ ] Arbitrage detection (cross-market opportunities)

---

## Conclusion

This architecture balances simplicity with production readiness. It is:
- **Generic**: Works across sports, crypto, equities, commodities
- **Risk-aware**: Kelly sizing + multi-layer controls prevent ruin
- **Auditable**: Every decision logged with full traceability
- **Scalable**: Async workers, caching, distributed architecture ready
- **Observable**: Comprehensive metrics and alerts

Start with Phase 1 MVP, validate with users, then expand to integrations and advanced features.
