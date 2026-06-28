"""
FastAPI routes for earnings beat/miss predictor.

Endpoints:
- POST /api/verticals/earnings/predict - Generate prediction for a stock
- GET /api/verticals/earnings/scan - Scan multiple stocks for edges
- GET /api/verticals/earnings/{symbol} - Get latest prediction for symbol
- GET /api/verticals/earnings/history/{symbol} - Get prediction history
- POST /api/verticals/earnings/history - Get historical earnings data
- POST /api/verticals/earnings/backtest - Run backtest on model
- GET /api/verticals/earnings/model/stats - Model statistics
"""

import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from database import get_db
from models.earnings import EarningsPredictionRecord, EarningsHistoryRecord
from schemas.earnings import (
    EarningsPredictionCreate,
    EarningsPredictionResponse,
    EarningsPredictionRecordResponse,
    EarningsPredictionListResponse,
    EdgeScanRequest,
    EdgeScanResponse,
    BacktestMetricsResponse,
    ModelStatsResponse,
)
from services.earnings_predictor import (
    EarningsPredictorEngine,
    EarningsPrediction,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/verticals/earnings", tags=["earnings"])

# Global engine instance
_engine: Optional[EarningsPredictorEngine] = None


def get_engine() -> EarningsPredictorEngine:
    """Get or initialize the earnings predictor engine."""
    global _engine
    if _engine is None:
        _engine = EarningsPredictorEngine()
    return _engine


@router.on_event("startup")
async def startup_event():
    """Initialize engine on startup."""
    global _engine
    _engine = EarningsPredictorEngine()
    logger.info("Earnings Predictor Engine initialized")


@router.post("/predict", response_model=EarningsPredictionResponse)
async def predict_earnings(
    request: EarningsPredictionCreate,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    Generate earnings beat/miss prediction for a stock.

    Args:
        request: EarningsPredictionCreate with stock symbol
        db: Database session
        background_tasks: Background task runner

    Returns:
        EarningsPredictionResponse with prediction and edge

    Example:
        POST /api/verticals/earnings/predict
        {
            "symbol": "TSLA",
            "company_name": "Tesla"
        }

        Response:
        {
            "symbol": "TSLA",
            "predicted_probability_beat": 0.62,
            "market_implied_prob_beat": 0.55,
            "edge_probability": 0.07,
            "edge_pct": 12.7,
            "recommendation": "BUY_CALL_SPREAD",
            "confidence": 78.5,
            ...
        }
    """
    try:
        symbol = request.symbol.upper()

        # Check if recent prediction exists (cache for 4 hours)
        existing = (
            db.query(EarningsPredictionRecord)
            .filter(
                EarningsPredictionRecord.symbol == symbol,
                EarningsPredictionRecord.prediction_date >= datetime.utcnow() - timedelta(hours=4),
            )
            .order_by(EarningsPredictionRecord.prediction_date.desc())
            .first()
        )

        if existing:
            logger.info(f"Returning cached prediction for {symbol}")
            return EarningsPredictionResponse(
                symbol=existing.symbol,
                company_name=existing.company_name,
                prediction_date=existing.prediction_date,
                earnings_date=existing.earnings_date,
                predicted_probability_beat=existing.predicted_prob_beat,
                predicted_probability_miss=existing.predicted_prob_miss,
                predicted_probability_in_line=existing.predicted_prob_in_line,
                market_implied_prob_beat=existing.market_implied_prob_beat,
                edge_probability=existing.edge_probability,
                edge_pct=existing.edge_pct,
                expected_move_pct=existing.expected_move_pct,
                recommendation=existing.recommendation,
                confidence=existing.confidence,
            )

        # Generate new prediction
        engine = get_engine()
        prediction = await engine.predict(symbol)

        if prediction is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not generate prediction for {symbol}. Check ticker symbol.",
            )

        # Save to database (background task for non-blocking)
        background_tasks.add_task(
            _save_prediction_to_db,
            db=db,
            prediction=prediction,
            user_id=1,  # TODO: Get from auth context
        )

        return EarningsPredictionResponse(
            symbol=prediction.symbol,
            company_name=prediction.company_name,
            prediction_date=prediction.prediction_date,
            earnings_date=prediction.earnings_date,
            predicted_probability_beat=prediction.predicted_probability_beat,
            predicted_probability_miss=prediction.predicted_probability_miss,
            predicted_probability_in_line=prediction.predicted_probability_in_line,
            market_implied_prob_beat=prediction.market_implied_prob_beat,
            edge_probability=prediction.edge_probability,
            edge_pct=prediction.edge_pct,
            expected_move_pct=prediction.expected_move_pct,
            recommendation=prediction.recommendation,
            confidence=prediction.confidence,
            analyst_estimates=(
                prediction.analyst_estimates.asdict()
                if prediction.analyst_estimates
                else None
            ),
            options_data=(
                prediction.options_data.asdict() if prediction.options_data else None
            ),
            calendar_data=(
                prediction.calendar_data.asdict()
                if prediction.calendar_data
                else None
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error predicting earnings for {request.symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}",
        )


@router.post("/scan", response_model=EdgeScanResponse)
async def scan_earnings_edges(
    request: EdgeScanRequest,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    Scan multiple stocks for earnings edges.

    Args:
        request: EdgeScanRequest with symbols list and filters
        db: Database session
        background_tasks: Background task runner

    Returns:
        EdgeScanResponse with predictions sorted by edge

    Example:
        POST /api/verticals/earnings/scan
        {
            "symbols": ["TSLA", "MSFT", "NVDA", "META"],
            "min_edge_pct": 5.0,
            "only_with_edge": true
        }
    """
    try:
        engine = get_engine()
        predictions: List[EarningsPrediction] = []

        # Generate predictions for each symbol
        for symbol in request.symbols:
            try:
                prediction = await engine.predict(symbol.upper())
                if prediction:
                    predictions.append(prediction)
                    background_tasks.add_task(
                        _save_prediction_to_db,
                        db=db,
                        prediction=prediction,
                        user_id=1,
                    )
            except Exception as e:
                logger.warning(f"Failed to predict {symbol}: {e}")

        # Filter by minimum edge
        filtered = predictions
        if request.only_with_edge:
            filtered = [p for p in predictions if p.edge_pct > request.min_edge_pct]

        # Sort by edge descending
        filtered.sort(key=lambda p: p.edge_pct, reverse=True)

        # Build response
        response_preds = [
            EarningsPredictionResponse(
                symbol=p.symbol,
                company_name=p.company_name,
                prediction_date=p.prediction_date,
                earnings_date=p.earnings_date,
                predicted_probability_beat=p.predicted_probability_beat,
                predicted_probability_miss=p.predicted_probability_miss,
                predicted_probability_in_line=p.predicted_probability_in_line,
                market_implied_prob_beat=p.market_implied_prob_beat,
                edge_probability=p.edge_probability,
                edge_pct=p.edge_pct,
                expected_move_pct=p.expected_move_pct,
                recommendation=p.recommendation,
                confidence=p.confidence,
            )
            for p in filtered
        ]

        avg_edge = (
            sum(p.edge_pct for p in filtered) / len(filtered) if filtered else 0.0
        )

        return EdgeScanResponse(
            scan_date=datetime.utcnow(),
            symbols_scanned=len(request.symbols),
            symbols_with_edge=len(filtered),
            predictions=response_preds,
            top_edge=response_preds[0] if response_preds else None,
            avg_edge=avg_edge,
        )

    except Exception as e:
        logger.error(f"Error scanning earnings edges: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scan failed: {str(e)}",
        )


@router.get("/{symbol}", response_model=EarningsPredictionRecordResponse)
async def get_latest_prediction(
    symbol: str,
    db: Session = Depends(get_db),
):
    """
    Get the latest earnings prediction for a symbol.

    Args:
        symbol: Stock ticker
        db: Database session

    Returns:
        EarningsPredictionRecordResponse with latest prediction
    """
    try:
        prediction = (
            db.query(EarningsPredictionRecord)
            .filter(EarningsPredictionRecord.symbol == symbol.upper())
            .order_by(EarningsPredictionRecord.prediction_date.desc())
            .first()
        )

        if not prediction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No prediction found for {symbol}",
            )

        return prediction

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching prediction for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fetch failed: {str(e)}",
        )


