from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from models import Bet, Bankroll
from config import settings


class RiskManager:
    """Service for managing risk limits and enforcing constraints."""

    @staticmethod
    def check_single_bet_limit(
        user_id: int,
        proposed_stake: float,
        db: Session,
    ) -> tuple[bool, str]:
        """
        Check if proposed bet exceeds single bet limit.

        Args:
            user_id: User ID
            proposed_stake: Proposed stake amount
            db: Database session

        Returns:
            Tuple of (is_valid, message)
        """
        bankroll = db.query(Bankroll).filter(Bankroll.user_id == user_id).first()
        if not bankroll:
            return False, "Bankroll not found"

        max_single_bet = bankroll.current_balance * settings.MAX_SINGLE_BET_FRACTION

        if proposed_stake > max_single_bet:
            return (
                False,
                f"Stake ${proposed_stake:.2f} exceeds limit ${max_single_bet:.2f} ({settings.MAX_SINGLE_BET_FRACTION*100:.1f}% of bankroll)",
            )

        return True, "Single bet limit OK"

    @staticmethod
    def check_daily_loss_limit(
        user_id: int,
        db: Session,
    ) -> tuple[bool, str, float]:
        """
        Check daily loss and remaining loss allowance.

        Args:
            user_id: User ID
            db: Database session

        Returns:
            Tuple of (is_valid, message, remaining_allowance)
        """
        bankroll = db.query(Bankroll).filter(Bankroll.user_id == user_id).first()
        if not bankroll:
            return False, "Bankroll not found", 0.0

        daily_loss_limit = bankroll.initial_amount * settings.MAX_DAILY_LOSS_FRACTION

        # Calculate today's losses
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())

        today_losses = (
            db.query(func.sum(Bet.pnl))
            .filter(
                Bet.user_id == user_id,
                Bet.is_settled == True,
                Bet.pnl < 0,
                Bet.settled_at >= today_start,
            )
            .scalar() or 0.0
        )

        # Convert to absolute loss amount
        today_losses = abs(today_losses)

        remaining = daily_loss_limit - today_losses

        if today_losses >= daily_loss_limit:
            return (
                False,
                f"Daily loss limit reached: ${today_losses:.2f} / ${daily_loss_limit:.2f}",
                remaining,
            )

        return (
            True,
            f"Daily loss limit OK: ${today_losses:.2f} / ${daily_loss_limit:.2f}",
            remaining,
        )

    @staticmethod
    def check_bankroll_sufficient(
        user_id: int,
        required_amount: float,
        db: Session,
    ) -> tuple[bool, str]:
        """
        Check if bankroll has sufficient funds.

        Args:
            user_id: User ID
            required_amount: Amount needed
            db: Database session

        Returns:
            Tuple of (is_valid, message)
        """
        bankroll = db.query(Bankroll).filter(Bankroll.user_id == user_id).first()
        if not bankroll:
            return False, "Bankroll not found"

        if bankroll.current_balance < required_amount:
            return (
                False,
                f"Insufficient funds: ${bankroll.current_balance:.2f} < ${required_amount:.2f}",
            )

        return True, "Sufficient funds available"

    @staticmethod
    def check_all_limits(
        user_id: int,
        proposed_stake: float,
        db: Session,
    ) -> tuple[bool, list[str]]:
        """
        Check all risk limits.

        Args:
            user_id: User ID
            proposed_stake: Proposed stake
            db: Database session

        Returns:
            Tuple of (all_valid, list_of_errors)
        """
        errors = []

        # Check bankroll exists and has funds
        is_valid, msg = RiskManager.check_bankroll_sufficient(user_id, proposed_stake, db)
        if not is_valid:
            errors.append(msg)

        # Check single bet limit
        is_valid, msg = RiskManager.check_single_bet_limit(user_id, proposed_stake, db)
        if not is_valid:
            errors.append(msg)

        # Check daily loss limit
        is_valid, msg, _ = RiskManager.check_daily_loss_limit(user_id, db)
        if not is_valid:
            errors.append(msg)

        return len(errors) == 0, errors

    @staticmethod
    def get_risk_summary(user_id: int, db: Session) -> dict:
        """
        Get risk summary for user.

        Args:
            user_id: User ID
            db: Database session

        Returns:
            dict with risk metrics
        """
        bankroll = db.query(Bankroll).filter(Bankroll.user_id == user_id).first()
        if not bankroll:
            return {}

        # Get today's stats
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())

        today_settled = (
            db.query(Bet)
            .filter(
                Bet.user_id == user_id,
                Bet.is_settled == True,
                Bet.settled_at >= today_start,
            )
            .all()
        )

        today_pnl = sum(b.pnl or 0 for b in today_settled)
        today_losses = abs(min(today_pnl, 0))

        # Get active bets
        active_bets = (
            db.query(Bet)
            .filter(
                Bet.user_id == user_id,
                Bet.status.in_(["LIVE"]),
            )
            .all()
        )

        active_exposure = sum(b.stake or 0 for b in active_bets)

        daily_limit = bankroll.initial_amount * settings.MAX_DAILY_LOSS_FRACTION
        single_limit = bankroll.current_balance * settings.MAX_SINGLE_BET_FRACTION

        return {
            "bankroll": bankroll.current_balance,
            "initial_bankroll": bankroll.initial_amount,
            "single_bet_limit": single_limit,
            "daily_loss_limit": daily_limit,
            "today_pnl": today_pnl,
            "today_losses": today_losses,
            "remaining_daily_loss": max(0, daily_limit - today_losses),
            "active_bets": len(active_bets),
            "active_exposure": active_exposure,
        }
