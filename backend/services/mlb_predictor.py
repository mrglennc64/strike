"""
MLB Strikeout Predictor - Poisson Regression Engine

Integrates Statcast data with Poisson regression to predict strikeout probabilities.
Compares predictions to DraftKings/FanDuel odds and calculates edges.

Features:
- Statcast data integration via DuckDB
- Poisson regression for lambda parameter
- P(Over line) calculation via Poisson CDF
- Real-time odds comparison
- Edge detection and filtering
- Backtesting infrastructure
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple, Any
import logging

import pandas as pd
import numpy as np
import duckdb
from scipy.stats import poisson
from sklearn.linear_model import PoissonRegressor
from sklearn.preprocessing import StandardScaler
import warnings

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class StatcastDataLoader:
    """Load and preprocess Statcast data from DuckDB."""

    def __init__(self, db_path: str = 'data/baseball.duckdb'):
        """Initialize DuckDB connection."""
        self.db_path = Path(db_path)
        self.con = duckdb.connect(str(self.db_path), read_only=True)

    def load_pitcher_games(
        self,
        start_date: str,
        end_date: str,
        min_batters_faced: int = 3
    ) -> pd.DataFrame:
        """
        Load pitcher-game data from Statcast.

        Returns:
            DataFrame with columns: game_date, game_pk, pitcher_id, pitcher_name,
                                   pitcher_team, opponent_team, batters_faced, strikeouts
        """
        try:
            query = f"""
            SELECT
                game_date,
                game_pk,
                pitcher,
                home_team,
                away_team,
                COUNT(DISTINCT at_bat_number) as batters_faced,
                SUM(CASE WHEN events LIKE '%strikeout%' THEN 1 ELSE 0 END) as strikeouts
            FROM pa_events
            WHERE game_date >= '{start_date}'
                AND game_date <= '{end_date}'
                AND pitcher IS NOT NULL
            GROUP BY game_date, game_pk, pitcher, home_team, away_team
            HAVING COUNT(DISTINCT at_bat_number) >= {min_batters_faced}
            ORDER BY game_date, game_pk, pitcher
            """

            df_raw = self.con.execute(query).fetchdf()
            logger.info(f"Loaded {len(df_raw)} pitcher-game records")

            if df_raw.empty:
                return pd.DataFrame()

            # Get pitcher names
            pitcher_names = self.con.execute("""
                SELECT DISTINCT player_id, name
                FROM pitchers
                WHERE season = 2026
            """).fetchdf()

            df = df_raw.merge(
                pitcher_names,
                left_on='pitcher',
                right_on='player_id',
                how='left'
            )

            df['pitcher_name'] = df['name'].fillna('Unknown')
            df['pitcher_id'] = df['pitcher'].astype(int)

            # Determine pitcher team and opponent
            pitcher_teams = self.con.execute("""
                SELECT DISTINCT pitcher, home_team
                FROM pa_events
                WHERE game_date >= '2026-06-01'
                    AND pitcher IS NOT NULL
                LIMIT 10000
            """).fetchdf()

            pitcher_team_map = {}
            for _, row in pitcher_teams.iterrows():
                pid = int(row['pitcher'])
                if pid not in pitcher_team_map:
                    pitcher_team_map[pid] = row['home_team']

            df['pitcher_team'] = df['pitcher_id'].map(pitcher_team_map)

            df['pitcher_actual_team'] = df.apply(
                lambda row: row['home_team']
                if row['pitcher_team'] == row['home_team']
                else row['away_team'],
                axis=1
            )

            df['opponent_team'] = df.apply(
                lambda row: row['away_team']
                if row['pitcher_actual_team'] == row['home_team']
                else row['home_team'],
                axis=1
            )

            return df[[
                'game_date', 'game_pk', 'pitcher_id', 'pitcher_name',
                'pitcher_team', 'opponent_team', 'batters_faced', 'strikeouts'
            ]].reset_index(drop=True)

        except Exception as e:
            logger.error(f"Error loading pitcher games: {e}")
            return pd.DataFrame()

    def get_today_probables(self) -> pd.DataFrame:
        """Get today's probable pitchers from schedule."""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

            query = f"""
            SELECT DISTINCT
                game_date,
                home_team,
                away_team,
                home_probable_pitcher,
                away_probable_pitcher
            FROM games
            WHERE game_date >= '{today}'
                AND game_date <= '{tomorrow}'
                AND (home_probable_pitcher IS NOT NULL
                     OR away_probable_pitcher IS NOT NULL)
            """

            df = self.con.execute(query).fetchdf()
            return df if not df.empty else pd.DataFrame()

        except Exception as e:
            logger.error(f"Error loading today's probables: {e}")
            return pd.DataFrame()


