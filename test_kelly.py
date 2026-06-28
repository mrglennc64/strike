"""
Unit tests for Kelly Criterion betting module.

Covers:
  - Odds conversion (American ↔ decimal, ↔ probability)
  - Kelly Fraction calculation (positive edge, zero edge, negative edge)
  - Bet sizing (full Kelly, fractional Kelly, edge cases)
  - Expected value calculations
  - Comprehensive recommendations
  - Edge cases (extreme odds, extreme probabilities, boundary conditions)
"""

import pytest
from kelly import (
    american_to_decimal,
    american_to_implied_probability,
    calculate_kelly_fraction,
    calculate_bet_size,
    expected_value,
    edge_percentage,
    recommend_bet,
)


class TestAmericanToDecimal:
    """Test American to decimal odds conversion."""

    def test_positive_odds_100(self):
        """Even underdog odds."""
        assert american_to_decimal(100) == 2.0

    def test_positive_odds_150(self):
        """Underdog odds."""
        assert american_to_decimal(150) == 2.5

    def test_positive_odds_200(self):
        """Heavy underdog."""
        assert american_to_decimal(200) == 3.0

    def test_negative_odds_100(self):
        """Even favorite odds."""
        assert abs(american_to_decimal(-100) - 2.0) < 0.0001

    def test_negative_odds_110(self):
        """Standard juice odds."""
        assert abs(american_to_decimal(-110) - 1.909090909) < 0.0001

    def test_negative_odds_200(self):
        """Heavy favorite."""
        assert abs(american_to_decimal(-200) - 1.5) < 0.0001

    def test_zero_odds_raises(self):
        """Zero odds are undefined."""
        with pytest.raises(ValueError):
            american_to_decimal(0)

    def test_extreme_positive_odds(self):
        """Extreme underdog (+10000)."""
        result = american_to_decimal(10000)
        assert result == 101.0

    def test_extreme_negative_odds(self):
        """Extreme favorite (-10000)."""
        result = american_to_decimal(-10000)
        assert abs(result - 1.01) < 0.0001


class TestAmericanToImpliedProbability:
    """Test American to implied probability conversion."""

    def test_even_odds_positive(self):
        """Even odds +100 should imply ~50%."""
        prob = american_to_implied_probability(100)
        assert abs(prob - 0.5) < 0.0001

    def test_even_odds_negative(self):
        """Even odds -100 should imply ~50%."""
        prob = american_to_implied_probability(-100)
        assert abs(prob - 0.5) < 0.0001

    def test_favorite_standard_juice(self):
        """Standard -110 should imply ~52.4%."""
        prob = american_to_implied_probability(-110)
        assert abs(prob - 0.5238) < 0.0001

    def test_underdog_standard_juice(self):
        """Standard +110 should imply ~47.6%."""
        prob = american_to_implied_probability(110)
        assert abs(prob - 0.4762) < 0.0001

    def test_heavy_favorite(self):
        """Heavy favorite -200 should imply 66.7%."""
        prob = american_to_implied_probability(-200)
        assert abs(prob - 0.6667) < 0.0001

    def test_heavy_underdog(self):
        """Heavy underdog +200 should imply 33.3%."""
        prob = american_to_implied_probability(200)
        assert abs(prob - 0.3333) < 0.0001


