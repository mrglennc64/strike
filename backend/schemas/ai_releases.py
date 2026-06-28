"""Schemas for AI Releases Predictor API."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Optional, List


class ReleaseFeatureSchema(BaseModel):
    """Release prediction features."""

    commits_last_7d: float = Field(..., description="Commits in last 7 days")
    commits_last_30d: float = Field(..., description="Commits in last 30 days")
    releases_last_90d: float = Field(..., description="Releases in last 90 days")
    days_since_last_release: float = Field(
        ..., description="Days since last release"
    )
    repository_stars: float = Field(..., description="GitHub repository stars")
    contributor_count: float = Field(..., description="Active contributors")
    issue_velocity: float = Field(..., description="Issues resolved per day")
    hf_models_last_30d: float = Field(
        ..., description="HuggingFace models uploaded in last 30 days"
    )
    hf_model_downloads: float = Field(
        ..., description="Total HuggingFace model downloads"
    )
    polymarket_price: float = Field(
        ..., ge=0, le=1, description="Current Polymarket YES price"
    )
    days_until_target: float = Field(..., description="Days until target date")
    quarter_progress: float = Field(
        ..., ge=0, le=1, description="Progress through current quarter"
    )
    is_major_event: bool = Field(
        ..., description="Whether target date is near major tech event"
    )
    avg_release_gap_days: float = Field(
        ..., description="Average days between releases (historical)"
    )
    last_release_recency_percentile: float = Field(
        ..., ge=0, le=1, description="Last release recency percentile"
    )


class ReleasePredictionRequest(BaseModel):
    """Request for release prediction."""

    provider: str = Field(
        ..., description="AI provider (anthropic|openai|xai)"
    )
    model_name: str = Field(..., description="Model name (e.g., Claude 4, GPT-5)")
    target_date: str = Field(
        ..., description="Target release date (ISO format)"
    )


class ReleasePredictionResponse(BaseModel):
    """Release prediction response."""

    provider: str = Field(..., description="AI provider")
    model_name: str = Field(..., description="Model name")
    prediction_date: datetime = Field(..., description="When prediction was made")
    target_date: datetime = Field(..., description="Target release date")
    predicted_probability: float = Field(
        ..., ge=0, le=1, description="P(Release by target_date)"
    )
    polymarket_price: float = Field(
        ..., ge=0, le=1, description="Current Polymarket price"
    )
    edge: float = Field(
        ..., description="Edge = predicted_prob - market_price"
    )
    edge_pct: float = Field(..., description="Edge as percentage")
    recommendation: str = Field(
        ..., description="Trading recommendation (STRONG_BUY|BUY|HOLD|SELL|STRONG_SELL)"
    )
    confidence: float = Field(
        ..., ge=0, le=1, description="Model confidence in prediction"
    )
    features: Dict = Field(..., description="Feature vector used for prediction")


class BatchPredictionRequest(BaseModel):
    """Request for batch predictions."""

    predictions: List[ReleasePredictionRequest] = Field(
        ..., description="List of prediction requests"
    )


class BatchPredictionResponse(BaseModel):
    """Batch prediction response."""

    predictions: List[ReleasePredictionResponse] = Field(
        ..., description="List of predictions"
    )
    generated_at: datetime = Field(..., description="When batch was generated")
    total_edge_usd: float = Field(
        ..., description="Total edge value (assuming $100 per prediction)"
    )


class MarketDataRequest(BaseModel):
    """Request for market data."""

    provider: str = Field(..., description="AI provider")
    model_name: str = Field(..., description="Model name")
    query: str = Field(..., description="Search query for markets")


class MarketDataResponse(BaseModel):
    """Market data response."""

    provider: str
    model_name: str
    markets: List[Dict] = Field(..., description="List of markets")
    top_market: Optional[Dict] = Field(None, description="Top market by volume")
    current_price: Optional[float] = Field(None, description="Current YES price")
