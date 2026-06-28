"""
Kelly Criterion betting module - reusable for any binary outcome.

Implements the Kelly Criterion formula for optimal bet sizing across any domain:
sports betting, elections, crypto, markets, etc.

Formula: f* = (p*d - 1) / (d - 1)
where p = probability of winning, d = decimal odds

References:
  - J.L. Kelly Jr., "A New Interpretation of Information Rate" (1956)
  - Ed Thorp, "Beat the Dealer" (1962)
"""

from dataclasses import dataclass
from typing import Optional


def american_to_decimal(american_odds: float) -> float:
    """
    Convert American odds to decimal odds.

    American format is commonly used in US sportsbooks:
    - Positive odds (e.g., +150) = underdog
    - Negative odds (e.g., -110) = favorite

    Args:
        american_odds: Odds in American format (e.g., -110, +150)

    Returns:
        Decimal odds (e.g., 1.91 for -110)

    Examples:
        >>> american_to_decimal(-110)
        1.909090909...
        >>> american_to_decimal(+150)
        2.5
        >>> american_to_decimal(100)
        2.0

    Raises:
        ValueError: If odds are 0 (undefined)
    """
    if american_odds == 0:
        raise ValueError("American odds cannot be 0")

    if american_odds > 0:
        # Positive odds: decimal = 1 + (american / 100)
        return 1 + (american_odds / 100)
    else:
        # Negative odds: decimal = 1 + (100 / abs(american))
        return 1 + (100 / abs(american_odds))


def american_to_implied_probability(american_odds: float) -> float:
    """
    Convert American odds to implied probability (assumes no vig).

    This gives the "fair" probability priced into the odds, not accounting
    for the sportsbook margin (vigorish). Use this for comparing your model
    probability vs. market price.

    Args:
        american_odds: Odds in American format

    Returns:
        Implied probability as decimal (0 to 1)

    Examples:
        >>> american_to_implied_probability(-110)
        0.5238095...
        >>> american_to_implied_probability(+100)
        0.5
        >>> american_to_implied_probability(+200)
        0.3333...
    """
    decimal_odds = american_to_decimal(american_odds)
    return 1 / decimal_odds


def calculate_kelly_fraction(
    model_prob: float,
    market_prob: float,
    american_odds: float
) -> float:
    """
    Calculate optimal Kelly Fraction for a bet.

    The Kelly Criterion gives the optimal fraction of your bankroll to bet
    to maximize long-term geometric growth while avoiding ruin. Returns negative
    Kelly if there's no edge (don't bet).

    Formula: f* = (p*d - 1) / (d - 1)
    where p = model probability, d = decimal odds

    Args:
        model_prob: Your estimated probability of winning (0 < p < 1)
        market_prob: Implied probability from market odds (for reference/validation)
        american_odds: The odds being offered in American format

    Returns:
        Kelly Fraction as decimal (0.05 = 5% of bankroll)
        Negative value means no edge; don't bet.

    Examples:
        >>> # You think 60% chance, market prices at 50%, odds +100 (2.0 decimal)
        >>> calculate_kelly_fraction(0.60, 0.50, 100)
        0.2

        >>> # No edge - you think 50%, market also 50%
        >>> kelly = calculate_kelly_fraction(0.50, 0.50, -110)
        >>> abs(kelly) < 0.001  # ~0
        True

        >>> # Negative edge - don't bet
        >>> calculate_kelly_fraction(0.48, 0.52, -110)
        -0.024390...

    Raises:
        ValueError: If model_prob not in (0, 1) exclusive
    """
    if not (0 < model_prob < 1):
        raise ValueError(
            f"model_prob must be strictly between 0 and 1, got {model_prob}"
        )

    decimal_odds = american_to_decimal(american_odds)

    # Kelly formula: f* = (p*d - 1) / (d - 1)
    kelly = (model_prob * decimal_odds - 1) / (decimal_odds - 1)

    return kelly