@router.get("/{symbol}/history", response_model=EarningsPredictionListResponse)
async def get_prediction_history(
    symbol: str,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """
    Get prediction history for a symbol.

    Args:
        symbol: Stock ticker
        limit: Number of predictions to return
        db: Database session

    Returns:
        EarningsPredictionListResponse with historical predictions
    """
    try:
        predictions = (
            db.query(EarningsPredictionRecord)
            .filter(EarningsPredictionRecord.symbol == symbol.upper())
            .order_by(EarningsPredictionRecord.prediction_date.desc())
            .limit(limit)
            .all()
        )

        return EarningsPredictionListResponse(
            total=len(predictions),
            predictions=predictions,
        )

    except Exception as e:
        logger.error(f"Error fetching prediction history for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fetch failed: {str(e)}",
        )


@router.post("/earnings-data")
async def get_historical_earnings(
    symbol: str,
    periods: int = 20,
    db: Session = Depends(get_db),
):
    """
    Get historical earnings data for backtesting.

    Args:
        symbol: Stock ticker
        periods: Number of historical periods to fetch
        db: Database session

    Returns:
        List of EarningsHistoryRecord
    """
    try:
        records = (
            db.query(EarningsHistoryRecord)
            .filter(EarningsHistoryRecord.symbol == symbol.upper())
            .order_by(EarningsHistoryRecord.earnings_date.desc())
            .limit(periods)
            .all()
        )

        return records

    except Exception as e:
        logger.error(f"Error fetching earnings history for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fetch failed: {str(e)}",
        )


@router.post("/backtest", response_model=BacktestMetricsResponse)
async def run_backtest(
    symbol: Optional[str] = None,
    days: int = 90,
    db: Session = Depends(get_db),
):
    """
    Run backtest on earnings predictions.

    Args:
        symbol: Optional symbol to limit backtest to
        days: Number of days to backtest
        db: Database session

    Returns:
        BacktestMetricsResponse with performance metrics
    """
    try:
        # Query predictions with known outcomes
        query = db.query(EarningsPredictionRecord).filter(
            EarningsPredictionRecord.actual_outcome != None,
            EarningsPredictionRecord.outcome_date >= datetime.utcnow() - timedelta(days=days),
        )

        if symbol:
            query = query.filter(EarningsPredictionRecord.symbol == symbol.upper())

        predictions = query.all()

        if not predictions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No predictions with outcomes found in period",
            )

        # Calculate metrics
        total = len(predictions)
        hits = sum(
            1
            for p in predictions
            if p.actual_outcome
            and (
                (p.actual_outcome == "beat" and p.predicted_prob_beat > 0.5)
                or (p.actual_outcome == "miss" and p.predicted_prob_miss > 0.5)
            )
        )

        edge_predictions = [p for p in predictions if p.edge_pct > 0]
        edge_hits = sum(
            1
            for p in edge_predictions
            if p.actual_outcome
            and (
                (p.actual_outcome == "beat" and p.predicted_prob_beat > 0.5)
                or (p.actual_outcome == "miss" and p.predicted_prob_miss > 0.5)
            )
        )

        return BacktestMetricsResponse(
            period=f"last_{days}_days",
            total_predictions=total,
            predictions_with_edge=len(edge_predictions),
            hit_rate=hits / total if total > 0 else 0.0,
            edge_hit_rate=edge_hits / len(edge_predictions) if edge_predictions else 0.0,
            total_edge_pct=sum(p.edge_pct for p in predictions),
            avg_edge_per_prediction=sum(p.edge_pct for p in predictions) / total if total > 0 else 0.0,
            profit_factor=1.5,  # Placeholder
            accuracy_by_confidence_bucket={},  # TODO: Implement
            largest_win=max((p.edge_pct for p in predictions if p.edge_pct > 0), default=0),
            largest_loss=min((p.edge_pct for p in predictions if p.edge_pct < 0), default=0),
            kelly_fraction=0.25,  # Conservative Kelly
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backtest failed: {str(e)}",
        )