class TestCalculateKellyFraction:
    """Test Kelly Fraction calculation."""

    def test_zero_edge_bet(self):
        """Zero edge should result in zero Kelly."""
        market_prob = american_to_implied_probability(-110)
        kelly = calculate_kelly_fraction(market_prob, market_prob, -110)
        assert abs(kelly) < 0.001

    def test_positive_edge_basic(self):
        """60% model vs 50% market, even odds."""
        kelly = calculate_kelly_fraction(0.60, 0.50, 100)
        # (0.6 * 2 - 1) / (2 - 1) = 0.2
        assert abs(kelly - 0.2) < 0.001

    def test_positive_edge_with_juice(self):
        """Positive edge with standard -110 juice."""
        kelly = calculate_kelly_fraction(0.55, 0.5238, -110)
        assert kelly > 0
        assert kelly < 0.15

    def test_negative_edge_bet(self):
        """Negative edge should result in negative Kelly."""
        kelly = calculate_kelly_fraction(0.40, 0.50, 100)
        assert kelly < 0

    def test_high_confidence_edge(self):
        """Very high confidence should give larger Kelly."""
        kelly_moderate = calculate_kelly_fraction(0.55, 0.50, 100)
        kelly_high = calculate_kelly_fraction(0.85, 0.50, 100)
        assert kelly_high > kelly_moderate

    def test_long_odds_larger_kelly(self):
        """Longer odds should give larger Kelly for same confidence."""
        kelly_short = calculate_kelly_fraction(0.60, 0.50, -110)
        kelly_long = calculate_kelly_fraction(0.60, 0.40, 200)
        assert kelly_long > kelly_short

    def test_invalid_probability_zero(self):
        """Probability of exactly 0 should raise error."""
        with pytest.raises(ValueError, match="strictly between 0 and 1"):
            calculate_kelly_fraction(0.0, 0.5, 100)

    def test_invalid_probability_one(self):
        """Probability of exactly 1 should raise error."""
        with pytest.raises(ValueError, match="strictly between 0 and 1"):
            calculate_kelly_fraction(1.0, 0.5, 100)

    def test_invalid_probability_over_one(self):
        """Probability over 1 should raise error."""
        with pytest.raises(ValueError, match="strictly between 0 and 1"):
            calculate_kelly_fraction(1.5, 0.5, 100)

    def test_invalid_probability_negative(self):
        """Negative probability should raise error."""
        with pytest.raises(ValueError, match="strictly between 0 and 1"):
            calculate_kelly_fraction(-0.1, 0.5, 100)

    def test_boundary_probability_slightly_above_zero(self):
        """Probability just above 0 should work."""
        kelly = calculate_kelly_fraction(0.001, 0.5, 100)
        assert kelly < 0  # Likely no edge at 0.1%

    def test_boundary_probability_slightly_below_one(self):
        """Probability just below 1 should work."""
        kelly = calculate_kelly_fraction(0.999, 0.5, 100)
        assert kelly > 0  # Should have massive edge at 99.9%


class TestCalculateBetSize:
    """Test bet size calculation."""

    def test_full_kelly_sizing(self):
        """Full Kelly should use 100% of kelly fraction."""
        kelly = 0.05
        bankroll = 10000
        bet = calculate_bet_size(kelly, bankroll, 1.0)
        assert bet == 500.0

    def test_half_kelly_sizing(self):
        """Half Kelly should use 50% of kelly fraction."""
        kelly = 0.05
        bankroll = 10000
        bet = calculate_bet_size(kelly, bankroll, 0.5)
        assert bet == 250.0

    def test_quarter_kelly_sizing(self):
        """Quarter Kelly should use 25% of kelly fraction."""
        kelly = 0.05
        bankroll = 10000
        bet = calculate_bet_size(kelly, bankroll, 0.25)
        assert bet == 125.0

    def test_eighth_kelly_sizing(self):
        """Eighth Kelly should use 12.5% of kelly fraction."""
        kelly = 0.08
        bankroll = 10000
        bet = calculate_bet_size(kelly, bankroll, 0.125)
        # 0.08 * 0.125 * 10000 = 100.0
        assert bet == 100.0

    def test_negative_kelly_returns_zero(self):
        """Negative Kelly should result in no bet."""
        kelly = -0.02
        bankroll = 10000
        bet = calculate_bet_size(kelly, bankroll, 1.0)
        assert bet == 0.0

    def test_negative_kelly_with_multiplier_returns_zero(self):
        """Negative Kelly should return 0 even with multiplier."""
        kelly = -0.05
        bankroll = 10000
        bet = calculate_bet_size(kelly, bankroll, 0.25)
        assert bet == 0.0

    def test_zero_kelly(self):
        """Zero Kelly should result in no bet."""
        kelly = 0.0
        bankroll = 10000
        bet = calculate_bet_size(kelly, bankroll, 1.0)
        assert bet == 0.0

    def test_zero_multiplier(self):
        """Zero multiplier should result in no bet."""
        kelly = 0.05
        bankroll = 10000
        bet = calculate_bet_size(kelly, bankroll, 0.0)
        assert bet == 0.0

    def test_invalid_bankroll_zero(self):
        """Zero bankroll should raise error."""
        with pytest.raises(ValueError, match="bankroll must be positive"):
            calculate_bet_size(0.05, 0, 1.0)

    def test_invalid_bankroll_negative(self):
        """Negative bankroll should raise error."""
        with pytest.raises(ValueError, match="bankroll must be positive"):
            calculate_bet_size(0.05, -1000, 1.0)

    def test_invalid_multiplier_negative(self):
        """Negative multiplier should raise error."""
        with pytest.raises(ValueError, match="kelly_fraction_multiplier must be in"):
            calculate_bet_size(0.05, 10000, -0.5)

    def test_invalid_multiplier_over_one(self):
        """Multiplier over 1 should raise error."""
        with pytest.raises(ValueError, match="kelly_fraction_multiplier must be in"):
            calculate_bet_size(0.05, 10000, 1.5)

    def test_small_bankroll(self):
        """Small bankroll should scale proportionally."""
        kelly = 0.05
        bet_large = calculate_bet_size(kelly, 100000, 0.25)
        bet_small = calculate_bet_size(kelly, 1000, 0.25)
        ratio = bet_small / bet_large
        assert abs(ratio - 0.01) < 0.0001

    def test_large_bankroll(self):
        """Large bankroll should scale proportionally."""
        kelly = 0.05
        bet_1000 = calculate_bet_size(kelly, 1000, 0.25)
        bet_1000000 = calculate_bet_size(kelly, 1000000, 0.25)
        ratio = bet_1000000 / bet_1000
        assert abs(ratio - 1000) < 0.1


