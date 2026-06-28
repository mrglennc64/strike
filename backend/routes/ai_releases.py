"""AI Releases Predictor routes."""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import logging

from services.ai_releases_predictor import (
    AIReleasesPredictorEngine,
    ModelProvider,
    ReleasePrediction,
)
from schemas.ai_releases import (
    ReleasePredictionRequest,
    ReleasePredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
    MarketDataRequest,
    MarketDataResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/verticals/ai-releases", tags=["AI Releases"])

# Global engine instance
_engine = None


def get_engine() -> AIReleasesPredictorEngine:
    """Get or initialize the prediction engine."""
    global _engine
    if _engine is None:
        _engine = AIReleasesPredictorEngine()
    return _engine


def _prediction_to_response(
    prediction: ReleasePrediction,
) -> ReleasePredictionResponse:
    """Convert ReleasePrediction to response schema."""
    return ReleasePredictionResponse(
        provider=prediction.provider.value,
        model_name=prediction.model_name,
        prediction_date=prediction.prediction_date,
        target_date=prediction.target_date,
        predicted_probability=prediction.predicted_probability,
        polymarket_price=prediction.polymarket_price,
        edge=prediction.edge,
        edge_pct=prediction.edge_pct,
        recommendation=prediction.recommendation,
        confidence=prediction.confidence,
        features=prediction.features,
    )


@router.get("/health")
async def health_check():
    """Health check for AI Releases service."""
    return {
        "status": "ok",
        "service": "ai-releases-predictor",
        "models": [p.value for p in ModelProvider],
    }


@router.post("/predict", response_model=ReleasePredictionResponse)
async def predict(
    request: ReleasePredictionRequest,
    engine: AIReleasesPredictorEngine = Depends(get_engine),
):
    """
    Predict release probability for an AI model.

    Example:
    ```json
    {
      "provider": "anthropic",
      "model_name": "Claude 4",
      "target_date": "2026-12-31"
    }
    ```

    Returns:
    - predicted_probability: P(Release by target_date)
    - polymarket_price: Current market price
    - edge: Predicted prob - Market price
    - recommendation: Trading signal
    """
    try:
        provider = ModelProvider(request.provider)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider. Must be one of: {[p.value for p in ModelProvider]}",
        )

    try:
        target_date = datetime.fromisoformat(request.target_date)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid target_date format. Use ISO format (YYYY-MM-DD)",
        )

    try:
        prediction = await engine.predict(
            provider=provider,
            model_name=request.model_name,
            target_date=target_date,
        )
        return _prediction_to_response(prediction)
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail="Prediction failed")


@router.post("/batch-predict", response_model=BatchPredictionResponse)
async def batch_predict(
    request: BatchPredictionRequest,
    engine: AIReleasesPredictorEngine = Depends(get_engine),
):
    """
    Generate multiple predictions in a single request.

    Returns batch with calculated total edge.
    """
    try:
        predictions = await engine.predict_batch(
            [asdict(p) for p in request.predictions]
        )

        responses = [_prediction_to_response(p) for p in predictions]

        # Calculate total edge (assuming $100 per position)
        total_edge_usd = sum(p.edge * 100 for p in responses)

        return BatchPredictionResponse(
            predictions=responses,
            generated_at=datetime.utcnow(),
            total_edge_usd=total_edge_usd,
        )
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(status_code=500, detail="Batch prediction failed")


@router.post("/markets", response_model=MarketDataResponse)
async def get_market_data(
    request: MarketDataRequest,
    engine: AIReleasesPredictorEngine = Depends(get_engine),
):
    """
    Search for Polymarket markets related to a model release.

    Returns available markets and current pricing.
    """
    try:
        markets = await engine.polymarket.search_markets(
            f"{request.provider} {request.model_name} {request.query}"
        )

        if not markets:
            raise HTTPException(
                status_code=404,
                detail="No markets found for this query",
            )

        top_market = markets[0] if markets else None
        current_price = None

        if top_market and "outcomes" in top_market:
            prices = top_market.get("outcomes", [])
            if prices:
                current_price = float(prices[0])

        return MarketDataResponse(
            provider=request.provider,
            model_name=request.model_name,
            markets=markets,
            top_market=top_market,
            current_price=current_price,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Market data error: {e}")
        raise HTTPException(status_code=500, detail="Market data fetch failed")


@router.get("/examples")
async def get_example_predictions(
    engine: AIReleasesPredictorEngine = Depends(get_engine),
):
    """
    Get example predictions for common models.

    Useful for testing and understanding the API.
    """
    from services.ai_releases_predictor import EXAMPLE_PREDICTIONS

    try:
        predictions = await engine.predict_batch(EXAMPLE_PREDICTIONS)
        responses = [_prediction_to_response(p) for p in predictions]

        return {
            "examples": responses,
            "note": "These are example predictions based on synthetic data",
            "generated_at": datetime.utcnow(),
        }
    except Exception as e:
        logger.error(f"Examples error: {e}")
        raise HTTPException(status_code=500, detail="Examples generation failed")


@router.get("/leaderboard")
async def get_leaderboard(
    min_edge: float = 0.05,
    engine: AIReleasesPredictorEngine = Depends(get_engine),
):
    """
    Get top predictions by edge (predicted_prob - market_price).

    Filters for positive edge (favorable predictions).
    """
    from services.ai_releases_predictor import EXAMPLE_PREDICTIONS

    try:
        predictions = await engine.predict_batch(EXAMPLE_PREDICTIONS)

        # Filter for positive edge and sort
        positive_edge = [p for p in predictions if p.edge >= min_edge]
        leaderboard = sorted(
            positive_edge, key=lambda p: p.edge_pct, reverse=True
        )

        responses = [_prediction_to_response(p) for p in leaderboard]

        return {
            "leaderboard": responses,
            "min_edge_filter": min_edge,
            "count": len(responses),
            "total_edge_usd": sum(p.edge * 100 for p in responses),
        }
    except Exception as e:
        logger.error(f"Leaderboard error: {e}")
        raise HTTPException(status_code=500, detail="Leaderboard failed")


@router.get("/providers")
async def get_supported_providers():
    """Get list of supported AI providers."""
    return {
        "providers": [
            {
                "name": p.value,
                "display": {
                    "anthropic": "Anthropic (Claude)",
                    "openai": "OpenAI (GPT)",
                    "xai": "xAI (Grok)",
                }.get(p.value, p.value),
            }
            for p in ModelProvider
        ],
    }


# Import for type hints
from dataclasses import asdict