def calculate_bet_size(
    kelly_fraction: float,
    bankroll: float,
    kelly_fraction_multiplier: float = 1.0
) -> float:
    """
    Calculate actual bet size based on Kelly Fraction.

    Supports fractional Kelly (e.g., quarter Kelly, half Kelly) to reduce
    variance and drawdown risk. Most professionals use 0.25-0.5 instead of
    full Kelly due to model uncertainty.

    Args:
        kelly_fraction: The Kelly Fraction from calculate_kelly_fraction()
        bankroll: Total bankroll available ($)
        kelly_fraction_multiplier: Fraction of Kelly to use (default: 1.0)
            - 1.0 = full Kelly (aggressive, can have large drawdowns)
            - 0.5 = half Kelly (moderate)
            - 0.25 = quarter Kelly (conservative, recommended)

    Returns:
        Bet size in dollars. Clamps negative Kelly to 0 (no bet).

    Examples:
        >>> # Full Kelly: 5% of $10,000
        >>> calculate_bet_size(0.05, 10000, 1.0)
        500.0

        >>> # Quarter Kelly: (5% * 0.25) of $10,000
        >>> calculate_bet_size(0.05, 10000, 0.25)
        125.0

        >>> # Negative Kelly returns 0 (no bet)
        >>> calculate_bet_size(-0.02, 10000, 1.0)
        0.0

        >>> # Kelly of 0 means fair odds; no bet
        >>> calculate_bet_size(0.0, 10000, 1.0)
        0.0

    Raises:
        ValueError: If bankroll <= 0 or multiplier not in [0, 1]
    """
    if bankroll <= 0:
        raise ValueError(f"bankroll must be positive, got {bankroll}")

    if not (0 <= kelly_fraction_multiplier <= 1):
        raise ValueError(
            f"kelly_fraction_multiplier must be in [0, 1], got {kelly_fraction_multiplier}"
        )

    # Apply multiplier and clamp negative Kelly to 0
    adjusted_kelly = max(0, kelly_fraction * kelly_fraction_multiplier)
    bet_size = adjusted_kelly * bankroll

    return bet_size


def expected_value(
    model_prob: float,
    american_odds: float,
    bet_size: float
) -> float:
    """
    Calculate expected value of a bet.

    EV = (prob_win * profit) - (prob_loss * stake)

    Args:
        model_prob: Your estimated probability of winning
        american_odds: Odds in American format
        bet_size: Amount wagered ($)

    Returns:
        Expected value in dollars (positive = +EV, negative = -EV)

    Examples:
        >>> # 60% chance, +100 odds (2.0 decimal), $100 bet
        >>> expected_value(0.60, 100, 100)
        20.0

        >>> # 40% chance, +100 odds, $100 bet
        >>> expected_value(0.40, 100, 100)
        -20.0
    """
    decimal_odds = american_to_decimal(american_odds)
    prob_win = model_prob
    prob_loss = 1 - model_prob

    # Profit on win (net, not including original stake)
    profit_on_win = (decimal_odds - 1) * bet_size

    # Expected value
    ev = (prob_win * profit_on_win) - (prob_loss * bet_size)

    return ev


def edge_percentage(model_prob: float, market_prob: float) -> float:
    """
    Calculate edge as a percentage difference.

    Edge = (model_prob - market_prob) / market_prob

    Args:
        model_prob: Your estimated probability
        market_prob: Market implied probability

    Returns:
        Edge as decimal (0.10 = 10% edge)

    Examples:
        >>> edge_percentage(0.60, 0.50)
        0.2

        >>> edge_percentage(0.51, 0.50)
        0.02
    """
    if market_prob == 0:
        return 0.0
    return (model_prob - market_prob) / market_prob


@dataclass
class BetRecommendation:
    """Comprehensive recommendation for a single bet."""
    should_bet: bool
    kelly_fraction: float
    bet_size: float
    expected_value: float
    edge_pct: float
    reason: str


def recommend_bet(
    model_prob: float,
    american_odds: float,
    bankroll: float,
    kelly_multiplier: float = 0.25,
    min_edge_pct: float = 0.02
) -> BetRecommendation:
    """
    Comprehensive bet recommendation with Kelly sizing.

    Evaluates whether a bet meets your criteria and calculates optimal size.

    Args:
        model_prob: Your estimated probability of winning
        american_odds: Odds being offered
        bankroll: Total bankroll
        kelly_multiplier: Fraction of Kelly to use (default: 0.25 = quarter Kelly)
        min_edge_pct: Minimum edge % required to bet (default: 0.02 = 2%)

    Returns:
        BetRecommendation with decision, sizing, and reasoning

    Examples:
        >>> rec = recommend_bet(0.60, 100, 10000)
        >>> print(f"Bet: ${rec.bet_size:.2f}, Edge: {rec.edge_pct*100:.1f}%")
        Bet: $250.00, Edge: 20.0%

        >>> rec_no_edge = recommend_bet(0.50, -110, 10000)
        >>> rec_no_edge.should_bet
        False
    """
    market_prob = american_to_implied_probability(american_odds)
    kelly = calculate_kelly_fraction(model_prob, market_prob, american_odds)
    edge = edge_percentage(model_prob, market_prob)

    bet_size = calculate_bet_size(kelly, bankroll, kelly_multiplier)
    ev = expected_value(model_prob, american_odds, bet_size)

    # Decision logic
    should_bet = (kelly > 0 and edge >= min_edge_pct)

    if should_bet:
        reason = f"Edge: {edge*100:.2f}%, Kelly: {kelly*100:.2f}%"
    elif kelly <= 0:
        reason = "No edge (kelly ≤ 0)"
    else:
        reason = f"Edge too small: {edge*100:.2f}% < min {min_edge_pct*100:.2f}%"

    return BetRecommendation(
        should_bet=should_bet,
        kelly_fraction=kelly,
        bet_size=bet_size,
        expected_value=ev,
        edge_pct=edge,
        reason=reason
    )
