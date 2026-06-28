from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AuditLogResponse(BaseModel):
    """Response schema for audit log."""
    id: int
    user_id: int
    action: str
    entity_type: str
    entity_id: Optional[int]
    status: str
    details: Optional[str]
    ip_address: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True
