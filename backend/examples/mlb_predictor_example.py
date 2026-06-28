#!/usr/bin/env python3
"""
MLB Strikeout Predictor - Usage Examples

Demonstrates how to use the MLBStrikeoutPredictor for:
1. Training the model
2. Making predictions
3. Running backtests
4. Comparing with bookmaker odds
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.mlb_predictor import MLBStrikeoutPredictor


def example_basic_workflow():
    """Basic workflow: train -> predict -> backtest."""
    print("\n" + "="*100)
    print("EXAMPLE 1: BASIC WORKFLOW")
    print("="*100)

    # Initialize predictor
    predictor = MLBStrikeoutPredictor(db_path='mlb-edge/data/baseball.duckdb')

    # Train on June 1-10
    print("\n[1] Training model on June 1-10...")
    success = predictor.train_on_historical(
        start_date='2026-06-01',
        train_end_date='2026-06-10'
    )

    if not success:
        print("Training failed!")
        return

    print("✓ Model trained successfully")

    # Make predictions for today
    print("\n[2] Generating predictions for today...")
    predictions = predictor.predict_today(
        line=5.5,
        edge_threshold=8.0
    )

    print(f"Found {len(predictions)} predictions with edge > 8%")

    if predictions:
        pred = predictions[0]
        print(f"\nExample prediction:")
        print(f"  Pitcher: {pred['pitcher_name']} (ID: {pred['pitcher_id']})")
        print(f"  Opponent: {pred['opponent']}")
        print(f"  Line: Over {pred['strikeout_line']}")
        print(f"  Expected Strikeouts (Lambda): {pred['lambda']:.2f}")
        print(f"  Model Probability: {pred['model_prob_pct']:.1f}%")
        print(f"  Book Probability: {pred['book_prob_pct']:.1f}%")
        print(f"  Edge: {pred['edge_pct']:+.1f}%")
        print(f"  Direction: {pred['direction']}")
        print(f"  Confidence: {pred['confidence']:.1f}%")

    # Backtest
    print("\n[3] Backtesting on June 15-27...")
    backtest = predictor.backtest(
        start_date='2026-06-15',
        end_date='2026-06-27',
        line=5.5,
        edge_threshold=8.0,
        confidence_threshold=70.0
    )

    if 'error' not in backtest:
        print(f"  Plays: {backtest['num_plays']}")
        print(f"  Wins: {backtest['wins']}")
        print(f"  Losses: {backtest['losses']}")
        print(f"  Win Rate: {backtest['win_rate']:.1f}%")
        print(f"  ROI: {backtest['roi']:+.1f}%")
        print(f"  Total Profit: ${backtest['total_profit']:+d}")
    else:
        print(f"  {backtest['error']}")


def example_output_format():
    """Show the standard output format for predictions."""
    print("\n" + "="*100)
    print("EXAMPLE 2: STANDARD OUTPUT FORMAT")
    print("="*100)

    predictor = MLBStrikeoutPredictor(db_path='mlb-edge/data/baseball.duckdb')

    if not predictor.train_on_historical():
        print("Training failed")
        return

    predictions = predictor.predict_today(line=5.5, edge_threshold=5.0)

    print("\nSTANDARD FORMAT (Copy-Paste Ready):")
    print("-" * 100)

    for pred in predictions[:5]:  # Show first 5
        format_str = (
            f"{pred['pitcher_name']} | "
            f"Over {pred['strikeout_line']} | "
            f"Model {pred['model_prob_pct']:.1f}% | "
            f"Book {pred['book_prob_pct']:.1f}% | "
            f"Edge {pred['edge_pct']:+.1f}%"
        )
        print(format_str)

    print("-" * 100)


def example_api_response_format():
    """Show what the FastAPI endpoints return."""
    print("\n" + "="*100)
    print("EXAMPLE 3: API RESPONSE FORMAT")
    print("="*100)

    print("\nGET /api/verticals/mlb/predictions/today")
    print("Response:")

    response = {
        "predictions": [
            {
                "pitcher_id": 604501,
                "pitcher_name": "Reid Detmers",
                "opponent": "LAA",
                "game_date": "2026-06-27",
                "strikeout_line": 6.5,
                "model_prob": 0.651,
                "model_prob_pct": 65.1,
                "book_prob": 0.524,
                "book_prob_pct": 52.4,
                "edge_pct": 12.7,
                "lambda": 6.84,
                "batters_faced": 27,
                "direction": "OVER",
                "confidence": 15.1
            }
        ],
        "total_plays": 1,
        "timestamp": "2026-06-28T10:30:00",
        "model_status": "ready"
    }

    print(json.dumps(response, indent=2))


def example_by_pitcher():
    """Get predictions for a specific pitcher."""
    print("\n" + "="*100)
    print("EXAMPLE 4: PITCHER-SPECIFIC PREDICTION")
    print("="*100)

    predictor = MLBStrikeoutPredictor(db_path='mlb-edge/data/baseball.duckdb')

    if not predictor.train_on_historical():
        return

    predictions = predictor.predict_today(line=5.5, edge_threshold=0)

    if predictions:
        pitcher = predictions[0]
        print(f"\nPitcher: {pitcher['pitcher_name']}")
        print(f"ID: {pitcher['pitcher_id']}")
        print(f"Opponent: {pitcher['opponent']}")
        print(f"Game Date: {pitcher['game_date']}")
        print(f"\nModel Analysis:")
        print(f"  Expected Strikeouts: {pitcher['lambda']:.2f}")
        print(f"  P(Over {pitcher['strikeout_line']}): {pitcher['model_prob']:.3f}")
        print(f"  P(Under {pitcher['strikeout_line']}): {1 - pitcher['model_prob']:.3f}")
        print(f"\nBookmaker Comparison:")
        print(f"  Implied P(Over): {pitcher['book_prob']:.3f}")
        print(f"  Model Edge: {pitcher['edge_pct']:+.1f}%")
        print(f"  Recommendation: {pitcher['direction']}")
        print(f"  Confidence: {pitcher['confidence']:.1f}%")


def example_filter_by_edge():
    """Show how to filter predictions by edge percentage."""
    print("\n" + "="*100)
    print("EXAMPLE 5: FILTERING BY EDGE THRESHOLD")
    print("="*100)

    predictor = MLBStrikeoutPredictor(db_path='mlb-edge/data/baseball.duckdb')

    if not predictor.train_on_historical():
        return

    for threshold in [5, 8, 10, 15]:
        predictions = predictor.predict_today(
            line=5.5,
            edge_threshold=threshold
        )
        print(f"\nEdge > {threshold}%: {len(predictions)} predictions")
        if predictions:
            avg_edge = sum(p['edge_pct'] for p in predictions) / len(predictions)
            max_edge = max(p['edge_pct'] for p in predictions)
            print(f"  Average Edge: {avg_edge:+.1f}%")
            print(f"  Max Edge: {max_edge:+.1f}%")


def example_backtest_parameters():
    """Show how to run backtests with different parameters."""
    print("\n" + "="*100)
    print("EXAMPLE 6: BACKTEST WITH DIFFERENT PARAMETERS")
    print("="*100)

    predictor = MLBStrikeoutPredictor(db_path='mlb-edge/data/baseball.duckdb')

    if not predictor.train_on_historical():
        return

    configs = [
        {"edge": 5.0, "confidence": 50.0, "name": "Loose (Edge > 5%, Conf > 50%)"},
        {"edge": 8.0, "confidence": 70.0, "name": "Moderate (Edge > 8%, Conf > 70%)"},
        {"edge": 10.0, "confidence": 80.0, "name": "Tight (Edge > 10%, Conf > 80%)"},
    ]

    print("\nBacktest Results (June 15-27):")
    print("-" * 80)

    for config in configs:
        backtest = predictor.backtest(
            start_date='2026-06-15',
            end_date='2026-06-27',
            edge_threshold=config['edge'],
            confidence_threshold=config['confidence']
        )

        if 'error' not in backtest:
            print(f"\n{config['name']}")
            print(f"  Plays: {backtest['num_plays']}")
            print(f"  W/L: {backtest['wins']}/{backtest['losses']}")
            print(f"  Win Rate: {backtest['win_rate']:.1f}%")
            print(f"  ROI: {backtest['roi']:+.1f}%")
            print(f"  Profit: ${backtest['total_profit']:+d}")


def main():
    """Run all examples."""
    print("\n")
    print("█" * 100)
    print("█" + " " * 98 + "█")
    print("█" + " MLB STRIKEOUT PREDICTOR - USAGE EXAMPLES".center(98) + "█")
    print("█" + " " * 98 + "█")
    print("█" * 100)

    try:
        example_basic_workflow()
        example_output_format()
        example_api_response_format()
        example_by_pitcher()
        example_filter_by_edge()
        example_backtest_parameters()

        print("\n" + "="*100)
        print("ALL EXAMPLES COMPLETED")
        print("="*100)

    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
