#!/usr/bin/env python3
"""
AI Releases Predictor - Example usage and demonstrations.

This script shows how to use the AI Releases Predictor in various scenarios.
Run with: python examples_ai_releases.py
"""

import asyncio
import json
from datetime import datetime, timedelta
from services.ai_releases_predictor import (
    AIReleasesPredictorEngine,
    ModelProvider,
    EXAMPLE_PREDICTIONS,
)


async def example_1_single_prediction():
    """Example 1: Single release prediction."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Single Release Prediction")
    print("=" * 80)

    engine = AIReleasesPredictorEngine()

    # Predict Claude 4 release within 6 months
    target_date = datetime.utcnow() + timedelta(days=180)

    prediction = await engine.predict(
        provider=ModelProvider.ANTHROPIC,
        model_name="Claude 4",
        target_date=target_date,
    )

    print(f"\nModel: {prediction.model_name}")
    print(f"Provider: {prediction.provider.value.upper()}")
    print(f"Target Date: {prediction.target_date.strftime('%Y-%m-%d')}")
    print(f"\nPredicted Probability: {prediction.predicted_probability * 100:.2f}%")
    print(f"Polymarket Price: {prediction.polymarket_price * 100:.2f}%")
    print(f"\nEdge: {prediction.edge * 100:.3f}%")
    print(f"Edge %: {prediction.edge_pct:.2f}%")
    print(f"Recommendation: {prediction.recommendation}")
    print(f"Confidence: {prediction.confidence * 100:.1f}%")

    # Betting calculation
    bet_size = 100  # $100 bet
    expected_return = bet_size * (prediction.predicted_probability / prediction.polymarket_price)
    expected_profit = expected_return - bet_size

    print(f"\n--- Betting Calculation (${bet_size} bet) ---")
    print(f"Expected return at predicted prob: ${expected_return:.2f}")
    print(f"Expected profit/loss: ${expected_profit:+.2f}")

    if prediction.edge > 0:
        kelly_fraction = prediction.edge / (1 - prediction.predicted_probability)
        kelly_bet = bet_size * kelly_fraction
        print(f"Kelly fraction: {kelly_fraction:.3f}")
        print(f"Recommended Kelly bet: ${kelly_bet:.2f}")


async def example_2_batch_predictions():
    """Example 2: Batch predictions across models."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Batch Predictions")
    print("=" * 80)

    engine = AIReleasesPredictorEngine()

    batch_spec = [
        {
            "provider": "anthropic",
            "model_name": "Claude 4",
            "target_date": (datetime.utcnow() + timedelta(days=180)).isoformat(),
        },
        {
            "provider": "openai",
            "model_name": "GPT-5",
            "target_date": (datetime.utcnow() + timedelta(days=240)).isoformat(),
        },
        {
            "provider": "xai",
            "model_name": "Grok 2",
            "target_date": (datetime.utcnow() + timedelta(days=120)).isoformat(),
        },
    ]

    predictions = await engine.predict_batch(batch_spec)

    print(f"\nGenerated {len(predictions)} predictions:\n")

    # Create leaderboard
    leaderboard = sorted(
        predictions, key=lambda p: p.edge_pct, reverse=True
    )

    print(f"{'Rank':<5} {'Model':<20} {'Prob':<8} {'Price':<8} {'Edge':<8} {'Rec':<12}")
    print("-" * 70)

    for idx, pred in enumerate(leaderboard, 1):
        print(
            f"{idx:<5} {pred.model_name:<20} "
            f"{pred.predicted_probability*100:>6.1f}% {pred.polymarket_price*100:>6.1f}% "
            f"{pred.edge_pct:>6.2f}% {pred.recommendation:<12}"
        )

    total_edge = sum(p.edge * 100 for p in predictions)
    print("-" * 70)
    print(f"Total edge (per $100 bets): ${total_edge:.2f}")


