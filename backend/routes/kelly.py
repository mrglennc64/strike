from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Bankroll
from schemas import KellyRequest, KellyResponse
from services import KellyCalculator
from .auth import get_current_user_id

router = APIRouter(prefix="/api/kelly", tags=["kelly"])


@router.post("/calculate", response_model=KellyResponse)
def calculate_kelly(
    request: KellyRequest,
    db: Session = Depends(get_db),
):
    """
    Calculate Kelly criterion bet sizing.

    Args:
        request: KellyRequest with win probability, odds, bankroll
        db: Database session

    Returns:
        KellyResponse with kelly fraction and suggested stake
    """
    # Validate probabilities
    if request.win_probability <= 0 or request.win_probability >= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="win_probability must be between 0 and 1 (exclusive)",
        )

    if request.odds <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="odds must be greater than 1",
        )

    if request.bankroll <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="bankroll must be positive",
        )

    # Calculate loss probability if not provided
    loss_probability = request.loss_prob

    # Calculate Kelly fraction
    try:
        kelly_result = KellyCalculator.calculate_kelly_fraction(
            win_probability=request.win_probability,
            loss_probability=loss_probability,
            decimal_odds=request.odds,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Calculate suggested stake (using 25% of Kelly by default)
    suggested_stake = KellyCalculator.calculate_stake(
        bankroll=request.bankroll,
        kelly_fraction=kelly_result["kelly_fraction"],
        kelly_multiplier=0.25,
    )

    return KellyResponse(
        kelly_fraction=kelly_result["kelly_fraction"],
        suggested_stake=suggested_stake,
        win_probability=request.win_probability,
        odds=request.odds,
        edge=kelly_result["edge"],
        has_positive_edge=kelly_result["has_positive_edge"],
    )


@router.post("/suggest-stake")
def suggest_stake(
    win_probability: float,
    odds: float,
    kelly_multiplier: float = 0.25,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Suggest bet stake based on user's bankroll.

    Args:
        win_probability: Win probability (0-1)
        odds: Decimal odds
        kelly_multiplier: Fraction of Kelly to use (default 0.25)
        db: Database session

    Returns:
        dict with suggested stake and details
    """
    # Get user's bankroll
    bankroll = db.query(Bankroll).filter(Bankroll.user_id == user_id).first()

    if not bankroll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bankroll not found",
        )

    loss_probability = 1.0 - win_probability

    try:
        kelly_result = KellyCalculator.calculate_kelly_fraction(
            win_probability=win_probability,
            loss_probability=loss_probability,
            decimal_odds=odds,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    suggested_stake = KellyCalculator.calculate_stake(
        bankroll=bankroll.current_balance,
        kelly_fraction=kelly_result["kelly_fraction"],
        kelly_multiplier=kelly_multiplier,
    )

    return {
        "bankroll": bankroll.current_balance,
        "kelly_fraction": kelly_result["kelly_fraction"],
        "kelly_multiplier": kelly_multiplier,
        "suggested_stake": suggested_stake,
        "potential_return": suggested_stake * odds,
        "edge": kelly_result["edge"],
        "has_positive_edge": kelly_result["has_positive_edge"],
    }
