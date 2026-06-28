from pydantic import BaseModel, Field
from datetime import datetime


class PredictionCreate(BaseModel):
    """Request schema for submitting a prediction."""
    event_id: str = Field(..., description="External event identifier")
    event_description: str = Field(..., description="Human-readable event description")
    outcome: str = Field(..., description="Predicted outcome")
    predicted_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Our predicted probability (0-1)"
    )
    market_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Implied market probability (0-1)"
    )
    market_odds: float = Field(..., gt=1.0, description="Decimal market odds")
    notes: str = Field(None, description="Optional notes or reasoning")


class PredictionResponse(BaseModel):
    """Response schema for prediction."""
    id: int
    user_id: int
    event_id: str
    event_description: str
    outcome: str
    predicted_probability: float
    market_probability: float
    market_odds: float
    edge_percentage: float
    has_positive_edge: bool
    notes: str
    created_at: datetime

    class Config:
        from_attributes = True