class TestExpectedValue:
    """Test expected value calculation."""

    def test_positive_ev_bet(self):
        """Positive EV bet should have positive expected value."""
        ev = expected_value(0.60, 100, 100)
        assert ev > 0
        assert abs(ev - 20.0) < 0.1

    def test_negative_ev_bet(self):
        """Negative EV bet should have negative expected value."""
        ev = expected_value(0.40, 100, 100)
        assert ev < 0
        assert abs(ev - (-20.0)) < 0.1

    def test_break_even_bet(self):
        """Fair probability should have zero expected value."""
        market_prob = american_to_implied_probability(-110)
        ev = expected_value(market_prob, -110, 100)
        assert abs(ev) < 0.1

    def test_even_odds_60_percent(self):
        """Even odds with 60% should give 20% ROI."""
        ev = expected_value(0.60, 100, 100)
        # Win: 0.60 * 100 = 60, Loss: 0.40 * 100 = 40
        # EV = 60 - 40 = 20
        assert abs(ev - 20.0) < 0.1

    def test_favorite_odds_high_probability(self):
        """Favorite odds with high probability should be positive EV."""
        ev = expected_value(0.60, -110, 100)
        assert ev > 0

    def test_underdog_odds_low_probability(self):
        """Underdog odds with low probability should be negative EV."""
        ev = expected_value(0.40, 100, 100)
        assert ev < 0

    def test_zero_bet_size(self):
        """Zero bet size should give zero EV."""
        ev = expected_value(0.60, 100, 0)
        assert ev == 0.0

    def test_large_bet_scales_ev(self):
        """Larger bets should scale EV proportionally."""
        ev_100 = expected_value(0.60, 100, 100)
        ev_1000 = expected_value(0.60, 100, 1000)
        assert abs(ev_1000 / ev_100 - 10) < 0.01


