#!/usr/bin/env python3
"""
MLB Strikeout Predictor - API Client Library

Simple client for interacting with the MLBStrikeoutPredictor REST API.

Usage:
    client = MLBPredictorClient()
    predictions = client.get_today_predictions(line=5.5, min_edge=8.0)
"""

from typing import List, Dict, Optional, Any
import httpx
import json
from datetime import datetime


class MLBPredictorClient:
    """HTTP client for MLB Strikeout Predictor API."""

    def __init__(self, base_url: str = "http://localhost:8000/api/verticals/mlb"):
        """
        Initialize the client.

        Args:
            base_url: Base URL of the API endpoint
        """
        self.base_url = base_url
        self.client = httpx.Client(timeout=30.0)

    def __del__(self):
        """Clean up HTTP client."""
        if hasattr(self, 'client'):
            self.client.close()

    def health_check(self) -> Dict[str, Any]:
        """Check API health and model status."""
        response = self.client.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def get_status(self) -> Dict[str, Any]:
        """Get detailed model status."""
        response = self.client.get(f"{self.base_url}/status")
        response.raise_for_status()
        return response.json()

    def train_model(
        self,
        start_date: str = "2026-06-01",
        end_date: str = "2026-06-10",
        force_retrain: bool = False
    ) -> Dict[str, Any]:
        """
        Train or retrain the model.

        Args:
            start_date: Training start date (YYYY-MM-DD)
            end_date: Training end date (YYYY-MM-DD)
            force_retrain: Force retrain even if already trained

        Returns:
            Model status response
        """
        response = self.client.post(
            f"{self.base_url}/train",
            json={
                "start_date": start_date,
                "end_date": end_date,
                "force_retrain": force_retrain
            }
        )
        response.raise_for_status()
        return response.json()

    def get_today_predictions(
        self,
        strikeout_line: float = 5.5,
        min_edge: float = 8.0
    ) -> List[Dict[str, Any]]:
        """
        Get today's strikeout predictions.

        Args:
            strikeout_line: Strikeout line to predict (e.g., 5.5)
            min_edge: Minimum edge percentage to return

        Returns:
            List of predictions with format:
            {
                'pitcher_id': int,
                'pitcher_name': str,
                'opponent': str,
                'game_date': str,
                'strikeout_line': float,
                'model_prob': float (0-1),
                'model_prob_pct': float,
                'book_prob': float (0-1),
                'book_prob_pct': float,
                'edge_pct': float,
                'lambda': float,
                'batters_faced': int,
                'direction': str ('OVER' or 'UNDER'),
                'confidence': float
            }
        """
        response = self.client.get(
            f"{self.base_url}/predictions/today",
            params={
                "strikeout_line": strikeout_line,
                "min_edge": min_edge
            }
        )
        response.raise_for_status()
        data = response.json()
        return data.get('predictions', [])

    def get_predictions(
        self,
        strikeout_line: float = 5.5,
        edge_threshold: float = 8.0
    ) -> Dict[str, Any]:
        """Get full predictions response with metadata."""
        response = self.client.post(
            f"{self.base_url}/predict",
            json={
                "strikeout_line": strikeout_line,
                "edge_threshold": edge_threshold
            }
        )
        response.raise_for_status()
        return response.json()

    def backtest(
        self,
        start_date: str = "2026-06-15",
        end_date: str = "2026-06-27",
        strikeout_line: float = 5.5,
        edge_threshold: float = 8.0,
        confidence_threshold: float = 70.0
    ) -> Dict[str, Any]:
        """
        Run backtest analysis on historical period.

        Args:
            start_date: Backtest start date
            end_date: Backtest end date
            strikeout_line: Strikeout line
            edge_threshold: Minimum edge % to trade
            confidence_threshold: Minimum confidence %

        Returns:
            {
                'num_plays': int,
                'wins': int,
                'losses': int,
                'win_rate': float,
                'roi': float,
                'total_profit': int,
                'avg_edge_pct': float,
                'timestamp': str
            }
        """
        response = self.client.post(
            f"{self.base_url}/backtest",
            json={
                "start_date": start_date,
                "end_date": end_date,
                "strikeout_line": strikeout_line,
                "edge_threshold": edge_threshold,
                "confidence_threshold": confidence_threshold
            }
        )
        response.raise_for_status()
        return response.json()

    def compare_odds(
        self,
        strikeout_line: float = 5.5
    ) -> List[Dict[str, Any]]:
        """
        Compare model predictions with bookmaker odds.

        Returns:
            List of odds comparisons with DraftKings and FanDuel
        """
        response = self.client.post(
            f"{self.base_url}/compare-odds",
            params={"strikeout_line": strikeout_line}
        )
        response.raise_for_status()
        return response.json()

    def get_pitcher_stats(self, pitcher_id: int) -> Dict[str, Any]:
        """Get strikeout statistics for a specific pitcher."""
        response = self.client.get(f"{self.base_url}/pitcher/{pitcher_id}")
        response.raise_for_status()
        return response.json()

    def format_prediction(self, pred: Dict[str, Any]) -> str:
        """
        Format a prediction for display.

        Example output:
        Reid Detmers | Over 6.5 | Model 65% | Book 54% | Edge +11%
        """
        return (
            f"{pred['pitcher_name']} | "
            f"{pred['direction']} {pred['strikeout_line']} | "
            f"Model {pred['model_prob_pct']:.1f}% | "
            f"Book {pred['book_prob_pct']:.1f}% | "
            f"Edge {pred['edge_pct']:+.1f}%"
        )

    def print_predictions(
        self,
        strikeout_line: float = 5.5,
        min_edge: float = 8.0,
        max_results: Optional[int] = None
    ):
        """Print formatted predictions to console."""
        predictions = self.get_today_predictions(
            strikeout_line=strikeout_line,
            min_edge=min_edge
        )

        if not predictions:
            print("No predictions found")
            return

        if max_results:
            predictions = predictions[:max_results]

        print("\n" + "="*100)
        print(f"MLB STRIKEOUT PREDICTIONS ({len(predictions)} plays)")
        print("="*100)

        for pred in predictions:
            print(self.format_prediction(pred))

        print("="*100)

    def print_backtest(
        self,
        start_date: str = "2026-06-15",
        end_date: str = "2026-06-27"
    ):
        """Print backtest results."""
        results = self.backtest(start_date=start_date, end_date=end_date)

        if 'error' in results:
            print(f"Backtest Error: {results['error']}")
            return

        print("\n" + "="*80)
        print(f"BACKTEST RESULTS ({start_date} to {end_date})")
        print("="*80)
        print(f"Plays Released: {results['num_plays']}")
        print(f"Win Rate: {results['win_rate']:.1f}%")
        print(f"ROI: {results['roi']:+.1f}%")
        print(f"Wins/Losses: {results['wins']}/{results['losses']}")
        print(f"Total Profit: ${results['total_profit']:+d}")
        print(f"Average Edge: {results['avg_edge_pct']:.2f}%")
        print("="*80)


