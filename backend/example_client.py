"""
Example client showing how to use the Betting Framework API programmatically.

Install requests: pip install requests
"""

import requests
import json
from typing import Optional

BASE_URL = "http://localhost:8000"


class BettingClient:
    """Python client for Betting Framework API."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.token = None
        self.headers = {"Content-Type": "application/json"}

    def signup(self, email: str, username: str, password: str) -> dict:
        """Sign up a new user."""
        response = requests.post(
            f"{self.base_url}/api/auth/signup",
            json={"email": email, "username": username, "password": password},
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def login(self, email: str, password: str) -> str:
        """Login and return access token."""
        response = requests.post(
            f"{self.base_url}/api/auth/login",
            json={"email": email, "password": password},
            headers=self.headers,
        )
        response.raise_for_status()
        data = response.json()
        self.token = data["access_token"]
        self.headers["Authorization"] = f"Bearer {self.token}"
        return self.token

    def get_current_user(self) -> dict:
        """Get current authenticated user."""
        response = requests.get(
            f"{self.base_url}/api/auth/me",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def initialize_bankroll(self, initial_amount: float) -> dict:
        """Initialize bankroll."""
        response = requests.post(
            f"{self.base_url}/api/bankroll/initialize",
            json={"initial_amount": initial_amount},
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def get_bankroll(self) -> dict:
        """Get current bankroll."""
        response = requests.get(
            f"{self.base_url}/api/bankroll/current",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def submit_prediction(
        self,
        event_id: str,
        event_description: str,
        outcome: str,
        predicted_probability: float,
        market_probability: float,
        market_odds: float,
        notes: str = None,
    ) -> dict:
        """Submit a prediction."""
        payload = {
            "event_id": event_id,
            "event_description": event_description,
            "outcome": outcome,
            "predicted_probability": predicted_probability,
            "market_probability": market_probability,
            "market_odds": market_odds,
        }
        if notes:
            payload["notes"] = notes

        response = requests.post(
            f"{self.base_url}/api/predictions/",
            json=payload,
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def list_predictions(self, skip: int = 0, limit: int = 100) -> list:
        """List all predictions."""
        response = requests.get(
            f"{self.base_url}/api/predictions/",
            params={"skip": skip, "limit": limit},
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def calculate_kelly(
        self, bankroll: float, win_probability: float, odds: float
    ) -> dict:
        """Calculate Kelly criterion."""
        response = requests.post(
            f"{self.base_url}/api/kelly/calculate",
            json={"bankroll": bankroll, "win_probability": win_probability, "odds": odds},
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def suggest_stake(
        self,
        win_probability: float,
        odds: float,
        kelly_multiplier: float = 0.25,
    ) -> dict:
        """Suggest optimal stake based on user's bankroll."""
        response = requests.post(
            f"{self.base_url}/api/kelly/suggest-stake",
            params={
                "win_probability": win_probability,
                "odds": odds,
                "kelly_multiplier": kelly_multiplier,
            },
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def place_bet(
        self,
        prediction_id: int,
        stake: float,
        kelly_fraction: float = 0.25,
    ) -> dict:
        """Place a new bet."""
        response = requests.post(
            f"{self.base_url}/api/place-bet/",
            json={
                "prediction_id": prediction_id,
                "stake": stake,
                "kelly_fraction": kelly_fraction,
            },
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def transition_bet(self, bet_id: int, new_status: str, notes: str = None) -> dict:
        """Transition bet to new status."""
        payload = {"status": new_status}
        if notes:
            payload["notes"] = notes

        response = requests.post(
            f"{self.base_url}/api/place-bet/{bet_id}/transition",
            json=payload,
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def get_bet(self, bet_id: int) -> dict:
        """Get specific bet."""
        response = requests.get(
            f"{self.base_url}/api/place-bet/{bet_id}",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def get_active_positions(self, skip: int = 0, limit: int = 100) -> list:
        """Get active (LIVE) positions."""
        response = requests.get(
            f"{self.base_url}/api/positions/active",
            params={"skip": skip, "limit": limit},
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def get_positions_summary(self) -> dict:
        """Get positions summary with P&L."""
        response = requests.get(
            f"{self.base_url}/api/positions/summary",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def settle_bet(
        self,
        bet_id: int,
        actual_outcome: str,
        is_winner: bool,
        actual_return: float,
    ) -> dict:
        """Settle a bet with outcome."""
        response = requests.post(
            f"{self.base_url}/api/settle/{bet_id}",
            json={
                "actual_outcome": actual_outcome,
                "is_winner": is_winner,
                "actual_return": actual_return,
            },
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def void_bet(self, bet_id: int, reason: str = None) -> dict:
        """Void a bet (return stake to bankroll)."""
        params = {}
        if reason:
            params["reason"] = reason

        response = requests.post(
            f"{self.base_url}/api/settle/{bet_id}/void",
            params=params,
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def get_audit_logs(self, days: int = 30, limit: int = 100) -> list:
        """Get audit logs."""
        response = requests.get(
            f"{self.base_url}/api/audit-log/",
            params={"days": days, "limit": limit},
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def get_audit_summary(self, days: int = 30) -> dict:
        """Get audit summary."""
        response = requests.get(
            f"{self.base_url}/api/audit-log/summary",
            params={"days": days},
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()


# Example usage
if __name__ == "__main__":
    client = BettingClient()

    try:
        # 1. Sign up
        print("1. Signing up...")
        user = client.signup(
            email="testuser@example.com",
            username="testuser",
            password="password123"
        )
        print(f"   Signed up: {user['username']} ({user['email']})")

        # 2. Login
        print("\n2. Logging in...")
        token = client.login("testuser@example.com", "password123")
        print(f"   Logged in, token: {token[:20]}...")

        # 3. Initialize bankroll
        print("\n3. Initializing bankroll...")
        bankroll = client.initialize_bankroll(10000.0)
        print(f"   Bankroll: ${bankroll['current_balance']:.2f}")

        # 4. Submit prediction
        print("\n4. Submitting prediction...")
        prediction = client.submit_prediction(
            event_id="MLB_2026_06_28_NYY_BOS",
            event_description="Yankees vs Red Sox, June 28 2026",
            outcome="Yankees ML",
            predicted_probability=0.62,
            market_probability=0.55,
            market_odds=1.82,
            notes="Strong bullpen matchup in favor of Yankees"
        )
        print(f"   Prediction submitted: {prediction['event_id']}")
        print(f"   Edge: {prediction['edge_percentage']:.2f}%")
        pred_id = prediction["id"]

        # 5. Calculate Kelly
        print("\n5. Calculating Kelly criterion...")
        kelly = client.calculate_kelly(
            bankroll=10000.0,
            win_probability=0.62,
            odds=1.82
        )
        print(f"   Kelly fraction: {kelly['kelly_fraction']:.4f}")
        print(f"   Suggested stake: ${kelly['suggested_stake']:.2f}")

        # 6. Get suggested stake
        print("\n6. Getting personalized stake suggestion...")
        suggestion = client.suggest_stake(
            win_probability=0.62,
            odds=1.82,
            kelly_multiplier=0.25
        )
        print(f"   Suggested stake: ${suggestion['suggested_stake']:.2f}")
        print(f"   Potential return: ${suggestion['potential_return']:.2f}")

        # 7. Place bet
        print("\n7. Placing bet...")
        bet = client.place_bet(
            prediction_id=pred_id,
            stake=490.0,
            kelly_fraction=0.25
        )
        bet_id = bet["id"]
        print(f"   Bet placed: #{bet_id} for ${bet['stake']:.2f}")
        print(f"   Status: {bet['status']}")

        # 8. Transition through states
        print("\n8. Transitioning bet through states...")
        for status in ["SUBMITTED", "CONFIRMED", "LIVE"]:
            bet = client.transition_bet(bet_id, status)
            print(f"   -> {status}")

        # 9. Get positions
        print("\n9. Checking positions...")
        summary = client.get_positions_summary()
        print(f"   Active bets: {summary['active_bets']}")
        print(f"   Active exposure: ${summary['active_exposure']:.2f}")

        # 10. Settle bet
        print("\n10. Settling bet...")
        settled = client.settle_bet(
            bet_id=bet_id,
            actual_outcome="Yankees won 5-2",
            is_winner=True,
            actual_return=891.80
        )
        print(f"   Settled: {settled['actual_outcome']}")
        print(f"   P&L: ${settled['pnl']:.2f}")
        print(f"   Status: {settled['status']}")

        # 11. Check final bankroll
        print("\n11. Checking final bankroll...")
        final_bankroll = client.get_bankroll()
        print(f"   Balance: ${final_bankroll['current_balance']:.2f}")
        print(f"   Profit/Loss: ${final_bankroll['profit_loss']:.2f}")
        print(f"   ROI: {final_bankroll['roi_percentage']:.2f}%")

        # 12. Check audit logs
        print("\n12. Checking audit logs...")
        logs = client.get_audit_logs(limit=5)
        print(f"   Recent actions: {len(logs)}")
        for log in logs[:3]:
            print(f"   - {log['action']} on {log['entity_type']}")

        # 13. Get audit summary
        summary = client.get_audit_summary(days=1)
        print(f"\n13. Audit summary:")
        print(f"   Total actions: {summary['total_logs']}")
        for action, count in summary["by_action"].items():
            print(f"   - {action}: {count}")

        print("\n✓ Example workflow completed successfully!")

    except requests.exceptions.RequestException as e:
        print(f"\n✗ Error: {e}")
        if hasattr(e.response, "json"):
            print(f"  Details: {e.response.json()}")
