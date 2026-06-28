from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from database import Base


class BetStatus(str, Enum):
    """State machine for bet status."""
    PENDING = "PENDING"  # Newly created, not yet submitted
    SUBMITTED = "SUBMITTED"  # Sent to validation
    CONFIRMED = "CONFIRMED"  # Ready to place
    LIVE = "LIVE"  # Placed and active
    SETTLED = "SETTLED"  # Bet resolved
    CANCELLED = "CANCELLED"  # Bet cancelled
    VOID = "VOID"  # Bet voided


class Bet(Base):
    """Bet model representing a placed bet with state machine."""

    __tablename__ = "bets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=False, index=True)
    status = Column(SQLEnum(BetStatus), default=BetStatus.PENDING, index=True)

    # Bet details
    stake = Column(Float, nullable=False)  # Amount wagered
    odds = Column(Float, nullable=False)  # Decimal odds at time of bet
    potential_return = Column(Float, nullable=False)  # stake * odds
    kelly_fraction_used = Column(Float)  # Kelly fraction applied
    kelly_stake = Column(Float)  # Calculated Kelly stake

    # Settlement
    is_settled = Column(Boolean, default=False, index=True)
    actual_outcome = Column(String(255))  # Actual outcome when settled
    is_winner = Column(Boolean)  # True if won, False if lost
    actual_return = Column(Float)  # Actual return amount
    pnl = Column(Float)  # Profit/Loss

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    submitted_at = Column(DateTime)
    confirmed_at = Column(DateTime)
    live_at = Column(DateTime)
    settled_at = Column(DateTime)

    # Audit
    notes = Column(Text)

    # Relationships
    user = relationship("User", back_populates="bets")
    prediction = relationship("Prediction", back_populates="bets")

    def __repr__(self):
        return f"<Bet(id={self.id}, status={self.status}, stake={self.stake}, pnl={self.pnl})>"
