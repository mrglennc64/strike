from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Prediction(Base):
    """Prediction model for storing prediction data."""

    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    event_id = Column(String(255), nullable=False, index=True)  # External event identifier
    event_description = Column(String(500), nullable=False)  # Event description (e.g., "Team A vs Team B")
    outcome = Column(String(255), nullable=False)  # Predicted outcome (e.g., "Team A wins")
    predicted_probability = Column(Float, nullable=False)  # Our predicted probability (0-1)
    market_probability = Column(Float, nullable=False)  # Implied market probability (0-1)
    market_odds = Column(Float, nullable=False)  # Decimal odds from market
    edge_percentage = Column(Float)  # Calculated edge (predicted - market) * 100
    notes = Column(Text)  # Additional notes or reasoning
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="predictions")
    bets = relationship("Bet", back_populates="prediction")

    @property
    def has_positive_edge(self) -> bool:
        """Check if prediction has positive edge."""
        return self.predicted_probability > self.market_probability

    def __repr__(self):
        return f"<Prediction(id={self.id}, event={self.event_id}, edge={self.edge_percentage:.2f}%)>"
