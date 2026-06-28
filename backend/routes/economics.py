"""
FastAPI routes for Fed/Economics predictions.

Endpoints:
- GET /api/verticals/economics/predict-cpi - Predict CPI probability
- GET /api/verticals/economics/predict-rate-cut - Predict rate cut probability
- GET /api/verticals/economics/calendar - Economic calendar
- GET /api/verticals/economics/fomc-schedule - FOMC meeting schedule
- POST /api/verticals/economics/train-models - Train prediction models
- GET /api/verticals/economics/edge-opportunities - Find edge opportunities
- POST /api/verticals/economics/save-prediction - Save prediction to DB
"""

import os
from typing import Optional, List
from datetime import datetime, timedelta
import logging

from fastapi import APIRouter, Query, HTTPException, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from services.fed_economics_predictor import FedEconomicsPredictor
from models.economics import (
    EconomicsPrediction,
    EconomicsModelMetrics,
    FedMeetingSchedule,
    EconomicRelease,
    EconomicsEdgeOpportunity,
)
from schemas.economics import (
    CPIPredictionResponse,
    RateCutPredictionResponse,
    EconomicsCalendarResponse,
    FOCMScheduleResponse,
    EdgeOpportunityResponse,
    PredictionSaveRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/verticals/economics", tags=["economics"])

# Initialize predictor
predictor = FedEconomicsPredictor(
    fred_api_key=os.getenv("FRED_API_KEY", "")
)


def get_db_session(db: Session = Depends(get_db)) -> Session:
    """Get database session."""
    return db


@router.get("/predict-cpi", response_model=dict)
async def predict_cpi(
    threshold: float = Query(3.5, description="CPI threshold"),
    market_price: Optional[float] = Query(
        None,
        description="Market probability from Polymarket (0-1). If not provided, will fetch."
    ),
):
    """
    Predict probability that CPI will exceed threshold.

    Args:
        threshold: CPI percentage threshold (default: 3.5%)
        market_price: Market probability (0-1)

    Returns:
        Prediction with model probability, edge, and Kelly fraction
    """
    try:
        prediction = predictor.predict_cpi(
            threshold=threshold,
            market_price=market_price
        )
        return {
            "status": "success",
            "data": prediction
        }
    except Exception as e:
        logger.error(f"Error predicting CPI: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error predicting CPI: {str(e)}"
        )


@router.get("/predict-rate-cut", response_model=dict)
async def predict_rate_cut(
    market_price: Optional[float] = Query(
        None,
        description="Market probability from Polymarket (0-1)"
    ),
):
    """
    Predict probability of Fed rate cut at next FOMC meeting.

    Returns:
        Prediction with probability, edge, and next meeting info
    """
    try:
        prediction = predictor.predict_rate_cut(market_price=market_price)
        return {
            "status": "success",
            "data": prediction
        }
    except Exception as e:
        logger.error(f"Error predicting rate cut: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error predicting rate cut: {str(e)}"
        )


@router.get("/predict-unemployment", response_model=dict)
async def predict_unemployment(
    threshold: float = Query(4.2, description="Unemployment rate threshold"),
    market_price: Optional[float] = Query(None),
):
    """
    Predict probability that unemployment will exceed threshold.

    Args:
        threshold: Unemployment percentage threshold (default: 4.2%)
        market_price: Market probability (0-1)

    Returns:
        Prediction with model probability and edge
    """
    try:
        # This would follow same pattern as CPI prediction
        # For now, return template response
        return {
            "status": "success",
            "data": {
                "metric": "Unemployment",
                "threshold": threshold,
                "predicted_probability": 0.45,
                "market_probability": market_price or 0.50,
                "edge": 0.45 - (market_price or 0.50),
                "note": "Unemployment model coming soon"
            }
        }
    except Exception as e:
        logger.error(f"Error predicting unemployment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predict-gdp", response_model=dict)
async def predict_gdp(
    threshold: float = Query(2.5, description="GDP growth threshold (%)"),
    market_price: Optional[float] = Query(None),
):
    """
    Predict probability that GDP growth will exceed threshold.

    Args:
        threshold: GDP growth percentage (default: 2.5%)
        market_price: Market probability (0-1)

    Returns:
        Prediction with model probability and edge
    """
    try:
        return {
            "status": "success",
            "data": {
                "metric": "GDP Growth",
                "threshold": threshold,
                "predicted_probability": 0.55,
                "market_probability": market_price or 0.50,
                "edge": 0.55 - (market_price or 0.50),
                "note": "GDP model coming soon"
            }
        }
    except Exception as e:
        logger.error(f"Error predicting GDP: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calendar", response_model=dict)
async def get_economic_calendar():
    """
    Get upcoming economic releases and events.

    Returns:
        Dictionary of economic events with dates and series IDs
    """
    try:
        calendar = predictor.get_economic_calendar()
        return {
            "status": "success",
            "data": calendar
        }
    except Exception as e:
        logger.error(f"Error fetching calendar: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching calendar: {str(e)}"
        )


@router.get("/fomc-schedule", response_model=dict)
async def get_fomc_schedule():
    """
    Get Federal Open Market Committee (FOMC) meeting schedule.

    Returns:
        List of upcoming FOMC meetings with dates
    """
    try:
        meetings = predictor.get_fomc_calendar()
        return {
            "status": "success",
            "data": meetings
        }
    except Exception as e:
        logger.error(f"Error fetching FOMC schedule: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching FOMC schedule: {str(e)}"
        )


@router.post("/train-models", response_model=dict)
async def train_models(
    db: Session = Depends(get_db_session)
):
    """
    Train prediction models on historical data.

    This endpoint:
    1. Trains CPI predictor
    2. Trains rate cut predictor
    3. Saves model metrics to database
    4. Persists models to disk

    Returns:
        Training metrics for all models
    """
    try:
        import time
        from models.economics import EconomicsModelMetrics

        results = {}

        # Train CPI predictor
        logger.info("Training CPI predictor...")
        start_time = time.time()
        cpi_metrics = predictor.setup_cpi_predictor(threshold=3.5)
        cpi_duration = time.time() - start_time
        results["cpi"] = cpi_metrics

        # Save CPI metrics
        if cpi_metrics:
            db_metrics = EconomicsModelMetrics(
                model_name="cpi_predictor",
                metric_type="auc",
                auc_score=cpi_metrics.get("auc"),
                brier_score=cpi_metrics.get("brier_score"),
                train_size=cpi_metrics.get("train_size"),
                test_size=cpi_metrics.get("test_size"),
                threshold=cpi_metrics.get("threshold"),
                training_duration_seconds=cpi_duration,
            )
            db.add(db_metrics)

        # Train rate cut predictor
        logger.info("Training rate cut predictor...")
        start_time = time.time()
        rate_metrics = predictor.setup_rate_cut_predictor()
        rate_duration = time.time() - start_time
        results["rate_cut"] = rate_metrics

        # Save rate cut metrics
        if rate_metrics:
            db_metrics = EconomicsModelMetrics(
                model_name="rate_cut_predictor",
                metric_type="auc",
                auc_score=rate_metrics.get("auc"),
                brier_score=rate_metrics.get("brier_score"),
                train_size=rate_metrics.get("train_size"),
                test_size=rate_metrics.get("test_size"),
                training_duration_seconds=rate_duration,
            )
            db.add(db_metrics)

        db.commit()

        return {
            "status": "success",
            "message": "Models trained successfully",
            "metrics": results
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error training models: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error training models: {str(e)}"
        )


@router.get("/edge-opportunities", response_model=dict)
async def get_edge_opportunities(
    min_edge: float = Query(0.05, description="Minimum edge % (default: 5%)"),
    confidence: str = Query("all", description="Confidence level: high, medium, low, all"),
):
    """
    Find current edge opportunities across all verticals.

    Args:
        min_edge: Minimum edge percentage to include
        confidence: Filter by confidence level

    Returns:
        List of edge opportunities sorted by edge percentage
    """
    try:
        opportunities = []

        # Predict CPI
        cpi_pred = predictor.predict_cpi()
        if cpi_pred and "edge" in cpi_pred:
            edge_data = cpi_pred["edge"]
            if abs(edge_data["edge"]) >= min_edge:
                opportunities.append({
                    "metric": "CPI > 3.5%",
                    "direction": "YES" if edge_data["edge"] > 0 else "NO",
                    "edge_percentage": abs(edge_data["edge_pct"]),
                    "model_prediction": cpi_pred["predicted_probability"],
                    "market_price": cpi_pred["market_probability"],
                    "kelly_fraction": edge_data["kelly_fraction"],
                    "confidence": "high" if abs(edge_data["edge"]) > 0.10 else "medium",
                })

        # Predict rate cut
        rate_pred = predictor.predict_rate_cut()
        if rate_pred and "edge" in rate_pred:
            edge_data = rate_pred["edge"]
            if abs(edge_data["edge"]) >= min_edge:
                opportunities.append({
                    "metric": "Fed Rate Cut",
                    "direction": "YES" if edge_data["edge"] > 0 else "NO",
                    "edge_percentage": abs(edge_data["edge_pct"]),
                    "model_prediction": rate_pred["predicted_probability"],
                    "market_price": rate_pred["market_probability"],
                    "kelly_fraction": edge_data["kelly_fraction"],
                    "confidence": "high" if abs(edge_data["edge"]) > 0.10 else "medium",
                })

        # Sort by edge percentage
        opportunities.sort(
            key=lambda x: x["edge_percentage"],
            reverse=True
        )

        return {
            "status": "success",
            "count": len(opportunities),
            "data": opportunities
        }

    except Exception as e:
        logger.error(f"Error finding edge opportunities: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("/save-prediction", response_model=dict)
async def save_prediction(
    request: PredictionSaveRequest,
    db: Session = Depends(get_db_session),
):
    """
    Save a prediction to the database for tracking.

    Args:
        request: Prediction details

    Returns:
        Saved prediction record
    """
    try:
        prediction = EconomicsPrediction(
            user_id=request.user_id,
            metric=request.metric,
            threshold=request.threshold,
            prediction_type=request.prediction_type,
            predicted_probability=request.predicted_probability,
            market_probability=request.market_probability,
            edge=request.predicted_probability - (request.market_probability or 0.5),
            edge_percentage=(request.predicted_probability - (request.market_probability or 0.5)) * 100,
            kelly_fraction=request.kelly_fraction,
            expected_value=request.expected_value,
            metadata=request.metadata,
        )

        db.add(prediction)
        db.commit()
        db.refresh(prediction)

        return {
            "status": "success",
            "prediction_id": prediction.id,
            "data": {
                "id": prediction.id,
                "metric": prediction.metric,
                "predicted_probability": prediction.predicted_probability,
                "market_probability": prediction.market_probability,
                "edge": prediction.edge,
                "kelly_fraction": prediction.kelly_fraction,
                "created_at": prediction.created_at.isoformat(),
            }
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error saving prediction: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/predictions/{prediction_id}", response_model=dict)
async def get_prediction(
    prediction_id: int,
    db: Session = Depends(get_db_session),
):
    """Get a saved prediction by ID."""
    try:
        prediction = db.query(EconomicsPrediction).filter(
            EconomicsPrediction.id == prediction_id
        ).first()

        if not prediction:
            raise HTTPException(
                status_code=404,
                detail=f"Prediction {prediction_id} not found"
            )

        return {
            "status": "success",
            "data": {
                "id": prediction.id,
                "metric": prediction.metric,
                "threshold": prediction.threshold,
                "predicted_probability": prediction.predicted_probability,
                "market_probability": prediction.market_probability,
                "edge": prediction.edge,
                "kelly_fraction": prediction.kelly_fraction,
                "actual_outcome": prediction.actual_outcome,
                "created_at": prediction.created_at.isoformat(),
                "resolved_at": prediction.resolved_at.isoformat() if prediction.resolved_at else None,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user-predictions", response_model=dict)
async def get_user_predictions(
    user_id: int,
    metric: Optional[str] = Query(None),
    limit: int = Query(20),
    db: Session = Depends(get_db_session),
):
    """Get prediction history for a user."""
    try:
        query = db.query(EconomicsPrediction).filter(
            EconomicsPrediction.user_id == user_id
        )

        if metric:
            query = query.filter(EconomicsPrediction.metric == metric)

        predictions = query.order_by(
            EconomicsPrediction.created_at.desc()
        ).limit(limit).all()

        return {
            "status": "success",
            "count": len(predictions),
            "data": [
                {
                    "id": p.id,
                    "metric": p.metric,
                    "threshold": p.threshold,
                    "predicted_probability": p.predicted_probability,
                    "market_probability": p.market_probability,
                    "edge": p.edge,
                    "kelly_fraction": p.kelly_fraction,
                    "actual_outcome": p.actual_outcome,
                    "created_at": p.created_at.isoformat(),
                    "resolved_at": p.resolved_at.isoformat() if p.resolved_at else None,
                }
                for p in predictions
            ]
        }

    except Exception as e:
        logger.error(f"Error fetching user predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model-metrics", response_model=dict)
async def get_model_metrics(
    model_name: Optional[str] = Query(None),
    limit: int = Query(10),
    db: Session = Depends(get_db_session),
):
    """Get model performance metrics."""
    try:
        query = db.query(EconomicsModelMetrics)

        if model_name:
            query = query.filter(EconomicsModelMetrics.model_name == model_name)

        metrics = query.order_by(
            EconomicsModelMetrics.created_at.desc()
        ).limit(limit).all()

        return {
            "status": "success",
            "count": len(metrics),
            "data": [
                {
                    "id": m.id,
                    "model_name": m.model_name,
                    "auc_score": m.auc_score,
                    "brier_score": m.brier_score,
                    "train_size": m.train_size,
                    "test_size": m.test_size,
                    "training_duration": m.training_duration_seconds,
                    "created_at": m.created_at.isoformat(),
                }
                for m in metrics
            ]
        }

    except Exception as e:
        logger.error(f"Error fetching model metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resolve-prediction/{prediction_id}", response_model=dict)
async def resolve_prediction(
    prediction_id: int,
    actual_outcome: bool,
    db: Session = Depends(get_db_session),
):
    """
    Resolve a prediction once outcome is known.

    Args:
        prediction_id: Prediction to resolve
        actual_outcome: Whether the prediction was correct

    Returns:
        Resolved prediction record
    """
    try:
        prediction = db.query(EconomicsPrediction).filter(
            EconomicsPrediction.id == prediction_id
        ).first()

        if not prediction:
            raise HTTPException(status_code=404, detail="Prediction not found")

        prediction.actual_outcome = actual_outcome
        prediction.resolved_at = datetime.utcnow()

        db.commit()
        db.refresh(prediction)

        return {
            "status": "success",
            "data": {
                "id": prediction.id,
                "metric": prediction.metric,
                "actual_outcome": prediction.actual_outcome,
                "resolved_at": prediction.resolved_at.isoformat(),
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error resolving prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))