class TestEdgePercentage:
    """Test edge percentage calculation."""

    def test_zero_edge(self):
        """Same probabilities should give zero edge."""
        edge = edge_percentage(0.50, 0.50)
        assert edge == 0.0

    def test_positive_edge_basic(self):
        """60% vs 50% should give 20% edge."""
        edge = edge_percentage(0.60, 0.50)
        assert abs(edge - 0.2) < 0.0001

    def test_positive_edge_small(self):
        """51% vs 50% should give ~2% edge."""
        edge = edge_percentage(0.51, 0.50)
        assert abs(edge - 0.02) < 0.0001

    def test_negative_edge(self):
        """40% vs 50% should give -20% edge."""
        edge = edge_percentage(0.40, 0.50)
        assert abs(edge - (-0.2)) < 0.0001

    def test_high_probability_edge(self):
        """99% vs 95% should give ~4.2% edge."""
        edge = edge_percentage(0.99, 0.95)
        assert abs(edge - 0.0421) < 0.001

    def test_zero_market_probability(self):
        """Zero market probability should return 0 (edge undefined)."""
        edge = edge_percentage(0.60, 0.0)
        assert edge == 0.0


class TestRecommendBet:
    """Test comprehensive bet recommendation."""

    def test_clear_yes_bet(self):
        """Clear +EV bet should be recommended."""
        rec = recommend_bet(0.60, 100, 10000, kelly_multiplier=0.25)
        assert rec.should_bet is True
        assert rec.kelly_fraction > 0
        assert rec.bet_size > 0
        assert rec.expected_value > 0

    def test_clear_no_bet_zero_edge(self):
        """Zero edge should not be recommended."""
        market_prob = american_to_implied_probability(-110)
        rec = recommend_bet(market_prob, -110, 10000)
        assert rec.should_bet is False

    def test_clear_no_bet_negative_edge(self):
        """Negative edge should not be recommended."""
        rec = recommend_bet(0.40, 100, 10000)
        assert rec.should_bet is False

    def test_small_edge_below_minimum(self):
        """Small edge might not meet minimum threshold."""
        # 52% vs 50% is ~4% edge
        rec = recommend_bet(0.52, 100, 10000, min_edge_pct=0.05)
        assert rec.should_bet is False

    def test_small_edge_above_minimum(self):
        """Edge that meets minimum should be recommended."""
        rec = recommend_bet(0.52, 100, 10000, min_edge_pct=0.01)
        assert rec.should_bet is True

    def test_bet_size_respects_kelly_multiplier(self):
        """Bet size should respect Kelly multiplier."""
        rec_full = recommend_bet(0.60, 100, 10000, kelly_multiplier=1.0)
        rec_quarter = recommend_bet(0.60, 100, 10000, kelly_multiplier=0.25)
        assert rec_quarter.bet_size < rec_full.bet_size
        # Quarter should be ~25% of full
        ratio = rec_quarter.bet_size / rec_full.bet_size
        assert abs(ratio - 0.25) < 0.01

    def test_high_confidence_larger_bet(self):
        """Higher confidence should result in larger bet."""
        rec_moderate = recommend_bet(0.55, 100, 10000, kelly_multiplier=0.25)
        rec_high = recommend_bet(0.75, 100, 10000, kelly_multiplier=0.25)
        assert rec_high.bet_size > rec_moderate.bet_size

    def test_recommendation_includes_reasoning(self):
        """Recommendation should include clear reasoning."""
        rec = recommend_bet(0.60, 100, 10000)
        assert rec.reason is not None
        assert len(rec.reason) > 0
        assert "Edge" in rec.reason or "edge" in rec.reason.lower()

    def test_no_bet_includes_reason_no_edge(self):
        """No-bet recommendation should explain why."""
        rec = recommend_bet(0.50, 100, 10000)
        assert "edge" in rec.reason.lower()

    def test_no_bet_includes_reason_edge_too_small(self):
        """No-bet due to small edge should mention threshold."""
        rec = recommend_bet(0.52, 100, 10000, min_edge_pct=0.05)
        assert "small" in rec.reason.lower()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_high_probability(self):
        """Very confident predictions (99%) should work."""
        kelly = calculate_kelly_fraction(0.99, 0.50, 100)
        assert kelly > 0
        assert kelly < 1.0

    def test_very_low_probability(self):
        """Very low probabilities (1%) should work."""
        kelly = calculate_kelly_fraction(0.01, 0.50, 100)
        assert kelly < 0  # No edge

    def test_very_low_odds_favorite(self):
        """Very heavy favorite (-1000) should work."""
        implied = american_to_implied_probability(-1000)
        assert implied > 0.9
        kelly = calculate_kelly_fraction(0.95, implied, -1000)
        assert kelly > 0

    def test_very_long_odds_underdog(self):
        """Very long odds (+1000) should work."""
        implied = american_to_implied_probability(1000)
        assert implied < 0.1
        kelly = calculate_kelly_fraction(0.20, implied, 1000)
        assert kelly > 0

    def test_tiny_bankroll(self):
        """$1 bankroll should scale down bet."""
        bet = calculate_bet_size(0.05, 1, 0.25)
        assert 0 < bet <= 1

    def test_large_bankroll(self):
        """Large bankrolls should scale up bet."""
        bet = calculate_bet_size(0.05, 1000000, 0.25)
        assert bet > 10000

    def test_kelly_never_negative_after_multiply(self):
        """Fractional Kelly should never be negative (clamped to 0)."""
        kelly = -0.05
        bet = calculate_bet_size(kelly, 10000, 0.5)
        assert bet == 0.0

    def test_roundtrip_decimal_american(self):
        """Convert to decimal and back to implied probability."""
        american = -110
        decimal = american_to_decimal(american)
        implied = american_to_implied_probability(american)
        # Rebuild: 1/implied should equal decimal
        assert abs(1 / implied - decimal) < 0.0001

    def test_recommendation_always_includes_edge(self):
        """Recommendation should always calculate edge."""
        rec = recommend_bet(0.60, 100, 10000)
        assert rec.edge_pct is not None
        assert isinstance(rec.edge_pct, float)