class PoissonStrikeoutEngine:
    """Poisson regression engine for strikeout prediction."""

    def __init__(self, db_path: str = 'data/baseball.duckdb'):
        """Initialize the engine."""
        self.loader = StatcastDataLoader(db_path)
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = None
        self.trained = False

    def build_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Build feature matrix for Poisson regression.

        Features:
        - Pitcher K rate (rolling average from previous games)
        - Opponent team dummies
        - Game sequence (normalized)
        """
        df = df.copy()
        df['game_date'] = pd.to_datetime(df['game_date'])
        df = df.sort_values('game_date').reset_index(drop=True)

        # One-hot encode opponent team
        opponent_dummies = pd.get_dummies(df['opponent_team'], prefix='opp', drop_first=False)
        df = pd.concat([df, opponent_dummies], axis=1)

        # Pitcher rolling K rate (from previous games only)
        df['pitcher_k_rate'] = 0.0
        df['pitcher_game_count'] = 0

        for i in range(len(df)):
            pitcher_id = df.loc[i, 'pitcher_id']
            prev_mask = (df['pitcher_id'] == pitcher_id) & (df.index < i)

            if prev_mask.sum() > 0:
                prev_games = df.loc[prev_mask]
                k_rate = prev_games['strikeouts'].sum() / prev_games['batters_faced'].sum()
                df.loc[i, 'pitcher_k_rate'] = k_rate
                df.loc[i, 'pitcher_game_count'] = prev_mask.sum()

        # Standardize features
        df['pitcher_kr_z'] = (df['pitcher_k_rate'] - df['pitcher_k_rate'].mean()) / (df['pitcher_k_rate'].std() + 1e-6)
        df['pitcher_kr_z'].fillna(0, inplace=True)

        # Game sequence
        df['game_seq'] = range(len(df))
        df['game_seq_z'] = (df['game_seq'] - df['game_seq'].mean()) / (df['game_seq'].std() + 1e-6)

        return df

    def train(self, df_train: pd.DataFrame) -> None:
        """Train Poisson regression model."""
        feature_cols = [col for col in df_train.columns
                       if col.startswith('opp_') or col.endswith('_z')]

        X = df_train[feature_cols].fillna(0)
        y = df_train['strikeouts'].astype(int)

        self.feature_names = feature_cols

        X_scaled = self.scaler.fit_transform(X)

        self.model = PoissonRegressor(
            alpha=0.01,
            max_iter=1000,
            solver='lbfgs'
        )
        self.model.fit(X_scaled, y)

        self.trained = True
        logger.info(f"Model trained on {len(df_train)} records")

    def predict_lambda(self, df_test: pd.DataFrame) -> np.ndarray:
        """Predict lambda (expected strikeouts)."""
        if not self.trained or self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        feature_cols = [col for col in df_test.columns
                       if col.startswith('opp_') or col.endswith('_z')]

        X = df_test[feature_cols].fillna(0)
        X_scaled = self.scaler.transform(X)

        return self.model.predict(X_scaled)

    def calculate_probabilities(
        self,
        lambda_pred: np.ndarray,
        line: float = 5.5
    ) -> Dict[str, np.ndarray]:
        """
        Calculate P(Over|line) using Poisson CDF.

        Args:
            lambda_pred: Predicted lambda values
            line: Strikeout line (e.g., 5.5)

        Returns:
            Dictionary with model_prob, book_prob, edge_pct
        """
        model_probs = []

        for lam in lambda_pred:
            prob_over = 1 - poisson.cdf(int(np.floor(line)), lam)
            model_probs.append(prob_over)

        model_probs = np.array(model_probs)

        # DraftKings/FanDuel implied probability for -110 odds
        book_prob = 110 / 210  # ~0.524

        edge_pct = (model_probs - book_prob) * 100

        return {
            'model_prob': model_probs,
            'book_prob': book_prob,
            'edge_pct': edge_pct
        }


class DraftKingsOddsClient:
    """Fetch and manage DraftKings odds for MLB strikeouts."""

    def __init__(self):
        """Initialize DraftKings client."""
        self.base_url = "https://api.draftkings.com/graphql"
        self.session_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'application/json',
        }

    def get_strikeout_lines(self) -> Dict[str, Any]:
        """
        Fetch current MLB strikeout lines from DraftKings.

        Returns:
            Dictionary mapping pitcher_name -> {line, over_odds, under_odds}
        """
        try:
            import requests

            # This is a simplified approach - actual DraftKings API requires authentication
            # For production, use official SDK or authenticated endpoints
            logger.info("Fetching DraftKings odds (mock implementation)")

            # Mock response - replace with actual API calls
            return {
                "Reid Detmers": {
                    "line": 6.5,
                    "over_odds": -110,
                    "under_odds": -110,
                    "implied_prob_over": 0.524
                }
            }

        except Exception as e:
            logger.error(f"Error fetching DraftKings odds: {e}")
            return {}

    def get_fanduel_lines(self) -> Dict[str, Any]:
        """Fetch current MLB strikeout lines from FanDuel."""
        try:
            # Similar to DraftKings
            logger.info("Fetching FanDuel odds (mock implementation)")
            return {}
        except Exception as e:
            logger.error(f"Error fetching FanDuel odds: {e}")
            return {}


class MLBStrikeoutPredictor:
    """
    Complete MLB Strikeout Predictor pipeline.

    Combines Statcast data, Poisson regression, and bookmaker odds
    to identify edges in strikeout markets.
    """

    def __init__(self, db_path: str = 'data/baseball.duckdb'):
        """Initialize the predictor."""
        self.engine = PoissonStrikeoutEngine(db_path)
        self.odds_client = DraftKingsOddsClient()
        self.last_trained = None

    def train_on_historical(
        self,
        start_date: str = '2026-06-01',
        train_end_date: str = '2026-06-10'
    ) -> bool:
        """Train model on historical data."""
        try:
            df_full = self.engine.loader.load_pitcher_games(start_date, train_end_date)

            if df_full.empty:
                logger.error("No data loaded for training")
                return False

            df_features = self.engine.build_features(df_full)

            # Use all data as training
            self.engine.train(df_features)
            self.last_trained = datetime.now()

            logger.info(f"Model trained successfully at {self.last_trained}")
            return True

        except Exception as e:
            logger.error(f"Error training model: {e}")
            return False

    def predict_today(
        self,
        line: float = 5.5,
        edge_threshold: float = 8.0
    ) -> List[Dict[str, Any]]:
        """
        Generate predictions for today's games.

        Returns:
            List of predictions with pitcher, line, model%, book%, edge%
        """
        if not self.engine.trained:
            logger.error("Model not trained. Call train_on_historical() first.")
            return []

        try:
            # Get today's probable pitchers
            probables = self.engine.loader.get_today_probables()

            if probables.empty:
                logger.info("No games scheduled for today")
                return []

            # Get recent stats for each pitcher to build features
            today = datetime.now().strftime('%Y-%m-%d')
            recent_data = self.engine.loader.load_pitcher_games(
                start_date='2026-06-01',
                end_date=today
            )

            if recent_data.empty:
                return []

            df_features = self.engine.build_features(recent_data)

            # Filter to recent games only (last 10 days)
            recent_cutoff = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
            df_recent = df_features[df_features['game_date'] >= recent_cutoff].copy()

            if df_recent.empty:
                return []

            # Predict lambda for recent games
            lambda_pred = self.engine.predict_lambda(df_recent)
            probs = self.engine.calculate_probabilities(lambda_pred, line=line)

            df_recent['lambda'] = lambda_pred
            df_recent['model_prob'] = probs['model_prob']
            df_recent['edge_pct'] = probs['edge_pct']

            # Get DraftKings lines
            dk_lines = self.odds_client.get_strikeout_lines()

            # Format predictions
            predictions = []

            for _, row in df_recent.iterrows():
                pitcher_name = row['pitcher_name']

                dk_info = dk_lines.get(pitcher_name, {})
                if not dk_info:
                    continue

                line_actual = dk_info.get('line', line)
                book_prob = dk_info.get('implied_prob_over', 0.524)

                edge_pct = (row['model_prob'] - book_prob) * 100

                if abs(edge_pct) >= edge_threshold:
                    predictions.append({
                        'pitcher_id': int(row['pitcher_id']),
                        'pitcher_name': pitcher_name,
                        'opponent': row['opponent_team'],
                        'game_date': str(row['game_date'].date()),
                        'strikeout_line': line_actual,
                        'model_prob': round(float(row['model_prob']), 3),
                        'model_prob_pct': round(float(row['model_prob']) * 100, 1),
                        'book_prob': round(book_prob, 3),
                        'book_prob_pct': round(book_prob * 100, 1),
                        'edge_pct': round(edge_pct, 2),
                        'lambda': round(float(row['lambda']), 2),
                        'batters_faced': int(row['batters_faced']),
                        'direction': 'OVER' if row['model_prob'] > book_prob else 'UNDER',
                        'confidence': round(abs(row['model_prob'] - 0.5) * 100, 1)
                    })

            # Sort by edge
            predictions.sort(key=lambda x: abs(x['edge_pct']), reverse=True)

            logger.info(f"Generated {len(predictions)} predictions with edge > {edge_threshold}%")
            return predictions

        except Exception as e:
            logger.error(f"Error generating predictions: {e}")
            return []

    def backtest(
        self,
        start_date: str = '2026-06-15',
        end_date: str = '2026-06-27',
        line: float = 5.5,
        edge_threshold: float = 8.0,
        confidence_threshold: float = 70.0
    ) -> Dict[str, Any]:
        """Backtest model on historical period."""
        try:
            df_full = self.engine.loader.load_pitcher_games(start_date, end_date)

            if df_full.empty:
                return {'error': 'No data for backtest period'}

            df_features = self.engine.build_features(df_full)

            lambda_pred = self.engine.predict_lambda(df_features)
            probs = self.engine.calculate_probabilities(lambda_pred, line=line)

            df_features['lambda'] = lambda_pred
            df_features['model_prob'] = probs['model_prob']
            df_features['edge_pct'] = probs['edge_pct']
            df_features['confidence'] = np.abs(df_features['model_prob'] - 0.5) * 100

            # Apply filters
            df_bets = df_features[
                (np.abs(df_features['edge_pct']) > edge_threshold) &
                (df_features['confidence'] > confidence_threshold)
            ].copy()

            if df_bets.empty:
                return {
                    'num_plays': 0,
                    'reason': f'No plays passed filters'
                }

            # Calculate outcomes
            df_bets['actual_over'] = df_bets['strikeouts'] > line
            df_bets['predicted_over'] = df_bets['model_prob'] > 0.5
            df_bets['correct'] = df_bets['actual_over'] == df_bets['predicted_over']

            wins = df_bets['correct'].sum()
            losses = len(df_bets) - wins
            win_rate = (wins / len(df_bets)) * 100 if len(df_bets) > 0 else 0

            total_profit = (wins * 100) - (losses * 110)
            total_wagered = len(df_bets) * 110
            roi = (total_profit / total_wagered) * 100 if total_wagered > 0 else 0

            return {
                'num_plays': len(df_bets),
                'wins': wins,
                'losses': losses,
                'win_rate': round(win_rate, 1),
                'roi': round(roi, 1),
                'total_profit': int(total_profit),
                'avg_edge_pct': round(df_bets['edge_pct'].mean(), 2)
            }

        except Exception as e:
            logger.error(f"Error in backtest: {e}")
            return {'error': str(e)}
