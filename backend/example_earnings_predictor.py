#!/usr/bin/env python3
"""
Example client for Earnings Predictor API

Usage:
    python example_earnings_predictor.py

This demonstrates:
1. Single stock prediction
2. Multi-stock edge scanning
3. Prediction history retrieval
4. Model performance backtesting
5. Historical earnings data
"""

import asyncio
import json
from datetime import datetime
from typing import List

import httpx

# API base URL
BASE_URL = "http://localhost:8000/api/verticals/earnings"


class EarningsPredictorClient:
    """Client for earnings predictor API."""

    def __init__(self, base_url: str = BASE_URL, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.client = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def predict_earnings(self, symbol: str) -> dict:
        """
        Predict earnings beat/miss for a single stock.

        Args:
            symbol: Stock ticker (e.g., "TSLA")

        Returns:
            EarningsPredictionResponse
        """
        response = await self.client.post("/predict", json={"symbol": symbol})
        response.raise_for_status()
        return response.json()

    async def scan_edges(self, symbols: List[str], min_edge_pct: float = 5.0) -> dict:
        """
        Scan multiple stocks for earnings edges.

        Args:
            symbols: List of stock tickers
            min_edge_pct: Minimum edge % to include in results

        Returns:
            EdgeScanResponse
        """
        payload = {
            "symbols": symbols,
            "min_edge_pct": min_edge_pct,
            "only_with_edge": True,
        }
        response = await self.client.post("/scan", json=payload)
        response.raise_for_status()
        return response.json()

    async def get_latest_prediction(self, symbol: str) -> dict:
        """
        Get the latest prediction for a symbol.

        Args:
            symbol: Stock ticker

        Returns:
            EarningsPredictionRecordResponse
        """
        response = await self.client.get(f"/{symbol}")
        response.raise_for_status()
        return response.json()

    async def get_prediction_history(self, symbol: str, limit: int = 20) -> dict:
        """
        Get prediction history for a symbol.

        Args:
            symbol: Stock ticker
            limit: Number of predictions to return

        Returns:
            EarningsPredictionListResponse
        """
        response = await self.client.get(f"/{symbol}/history", params={"limit": limit})
        response.raise_for_status()
        return response.json()

    async def get_earnings_history(self, symbol: str, periods: int = 20) -> list:
        """
        Get historical earnings data.

        Args:
            symbol: Stock ticker
            periods: Number of periods to fetch

        Returns:
            List of EarningsHistoryRecord
        """
        response = await self.client.post(
            "/earnings-data", params={"symbol": symbol, "periods": periods}
        )
        response.raise_for_status()
        return response.json()

    async def run_backtest(self, symbol: str = None, days: int = 90) -> dict:
        """
        Run backtest on earnings predictions.

        Args:
            symbol: Optional symbol to limit backtest to
            days: Number of days to backtest

        Returns:
            BacktestMetricsResponse
        """
        params = {"days": days}
        if symbol:
            params["symbol"] = symbol

        response = await self.client.post("/backtest", params=params)
        response.raise_for_status()
        return response.json()

    async def get_model_stats(self) -> dict:
        """
        Get model statistics and training info.

        Returns:
            ModelStatsResponse
        """
        response = await self.client.get("/model/stats")
        response.raise_for_status()
        return response.json()


def print_prediction(pred: dict):
    """Pretty print a prediction."""
    print("\n" + "=" * 80)
    print(f"EARNINGS PREDICTION: {pred['symbol']} - {pred['company_name']}")
    print("=" * 80)

    print(f"\nEarnings Date: {pred['earnings_date']}")
    print(f"Expected Move: ±{pred['expected_move_pct']:.2f}%")

    print("\n--- Model Prediction ---")
    print(f"  P(Beat):  {pred['predicted_probability_beat']:.1%}")
    print(f"  P(Miss):  {pred['predicted_probability_miss']:.1%}")
    print(f"  Market P(Beat): {pred['market_implied_prob_beat']:.1%}")

    print("\n--- Edge Analysis ---")
    print(f"  Edge: {pred['edge_probability']:.4f} ({pred['edge_pct']:+.2f}%)")
    print(f"  Recommendation: {pred['recommendation']}")
    print(f"  Confidence: {pred['confidence']:.1f}%")

    if pred.get("analyst_estimates"):
        ae = pred["analyst_estimates"]
        print("\n--- Analyst Consensus ---")
        print(f"  Number of Analysts: {ae['num_analysts']}")
        print(f"  EPS Estimate: ${ae['current_eps_estimate']:.2f}")
        print(f"  Guidance Revision: {ae['guidance_revision_trend']:+.2f}%")
        print(f"  Revisions: ↑{ae['estimate_revisions_up']} ↓{ae['estimate_revisions_down']}")

    if pred.get("options_data"):
        od = pred["options_data"]
        print("\n--- Options Market ---")
        print(f"  IV Rank: {od['iv_rank']:.0f}")
        print(f"  Vol Skew: {od['vol_skew']:+.2f}")
        print(f"  Put/Call Ratio: {od['put_call_iv_ratio']:.2f}")
        print(f"  Smart Money: {od['smart_money_flow'].upper()}")


async def main():
    """Run example demonstrations."""

    async with EarningsPredictorClient() as client:
        print("\n" + "=" * 80)
        print("EARNINGS PREDICTOR - EXAMPLE CLIENT")
        print("=" * 80)

        # Example 1: Single Stock Prediction
        print("\n--- Example 1: Single Stock Prediction ---")
        try:
            pred = await client.predict_earnings("TSLA")
            print_prediction(pred)
        except Exception as e:
            print(f"Error predicting TSLA: {e}")

        # Example 2: Multi-Stock Edge Scan
        print("\n--- Example 2: Multi-Stock Edge Scan ---")
        try:
            symbols = ["TSLA", "MSFT", "NVDA", "META", "AAPL", "GOOGL", "AMZN"]
            scan = await client.scan_edges(symbols, min_edge_pct=5.0)

            print(f"\nScanned: {scan['symbols_scanned']} stocks")
            print(f"With Edge: {scan['symbols_with_edge']} stocks")
            print(f"Average Edge: {scan['avg_edge']:.2f}%")

            if scan["top_edge"]:
                print(f"\nTop Edge: {scan['top_edge']['symbol']} ({scan['top_edge']['edge_pct']:+.2f}%)")

            print("\nTop 5 Opportunities by Edge:")
            for i, pred in enumerate(scan["predictions"][:5], 1):
                print(
                    f"  {i}. {pred['symbol']:6} | "
                    f"Edge: {pred['edge_pct']:+6.2f}% | "
                    f"Rec: {pred['recommendation']:18} | "
                    f"Conf: {pred['confidence']:5.1f}%"
                )
        except Exception as e:
            print(f"Error scanning edges: {e}")

        # Example 3: Get Latest Prediction
        print("\n--- Example 3: Latest Prediction History ---")
        try:
            history = await client.get_prediction_history("TSLA", limit=5)
            print(f"Total predictions for TSLA: {history['total']}")

            if history["predictions"]:
                latest = history["predictions"][0]
                print(f"\nLatest prediction:")
                print(f"  Date: {latest['prediction_date']}")
                print(f"  P(Beat): {latest['predicted_prob_beat']:.1%}")
                print(f"  Edge: {latest['edge_pct']:+.2f}%")
                print(f"  Recommendation: {latest['recommendation']}")
        except Exception as e:
            print(f"Error fetching history: {e}")

        # Example 4: Model Statistics
        print("\n--- Example 4: Model Statistics ---")
        try:
            stats = await client.get_model_stats()
            print(f"Model Type: {stats['model_type']}")
            print(f"Version: {stats['version']}")
            print(f"Features: {stats['feature_count']}")
            print(f"Is Live: {stats['is_live']}")

            if stats.get("training_samples"):
                print(f"Training Samples: {stats['training_samples']}")
                print(f"Training Date: {stats.get('training_date', 'N/A')}")
        except Exception as e:
            print(f"Error fetching model stats: {e}")

        # Example 5: Backtest Performance
        print("\n--- Example 5: 90-Day Backtest ---")
        try:
            backtest = await client.run_backtest(days=90)
            print(f"Period: {backtest['period']}")
            print(f"Total Predictions: {backtest['total_predictions']}")
            print(f"Predictions with Edge: {backtest['predictions_with_edge']}")
            print(f"Overall Hit Rate: {backtest['hit_rate']:.1%}")
            print(f"Edge Hit Rate: {backtest['edge_hit_rate']:.1%}")
            print(f"Avg Edge/Prediction: {backtest['avg_edge_per_prediction']:+.2f}%")
            print(f"Profit Factor: {backtest['profit_factor']:.2f}x")
            print(f"Largest Win: +{backtest['largest_win']:.2f}%")
            print(f"Largest Loss: {backtest['largest_loss']:.2f}%")
            print(f"Kelly Fraction: {backtest['kelly_fraction']:.1%}")
        except Exception as e:
            print(f"Error running backtest: {e}")

        print("\n" + "=" * 80)
        print("EXAMPLES COMPLETE")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