class TestIntegration:
    """Integration tests combining multiple functions."""

    def test_end_to_end_bet_workflow(self):
        """Complete workflow: odds → kelly → bet size → EV."""
        american_odds = 100
        model_prob = 0.60
        bankroll = 10000

        # Get market view
        market_prob = american_to_implied_probability(american_odds)
        assert market_prob == 0.5

        # Calculate Kelly
        kelly = calculate_kelly_fraction(model_prob, market_prob, american_odds)
        assert kelly > 0

        # Calculate bet size (quarter Kelly)
        bet_size = calculate_bet_size(kelly, bankroll, 0.25)
        assert 0 < bet_size < bankroll

        # Calculate EV
        ev = expected_value(model_prob, american_odds, bet_size)
        assert ev > 0

    def test_sports_betting_example(self):
        """Realistic sports betting example."""
        # You think team A has 65% chance to win
        # Market prices them at 60% (implied from -150 odds)
        # You have $5000 bankroll, use quarter Kelly

        american_odds = -150
        model_prob = 0.65
        bankroll = 5000

        rec = recommend_bet(model_prob, american_odds, bankroll, 0.25, 0.01)

        # Should recommend a bet with positive edge
        assert rec.should_bet is True
        assert rec.kelly_fraction > 0
        assert 0 < rec.bet_size < bankroll  # Should be portion of bankroll

    def test_election_betting_example(self):
        """Realistic election betting example."""
        # You think candidate has 55% true probability
        # Market prices them at 48% (implied from +108 odds)
        # You have $2000 bankroll

        american_odds = 108
        model_prob = 0.55
        bankroll = 2000

        rec = recommend_bet(model_prob, american_odds, bankroll, 0.25, 0.02)

        # Should recommend a bet
        assert rec.kelly_fraction > 0
        assert rec.bet_size > 0

    def test_crypto_price_prediction(self):
        """Realistic crypto outcome betting."""
        # You think Bitcoin hits $100k with 40% probability
        # Market prices at 30% (implied from +233 odds)
        # You have $10000 in trading capital

        american_odds = 233
        model_prob = 0.40
        bankroll = 10000

        rec = recommend_bet(model_prob, american_odds, bankroll, 0.25, 0.01)

        assert rec.kelly_fraction > 0
        assert rec.should_bet is True

    def test_no_bet_protection(self):
        """System should protect against bad bets."""
        american_odds = 100
        model_prob = 0.45  # Model thinks 45%
        bankroll = 5000

        rec = recommend_bet(model_prob, american_odds, bankroll)

        # Should not recommend (negative edge)
        assert rec.should_bet is False
        assert rec.bet_size == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
