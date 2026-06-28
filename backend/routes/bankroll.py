from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Bankroll, AuditLog
from schemas import BankrollCreate, BankrollResponse, BankrollUpdate
import json

router = APIRouter(prefix="/api/bankroll", tags=["bankroll"])


def get_current_user_id(request) -> int:
    """Extract user_id from request (would come from JWT in real implementation)."""
    return getattr(request.state, "user_id", 1)  # Default to 1 for demo


@router.post("/initialize", response_model=BankrollResponse)
def initialize_bankroll(
    request: BankrollCreate,
    db: Session = Depends(get_db),
):
    """
    Initialize or reset bankroll with initial amount.

    Args:
        request: BankrollCreate with initial_amount
        db: Database session

    Returns:
        BankrollResponse with bankroll details
    """
    # In real app, would get user_id from JWT token
    user_id = 1  # TODO: Get from auth context

    # Check if bankroll exists
    bankroll = db.query(Bankroll).filter(Bankroll.user_id == user_id).first()

    if bankroll:
        # Update existing bankroll
        bankroll.initial_amount = request.initial_amount
        bankroll.current_balance = request.initial_amount
        bankroll.profit_loss = 0.0
        bankroll.total_wagered = 0.0
        bankroll.total_returns = 0.0
    else:
        # Create new bankroll
        bankroll = Bankroll(
            user_id=user_id,
            initial_amount=request.initial_amount,
            current_balance=request.initial_amount,
        )
        db.add(bankroll)

    db.commit()
    db.refresh(bankroll)

    # Audit log
    audit = AuditLog(
        user_id=user_id,
        action="INITIALIZE_BANKROLL",
        entity_type="bankroll",
        entity_id=bankroll.id,
        status="SUCCESS",
        details=json.dumps({"initial_amount": request.initial_amount}),
    )
    db.add(audit)
    db.commit()

    return bankroll


@router.get("/current", response_model=BankrollResponse)
def get_bankroll(db: Session = Depends(get_db)):
    """
    Get current bankroll status.

    Args:
        db: Database session

    Returns:
        BankrollResponse with current bankroll
    """
    # In real app, would get user_id from JWT token
    user_id = 1  # TODO: Get from auth context

    bankroll = db.query(Bankroll).filter(Bankroll.user_id == user_id).first()

    if not bankroll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bankroll not found. Initialize with /bankroll/initialize",
        )

    return bankroll


@router.put("/update", response_model=BankrollResponse)
def update_bankroll(
    request: BankrollUpdate,
    db: Session = Depends(get_db),
):
    """
    Update bankroll balance (admin only - used for settlement).

    Args:
        request: BankrollUpdate with new balance
        db: Database session

    Returns:
        BankrollResponse with updated bankroll
    """
    # In real app, would get user_id from JWT token
    user_id = 1  # TODO: Get from auth context

    bankroll = db.query(Bankroll).filter(Bankroll.user_id == user_id).first()

    if not bankroll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bankroll not found",
        )

    old_balance = bankroll.current_balance
    bankroll.current_balance = request.current_balance
    bankroll.profit_loss = bankroll.current_balance - bankroll.initial_amount

    db.commit()
    db.refresh(bankroll)

    # Audit log
    audit = AuditLog(
        user_id=user_id,
        action="UPDATE_BANKROLL",
        entity_type="bankroll",
        entity_id=bankroll.id,
        status="SUCCESS",
        details=json.dumps({
            "old_balance": old_balance,
            "new_balance": request.current_balance,
        }),
    )
    db.add(audit)
    db.commit()

    return bankroll
