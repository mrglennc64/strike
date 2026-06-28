from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from database import Base


class BetStatus(str, Enum):
    """CLV Bet status."""
    PENDING = "PENDING"
    RECORDED = "RECORDED"
    CLOSED = "CLOSED"
    ANALYZED = "ANALYZED"


class CLVBet(Base):
    """CLV Bet model for tracking closing line value."""

    __tablename__ = "clv_bets"
    __table_args__ = (
        UniqueConstraint('date', 'player', 'your_side', name='uq_clv_bet_identity'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Bet details
    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    player = Column(String(255), nullable=False, index=True)
    your_side = Column(String(10), nullable=False)  # 'over' or 'under'

    # Odds
    your_american = Column(Float, nullable=False)  # Your odds (American format)
    your_decimal = Column(Float)  # Your odds (Decimal format)
    close_over_american = Column(Float)  # Close Over odds
    close_under_american = Column(Float)  # Close Under odds

    # CLV calculation
    close_fair_prob = Column(Float)  # De-vigged fair prob at close
    your_break_even = Column(Float)  # Break-even prob from your odds
    clv_value = Column(Float)  # Closing Line Value (fair_prob - break_even)

    # Metadata
    status = Column(SQLEnum(BetStatus), default=BetStatus.PENDING, index=True)
    sport = Column(String(50), default="baseball_mlb")
    market = Column(String(100), default="pitcher_strikeouts")
    bookmaker = Column(String(100))

    # Notes
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    recorded_at = Column(DateTime)
    closed_at = Column(DateTime)
    analyzed_at = Column(DateTime)

    def __repr__(self):
        return f"<CLVBet(player={self.player}, side={self.your_side}, clv={self.clv_value}, status={self.status})>"


class LineCapture(Base):
    """Historical line captures for movement analysis."""

    __tablename__ = "line_captures"

    id = Column(Integer, primary_key=True, index=True)

    # Capture info
    date = Column(String(10), nullable=False, index=True)
    captured_at = Column(DateTime, default=datetime.utcnow, index=True)
    tag = Column(String(20), nullable=False)  # 'open' or 'close'

    # Event details
    event = Column(String(255))  # Away @ Home
    player = Column(String(255), nullable=False, index=True)

    # Odds
    line = Column(Float, nullable=False)
    over_odds = Column(Float, nullable=False)
    under_odds = Column(Float, nullable=False)
    bookmaker = Column(String(100), nullable=False)

    # Metadata
    sport = Column(String(50), default="baseball_mlb")
    market = Column(String(100), default="pitcher_strikeouts")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<LineCapture(player={self.player}, tag={self.tag}, line={self.line})>"
