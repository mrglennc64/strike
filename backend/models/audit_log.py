from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class AuditLog(Base):
    """Audit log model for tracking all user actions and system events."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)  # e.g., 'bet', 'bankroll', 'prediction'
    entity_id = Column(Integer, index=True)  # ID of the entity being acted upon
    status = Column(String(50))  # Status after action (e.g., 'SUCCESS', 'FAILED')
    details = Column(Text)  # JSON string with action details
    ip_address = Column(String(45))  # IPv4 or IPv6
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(user_id={self.user_id}, action={self.action}, entity={self.entity_type})>"
