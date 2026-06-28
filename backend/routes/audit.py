from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from models import AuditLog
from schemas import AuditLogResponse
from typing import List
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/audit-log", tags=["audit"])


@router.get("/", response_model=List[AuditLogResponse])
def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    action_filter: str = None,
    entity_type_filter: str = None,
    days: int = 30,
    db: Session = Depends(get_db),
):
    """
    Query audit trail with filtering.

    Args:
        skip: Number of records to skip
        limit: Number of records to return
        action_filter: Filter by action (PLACE_BET, SETTLE_BET, etc.)
        entity_type_filter: Filter by entity type (bet, prediction, bankroll, etc.)
        days: Include logs from last N days (default 30)
        db: Database session

    Returns:
        List of AuditLogResponse sorted by timestamp (newest first)
    """
    # In real app, would get user_id from JWT token
    user_id = 1  # TODO: Get from auth context

    # Calculate cutoff date
    cutoff = datetime.utcnow() - timedelta(days=days)

    query = db.query(AuditLog).filter(
        AuditLog.user_id == user_id,
        AuditLog.timestamp >= cutoff,
    )

    if action_filter:
        query = query.filter(AuditLog.action == action_filter)

    if entity_type_filter:
        query = query.filter(AuditLog.entity_type == entity_type_filter)

    logs = query.order_by(desc(AuditLog.timestamp)).offset(skip).limit(limit).all()

    return logs


@router.get("/action/{action}", response_model=List[AuditLogResponse])
def get_logs_by_action(
    action: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Get audit logs filtered by action.

    Args:
        action: Action name (PLACE_BET, SETTLE_BET, UPDATE_BET_STATUS, etc.)
        skip: Number of records to skip
        limit: Number of records to return
        db: Database session

    Returns:
        List of AuditLogResponse
    """
    # In real app, would get user_id from JWT token
    user_id = 1  # TODO: Get from auth context

    logs = db.query(AuditLog).filter(
        AuditLog.user_id == user_id,
        AuditLog.action == action,
    ).order_by(desc(AuditLog.timestamp)).offset(skip).limit(limit).all()

    return logs


@router.get("/entity/{entity_type}/{entity_id}", response_model=List[AuditLogResponse])
def get_logs_by_entity(
    entity_type: str,
    entity_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Get audit logs for a specific entity (e.g., all logs for a specific bet).

    Args:
        entity_type: Entity type (bet, prediction, bankroll, etc.)
        entity_id: Entity ID
        skip: Number of records to skip
        limit: Number of records to return
        db: Database session

    Returns:
        List of AuditLogResponse
    """
    # In real app, would get user_id from JWT token
    user_id = 1  # TODO: Get from auth context

    logs = db.query(AuditLog).filter(
        AuditLog.user_id == user_id,
        AuditLog.entity_type == entity_type,
        AuditLog.entity_id == entity_id,
    ).order_by(desc(AuditLog.timestamp)).offset(skip).limit(limit).all()

    return logs


@router.get("/summary")
def get_audit_summary(
    days: int = 30,
    db: Session = Depends(get_db),
):
    """
    Get summary of audit activity.

    Args:
        days: Summary period (default 30 days)
        db: Database session

    Returns:
        dict with activity summary
    """
    # In real app, would get user_id from JWT token
    user_id = 1  # TODO: Get from auth context

    cutoff = datetime.utcnow() - timedelta(days=days)

    logs = db.query(AuditLog).filter(
        AuditLog.user_id == user_id,
        AuditLog.timestamp >= cutoff,
    ).all()

    # Count by action
    action_counts = {}
    entity_counts = {}
    status_counts = {}

    for log in logs:
        action_counts[log.action] = action_counts.get(log.action, 0) + 1
        entity_counts[log.entity_type] = entity_counts.get(log.entity_type, 0) + 1
        status_counts[log.status] = status_counts.get(log.status, 0) + 1

    return {
        "period_days": days,
        "total_logs": len(logs),
        "by_action": action_counts,
        "by_entity_type": entity_counts,
        "by_status": status_counts,
    }
