"""
Database models for Fed/Economics predictions.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from database import Base


class EconomicsPrediction(Base):
    """Store predictions from the Fed/Economics model."""

    __tablename__ = "economics_predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), index=True)

    # Prediction details
    metric = Column(String(50), index=True)  # e.g., "CPI", "Rate Cut", "Unemployment"
    threshold = Column(Float, nullable=True)  # e.g., 3.5 for CPI > 3.5%
    prediction_type = Column(String(50))  # e.g., "binary", "continuous"

    # Model prediction
    predicted_probability = Column(Float)  # 0.0 - 1.0
    confidence = Column(Float, nullable=True)

    # Market data
    market_probability = Column(Float, nullable=True)
    market_source = Column(String(50), nullable=True)  # "polymarket", "kalshi"

    # Latest actual value
    latest_value = Column(Float, nullable=True)
    actual_outcome = Column(Boolean, nullable=True)  # Did it happen?

    # Edge & Kelly
    edge = Column(Float)  # predicted - market
    edge_percentage = Column(Float)
    kelly_fraction = Column(Float)
    expected_value = Column(Float)

    # Metadata
    fomc_meeting_date = Column(DateTime, nullable=True)
    next_release_date = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # JSON store for additional data
    metadata = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<EconomicsPrediction {self.metric} {self.threshold}>"


class EconomicsModelMetrics(Base):
    """Track model performance metrics over time."""

    __tablename__ = "economics_model_metrics"

    id = Column(Integer, primary_key=True, index=True)

    model_name = Column(String(100), index=True)  # "cpi_predictor", "rate_cut_predictor"
    metric_type = Column(String(50))  # "auc", "brier_score", "accuracy"

    # Metrics
    auc_score = Column(Float, nullable=True)
    brier_score = Column(Float, nullable=True)
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)

    train_size = Column(Integer)
    test_size = Column(Integer)
    threshold = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    training_duration_seconds = Column(Float, nullable=True)

    def __repr__(self):
        return f"<EconomicsModelMetrics {self.model_name}>"


class FedMeetingSchedule(Base):
    """Cache FOMC meeting schedule."""

    __tablename__ = "fed_meeting_schedule"

    id = Column(Integer, primary_key=True, index=True)

    meeting_date = Column(DateTime, unique=True, index=True)
    decision_date = Column(DateTime, nullable=True)
    description = Column(String(255))

    expected_rate_cut = Column(Boolean, nullable=True)
    actual_rate_cut = Column(Boolean, nullable=True)
    rate_change_bps = Column(Integer, nullable=True)  # basis points

    notes = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<FedMeetingSchedule {self.meeting_date.date()}>"


class EconomicRelease(Base):
    """Track economic data releases (CPI, jobs, GDP, etc.)."""

    __tablename__ = "economic_releases"

    id = Column(Integer, primary_key=True, index=True)

    release_name = Column(String(100), index=True)  # "CPI", "Non-Farm Payrolls", etc.
    series_id = Column(String(50), unique=True)  # FRED series ID
    release_schedule = Column(String(50))  # "monthly", "weekly", "quarterly"

    # Most recent release
    last_release_date = Column(DateTime, nullable=True)
    last_value = Column(Float, nullable=True)
    last_forecast = Column(Float, nullable=True)
    last_prior = Column(Float, nullable=True)

    # Next release
    next_release_date = Column(DateTime, nullable=True)
    next_forecast = Column(Float, nullable=True)

    # Historical stats
    mean_value = Column(Float, nullable=True)
    std_dev = Column(Float, nullable=True)
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<EconomicRelease {self.release_name}>"


class EconomicsEdgeOpportunity(Base):
    """Track identified edge opportunities."""

    __tablename__ = "economics_edge_opportunities"

    id = Column(Integer, primary_key=True, index=True)

    metric = Column(String(100), index=True)
    direction = Column(String(10))  # "YES", "NO"
    edge_percentage = Column(Float)
    kelly_fraction = Column(Float)
    kelly_adjusted_fraction = Column(Float, default=0.25)  # Max 25% Kelly

    market_source = Column(String(50))  # "polymarket", "kalshi"
    market_price = Column(Float)
    market_liquidity = Column(Float, nullable=True)

    model_prediction = Column(Float)
    confidence_level = Column(String(20))  # "high", "medium", "low"

    # Action tracking
    bet_placed = Column(Boolean, default=False)
    bet_id = Column(Integer, ForeignKey("bet.id"), nullable=True)
    position_size = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime)  # Edge expiry
    resolved_at = Column(DateTime, nullable=True)

    outcome = Column(Boolean, nullable=True)  # Did the prediction hit?
    realized_edge = Column(Float, nullable=True)

    notes = Column(String(500), nullable=True)

    def __repr__(self):
        return f"<EconomicsEdgeOpportunity {self.metric} {self.direction}>"
