from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import Bet
from schemas import BetResponse
from typing import List
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/positions", tags=["positions"])


@router.get("/active", response_model=List[BetResponse])
def get_active_positions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Get all active (LIVE) bets for current user.

    Args:
        skip: Number of records to skip
        limit: Number of records to return
        db: Database session

    Returns:
        List of BetResponse for active bets
    """
    # In real app, would get user_id from JWT token
    user_id = 1  # TODO: Get from auth context

    bets = db.query(Bet).filter(
        Bet.user_id == user_id,
        Bet.status == "LIVE",
    ).offset(skip).limit(limit).all()

    return bets


@router.get("/all", response_model=List[BetResponse])
def get_all_bets(
    skip: int = 0,
    limit: int = 100,
    status_filter: str = None,
    db: Session = Depends(get_db),
):
    """
    Get all bets for current user with optional status filter.

    Args:
        skip: Number of records to skip
        limit: Number of records to return
        status_filter: Filter by status (PENDING, SUBMITTED, CONFIRMED, LIVE, SETTLED, etc.)
        db: Database session

    Returns:
        List of BetResponse
    """
    # In real app, would get user_id from JWT token
    user_id = 1  # TODO: Get from auth context

    query = db.query(Bet).filter(Bet.user_id == user_id)

    if status_filter:
        query = query.filter(Bet.status == status_filter)

    bets = query.offset(skip).limit(limit).all()

    return bets


@router.get("/summary")
def get_positions_summary(db: Session = Depends(get_db)):
    """
    Get summary of positions and P&L.

    Args:
        db: Database session

    Returns:
        dict with summary metrics
    """
    # In real app, would get user_id from JWT token
    user_id = 1  # TODO: Get from auth context

    # Get active bets
    active_bets = db.query(Bet).filter(
        Bet.user_id == user_id,
        Bet.status == "LIVE",
    ).all()

    # Get settled bets today
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())

    today_settled = db.query(Bet).filter(
        Bet.user_id == user_id,
        Bet.is_settled == True,
        Bet.settled_at >= today_start,
    ).all()

    # Calculate metrics
    active_exposure = sum(b.stake or 0 for b in active_bets)
    active_potential = sum(b.potential_return or 0 for b in active_bets)

    today_wins = sum(1 for b in today_settled if b.is_winner)
    today_losses = sum(1 for b in today_settled if not b.is_winner)
    today_pnl = sum(b.pnl or 0 for b in today_settled)
    today_win_rate = (today_wins / (today_wins + today_losses) * 100) if (today_wins + today_losses) > 0 else 0

    # Get all-time metrics
    all_settled = db.query(Bet).filter(
        Bet.user_id == user_id,
        Bet.is_settled == True,
    ).all()

    total_wins = sum(1 for b in all_settled if b.is_winner)
    total_losses = sum(1 for b in all_settled if not b.is_winner)
    total_pnl = sum(b.pnl or 0 for b in all_settled)
    total_win_rate = (total_wins / (total_wins + total_losses) * 100) if (total_wins + total_losses) > 0 else 0

    return {
        "active_bets": len(active_bets),
        "active_exposure": active_exposure,
        "active_potential_return": active_potential,
        "today": {
            "settled_bets": len(today_settled),
            "wins": today_wins,
            "losses": today_losses,
            "win_rate": round(today_win_rate, 2),
            "pnl": round(today_pnl, 2),
        },
        "all_time": {
            "settled_bets": len(all_settled),
            "wins": total_wins,
            "losses": total_losses,
            "win_rate": round(total_win_rate, 2),
            "pnl": round(total_pnl, 2),
        },
    }