def main():
    """Example usage."""
    # Initialize client
    client = MLBPredictorClient()

    try:
        # Check health
        print("Checking API health...")
        health = client.health_check()
        print(f"✓ API Status: {health['status']}")
        print(f"  Model Trained: {health['model_trained']}")

        # Get status
        status = client.get_status()
        print(f"\n✓ Model Status:")
        print(f"  Trained: {status['trained']}")
        print(f"  Records: {status['training_data_records']:,}")
        print(f"  Pitchers: {status['unique_pitchers']}")

        # Get today's predictions
        print(f"\n✓ Fetching predictions...")
        predictions = client.get_today_predictions(
            strikeout_line=5.5,
            min_edge=8.0
        )

        if predictions:
            print(f"  Found {len(predictions)} predictions\n")
            for pred in predictions[:5]:
                print(f"  {client.format_prediction(pred)}")

            if len(predictions) > 5:
                print(f"  ... and {len(predictions) - 5} more")
        else:
            print("  No predictions with edge > 8%")

        # Run backtest
        print(f"\n✓ Running backtest...")
        results = client.backtest()
        if 'num_plays' in results:
            print(f"  Plays: {results['num_plays']}")
            print(f"  Win Rate: {results['win_rate']:.1f}%")
            print(f"  ROI: {results['roi']:+.1f}%")

    except httpx.ConnectError:
        print("✗ Could not connect to API. Is the server running?")
        print("  Start server with: python -m uvicorn main:app --reload")
    except Exception as e:
        print(f"✗ Error: {e}")


if __name__ == "__main__":
    main()
