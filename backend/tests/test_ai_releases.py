"""Tests for AI Release Predictor."""

import pytest
from datetime import datetime, timedelta
from services.ai_releases_predictor import (
    AIReleasesPredictorEngine,
    ReleaseFeatures,
    ModelProvider,
    GitHubScraper,
    PolymarketAPI,
    HuggingFaceScraper,
    ReleasePredictor,
)


@pytest.mark.asyncio
async def test_release_predictor_initialization():
    """Test that predictor initializes correctly."""
    predictor = ReleasePredictor()
    assert predictor.model is not None
    assert predictor.scaler is not None


@pytest.mark.asyncio
async def test_release_features_to_array():
    """Test ReleaseFeatures conversion to numpy array."""
    features = ReleaseFeatures(
        commits_last_7d=10.0,
        commits_last_30d=50.0,
        releases_last_90d=3.0,
        days_since_last_release=45.0,
        repository_stars=1000.0,
        contributor_count=50.0,
        issue_velocity=1.43,
        hf_models_last_30d=5.0,
        hf_model_downloads=10000.0,
        polymarket_price=0.35,
        days_until_target=180.0,
        quarter_progress=0.5,
        is_major_event=False,
        avg_release_gap_days=90.0,
        last_release_recency_percentile=0.5,
    )

    array = features.to_array()
    assert array.shape == (1, 15)


@pytest.mark.asyncio
async def test_github_scraper_initialization():
    """Test GitHubScraper initialization."""
    scraper = GitHubScraper()
    assert scraper.headers is not None


@pytest.mark.asyncio
async def test_polymarket_api_initialization():
    """Test PolymarketAPI initialization."""
    api = PolymarketAPI()
    assert api.BASE_URL == "https://gamma-api.polymarket.com"


@pytest.mark.asyncio
async def test_huggingface_scraper_initialization():
    """Test HuggingFaceScraper initialization."""
    scraper = HuggingFaceScraper()
    assert scraper is not None


@pytest.mark.asyncio
async def test_ai_releases_engine_initialization():
    """Test AIReleasesPredictorEngine initialization."""
    engine = AIReleasesPredictorEngine()
    assert engine.predictor is not None
    assert engine.github is not None
    assert engine.polymarket is not None
    assert engine.huggingface is not None


@pytest.mark.asyncio
async def test_is_major_event():
    """Test major event detection."""
    engine = AIReleasesPredictorEngine()

    # June = WWDC
    june_date = datetime(2026, 6, 15)
    assert engine._is_major_event(ModelProvider.ANTHROPIC, june_date) is True

    # May = Not a major event
    may_date = datetime(2026, 5, 15)
    assert engine._is_major_event(ModelProvider.ANTHROPIC, may_date) is False


@pytest.mark.asyncio
async def test_model_provider_enum():
    """Test ModelProvider enum values."""
    assert ModelProvider.ANTHROPIC.value == "anthropic"
    assert ModelProvider.OPENAI.value == "openai"
    assert ModelProvider.XAI.value == "xai"


@pytest.mark.asyncio
async def test_release_predictor_probability():
    """Test probability prediction."""
    predictor = ReleasePredictor()

    features = ReleaseFeatures(
        commits_last_7d=10.0,
        commits_last_30d=50.0,
        releases_last_90d=3.0,
        days_since_last_release=45.0,
        repository_stars=1000.0,
        contributor_count=50.0,
        issue_velocity=1.43,
        hf_models_last_30d=5.0,
        hf_model_downloads=10000.0,
        polymarket_price=0.35,
        days_until_target=180.0,
        quarter_progress=0.5,
        is_major_event=False,
        avg_release_gap_days=90.0,
        last_release_recency_percentile=0.5,
    )

    prob, confidence = predictor.predict_probability(features)

    assert 0 <= prob <= 1
    assert 0 <= confidence <= 1


