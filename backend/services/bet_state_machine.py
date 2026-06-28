from enum import Enum
from datetime import datetime
from typing import Tuple


class BetStatus(str, Enum):
    """Bet status states."""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    CONFIRMED = "CONFIRMED"
    LIVE = "LIVE"
    SETTLED = "SETTLED"
    CANCELLED = "CANCELLED"
    VOID = "VOID"


class BetStateMachine:
    """State machine for managing bet lifecycle."""

    # Valid transitions: from_state -> list of allowed to_states
    VALID_TRANSITIONS = {
        BetStatus.PENDING: [BetStatus.SUBMITTED, BetStatus.CANCELLED],
        BetStatus.SUBMITTED: [BetStatus.CONFIRMED, BetStatus.CANCELLED],
        BetStatus.CONFIRMED: [BetStatus.LIVE, BetStatus.CANCELLED],
        BetStatus.LIVE: [BetStatus.SETTLED, BetStatus.VOID],
        BetStatus.SETTLED: [],  # Terminal state
        BetStatus.CANCELLED: [],  # Terminal state
        BetStatus.VOID: [],  # Terminal state
    }

    @staticmethod
    def is_transition_valid(from_status: str, to_status: str) -> bool:
        """
        Check if transition is valid.

        Args:
            from_status: Current status
            to_status: Target status

        Returns:
            True if transition is allowed
        """
        try:
            from_status_enum = BetStatus(from_status)
            to_status_enum = BetStatus(to_status)
            allowed = BetStateMachine.VALID_TRANSITIONS.get(from_status_enum, [])
            return to_status_enum in allowed
        except ValueError:
            return False

    @staticmethod
    def get_allowed_transitions(current_status: str) -> list[str]:
        """
        Get list of allowed next statuses.

        Args:
            current_status: Current bet status

        Returns:
            List of allowed statuses
        """
        try:
            current_enum = BetStatus(current_status)
            allowed = BetStateMachine.VALID_TRANSITIONS.get(current_enum, [])
            return [s.value for s in allowed]
        except ValueError:
            return []

    @staticmethod
    def transition_with_timestamp(
        current_status: str,
        new_status: str,
    ) -> Tuple[bool, str, dict]:
        """
        Perform state transition and return timestamp fields to update.

        Args:
            current_status: Current bet status
            new_status: Target bet status

        Returns:
            Tuple of (is_valid, message, updates_dict)
        """
        if not BetStateMachine.is_transition_valid(current_status, new_status):
            return False, f"Invalid transition: {current_status} -> {new_status}", {}

        updates = {"status": new_status}
        now = datetime.utcnow()

        # Set appropriate timestamp based on new status
        if new_status == BetStatus.SUBMITTED:
            updates["submitted_at"] = now
        elif new_status == BetStatus.CONFIRMED:
            updates["confirmed_at"] = now
        elif new_status == BetStatus.LIVE:
            updates["live_at"] = now
        elif new_status in [BetStatus.SETTLED, BetStatus.VOID]:
            updates["settled_at"] = now

        return True, f"Transitioned to {new_status}", updates

    @staticmethod
    def can_be_settled(status: str) -> bool:
        """
        Check if bet can be settled.

        Args:
            status: Current bet status

        Returns:
            True if bet is in LIVE state (can be settled)
        """
        return status == BetStatus.LIVE.value

    @staticmethod
    def is_terminal(status: str) -> bool:
        """
        Check if status is terminal (no further transitions possible).

        Args:
            status: Current bet status

        Returns:
            True if no further transitions allowed
        """
        try:
            status_enum = BetStatus(status)
            return len(BetStateMachine.VALID_TRANSITIONS.get(status_enum, [])) == 0
        except ValueError:
            return True