@router.get("/model/stats", response_model=ModelStatsResponse)
async def get_model_stats():
    """
    Get earnings prediction model statistics.

    Returns:
        ModelStatsResponse with model info and performance metrics
    """
    try:
        engine = get_engine()

        return ModelStatsResponse(
            version="1.0.0",
            model_type="XGBoost",
            training_date=None,
            training_samples=0,
            feature_count=18,
            feature_names=engine.predictor_model.feature_names,
            auc_score=None,
            precision=None,
            recall=None,
            f1_score=None,
            last_retrain_date=None,
            is_live=True,
        )

    except Exception as e:
        logger.error(f"Error fetching model stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stats fetch failed: {str(e)}",
        )


# Helper functions


async def _save_prediction_to_db(
    db: Session,
    prediction: EarningsPrediction,
    user_id: int,
):
    """Save prediction to database."""
    try:
        record = EarningsPredictionRecord(
            user_id=user_id,
            symbol=prediction.symbol,
            company_name=prediction.company_name,
            prediction_date=prediction.prediction_date,
            earnings_date=prediction.earnings_date,
            predicted_prob_beat=prediction.predicted_probability_beat,
            predicted_prob_miss=prediction.predicted_probability_miss,
            predicted_prob_in_line=prediction.predicted_probability_in_line,
            market_implied_prob_beat=prediction.market_implied_prob_beat,
            edge_probability=prediction.edge_probability,
            edge_pct=prediction.edge_pct,
            expected_move_pct=prediction.expected_move_pct,
            recommendation=prediction.recommendation,
            confidence=prediction.confidence,
            analyst_consensus_strength=(
                prediction.analyst_estimates.eps_estimate_variance
                if prediction.analyst_estimates
                else None
            ),
            num_analysts=prediction.analyst_estimates.num_analysts
            if prediction.analyst_estimates
            else None,
            guidance_revision_trend=(
                prediction.analyst_estimates.guidance_revision_trend
                if prediction.analyst_estimates
                else None
            ),
            iv_rank=prediction.options_data.iv_rank
            if prediction.options_data
            else None,
            vol_skew=prediction.options_data.vol_skew
            if prediction.options_data
            else None,
            implied_move_pct=prediction.options_data.implied_move_pct
            if prediction.options_data
            else None,
            smart_money_flow=(
                prediction.options_data.smart_money_flow
                if prediction.options_data
                else None
            ),
        )

        db.add(record)
        db.commit()
        logger.info(f"Saved prediction for {prediction.symbol}")
    except Exception as e:
        logger.error(f"Error saving prediction to database: {e}")
        db.rollback()


# Add missing import
from datetime import timedelta
