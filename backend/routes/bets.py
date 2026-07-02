from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from models import Bet, Prediction, Bankroll, AuditLog
from schemas import BetCreate, BetResponse, BetStatusUpdate
from services import KellyCalculator, BetStateMachine, RiskManager
from .auth import get_current_user_id
import json

router = APIRouter(prefix="/api/place-bet", tags=["bets"])


@router.post("/", response_model=BetResponse)
def place_bet(
    request: BetCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Place a new bet with state machine.

    Creates bet in PENDING state, validates risk limits, and manages state transitions.

    Args:
        request: BetCreate with prediction_id and stake
        user_id: Authenticated user id (from bearer token)
        db: Database session

    Returns:
        BetResponse with created bet
    """
    # Get prediction
    prediction = db.query(Prediction).filter(
        Prediction.id == request.prediction_id,
        Prediction.user_id == user_id,
    ).first()

    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found",
        )

    # Check risk limits
    is_valid, errors = RiskManager.check_all_limits(user_id, request.stake, db)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Risk limits exceeded",
            headers={"X-Risk-Errors": ", ".join(errors)},
        )

    # Calculate Kelly stake
    kelly_result = KellyCalculator.calculate_kelly_fraction(
        win_probability=prediction.predicted_probability,
        loss_probability=1.0 - prediction.predicted_probability,
        decimal_odds=prediction.market_odds,
    )

    # Create bet in PENDING state
    bet = Bet(
        user_id=user_id,
        prediction_id=request.prediction_id,
        status="PENDING",
        stake=request.stake,
        odds=prediction.market_odds,
        potential_return=request.stake * prediction.market_odds,
        kelly_fraction_used=request.kelly_fraction,
        kelly_stake=KellyCalculator.calculate_stake(
            bankroll=request.stake,
            kelly_fraction=kelly_result["kelly_fraction"],
            kelly_multiplier=request.kelly_fraction,
        ),
    )
    db.add(bet)
    db.commit()
    db.refresh(bet)

    # Audit log
    audit = AuditLog(
        user_id=user_id,
        action="PLACE_BET",
        entity_type="bet",
        entity_id=bet.id,
        status="SUCCESS",
        details=json.dumps({
            "prediction_id": request.prediction_id,
            "stake": request.stake,
            "potential_return": request.stake * prediction.market_odds,
        }),
    )
    db.add(audit)
    db.commit()

    return bet


@router.post("/{bet_id}/transition", response_model=BetResponse)
def transition_bet_status(
    bet_id: int,
    request: BetStatusUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Transition bet to new status.

    Enforces state machine transitions (PENDING -> SUBMITTED -> CONFIRMED -> LIVE -> SETTLED).

    Args:
        bet_id: Bet ID
        request: BetStatusUpdate with new status
        db: Database session

    Returns:
        BetResponse with updated bet
    """
    # Get bet
    bet = db.query(Bet).filter(
        Bet.id == bet_id,
        Bet.user_id == user_id,
    ).first()

    if not bet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bet not found",
        )

    # Validate transition
    is_valid, msg, updates = BetStateMachine.transition_with_timestamp(
        current_status=bet.status,
        new_status=request.status,
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg,
        )

    # Update bet
    for key, value in updates.items():
        setattr(bet, key, value)

    db.commit()
    db.refresh(bet)

    # Audit log
    audit = AuditLog(
        user_id=user_id,
        action="UPDATE_BET_STATUS",
        entity_type="bet",
        entity_id=bet.id,
        status="SUCCESS",
        details=json.dumps({
            "old_status": bet.status,
            "new_status": request.status,
            "notes": request.notes,
        }),
    )
    db.add(audit)
    db.commit()

    return bet


@router.get("/{bet_id}", response_model=BetResponse)
def get_bet(
    bet_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Get a specific bet.

    Args:
        bet_id: Bet ID
        user_id: Authenticated user id (from bearer token)
        db: Database session

    Returns:
        BetResponse
    """
    bet = db.query(Bet).filter(
        Bet.id == bet_id,
        Bet.user_id == user_id,
    ).first()

    if not bet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bet not found",
        )

    return bet
