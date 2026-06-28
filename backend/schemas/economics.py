"""
Pydantic schemas for economics endpoints.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class EdgeData(BaseModel):
    """Edge calculation results."""
    edge: float = Field(description="Edge: predicted - market")
    edge_pct: float = Field(description="Edge as percentage")
    ev_yes: float = Field(description="Expected value if betting YES")
    ev_no: float = Field(description="Expected value if betting NO")
    best_side: str = Field(description="YES or NO")
    kelly_fraction: float = Field(description="Kelly criterion fraction")


class CPIPredictionResponse(BaseModel):
    """CPI prediction response."""
    metric: str
    threshold: float
    predicted_probability: float
    market_probability: float
    latest_value: float
    edge: EdgeData
    timestamp: str


class RateCutPredictionResponse(BaseModel):
    """Rate cut prediction response."""
    metric: str
    predicted_probability: float
    market_probability: float
    next_meeting: Optional[Dict[str, Any]]
    current_rate: Optional[float]
    edge: EdgeData
    timestamp: str


class EconomicEvent(BaseModel):
    """Economic event (CPI, jobs, etc.)."""
    series_id: str
    release_schedule: str
    release_day: Optional[int]
    description: str


class EconomicsCalendarResponse(BaseModel):
    """Economic calendar response."""
    CPI: EconomicEvent
    PCE: EconomicEvent
    UNEMPLOYMENT: EconomicEvent
    NON_FARM_PAYROLLS: EconomicEvent
    RETAIL_SALES: EconomicEvent
    INITIAL_JOBLESS: EconomicEvent
    GDP: EconomicEvent
    FED_FUNDS_RATE: EconomicEvent


class FOCMMeeting(BaseModel):
    """FOMC meeting."""
    description: str
    date: str
    decision_date: str


class FOCMScheduleResponse(BaseModel):
    """FOMC schedule response."""
    meetings: List[FOCMMeeting]


class EdgeOpportunity(BaseModel):
    """Edge opportunity."""
    metric: str
    direction: str  # YES or NO
    edge_percentage: float
    model_prediction: float
    market_price: float
    kelly_fraction: float
    confidence: str  # high, medium, low


class EdgeOpportunitiesResponse(BaseModel):
    """Edge opportunities response."""
    count: int
    opportunities: List[EdgeOpportunity]


class PredictionSaveRequest(BaseModel):
    """Request to save a prediction."""
    user_id: int
    metric: str = Field(description="e.g., 'CPI', 'Rate Cut'")
    threshold: Optional[float] = Field(description="Threshold for binary classification")
    prediction_type: str = Field(default="binary", description="binary or continuous")
    predicted_probability: float = Field(description="Model prediction (0-1)")
    market_probability: Optional[float] = Field(description="Market price (0-1)")
    kelly_fraction: Optional[float] = Field(description="Kelly criterion fraction")
    expected_value: Optional[float] = Field(description="Expected value")
    metadata: Optional[Dict[str, Any]] = Field(default=None)


class EconomicsPredictionDB(BaseModel):
    """Database economics prediction."""
    id: int
    user_id: int
    metric: str
    threshold: Optional[float]
    prediction_type: str
    predicted_probability: float
    confidence: Optional[float]
    market_probability: Optional[float]
    market_source: Optional[str]
    latest_value: Optional[float]
    actual_outcome: Optional[bool]
    edge: float
    edge_percentage: float
    kelly_fraction: float
    expected_value: float
    fomc_meeting_date: Optional[datetime]
    next_release_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class ModelMetric(BaseModel):
    """Model metrics."""
    id: int
    model_name: str
    metric_type: str
    auc_score: Optional[float]
    brier_score: Optional[float]
    accuracy: Optional[float]
    precision: Optional[float]
    recall: Optional[float]
    train_size: int
    test_size: int
    threshold: Optional[float]
    created_at: datetime
    training_duration_seconds: Optional[float]

    class Config:
        from_attributes = True


class FedMeeting(BaseModel):
    """Fed meeting."""
    id: int
    meeting_date: datetime
    decision_date: Optional[datetime]
    description: str
    expected_rate_cut: Optional[bool]
    actual_rate_cut: Optional[bool]
    rate_change_bps: Optional[int]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EconomicRelease(BaseModel):
    """Economic release."""
    id: int
    release_name: str
    series_id: str
    release_schedule: str
    last_release_date: Optional[datetime]
    last_value: Optional[float]
    last_forecast: Optional[float]
    last_prior: Optional[float]
    next_release_date: Optional[datetime]
    next_forecast: Optional[float]
    mean_value: Optional[float]
    std_dev: Optional[float]
    min_value: Optional[float]
    max_value: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EdgeOpportunityDB(BaseModel):
    """Edge opportunity in database."""
    id: int
    metric: str
    direction: str
    edge_percentage: float
    kelly_fraction: float
    kelly_adjusted_fraction: float
    market_source: str
    market_price: float
    market_liquidity: Optional[float]
    model_prediction: float
    confidence_level: str
    bet_placed: bool
    bet_id: Optional[int]
    position_size: Optional[float]
    created_at: datetime
    expires_at: datetime
    resolved_at: Optional[datetime]
    outcome: Optional[bool]
    realized_edge: Optional[float]
    notes: Optional[str]

    class Config:
        from_attributes = True


class TrainModelsResponse(BaseModel):
    """Response from training models."""
    status: str
    message: str
    metrics: Dict[str, Dict[str, float]]
