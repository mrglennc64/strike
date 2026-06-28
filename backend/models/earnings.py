"""
Database models for earnings beat/miss predictions.
"""

from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class EarningsPredictionRecord(Base):
    """Database record for an earnings prediction."""

    __tablename__ = "earnings_predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)

    # Stock information
    symbol = Column(String(20), index=True)
    company_name = Column(String(255))

    # Dates
    prediction_date = Column(DateTime, default=datetime.utcnow, index=True)
    earnings_date = Column(DateTime, index=True)

    # Predictions
    predicted_prob_beat = Column(Float)  # 0-1
    predicted_prob_miss = Column(Float)  # 0-1
    predicted_prob_in_line = Column(Float)  # 0-1

    # Market implied
    market_implied_prob_beat = Column(Float)

    # Edge
    edge_probability = Column(Float)
    edge_pct = Column(Float)
    expected_move_pct = Column(Float)

    # Recommendation
    recommendation = Column(String(50))
    confidence = Column(Float)  # 0-100

    # Feature vector (for audit/debugging)
    features_json = Column(JSON)

    # Source data (for reference)
    analyst_consensus_strength = Column(Float)
    num_analysts = Column(Integer)
    guidance_revision_trend = Column(Float)
    iv_rank = Column(Float)
    vol_skew = Column(Float)
    implied_move_pct = Column(Float)
    smart_money_flow = Column(String(20))

    # Actual outcome (filled later when earnings announced)
    actual_outcome = Column(String(20))  # "beat", "miss", "in_line"
    actual_eps = Column(Float)
    actual_revenue = Column(Float)
    surprise_pct = Column(Float)

    # Outcome date (when we find out the result)
    outcome_date = Column(DateTime)

    # Notes
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<EarningsPrediction {self.symbol} {self.earnings_date} P(beat)={self.predicted_prob_beat:.2%}>"


class EarningsHistoryRecord(Base):
    """Historical earnings data for backtesting and calibration."""

    __tablename__ = "earnings_history"

    id = Column(Integer, primary_key=True, index=True)

    # Stock information
    symbol = Column(String(20), index=True)
    company_name = Column(String(255))

    # Earnings event
    earnings_date = Column(DateTime, index=True)
    fiscal_period = Column(String(20))

    # Estimates
    eps_estimate = Column(Float)
    revenue_estimate = Column(Float)
    guidance_eps_low = Column(Float)
    guidance_eps_high = Column(Float)

    # Actual results
    eps_actual = Column(Float)
    revenue_actual = Column(Float)

    # Calculated metrics
    eps_surprise_pct = Column(Float)
    revenue_surprise_pct = Column(Float)
    beat_miss = Column(String(20))  # "beat", "miss", "in_line"

    # Market reaction
    stock_price_pre_earnings = Column(Float)
    stock_price_post_earnings = Column(Float)
    post_earnings_move_pct = Column(Float)

    # Pre-earnings market data
    iv_rank = Column(Float)
    implied_move_pct = Column(Float)
    put_call_ratio = Column(Float)

    # Analyst data
    num_analysts = Column(Integer)
    guidance_revision_trend = Column(Float)

    # Sector info
    sector = Column(String(100))
    sector_avg_surprise = Column(Float)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<EarningsHistory {self.symbol} {self.earnings_date} surprise={self.eps_surprise_pct:.2f}%>"
