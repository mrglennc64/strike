from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Bankroll(Base):
    """Bankroll model for tracking betting capital and balance."""

    __tablename__ = "bankrolls"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    initial_amount = Column(Float, nullable=False)  # Starting capital
    current_balance = Column(Float, nullable=False)  # Current available amount
    total_wagered = Column(Float, default=0.0)  # Total amount bet
    total_returns = Column(Float, default=0.0)  # Total returns
    profit_loss = Column(Float, default=0.0)  # Net P/L
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="bankroll")

    @property
    def roi_percentage(self) -> float:
        """Calculate ROI as percentage."""
        if self.initial_amount == 0:
            return 0.0
        return (self.profit_loss / self.initial_amount) * 100

    def __repr__(self):
        return f"<Bankroll(user_id={self.user_id}, balance={self.current_balance}, roi={self.roi_percentage:.2f}%)>"