async def example_3_market_analysis():
    """Example 3: Market analysis and feature importance."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Feature Analysis")
    print("=" * 80)

    engine = AIReleasesPredictorEngine()

    features = await engine.build_features(
        provider=ModelProvider.ANTHROPIC,
        model_name="Claude 4",
        target_date=datetime.utcnow() + timedelta(days=180),
    )

    print(f"\nExtracted Features for Claude 4 Release Prediction:\n")

    # Activity metrics
    print("GitHub Activity:")
    print(f"  - Commits (last 7 days): {features.commits_last_7d:.0f}")
    print(f"  - Commits (last 30 days): {features.commits_last_30d:.0f}")
    print(f"  - Releases (last 90 days): {features.releases_last_90d:.0f}")
    print(f"  - Days since last release: {features.days_since_last_release:.0f}")
    print(f"  - Repository stars: {features.repository_stars:.0f}")
    print(f"  - Contributors: {features.contributor_count:.0f}")

    # HuggingFace activity
    print("\nHuggingFace Activity:")
    print(f"  - Models uploaded (last 30 days): {features.hf_models_last_30d:.0f}")
    print(f"  - Total model downloads: {features.hf_model_downloads:.0f}")

    # Market data
    print("\nMarket Data:")
    print(f"  - Polymarket price: {features.polymarket_price * 100:.2f}%")

    # Temporal data
    print("\nTemporal Features:")
    print(f"  - Days until target: {features.days_until_target:.0f}")
    print(f"  - Quarter progress: {features.quarter_progress * 100:.1f}%")
    print(f"  - Major event nearby: {features.is_major_event}")

    # Historical cadence
    print("\nHistorical Cadence:")
    print(f"  - Avg gap between releases: {features.avg_release_gap_days:.0f} days")
    print(f"  - Last release recency: {features.last_release_recency_percentile * 100:.1f}%ile")


async def example_4_edge_strategy():
    """Example 4: Edge-based trading strategy."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Edge-Based Trading Strategy")
    print("=" * 80)

    engine = AIReleasesPredictorEngine()

    predictions = await engine.predict_batch(EXAMPLE_PREDICTIONS)

    print("\nTrading Decisions (assuming $100 per position):\n")

    print(f"{'Model':<20} {'Prob':<8} {'Price':<8} {'Edge':<8} {'Action':<15} {'Bet Size':<10}")
    print("-" * 85)

    portfolio_value = 0
    position_count = 0

    for pred in sorted(predictions, key=lambda p: p.edge_pct, reverse=True):
        if pred.edge > 0.05:  # Only take positions with 5%+ edge
            action = "YES (BUY)" if pred.recommendation in ["BUY", "STRONG_BUY"] else "NO (SELL)"
            bet_size = min(100, abs(pred.edge * 1000))  # Kelly-like sizing
            position_count += 1
            portfolio_value += pred.edge * bet_size

            print(
                f"{pred.model_name:<20} {pred.predicted_probability*100:>6.1f}% "
                f"{pred.polymarket_price*100:>6.1f}% {pred.edge_pct:>6.2f}% "
                f"{action:<15} ${bet_size:>7.2f}"
            )

    print("-" * 85)
    print(f"Total positions: {position_count}")
    print(f"Expected portfolio value: ${portfolio_value:.2f}")
    if position_count > 0:
        print(f"Average edge per position: {(portfolio_value / position_count):.3f}")


async def example_5_comparison():
    """Example 5: Model comparison and sensitivity analysis."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Sensitivity Analysis - Same Model, Different Dates")
    print("=" * 80)

    engine = AIReleasesPredictorEngine()

    target_dates = [
        ("3 months", datetime.utcnow() + timedelta(days=90)),
        ("6 months", datetime.utcnow() + timedelta(days=180)),
        ("12 months", datetime.utcnow() + timedelta(days=365)),
    ]

    print(f"\nClaude 4 Release Predictions at Different Horizons:\n")
    print(f"{'Horizon':<15} {'Prob':<8} {'Price':<8} {'Edge':<8} {'Confidence':<12}")
    print("-" * 60)

    for label, date in target_dates:
        pred = await engine.predict(
            provider=ModelProvider.ANTHROPIC,
            model_name="Claude 4",
            target_date=date,
        )

        print(
            f"{label:<15} {pred.predicted_probability*100:>6.1f}% "
            f"{pred.polymarket_price*100:>6.1f}% {pred.edge_pct:>6.2f}% "
            f"{pred.confidence*100:>10.1f}%"
        )


async def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("AI RELEASES PREDICTOR - EXAMPLES")
    print("=" * 80)

    try:
        await example_1_single_prediction()
        await example_2_batch_predictions()
        await example_3_market_analysis()
        await example_4_edge_strategy()
        await example_5_comparison()

        print("\n" + "=" * 80)
        print("Examples completed successfully!")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
