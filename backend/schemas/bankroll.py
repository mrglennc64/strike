from pydantic import BaseModel, Field
from datetime import datetime


class BankrollCreate(BaseModel):
    """Request schema for creating/initializing bankroll."""
    initial_amount: float = Field(..., gt=0, description="Initial bankroll amount")


class BankrollUpdate(BaseModel):
    """Request schema for updating bankroll (admin only)."""
    current_balance: float = Field(..., ge=0, description="Updated balance")


class BankrollResponse(BaseModel):
    """Response schema for bankroll."""
    id: int
    user_id: int
    initial_amount: float
    current_balance: float
    total_wagered: float
    total_returns: float
    profit_loss: float
    roi_percentage: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
