from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from models import Bet, Bankroll, AuditLog
from schemas import BetResponse, BetSettlement
from services import BetStateMachine
import json

router = APIRouter(prefix="/api/settle", tags=["settlement"])


@router.post("/{bet_id}", response_model=BetResponse)
def settle_bet(
    bet_id: int,
    request: BetSettlement,
    db: Session = Depends(get_db),
):
    """
    Settle a bet with actual outcome and result.

    Only LIVE bets can be settled. Updates P&L and bankroll accordingly.

    Args:
        bet_id: Bet ID
        request: BetSettlement with outcome and result
        db: Database session

    Returns:
        BetResponse with settled bet
    """
    # In real app, would get user_id from JWT token
    user_id = 1  # TODO: Get from auth context

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

    # Check if bet can be settled
    if not BetStateMachine.can_be_settled(bet.status):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bet in {bet.status} state cannot be settled. Must be LIVE.",
        )

    # Calculate P&L
    pnl = 0.0
    if request.is_winner:
        pnl = request.actual_return - bet.stake
    else:
        pnl = -bet.stake

    # Update bet
    bet.actual_outcome = request.actual_outcome
    bet.is_winner = request.is_winner
    bet.actual_return = request.actual_return
    bet.pnl = pnl
    bet.is_settled = True
    bet.status = "SETTLED"
    bet.settled_at = datetime.utcnow()

    db.commit()

    # Update bankroll
    bankroll = db.query(Bankroll).filter(Bankroll.user_id == user_id).first()

    if bankroll:
        bankroll.current_balance += pnl
        bankroll.total_returns += request.actual_return
        bankroll.profit_loss = bankroll.current_balance - bankroll.initial_amount

        if request.is_winner:
            bankroll.total_wagered += bet.stake
        else:
            bankroll.total_wagered += bet.stake

        db.commit()

    db.refresh(bet)

    # Audit log
    audit = AuditLog(
        user_id=user_id,
        action="SETTLE_BET",
        entity_type="bet",
        entity_id=bet.id,
        status="SUCCESS",
        details=json.dumps({
            "outcome": request.actual_outcome,
            "is_winner": request.is_winner,
            "pnl": pnl,
        }),
    )
    db.add(audit)
    db.commit()

    return bet


@router.post("/{bet_id}/void", response_model=BetResponse)
def void_bet(
    bet_id: int,
    reason: str = "No reason provided",
    db: Session = Depends(get_db),
):
    """
    Void a bet (mark as VOID, return stake to bankroll).

    Only LIVE bets can be voided.

    Args:
        bet_id: Bet ID
        reason: Reason for voiding
        db: Database session

    Returns:
        BetResponse with voided bet
    """
    # In real app, would get user_id from JWT token
    user_id = 1  # TODO: Get from auth context

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

    # Check if bet can be voided
    if not BetStateMachine.can_be_settled(bet.status):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bet in {bet.status} state cannot be voided. Must be LIVE.",
        )

    # Update bet
    bet.status = "VOID"
    bet.is_settled = True
    bet.settled_at = datetime.utcnow()
    bet.pnl = 0.0  # No loss, stake returned
    db.commit()

    # Update bankroll (return stake)
    bankroll = db.query(Bankroll).filter(Bankroll.user_id == user_id).first()

    if bankroll:
        bankroll.current_balance += bet.stake
        db.commit()

    db.refresh(bet)

    # Audit log
    audit = AuditLog(
        user_id=user_id,
        action="VOID_BET",
        entity_type="bet",
        entity_id=bet.id,
        status="SUCCESS",
        details=json.dumps({
            "reason": reason,
            "stake_returned": bet.stake,
        }),
    )
    db.add(audit)
    db.commit()

    return bet
