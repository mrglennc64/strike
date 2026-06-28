"""
Tests for Fed/Economics Predictor system.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from services.fed_economics_predictor import (
    FREDDataProvider,
    FedMeetingCalendar,
    EconomicFeatureEngineer,
    EconomicsPredictionModel,
    EdgeCalculator,
    FedEconomicsPredictor,
)


class TestFREDDataProvider:
    """Tests for FRED data provider."""

    def test_fred_provider_init(self):
        """Test FRED provider initialization."""
        provider = FREDDataProvider(api_key="test_key")
        assert provider.api_key == "test_key"
        assert provider.base_url == "https://api.stlouisfed.org/fred"

    def test_economic_calendar(self):
        """Test economic calendar structure."""
        provider = FREDDataProvider()
        calendar = provider.get_economic_calendar()

        assert "CPI" in calendar
        assert "UNEMPLOYMENT" in calendar
        assert "GDP" in calendar
        assert "FED_FUNDS_RATE" in calendar

        # Check calendar event structure
        cpi = calendar["CPI"]
        assert "series_id" in cpi
        assert "release_schedule" in cpi
        assert "description" in cpi

    def test_get_latest_value(self):
        """Test fetching latest value (integration test)."""
        provider = FREDDataProvider()
        # This test requires API key and internet
        # Skipping in unit test environment
        pass


class TestFedMeetingCalendar:
    """Tests for FOMC meeting calendar."""

    def test_fomc_meetings_structure(self):
        """Test FOMC meetings return structure."""
        # Mock test - full test requires web scraping
        meetings = FedMeetingCalendar.fetch_fomc_meetings()

        # Should return list or empty list
        assert isinstance(meetings, list)

        # If meetings found, check structure
        if meetings:
            meeting = meetings[0]
            assert "date" in meeting or "description" in meeting

    def test_get_next_meeting(self):
        """Test getting next meeting."""
        meeting = FedMeetingCalendar.get_next_meeting()

        # Should return dict or None
        assert meeting is None or isinstance(meeting, dict)

        if meeting:
            assert "date" in meeting


class TestEconomicFeatureEngineer:
    """Tests for feature engineering."""

    @pytest.fixture
    def sample_series(self):
        """Create sample time series."""
        dates = pd.date_range(start="2020-01-01", periods=120, freq="M")
        data = np.random.randn(120).cumsum() + 100
        return pd.Series(data, index=dates)

    def test_lag_features(self, sample_series):
        """Test lag feature creation."""
        lags = [1, 3, 6]
        lag_df = EconomicFeatureEngineer.create_lag_features(sample_series, lags)

        assert len(lag_df) == len(sample_series)
        assert f"lag_1" in lag_df.columns
        assert f"lag_3" in lag_df.columns
        assert f"lag_6" in lag_df.columns

    def test_rolling_features(self, sample_series):
        """Test rolling feature creation."""
        windows = [3, 6]
        rolling_df = EconomicFeatureEngineer.create_rolling_features(
            sample_series, windows
        )

        assert len(rolling_df) == len(sample_series)
        assert "rolling_mean_3" in rolling_df.columns
        assert "rolling_std_3" in rolling_df.columns
        assert "rolling_min_6" in rolling_df.columns
        assert "rolling_max_6" in rolling_df.columns

    def test_rate_of_change(self, sample_series):
        """Test rate of change features."""
        periods = [1, 3]
        roc_df = EconomicFeatureEngineer.create_rate_of_change(
            sample_series, periods
        )

        assert len(roc_df) == len(sample_series)
        assert "pct_change_1" in roc_df.columns
        assert "rate_of_change_3" in roc_df.columns

    def test_volatility_features(self, sample_series):
        """Test volatility feature creation."""
        windows = [3, 6]
        vol_df = EconomicFeatureEngineer.create_volatility_features(
            sample_series, windows
        )

        assert len(vol_df) == len(sample_series)
        assert "volatility_3" in vol_df.columns
        assert "volatility_6" in vol_df.columns

    def test_combine_features(self, sample_series):
        """Test combining multiple series into feature matrix."""
        series_dict = {
            "series1": sample_series,
            "series2": sample_series * 0.5,
            "series3": sample_series + 50,
        }

        features = EconomicFeatureEngineer.combine_features(series_dict)

        # Should have multiple features
        assert len(features.columns) > 5
        # Should have same or fewer rows (after NaN removal)
        assert len(features) <= len(sample_series)


class TestEconomicsPredictionModel:
    """Tests for prediction model."""

    @pytest.fixture
    def sample_data(self):
        """Create sample training data."""
        np.random.seed(42)
        n_samples = 100
        n_features = 10

        dates = pd.date_range(start="2020-01-01", periods=n_samples, freq="M")
        X = np.random.randn(n_samples, n_features)
        y = (np.random.randn(n_samples) > 0).astype(int)

        X_df = pd.DataFrame(X, index=dates, columns=[f"feature_{i}" for i in range(n_features)])
        y_series = pd.Series(y, index=dates)

        return X_df, y_series

    def test_model_creation(self):
        """Test model initialization."""
        model = EconomicsPredictionModel("test_model")
        assert model.model_name == "test_model"
        assert model.model is None
        assert model.scaler is not None

    def test_prepare_training_data(self, sample_data):
        """Test data preparation."""
        X, y = sample_data
        model = EconomicsPredictionModel("test_model")

        X_prepared, y_prepared = model.prepare_training_data(X, y, threshold=0.5)

        assert len(X_prepared) == len(y_prepared)
        assert X_prepared.shape[1] == X.shape[1]  # Same features
        assert np.all((y_prepared == 0) | (y_prepared == 1))  # Binary

    def test_model_training(self, sample_data):
        """Test model training."""
        X, y = sample_data
        model = EconomicsPredictionModel("test_model")

        X_prepared, y_prepared = model.prepare_training_data(X, y, threshold=0.5)
        metrics = model.train(X_prepared, y_prepared, test_size=0.2)

        assert "auc" in metrics
        assert "brier_score" in metrics
        assert metrics["auc"] > 0
        assert metrics["auc"] <= 1

    def test_prediction(self, sample_data):
        """Test making predictions."""
        X, y = sample_data
        model = EconomicsPredictionModel("test_model")

        X_prepared, y_prepared = model.prepare_training_data(X, y, threshold=0.5)
        model.train(X_prepared, y_prepared, test_size=0.2)

        # Predict on sample
        prob = model.predict_probability(X.iloc[[0]])
        assert 0 <= prob <= 1


class TestEdgeCalculator:
    """Tests for edge calculation."""

    def test_edge_calculation_positive(self):
        """Test edge calculation with positive edge."""
        predicted = 0.65
        market = 0.60

        edge = EdgeCalculator.calculate_edge(predicted, market)

        assert edge["edge"] == pytest.approx(0.05, abs=0.001)
        assert edge["best_side"] == "YES"
        assert edge["kelly_fraction"] > 0

    def test_edge_calculation_negative(self):
        """Test edge calculation with negative edge."""
        predicted = 0.45
        market = 0.50

        edge = EdgeCalculator.calculate_edge(predicted, market)

        assert edge["edge"] == pytest.approx(-0.05, abs=0.001)
        assert edge["best_side"] == "NO"

    def test_kelly_fraction_cap(self):
        """Test Kelly fraction is capped at 25%."""
        predicted = 0.95
        market = 0.50

        edge = EdgeCalculator.calculate_edge(predicted, market)

        assert edge["kelly_fraction"] <= 0.25

    def test_kelly_zero_edge(self):
        """Test Kelly fraction when no edge."""
        predicted = 0.50
        market = 0.50

        edge = EdgeCalculator.calculate_edge(predicted, market)

        assert edge["kelly_fraction"] == 0

    def test_kelly_invalid_probability(self):
        """Test Kelly with boundary probabilities."""
        # Market prob = 0 (invalid)
        edge = EdgeCalculator.calculate_edge(0.5, 0)
        assert edge["kelly_fraction"] == 0

        # Market prob = 1 (invalid)
        edge = EdgeCalculator.calculate_edge(0.5, 1)
        assert edge["kelly_fraction"] == 0


class TestFedEconomicsPredictor:
    """Integration tests for full predictor."""

    def test_predictor_initialization(self):
        """Test predictor initialization."""
        predictor = FedEconomicsPredictor(fred_api_key="test_key")
        assert predictor.fred is not None
        assert predictor.engineer is not None

    def test_economic_calendar(self):
        """Test getting economic calendar."""
        predictor = FedEconomicsPredictor()
        calendar = predictor.get_economic_calendar()

        assert isinstance(calendar, dict)
        assert len(calendar) > 0

    def test_fomc_calendar(self):
        """Test getting FOMC calendar."""
        predictor = FedEconomicsPredictor()
        meetings = predictor.get_fomc_calendar()

        assert isinstance(meetings, list)


class TestIntegration:
    """Integration tests."""

    def test_end_to_end_workflow(self):
        """Test complete prediction workflow."""
        # Initialize
        predictor = FedEconomicsPredictor()

        # Get calendars (doesn't require data)
        calendar = predictor.get_economic_calendar()
        assert "CPI" in calendar

        fomc = predictor.get_fomc_calendar()
        assert isinstance(fomc, list)

    def test_edge_opportunity_ranking(self):
        """Test edge opportunity ranking."""
        opportunities = [
            {"metric": "A", "edge_percentage": 0.05},
            {"metric": "B", "edge_percentage": 0.15},
            {"metric": "C", "edge_percentage": 0.08},
        ]

        sorted_opps = sorted(
            opportunities,
            key=lambda x: x["edge_percentage"],
            reverse=True
        )

        assert sorted_opps[0]["metric"] == "B"
        assert sorted_opps[1]["metric"] == "C"
        assert sorted_opps[2]["metric"] == "A"


# Performance tests (can be slow)

class TestPerformance:
    """Performance tests."""

    def test_feature_engineering_speed(self):
        """Test feature engineering is fast."""
        import time

        # Create larger dataset
        dates = pd.date_range(start="2010-01-01", periods=1000, freq="D")
        series = pd.Series(np.random.randn(1000).cumsum() + 100, index=dates)

        start = time.time()
        features = EconomicFeatureEngineer.combine_features({"data": series})
        elapsed = time.time() - start

        # Should complete in reasonable time
        assert elapsed < 5.0
        assert len(features) > 0

    def test_model_training_speed(self):
        """Test model training completes in reasonable time."""
        import time

        np.random.seed(42)
        n_samples = 200
        n_features = 20

        X = np.random.randn(n_samples, n_features)
        y = (np.random.randn(n_samples) > 0).astype(int)

        model = EconomicsPredictionModel("speed_test")
        model.feature_names = [f"f_{i}" for i in range(n_features)]

        start = time.time()
        metrics = model.train(X, y, test_size=0.2)
        elapsed = time.time() - start

        # Should train in reasonable time
        assert elapsed < 10.0
        assert metrics["auc"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
