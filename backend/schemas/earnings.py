"""
Pydantic schemas for earnings predictor API.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class AnalystEstimatesSchema(BaseModel):
    """Analyst estimates data."""

    symbol: str
    company_name: str
    earnings_date: datetime

    current_eps_estimate: float
    num_analysts: int
    eps_estimate_variance: float
    revenue_estimate: float
    revenue_variance: float

    last_quarter_surprise: float
    avg_surprise_pct: float
    beats_last_4_quarters: int
    guidance_revision_trend: float
    estimate_revisions_up: int
    estimate_revisions_down: int


class OptionsDataSchema(BaseModel):
    """Options market data."""

    symbol: str
    data_date: datetime

    put_call_iv_ratio: float
    at_money_iv: float
    iv_rank: float
    iv_percentile: float

    vol_skew: float
    put_spread: float

    implied_move_pct: float
    implied_move_std: float

    call_volume: int
    put_volume: int
    call_oi: int
    put_oi: int
    smart_money_flow: str

    market_implied_prob_up: float
    market_implied_prob_down: float


class EarningsCalendarDataSchema(BaseModel):
    """Earnings calendar event data."""

    symbol: str
    company_name: str
    earnings_date: datetime
    fiscal_period: str

    eps_estimate: float
    revenue_estimate: float
    eps_actual: Optional[float] = None
    revenue_actual: Optional[float] = None

    track_record_beats: int = 0
    track_record_misses: int = 0
    average_surprise_pct: float = 0.0

    is_peak_earnings_season: bool = False
    sector_avg_surprise: float = 0.0


class EarningsPredictionResponse(BaseModel):
    """Earnings beat/miss prediction response."""

    symbol: str
    company_name: str
    prediction_date: datetime
    earnings_date: datetime

    # Predictions
    predicted_probability_beat: float = Field(
        ..., description="P(Beat) from XGBoost model (0-1)"
    )
    predicted_probability_miss: float = Field(
        ..., description="P(Miss) from XGBoost model (0-1)"
    )
    predicted_probability_in_line: float = Field(
        default=0.0, description="P(In-line) (0-1)"
    )

    # Market implied
    market_implied_prob_beat: float = Field(
        ..., description="Market-implied P(Beat) from options pricing"
    )

    # Edge
    edge_probability: float = Field(
        ..., description="predicted_prob_beat - market_implied_prob_beat"
    )
    edge_pct: float = Field(..., description="edge / market_implied_prob * 100")
    expected_move_pct: float = Field(
        ..., description="Market's expected post-earnings move (%)"
    )

    # Recommendation and confidence
    recommendation: str = Field(
        ...,
        description="Trading recommendation (BUY_CALL, BUY_PUT, STRADDLE, NEUTRAL, etc)"
    )
    confidence: float = Field(..., description="Confidence score (0-100)")

    # Source data
    analyst_estimates: Optional[AnalystEstimatesSchema] = None
    options_data: Optional[OptionsDataSchema] = None
    calendar_data: Optional[EarningsCalendarDataSchema] = None

    class Config:
        from_attributes = True


class EarningsPredictionCreate(BaseModel):
    """Request to create an earnings prediction."""

    symbol: str = Field(..., description="Stock ticker (e.g., TSLA)")
    company_name: Optional[str] = None


class EarningsPredictionHistoryResponse(BaseModel):
    """Historical earnings data for backtesting."""

    symbol: str
    company_name: str
    earnings_date: datetime
    fiscal_period: str

    eps_estimate: float
    revenue_estimate: float
    eps_actual: float
    revenue_actual: float

    eps_surprise_pct: float = Field(
        ..., description="(actual - estimate) / estimate * 100"
    )
    revenue_surprise_pct: float
    beat_miss: str = Field(..., description="'beat', 'miss', or 'in_line'")

    stock_price_pre_earnings: float
    stock_price_post_earnings: float
    post_earnings_move_pct: float

    iv_rank: float
    implied_move_pct: float
    put_call_ratio: float
    num_analysts: int
    guidance_revision_trend: float

    sector: str
    sector_avg_surprise: float


class EarningsPredictionRecordResponse(BaseModel):
    """Complete prediction record from database."""

    id: int
    symbol: str
    company_name: str

    prediction_date: datetime
    earnings_date: datetime

    predicted_prob_beat: float
    predicted_prob_miss: float
    predicted_prob_in_line: float

    market_implied_prob_beat: float

    edge_probability: float
    edge_pct: float
    expected_move_pct: float

    recommendation: str
    confidence: float

    # Pre-earnings feature data
    analyst_consensus_strength: Optional[float] = None
    num_analysts: Optional[int] = None
    guidance_revision_trend: Optional[float] = None
    iv_rank: Optional[float] = None
    vol_skew: Optional[float] = None
    implied_move_pct: Optional[float] = None
    smart_money_flow: Optional[str] = None

    # Post-earnings outcome
    actual_outcome: Optional[str] = None
    actual_eps: Optional[float] = None
    actual_revenue: Optional[float] = None
    surprise_pct: Optional[float] = None
    outcome_date: Optional[datetime] = None

    notes: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EarningsPredictionListResponse(BaseModel):
    """List of earnings predictions."""

    total: int
    predictions: List[EarningsPredictionRecordResponse]


class EdgeScanRequest(BaseModel):
    """Request to scan multiple stocks for earnings edges."""

    symbols: List[str] = Field(..., description="List of stock tickers")
    min_edge_pct: float = Field(
        default=5.0, description="Minimum edge % to include in results"
    )
    only_with_edge: bool = Field(
        default=True, description="Only return predictions with edge"
    )


class EdgeScanResponse(BaseModel):
    """Scan results for earnings edges."""

    scan_date: datetime
    symbols_scanned: int
    symbols_with_edge: int

    predictions: List[EarningsPredictionResponse] = Field(
        description="Sorted by edge_pct descending"
    )

    top_edge: Optional[EarningsPredictionResponse] = Field(
        None, description="Prediction with highest edge"
    )
    avg_edge: float = Field(description="Average edge across all predictions")


class BacktestMetricsResponse(BaseModel):
    """Model backtesting performance metrics."""

    period: str = Field(description="e.g., 'last_90_days'")
    total_predictions: int
    predictions_with_edge: int
    hit_rate: float = Field(description="% of predictions that were correct")
    edge_hit_rate: float = Field(
        description="Hit rate for predictions with positive edge"
    )

    total_edge_pct: float
    avg_edge_per_prediction: float
    profit_factor: float = Field(
        description="(sum of winning edges) / (sum of losing edges)"
    )

    accuracy_by_confidence_bucket: dict = Field(
        description="Performance stratified by confidence level"
    )

    largest_win: float
    largest_loss: float
    kelly_fraction: float = Field(
        description="Recommended Kelly fraction based on performance"
    )


class ModelStatsResponse(BaseModel):
    """Model statistics and training info."""

    version: str
    model_type: str = "XGBoost"
    training_date: Optional[datetime]
    training_samples: int
    feature_count: int
    feature_names: List[str]

    auc_score: Optional[float]
    precision: Optional[float]
    recall: Optional[float]
    f1_score: Optional[float]

    last_retrain_date: Optional[datetime]
    is_live: bool
