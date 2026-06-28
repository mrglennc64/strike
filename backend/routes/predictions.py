from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Prediction, AuditLog
from schemas import PredictionCreate, PredictionResponse
from typing import List
import json

router = APIRouter(prefix="/api/predictions", tags=["predictions"])


@router.post("/", response_model=PredictionResponse)
def submit_prediction(
    request: PredictionCreate,
    db: Session = Depends(get_db),
):
    """
    Submit a new prediction.

    Args:
        request: PredictionCreate with event, probabilities, and odds
        db: Database session

    Returns:
        PredictionResponse with created prediction
    """
    # In real app, would get user_id from JWT token
    user_id = 1  # TODO: Get from auth context

    # Validate probabilities
    if request.predicted_probability <= 0 or request.predicted_probability > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="predicted_probability must be between 0 and 1",
        )

    if request.market_probability <= 0 or request.market_probability > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="market_probability must be between 0 and 1",
        )

    # Calculate edge
    edge_percentage = (request.predicted_probability - request.market_probability) * 100

    # Create prediction
    prediction = Prediction(
        user_id=user_id,
        event_id=request.event_id,
        event_description=request.event_description,
        outcome=request.outcome,
        predicted_probability=request.predicted_probability,
        market_probability=request.market_probability,
        market_odds=request.market_odds,
        edge_percentage=edge_percentage,
        notes=request.notes,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    # Audit log
    audit = AuditLog(
        user_id=user_id,
        action="SUBMIT_PREDICTION",
        entity_type="prediction",
        entity_id=prediction.id,
        status="SUCCESS",
        details=json.dumps({
            "event_id": request.event_id,
            "edge_percentage": edge_percentage,
        }),
    )
    db.add(audit)
    db.commit()

    return prediction


@router.get("/{prediction_id}", response_model=PredictionResponse)
def get_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
):
    """
    Get a specific prediction.

    Args:
        prediction_id: Prediction ID
        db: Database session

    Returns:
        PredictionResponse
    """
    prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()

    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found",
        )

    return prediction


@router.get("/", response_model=List[PredictionResponse])
def list_predictions(
    skip: int = 0,
    limit: int = 100,
    has_edge: bool = None,
    db: Session = Depends(get_db),
):
    """
    List all predictions for current user.

    Args:
        skip: Number of records to skip
        limit: Number of records to return
        has_edge: Filter by positive edge (optional)
        db: Database session

    Returns:
        List of PredictionResponse
    """
    # In real app, would get user_id from JWT token
    user_id = 1  # TODO: Get from auth context

    query = db.query(Prediction).filter(Prediction.user_id == user_id)

    if has_edge is not None:
        if has_edge:
            query = query.filter(Prediction.predicted_probability > Prediction.market_probability)
        else:
            query = query.filter(Prediction.predicted_probability <= Prediction.market_probability)

    predictions = query.offset(skip).limit(limit).all()

    return predictions
