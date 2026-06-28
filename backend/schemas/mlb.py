"""Pydantic schemas for MLB Strikeout Predictor."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PredictionRequest(BaseModel):
    """Request for MLB strikeout prediction."""

    pitcher_id: Optional[int] = Field(None, description="MLB pitcher ID")
    pitcher_name: Optional[str] = Field(None, description="Pitcher name")
    opponent_team: Optional[str] = Field(None, description="Opponent team code")
    game_date: Optional[str] = Field(None, description="Game date (YYYY-MM-DD)")
    strikeout_line: float = Field(5.5, description="Strikeout line to predict against")
    edge_threshold: float = Field(8.0, description="Minimum edge% to return")


class PredictionResponse(BaseModel):
    """Single strikeout prediction."""

    pitcher_id: int
    pitcher_name: str
    opponent: str
    game_date: str
    strikeout_line: float
    model_prob: float = Field(description="Model probability (0-1)")
    model_prob_pct: float = Field(description="Model probability percentage")
    book_prob: float = Field(description="Book implied probability (0-1)")
    book_prob_pct: float = Field(description="Book implied probability percentage")
    edge_pct: float = Field(description="Edge percentage (Model - Book)")
    lambda: float = Field(description="Expected strikeouts (Poisson lambda)")
    batters_faced: int = Field(description="Expected batters faced")
    direction: str = Field(description="OVER or UNDER")
    confidence: float = Field(description="Confidence score (0-100)")


class BatchPredictionResponse(BaseModel):
    """Response with multiple predictions."""

    predictions: List[PredictionResponse]
    total_plays: int
    timestamp: datetime
    model_status: str = "ready"


class BacktestRequest(BaseModel):
    """Request for model backtest."""

    start_date: str = Field("2026-06-15", description="Start date (YYYY-MM-DD)")
    end_date: str = Field("2026-06-27", description="End date (YYYY-MM-DD)")
    strikeout_line: float = Field(5.5, description="Strikeout line")
    edge_threshold: float = Field(8.0, description="Minimum edge%")
    confidence_threshold: float = Field(70.0, description="Minimum confidence%")


class BacktestResult(BaseModel):
    """Backtest results."""

    num_plays: int
    wins: int
    losses: int
    win_rate: float
    roi: float
    total_profit: int
    avg_edge_pct: float
    timestamp: datetime


class ModelStatusResponse(BaseModel):
    """Model training status."""

    trained: bool
    last_trained: Optional[datetime] = None
    training_data_records: int = 0
    unique_pitchers: int = 0
    unique_games: int = 0
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None


class OddsComparisonResponse(BaseModel):
    """Comparison with bookmaker odds."""

    pitcher_name: str
    strikeout_line: float
    draftkings_prob: float
    draftkings_prob_pct: float
    fanduel_prob: Optional[float] = None
    fanduel_prob_pct: Optional[float] = None
    model_prob: float
    model_prob_pct: float
    best_edge_book: str = "DraftKings"
    edge_vs_best: float


class TrainRequest(BaseModel):
    """Request to train model."""

    start_date: str = Field("2026-06-01", description="Training start date")
    end_date: str = Field("2026-06-10", description="Training end date")
    force_retrain: bool = Field(False, description="Force retrain even if already trained")
