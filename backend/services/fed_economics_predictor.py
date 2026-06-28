"""
Federal Reserve & Economics Predictor

Predicts economic outcomes (CPI, rate cuts, unemployment, GDP) using:
- FRED API integration (Federal Reserve economic data)
- Time-series feature engineering
- XGBoost classifier models
- Fed meeting calendar scraper
- Polymarket + Kalshi market price integration
- Edge calculation (model prediction vs market probability)

Example predictions:
- P(CPI > 3.5% next month)
- P(Rate cut at next FOMC meeting)
- P(Unemployment > 4.2%)
- P(GDP > 2.5% annualized)
"""

import os
import pickle
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

import numpy as np
import pandas as pd
import pandas_datareader as pdr
import xgboost as xgb
import requests
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, brier_score_loss
import joblib
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class FREDDataProvider:
    """Integrates with Federal Reserve Economic Data (FRED) API."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize FRED data provider with API key."""
        self.api_key = api_key or os.getenv("FRED_API_KEY", "")
        self.base_url = "https://api.stlouisfed.org/fred"

        if not self.api_key:
            logger.warning("FRED_API_KEY not set. Limited to 120 requests/minute.")

    def fetch_series(
        self,
        series_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Fetch economic series from FRED API.

        Args:
            series_id: FRED series ID (e.g., 'CPIAUCSL' for CPI)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with date index and 'value' column
        """
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365*5)).strftime("%Y-%m-%d")
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")

            # Use pandas_datareader for direct FRED access
            data = pdr.get_data_fred(series_id, start_date, end_date)

            # Rename column to 'value' and return
            if isinstance(data, pd.DataFrame):
                data = data.iloc[:, 0]

            df = pd.DataFrame({"value": data})
            df.index.name = "date"
            df = df.dropna()

            logger.info(f"Fetched {len(df)} records for {series_id}")
            return df

        except Exception as e:
            logger.error(f"Error fetching FRED series {series_id}: {e}")
            return pd.DataFrame()

    def get_latest_value(self, series_id: str) -> Optional[float]:
        """Get the latest value for a FRED series."""
        df = self.fetch_series(series_id)
        if not df.empty:
            return df["value"].iloc[-1]
        return None

    def get_economic_calendar(self) -> Dict[str, Dict]:
        """
        Get upcoming economic releases.

        Returns dict with event names, dates, and forecast/actual values.
        """
        # Key FRED series to monitor
        calendar = {
            "CPI": {
                "series_id": "CPIAUCSL",
                "release_schedule": "monthly",
                "release_day": 12,  # Around the 12th of month
                "description": "Consumer Price Index - All Urban Consumers",
            },
            "PCE": {
                "series_id": "PCEPI",
                "release_schedule": "monthly",
                "release_day": 28,
                "description": "Personal Consumption Expenditures Price Index",
            },
            "UNEMPLOYMENT": {
                "series_id": "UNRATE",
                "release_schedule": "monthly",
                "release_day": 7,
                "description": "Unemployment Rate",
            },
            "NON_FARM_PAYROLLS": {
                "series_id": "PAYEMS",
                "release_schedule": "monthly",
                "release_day": 7,
                "description": "Total Nonfarm Payroll",
            },
            "RETAIL_SALES": {
                "series_id": "RSXFS",
                "release_schedule": "monthly",
                "release_day": 15,
                "description": "Retail Sales",
            },
            "INITIAL_JOBLESS": {
                "series_id": "ICSA",
                "release_schedule": "weekly",
                "description": "Initial Jobless Claims",
            },
            "GDP": {
                "series_id": "A191RA1Q225SBEA",
                "release_schedule": "quarterly",
                "description": "Real Gross Domestic Product",
            },
            "FED_FUNDS_RATE": {
                "series_id": "FEDFUNDS",
                "release_schedule": "monthly",
                "description": "Effective Federal Funds Rate",
            },
        }

        return calendar


class FedMeetingCalendar:
    """Scrapes and manages Fed FOMC meeting schedule."""

    @staticmethod
    def fetch_fomc_meetings() -> List[Dict]:
        """
        Fetch upcoming FOMC meeting dates from Federal Reserve website.

        Returns list of meetings with dates.
        """
        try:
            url = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            meetings = []
            # Parse table rows for meeting dates
            for row in soup.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) >= 2:
                    try:
                        # Extract meeting date and decision date
                        meeting_text = cells[0].get_text(strip=True)
                        date_text = cells[1].get_text(strip=True)

                        # Try to parse date
                        meeting_date = datetime.strptime(date_text, "%B %d-%d, %Y")

                        meetings.append({
                            "description": meeting_text,
                            "date": meeting_date.date(),
                            "decision_date": meeting_date.date(),
                        })
                    except (ValueError, AttributeError):
                        continue

            return meetings

        except Exception as e:
            logger.error(f"Error fetching FOMC meetings: {e}")
            return []

    @staticmethod
    def get_next_meeting() -> Optional[Dict]:
        """Get the next scheduled FOMC meeting."""
        meetings = FedMeetingCalendar.fetch_fomc_meetings()
        today = datetime.now().date()

        for meeting in meetings:
            if meeting["date"] >= today:
                return meeting

        return None


class EconomicFeatureEngineer:
    """Generates time-series features from economic data."""

    @staticmethod
    def create_lag_features(
        series: pd.Series,
        lags: List[int] = None,
    ) -> pd.DataFrame:
        """
        Create lagged features from a time series.

        Args:
            series: Time series data
            lags: List of lag periods (default: [1, 3, 6, 12])

        Returns:
            DataFrame with lag features
        """
        if lags is None:
            lags = [1, 3, 6, 12]

        df = pd.DataFrame(index=series.index)

        for lag in lags:
            df[f"lag_{lag}"] = series.shift(lag)

        return df

    @staticmethod
    def create_rolling_features(
        series: pd.Series,
        windows: List[int] = None,
    ) -> pd.DataFrame:
        """
        Create rolling window features.

        Args:
            series: Time series data
            windows: List of window sizes (default: [3, 6, 12])

        Returns:
            DataFrame with rolling features
        """
        if windows is None:
            windows = [3, 6, 12]

        df = pd.DataFrame(index=series.index)

        for window in windows:
            df[f"rolling_mean_{window}"] = series.rolling(window).mean()
            df[f"rolling_std_{window}"] = series.rolling(window).std()
            df[f"rolling_min_{window}"] = series.rolling(window).min()
            df[f"rolling_max_{window}"] = series.rolling(window).max()

        return df

    @staticmethod
    def create_rate_of_change(
        series: pd.Series,
        periods: List[int] = None,
    ) -> pd.DataFrame:
        """
        Create rate of change features.

        Args:
            series: Time series data
            periods: List of periods (default: [1, 3, 6, 12])

        Returns:
            DataFrame with rate of change features
        """
        if periods is None:
            periods = [1, 3, 6, 12]

        df = pd.DataFrame(index=series.index)

        for period in periods:
            df[f"pct_change_{period}"] = series.pct_change(period)
            df[f"rate_of_change_{period}"] = series.diff(period)

        return df

    @staticmethod
    def create_volatility_features(
        series: pd.Series,
        windows: List[int] = None,
    ) -> pd.DataFrame:
        """
        Create volatility features using rolling standard deviation.

        Args:
            series: Time series data
            windows: List of window sizes

        Returns:
            DataFrame with volatility features
        """
        if windows is None:
            windows = [3, 6, 12]

        df = pd.DataFrame(index=series.index)

        for window in windows:
            returns = series.pct_change()
            df[f"volatility_{window}"] = returns.rolling(window).std()

        return df

    @staticmethod
    def combine_features(
        series_dict: Dict[str, pd.Series],
    ) -> pd.DataFrame:
        """
        Combine multiple series into a feature matrix.

        Args:
            series_dict: Dictionary of series names to Series objects

        Returns:
            DataFrame with all combined features
        """
        features = pd.DataFrame()

        for name, series in series_dict.items():
            features[name] = series
            features = pd.concat([
                features,
                EconomicFeatureEngineer.create_lag_features(series),
            ], axis=1)
            features = pd.concat([
                features,
                EconomicFeatureEngineer.create_rolling_features(series),
            ], axis=1)
            features = pd.concat([
                features,
                EconomicFeatureEngineer.create_rate_of_change(series),
            ], axis=1)

        # Drop rows with NaN values
        features = features.dropna()

        return features


class EconomicsPredictionModel:
    """
    XGBoost model for predicting economic outcomes.

    Predicts:
    - P(CPI > 3.5%)
    - P(Rate cut at next meeting)
    - P(Unemployment > threshold)
    - P(GDP > threshold)
    """

    def __init__(self, model_name: str = "cpi_predictor"):
        """Initialize the prediction model."""
        self.model_name = model_name
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = None
        self.threshold = None
        self.model_path = f"/tmp/{model_name}_model.pkl"
        self.scaler_path = f"/tmp/{model_name}_scaler.pkl"

    def prepare_training_data(
        self,
        features: pd.DataFrame,
        target_series: pd.Series,
        threshold: float,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare data for training.

        Args:
            features: Feature matrix
            target_series: Target time series
            threshold: Threshold for binary classification

        Returns:
            (X, y) arrays
        """
        # Align indices
        common_index = features.index.intersection(target_series.index)
        features = features.loc[common_index]
        target = target_series.loc[common_index]

        # Create binary target: 1 if value > threshold, 0 otherwise
        y = (target > threshold).astype(int).values

        # Scale features
        X = self.scaler.fit_transform(features)

        self.feature_names = features.columns.tolist()
        self.threshold = threshold

        return X, y

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> Dict:
        """
        Train XGBoost model.

        Args:
            X: Feature matrix
            y: Target labels
            test_size: Test set fraction
            random_state: Random seed

        Returns:
            Dictionary with training metrics
        """
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )

        # Train model
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=random_state,
            eval_metric="logloss",
        )

        self.model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False,
        )

        # Evaluate
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        auc_score = roc_auc_score(y_test, y_pred_proba)
        brier = brier_score_loss(y_test, y_pred_proba)

        metrics = {
            "auc": float(auc_score),
            "brier_score": float(brier),
            "train_size": len(X_train),
            "test_size": len(X_test),
            "threshold": self.threshold,
        }

        logger.info(f"Model {self.model_name} trained: AUC={auc_score:.4f}")

        return metrics

    def predict_probability(self, features: pd.DataFrame) -> float:
        """
        Predict probability of outcome.

        Args:
            features: Feature matrix (same features as training)

        Returns:
            Probability estimate (0-1)
        """
        if self.model is None:
            logger.error("Model not trained yet")
            return None

        # Scale features
        X = self.scaler.transform(features[[col for col in features.columns if col in self.feature_names]])

        # Predict probability
        proba = self.model.predict_proba(X)[:, 1]

        return float(proba[0]) if len(proba) > 0 else None

    def save_model(self):
        """Save model and scaler to disk."""
        if self.model is not None:
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            logger.info(f"Model saved to {self.model_path}")

    def load_model(self):
        """Load model and scaler from disk."""
        try:
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
            logger.info(f"Model loaded from {self.model_path}")
        except FileNotFoundError:
            logger.warning(f"Model file not found at {self.model_path}")


