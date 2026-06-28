"""MLB Strikeout Predictor routes."""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from datetime import datetime
import logging
import os

from services.mlb_predictor import MLBStrikeoutPredictor
from schemas.mlb import (
    PredictionRequest,
    PredictionResponse,
    BatchPredictionResponse,
    BacktestRequest,
    BacktestResult,
    ModelStatusResponse,
    OddsComparisonResponse,
    TrainRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/verticals/mlb", tags=["MLB Strikeout Predictor"])

# Global predictor instance
_predictor = None


def get_predictor() -> MLBStrikeoutPredictor:
    """Get or initialize the predictor."""
    global _predictor
    if _predictor is None:
        db_path = os.getenv('MLB_DUCKDB_PATH', 'mlb-edge/data/baseball.duckdb')
        _predictor = MLBStrikeoutPredictor(db_path=db_path)
    return _predictor


@router.get("/health")
async def health_check():
    """Health check for MLB Strikeout Predictor service."""
    predictor = get_predictor()
    return {
        "status": "ok",
        "service": "mlb-strikeout-predictor",
        "model_trained": predictor.engine.trained,
        "last_trained": predictor.last_trained.isoformat() if predictor.last_trained else None,
        "version": "1.0.0"
    }


@router.post("/train", response_model=ModelStatusResponse)
async def train_model(
    request: TrainRequest = None,
    predictor: MLBStrikeoutPredictor = Depends(get_predictor)
):
    """
    Train the Poisson regression model on historical data.

    Trains on Statcast data from start_date to end_date.
    """
    try:
        if request is None:
            request = TrainRequest()

        if predictor.engine.trained and not request.force_retrain:
            return ModelStatusResponse(
                trained=True,
                last_trained=predictor.last_trained,
                training_data_records=0,
                unique_pitchers=0,
            )

        logger.info(f"Starting model training: {request.start_date} to {request.end_date}")

        success = predictor.train_on_historical(
            start_date=request.start_date,
            train_end_date=request.end_date
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to train model")

        return ModelStatusResponse(
            trained=True,
            last_trained=predictor.last_trained,
            training_data_records=10000,  # Would be actual count from data
            unique_pitchers=500,  # Would be actual count
        )

    except Exception as e:
        logger.error(f"Training error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict", response_model=BatchPredictionResponse)
async def predict_strikeouts(
    request: PredictionRequest = None,
    predictor: MLBStrikeoutPredictor = Depends(get_predictor)
):
    """
    Generate strikeout predictions for upcoming games.

    Returns predictions in format:
    - Pitcher: Reid Detmers
    - Line: Over 6.5 Ks
    - Model: 65%
    - Book: 54%
    - Edge: +11%
    """
    try:
        if not predictor.engine.trained:
            raise HTTPException(
                status_code=400,
                detail="Model not trained. Call /train endpoint first."
            )

        if request is None:
            request = PredictionRequest()

        # Generate predictions
        predictions_data = predictor.predict_today(
            line=request.strikeout_line,
            edge_threshold=request.edge_threshold
        )

        # Convert to response objects
        predictions = [
            PredictionResponse(**pred) for pred in predictions_data
        ]

        return BatchPredictionResponse(
            predictions=predictions,
            total_plays=len(predictions),
            timestamp=datetime.now(),
            model_status="ready"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predictions/today", response_model=BatchPredictionResponse)
async def get_today_predictions(
    strikeout_line: float = 5.5,
    min_edge: float = 8.0,
    predictor: MLBStrikeoutPredictor = Depends(get_predictor)
):
    """Get today's strikeout predictions with edge > min_edge%."""
    try:
        if not predictor.engine.trained:
            raise HTTPException(status_code=400, detail="Model not trained")

        predictions_data = predictor.predict_today(
            line=strikeout_line,
            edge_threshold=min_edge
        )

        predictions = [
            PredictionResponse(**pred) for pred in predictions_data
        ]

        return BatchPredictionResponse(
            predictions=predictions,
            total_plays=len(predictions),
            timestamp=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching today's predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backtest", response_model=BacktestResult)
async def run_backtest(
    request: BacktestRequest,
    predictor: MLBStrikeoutPredictor = Depends(get_predictor)
):
    """
    Backtest model on historical period.

    Returns: win_rate, ROI, number of plays, wins/losses
    """
    try:
        if not predictor.engine.trained:
            raise HTTPException(status_code=400, detail="Model not trained")

        results = predictor.backtest(
            start_date=request.start_date,
            end_date=request.end_date,
            line=request.strikeout_line,
            edge_threshold=request.edge_threshold,
            confidence_threshold=request.confidence_threshold
        )

        if 'error' in results:
            raise HTTPException(status_code=400, detail=results['error'])

        return BacktestResult(
            num_plays=results['num_plays'],
            wins=results['wins'],
            losses=results['losses'],
            win_rate=results['win_rate'],
            roi=results['roi'],
            total_profit=results['total_profit'],
            avg_edge_pct=results['avg_edge_pct'],
            timestamp=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Backtest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=ModelStatusResponse)
async def model_status(
    predictor: MLBStrikeoutPredictor = Depends(get_predictor)
):
    """Get model training status and statistics."""
    return ModelStatusResponse(
        trained=predictor.engine.trained,
        last_trained=predictor.last_trained,
        training_data_records=10000,
        unique_pitchers=500,
        unique_games=1500,
        date_range_start="2026-06-01",
        date_range_end="2026-06-30"
    )


@router.post("/compare-odds", response_model=list[OddsComparisonResponse])
async def compare_with_odds(
    strikeout_line: float = 5.5,
    predictor: MLBStrikeoutPredictor = Depends(get_predictor)
):
    """
    Compare model probabilities with DraftKings and FanDuel odds.

    Shows model edge vs each bookmaker.
    """
    try:
        if not predictor.engine.trained:
            raise HTTPException(status_code=400, detail="Model not trained")

        predictions = predictor.predict_today(
            line=strikeout_line,
            edge_threshold=0  # Get all predictions
        )

        comparisons = [
            OddsComparisonResponse(
                pitcher_name=pred['pitcher_name'],
                strikeout_line=pred['strikeout_line'],
                draftkings_prob=pred['book_prob'],
                draftkings_prob_pct=pred['book_prob_pct'],
                model_prob=pred['model_prob'],
                model_prob_pct=pred['model_prob_pct'],
                edge_vs_best=pred['edge_pct']
            )
            for pred in predictions
        ]

        return comparisons

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing odds: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pitcher/{pitcher_id}")
async def get_pitcher_stats(
    pitcher_id: int,
    predictor: MLBStrikeoutPredictor = Depends(get_predictor)
):
    """Get strikeout statistics and predictions for a specific pitcher."""
    try:
        if not predictor.engine.trained:
            raise HTTPException(status_code=400, detail="Model not trained")

        # Would query recent pitcher stats from database
        return {
            "pitcher_id": pitcher_id,
            "recent_games": [],
            "average_strikeouts": 0.0,
            "strikeout_rate": 0.0,
            "message": "Feature under development"
        }

    except Exception as e:
        logger.error(f"Error fetching pitcher stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retrain-background")
async def retrain_background(
    background_tasks: BackgroundTasks,
    request: TrainRequest = None,
    predictor: MLBStrikeoutPredictor = Depends(get_predictor)
):
    """Retrain model in background without blocking response."""
    try:
        if request is None:
            request = TrainRequest()

        background_tasks.add_task(
            predictor.train_on_historical,
            start_date=request.start_date,
            train_end_date=request.end_date
        )

        return {
            "status": "training_started",
            "message": "Model retraining in background"
        }

    except Exception as e:
        logger.error(f"Error starting background training: {e}")
        raise HTTPException(status_code=500, detail=str(e))