@pytest.mark.asyncio
async def test_historical_releases_data():
    """Test historical release data structure."""
    engine = AIReleasesPredictorEngine()

    # Claude 3 releases
    claude_releases = engine.HISTORICAL_RELEASES.get(
        (ModelProvider.ANTHROPIC, "Claude 3"), []
    )
    assert len(claude_releases) > 0
    assert all(isinstance(d, datetime) for d in claude_releases)


def test_example_predictions_format():
    """Test example predictions have correct format."""
    from services.ai_releases_predictor import EXAMPLE_PREDICTIONS

    assert len(EXAMPLE_PREDICTIONS) > 0

    for example in EXAMPLE_PREDICTIONS:
        assert "provider" in example
        assert "model_name" in example
        assert "target_date" in example
        assert example["provider"] in ["anthropic", "openai", "xai"]


@pytest.mark.asyncio
async def test_edge_calculation():
    """Test edge calculation logic."""
    engine = AIReleasesPredictorEngine()

    # Create features with known probabilities
    features = ReleaseFeatures(
        commits_last_7d=20.0,
        commits_last_30d=100.0,
        releases_last_90d=5.0,
        days_since_last_release=30.0,
        repository_stars=5000.0,
        contributor_count=100.0,
        issue_velocity=2.86,
        hf_models_last_30d=10.0,
        hf_model_downloads=50000.0,
        polymarket_price=0.40,
        days_until_target=150.0,
        quarter_progress=0.6,
        is_major_event=True,
        avg_release_gap_days=60.0,
        last_release_recency_percentile=0.8,
    )

    prob, _ = engine.predictor.predict_probability(features)
    edge = prob - features.polymarket_price

    # Edge should be reasonable
    assert -1 <= edge <= 1


@pytest.mark.asyncio
async def test_recommendation_logic():
    """Test recommendation generation."""
    from services.ai_releases_predictor import ReleasePrediction
    from datetime import datetime, timedelta

    # Create a prediction with strong positive edge
    pred_strong_buy = ReleasePrediction(
        provider=ModelProvider.ANTHROPIC,
        model_name="Claude 4",
        prediction_date=datetime.utcnow(),
        target_date=datetime.utcnow() + timedelta(days=180),
        predicted_probability=0.65,
        polymarket_price=0.40,
        edge=0.25,
        edge_pct=62.5,
        recommendation="STRONG_BUY",
        confidence=0.85,
        features={},
    )

    assert pred_strong_buy.recommendation == "STRONG_BUY"
    assert pred_strong_buy.edge > 0.10


@pytest.mark.asyncio
async def test_batch_prediction_example():
    """Test batch prediction with example data."""
    engine = AIReleasesPredictorEngine()

    from services.ai_releases_predictor import EXAMPLE_PREDICTIONS

    predictions = await engine.predict_batch(EXAMPLE_PREDICTIONS)

    assert len(predictions) == len(EXAMPLE_PREDICTIONS)
    assert all(hasattr(p, 'predicted_probability') for p in predictions)
    assert all(hasattr(p, 'edge') for p in predictions)
    assert all(hasattr(p, 'recommendation') for p in predictions)


# Integration tests
@pytest.mark.asyncio
async def test_full_prediction_pipeline():
    """Test complete prediction pipeline."""
    engine = AIReleasesPredictorEngine()

    target_date = datetime.utcnow() + timedelta(days=180)

    prediction = await engine.predict(
        provider=ModelProvider.ANTHROPIC,
        model_name="Claude 4",
        target_date=target_date,
    )

    # Verify all fields are populated
    assert prediction.provider == ModelProvider.ANTHROPIC
    assert prediction.model_name == "Claude 4"
    assert prediction.target_date == target_date
    assert 0 <= prediction.predicted_probability <= 1
    assert 0 <= prediction.polymarket_price <= 1
    assert 0 <= prediction.confidence <= 1
    assert prediction.recommendation in [
        "STRONG_BUY",
        "BUY",
        "HOLD",
        "SELL",
        "STRONG_SELL",
    ]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
