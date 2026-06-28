from config import settings


class KellyCalculator:
    """Service for calculating Kelly criterion bet sizing."""

    @staticmethod
    def calculate_kelly_fraction(
        win_probability: float,
        loss_probability: float,
        decimal_odds: float,
    ) -> dict:
        """
        Calculate Kelly criterion fraction.

        Formula: f* = (bp - q) / b
        where:
            b = (odds - 1)
            p = win probability
            q = loss probability (1 - p)
            f* = Kelly fraction

        Args:
            win_probability: Probability of winning (0-1)
            loss_probability: Probability of loss (0-1)
            decimal_odds: Decimal odds (e.g., 2.0)

        Returns:
            dict with kelly_fraction, suggested_stake, edge, etc.
        """
        if not (0 < win_probability < 1):
            raise ValueError("win_probability must be between 0 and 1")

        if decimal_odds <= 1:
            raise ValueError("decimal_odds must be greater than 1")

        # Ensure probabilities sum to 1
        if not (-0.01 < win_probability + loss_probability - 1 < 0.01):
            raise ValueError("win_probability + loss_probability must equal 1")

        # Calculate Kelly fraction
        b = decimal_odds - 1  # Odds minus 1
        p = win_probability
        q = loss_probability

        kelly_fraction = (b * p - q) / b

        # Clamp to valid range
        kelly_fraction = max(0.0, kelly_fraction)  # Cannot be negative
        kelly_fraction = min(kelly_fraction, settings.MAX_KELLY_FRACTION)

        # Calculate edge
        edge = (p * decimal_odds) - 1  # Expected value

        return {
            "kelly_fraction": kelly_fraction,
            "edge": edge,
            "has_positive_edge": edge > 0,
        }

    @staticmethod
    def calculate_stake(
        bankroll: float,
        kelly_fraction: float,
        kelly_multiplier: float = 0.25,
    ) -> float:
        """
        Calculate actual stake based on bankroll and Kelly fraction.

        Typically uses fractional Kelly (e.g., 25% of full Kelly) for safety.

        Args:
            bankroll: Current available bankroll
            kelly_fraction: Raw Kelly fraction
            kelly_multiplier: Fraction of Kelly to use (default 0.25 = 25%)

        Returns:
            Suggested stake amount
        """
        # Apply fractional Kelly for risk management
        fractional_kelly = kelly_fraction * kelly_multiplier

        # Clamp multiplier
        fractional_kelly = min(fractional_kelly, settings.MAX_KELLY_FRACTION)
        fractional_kelly = max(fractional_kelly, settings.MIN_KELLY_FRACTION)

        stake = bankroll * fractional_kelly

        return round(stake, 2)

    @staticmethod
    def validate_bet_size(
        stake: float,
        bankroll: float,
        daily_loss: float = 0.0,
    ) -> tuple[bool, str]:
        """
        Validate bet size against risk limits.

        Args:
            stake: Proposed stake
            bankroll: Current bankroll
            daily_loss: Daily losses so far

        Returns:
            Tuple of (is_valid, message)
        """
        # Check single bet limit
        if stake > bankroll * settings.MAX_SINGLE_BET_FRACTION:
            return (
                False,
                f"Stake exceeds max single bet ({settings.MAX_SINGLE_BET_FRACTION*100:.1f}% of bankroll)",
            )

        # Check daily loss limit
        if daily_loss > bankroll * settings.MAX_DAILY_LOSS_FRACTION:
            return (
                False,
                f"Daily loss limit exceeded ({settings.MAX_DAILY_LOSS_FRACTION*100:.1f}% of bankroll)",
            )

        return True, "Bet size valid"