class MarketPriceProvider:
    """Integrates with Polymarket and Kalshi for market prices."""

    @staticmethod
    def fetch_polymarket_price(market_question: str) -> Optional[Dict]:
        """
        Fetch Polymarket prediction price for a question.

        Args:
            market_question: Market question text (e.g., "Will CPI be above 3.5%?")

        Returns:
            Dict with price, volume, liquidity
        """
        try:
            # Polymarket API endpoint (simplified - would need actual API key)
            headers = {
                "accept": "application/json",
            }

            # Search for market
            url = "https://api.polymarket.com/markets"
            params = {"q": market_question, "active": True}

            response = requests.get(url, params=params, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data:
                    market = data[0]
                    return {
                        "source": "polymarket",
                        "market_id": market.get("id"),
                        "price": float(market.get("bid", 0.5)),  # Mid price
                        "bid": float(market.get("bid", 0.5)),
                        "ask": float(market.get("ask", 0.5)),
                        "volume_24h": market.get("volume_24h", 0),
                    }

            return None

        except Exception as e:
            logger.error(f"Error fetching Polymarket price: {e}")
            return None

    @staticmethod
    def fetch_kalshi_price(event_slug: str) -> Optional[Dict]:
        """
        Fetch Kalshi prediction market price.

        Args:
            event_slug: Kalshi event slug

        Returns:
            Dict with price, volume
        """
        try:
            # Kalshi API (simplified - would need API credentials)
            url = f"https://api.kalshi.com/events/{event_slug}"

            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return {
                    "source": "kalshi",
                    "event_slug": event_slug,
                    "price": float(data.get("market_price", 0.5)),
                    "bid": float(data.get("bid_price", 0.5)),
                    "ask": float(data.get("ask_price", 0.5)),
                    "volume": data.get("volume", 0),
                }

            return None

        except Exception as e:
            logger.error(f"Error fetching Kalshi price: {e}")
            return None


class EdgeCalculator:
    """Calculates edge: predicted probability vs market probability."""

    @staticmethod
    def calculate_edge(
        predicted_probability: float,
        market_probability: float,
    ) -> Dict:
        """
        Calculate betting edge.

        Args:
            predicted_probability: Model prediction (0-1)
            market_probability: Market implied probability (0-1)

        Returns:
            Dict with edge metrics
        """
        edge = predicted_probability - market_probability
        edge_pct = (edge / market_probability) * 100 if market_probability > 0 else 0

        # Expected value calculation
        # If we bet YES: EV = predicted_prob * (1/market_prob - 1) - (1 - predicted_prob)
        if market_probability > 0 and market_probability < 1:
            implied_odds = (1 - market_probability) / market_probability
            ev_yes = predicted_probability * implied_odds - (1 - predicted_probability)
            ev_no = (1 - predicted_probability) * (market_probability / (1 - market_probability)) - predicted_probability
        else:
            ev_yes = ev_no = 0

        return {
            "edge": edge,
            "edge_pct": edge_pct,
            "ev_yes": ev_yes,
            "ev_no": ev_no,
            "best_side": "YES" if ev_yes > ev_no else "NO",
            "kelly_fraction": EdgeCalculator._kelly_fraction(ev_yes, market_probability),
        }

    @staticmethod
    def _kelly_fraction(ev: float, market_prob: float) -> float:
        """
        Calculate Kelly criterion fraction.

        Formula: f = (p * b - q) / b
        Where p = probability of win, q = 1-p, b = odds
        """
        if market_prob <= 0 or market_prob >= 1:
            return 0

        b = (1 - market_prob) / market_prob
        f = (market_prob * b - (1 - market_prob)) / b if b > 0 else 0

        # Cap at 25% Kelly for safety
        return max(0, min(f, 0.25))


class FedEconomicsPredictor:
    """
    Main orchestrator for Fed/Economics predictions.

    Coordinates FRED data, feature engineering, model training,
    market price integration, and edge calculation.
    """

    def __init__(self, fred_api_key: Optional[str] = None):
        """Initialize the predictor."""
        self.fred = FREDDataProvider(fred_api_key)
        self.engineer = EconomicFeatureEngineer()
        self.models = {}
        self.market_prices = {}

    def setup_cpi_predictor(self, threshold: float = 3.5) -> Dict:
        """
        Setup and train CPI predictor model.

        Args:
            threshold: CPI threshold for classification

        Returns:
            Training metrics
        """
        logger.info("Setting up CPI predictor...")

        # Fetch data
        cpi = self.fred.fetch_series("CPIAUCSL")
        pce = self.fred.fetch_series("PCEPI")
        fedfunds = self.fred.fetch_series("FEDFUNDS")

        if cpi.empty or pce.empty:
            logger.error("Could not fetch CPI data")
            return {}

        # Create features
        series_dict = {
            "cpi": cpi["value"],
            "pce": pce["value"],
            "fedfunds": fedfunds["value"],
        }

        features = self.engineer.combine_features(series_dict)

        # Train model
        model = EconomicsPredictionModel("cpi_predictor")
        X, y = model.prepare_training_data(features, cpi["value"], threshold)
        metrics = model.train(X, y)
        model.save_model()

        self.models["cpi"] = model

        return metrics

    def setup_rate_cut_predictor(self) -> Dict:
        """
        Setup and train rate cut predictor model.

        Returns:
            Training metrics
        """
        logger.info("Setting up rate cut predictor...")

        # Fetch data
        fedfunds = self.fred.fetch_series("FEDFUNDS")
        unemployment = self.fred.fetch_series("UNRATE")
        cpi = self.fred.fetch_series("CPIAUCSL")

        if fedfunds.empty:
            logger.error("Could not fetch Fed Funds data")
            return {}

        # Create target: 1 if next month's rate is lower
        target = (fedfunds["value"].shift(-1) < fedfunds["value"]).astype(int)

        # Create features
        series_dict = {
            "fedfunds": fedfunds["value"],
            "unemployment": unemployment["value"],
            "cpi": cpi["value"],
        }

        features = self.engineer.combine_features(series_dict)

        # Train model
        model = EconomicsPredictionModel("rate_cut_predictor")
        X = model.scaler.fit_transform(features)
        y = target.loc[features.index].values
        model.feature_names = features.columns.tolist()

        metrics = model.train(X, y)
        model.save_model()

        self.models["rate_cut"] = model

        return metrics

    def predict_cpi(
        self,
        threshold: float = 3.5,
        market_price: Optional[float] = None,
    ) -> Dict:
        """
        Predict CPI probability.

        Args:
            threshold: CPI threshold
            market_price: Market probability from Polymarket/Kalshi

        Returns:
            Prediction dict with probability and edge
        """
        # Fetch latest data
        cpi = self.fred.fetch_series("CPIAUCSL", start_date=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"))
        pce = self.fred.fetch_series("PCEPI", start_date=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"))
        fedfunds = self.fred.fetch_series("FEDFUNDS", start_date=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"))

        if cpi.empty:
            return {"error": "Could not fetch CPI data"}

        # Create features
        series_dict = {
            "cpi": cpi["value"],
            "pce": pce["value"],
            "fedfunds": fedfunds["value"],
        }

        features = self.engineer.combine_features(series_dict)

        # Get latest row for prediction
        latest_features = features.iloc[[-1]]

        # Load or train model
        if "cpi" not in self.models:
            self.setup_cpi_predictor(threshold)

        model = self.models["cpi"]
        predicted_prob = model.predict_probability(latest_features)

        # Get market price if not provided
        if market_price is None:
            market_data = MarketPriceProvider.fetch_polymarket_price(
                f"Will CPI be above {threshold}% next month?"
            )
            market_price = market_data.get("price", 0.5) if market_data else 0.5

        # Calculate edge
        edge_data = EdgeCalculator.calculate_edge(predicted_prob, market_price)

        return {
            "metric": "CPI",
            "threshold": threshold,
            "predicted_probability": predicted_prob,
            "market_probability": market_price,
            "latest_value": float(cpi["value"].iloc[-1]),
            "edge": edge_data,
            "timestamp": datetime.now().isoformat(),
        }

    def predict_rate_cut(self, market_price: Optional[float] = None) -> Dict:
        """
        Predict probability of rate cut at next meeting.

        Args:
            market_price: Market probability

        Returns:
            Prediction dict
        """
        # Load or train model
        if "rate_cut" not in self.models:
            self.setup_rate_cut_predictor()

        # Fetch latest data
        fedfunds = self.fred.fetch_series("FEDFUNDS", start_date=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"))
        unemployment = self.fred.fetch_series("UNRATE", start_date=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"))
        cpi = self.fred.fetch_series("CPIAUCSL", start_date=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"))

        if fedfunds.empty:
            return {"error": "Could not fetch Fed Funds data"}

        # Create features
        series_dict = {
            "fedfunds": fedfunds["value"],
            "unemployment": unemployment["value"],
            "cpi": cpi["value"],
        }

        features = self.engineer.combine_features(series_dict)
        latest_features = features.iloc[[-1]]

        model = self.models["rate_cut"]
        predicted_prob = model.predict_probability(latest_features)

        # Get market price
        if market_price is None:
            market_data = MarketPriceProvider.fetch_polymarket_price(
                "Will Fed cut rates at next FOMC meeting?"
            )
            market_price = market_data.get("price", 0.5) if market_data else 0.5

        # Calculate edge
        edge_data = EdgeCalculator.calculate_edge(predicted_prob, market_price)

        # Get next meeting info
        next_meeting = FedMeetingCalendar.get_next_meeting()

        return {
            "metric": "Rate Cut",
            "predicted_probability": predicted_prob,
            "market_probability": market_price,
            "next_meeting": next_meeting,
            "current_rate": float(fedfunds["value"].iloc[-1]) if not fedfunds.empty else None,
            "edge": edge_data,
            "timestamp": datetime.now().isoformat(),
        }

    def get_economic_calendar(self) -> Dict:
        """Get upcoming economic events and releases."""
        return self.fred.get_economic_calendar()

    def get_fomc_calendar(self) -> List[Dict]:
        """Get FOMC meeting schedule."""
        return FedMeetingCalendar.fetch_fomc_meetings()
