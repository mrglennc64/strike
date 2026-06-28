from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class BetCreate(BaseModel):
    """Request schema for creating a bet."""
    prediction_id: int = Field(..., description="Associated prediction ID")
    stake: float = Field(..., gt=0, description="Amount to wager")
    kelly_fraction: float = Field(
        default=0.25,
        ge=0.01,
        le=1.0,
        description="Kelly fraction to use (default 25%)"
    )


class BetStatusUpdate(BaseModel):
    """Request schema for updating bet status."""
    status: str = Field(
        ...,
        description="New bet status (SUBMITTED, CONFIRMED, LIVE, SETTLED, CANCELLED, VOID)"
    )
    notes: Optional[str] = Field(None, description="Optional notes")


class BetSettlement(BaseModel):
    """Request schema for settling a bet."""
    actual_outcome: str = Field(..., description="Actual outcome")
    is_winner: bool = Field(..., description="Whether bet won")
    actual_return: float = Field(..., ge=0, description="Actual return amount")


class BetResponse(BaseModel):
    """Response schema for bet."""
    id: int
    user_id: int
    prediction_id: int
    status: str
    stake: float
    odds: float
    potential_return: float
    kelly_fraction_used: Optional[float]
    kelly_stake: Optional[float]
    is_settled: bool
    actual_outcome: Optional[str]
    is_winner: Optional[bool]
    actual_return: Optional[float]
    pnl: Optional[float]
    created_at: datetime
    submitted_at: Optional[datetime]
    confirmed_at: Optional[datetime]
    live_at: Optional[datetime]
    settled_at: Optional[datetime]
    notes: Optional[str]

    class Config:
        from_attributes = True
