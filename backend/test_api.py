"""
Example API tests using FastAPI TestClient.

Run with: pytest test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from database import Base, get_db
from config import settings

# Use SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


class TestHealth:
    """Test health check endpoints."""

    def test_health(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_root(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "endpoints" in response.json()


class TestAuth:
    """Test authentication endpoints."""

    def test_signup_success(self):
        response = client.post(
            "/api/auth/signup",
            json={
                "email": "testuser@example.com",
                "username": "testuser",
                "password": "password123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "testuser@example.com"
        assert data["username"] == "testuser"
        assert "id" in data

    def test_signup_duplicate_email(self):
        # First signup
        client.post(
            "/api/auth/signup",
            json={
                "email": "duplicate@example.com",
                "username": "user1",
                "password": "password123",
            },
        )

        # Try duplicate
        response = client.post(
            "/api/auth/signup",
            json={
                "email": "duplicate@example.com",
                "username": "user2",
                "password": "password123",
            },
        )
        assert response.status_code == 400

    def test_login_success(self):
        # Create user
        client.post(
            "/api/auth/signup",
            json={
                "email": "login@example.com",
                "username": "loginuser",
                "password": "password123",
            },
        )

        # Login
        response = client.post(
            "/api/auth/login",
            json={"email": "login@example.com", "password": "password123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_password(self):
        # Create user
        client.post(
            "/api/auth/signup",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "password123",
            },
        )

        # Wrong password
        response = client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401


class TestBankroll:
    """Test bankroll endpoints."""

    def test_initialize_bankroll(self):
        response = client.post(
            "/api/bankroll/initialize", json={"initial_amount": 10000.0}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["initial_amount"] == 10000.0
        assert data["current_balance"] == 10000.0
        assert data["roi_percentage"] == 0.0

    def test_get_bankroll(self):
        client.post("/api/bankroll/initialize", json={"initial_amount": 10000.0})

        response = client.get("/api/bankroll/current")
        assert response.status_code == 200
        data = response.json()
        assert data["initial_amount"] == 10000.0

    def test_update_bankroll(self):
        client.post("/api/bankroll/initialize", json={"initial_amount": 10000.0})

        response = client.put(
            "/api/bankroll/update", json={"current_balance": 9500.0}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["current_balance"] == 9500.0
        assert data["profit_loss"] == -500.0


class TestPredictions:
    """Test prediction endpoints."""

    def test_submit_prediction(self):
        response = client.post(
            "/api/predictions/",
            json={
                "event_id": "MLB_2026_06_28",
                "event_description": "Yankees vs Red Sox",
                "outcome": "Yankees ML",
                "predicted_probability": 0.62,
                "market_probability": 0.55,
                "market_odds": 1.82,
                "notes": "Strong matchup",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["event_id"] == "MLB_2026_06_28"
        assert data["has_positive_edge"] is True
        assert data["edge_percentage"] > 0

    def test_get_prediction(self):
        # Create prediction
        create_resp = client.post(
            "/api/predictions/",
            json={
                "event_id": "TEST_EVENT",
                "event_description": "Test event",
                "outcome": "Test outcome",
                "predicted_probability": 0.60,
                "market_probability": 0.50,
                "market_odds": 2.0,
            },
        )
        pred_id = create_resp.json()["id"]

        # Get prediction
        response = client.get(f"/api/predictions/{pred_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["event_id"] == "TEST_EVENT"

    def test_list_predictions(self):
        # Create multiple predictions
        for i in range(3):
            client.post(
                "/api/predictions/",
                json={
                    "event_id": f"EVENT_{i}",
                    "event_description": f"Event {i}",
                    "outcome": f"Outcome {i}",
                    "predicted_probability": 0.60,
                    "market_probability": 0.50,
                    "market_odds": 2.0,
                },
            )

        response = client.get("/api/predictions/?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3


class TestKelly:
    """Test Kelly criterion calculation."""

    def test_calculate_kelly(self):
        response = client.post(
            "/api/kelly/calculate",
            json={"bankroll": 10000.0, "win_probability": 0.62, "odds": 1.82},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["kelly_fraction"] > 0
        assert data["suggested_stake"] > 0
        assert data["has_positive_edge"] is True

    def test_kelly_no_edge(self):
        response = client.post(
            "/api/kelly/calculate",
            json={"bankroll": 10000.0, "win_probability": 0.50, "odds": 1.82},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["has_positive_edge"] is False

    def test_kelly_invalid_probability(self):
        response = client.post(
            "/api/kelly/calculate",
            json={"bankroll": 10000.0, "win_probability": 1.5, "odds": 1.82},
        )
        assert response.status_code == 400


class TestBets:
    """Test bet placement and state transitions."""

    def setup_method(self):
        """Setup for each test."""
        # Initialize bankroll
        client.post("/api/bankroll/initialize", json={"initial_amount": 10000.0})

        # Create prediction
        pred_resp = client.post(
            "/api/predictions/",
            json={
                "event_id": "TEST_BET_EVENT",
                "event_description": "Test event for betting",
                "outcome": "Test outcome",
                "predicted_probability": 0.62,
                "market_probability": 0.55,
                "market_odds": 1.82,
            },
        )
        self.prediction_id = pred_resp.json()["id"]

    def test_place_bet(self):
        response = client.post(
            "/api/place-bet/",
            json={"prediction_id": self.prediction_id, "stake": 500.0},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PENDING"
        assert data["stake"] == 500.0

    def test_bet_state_transitions(self):
        # Place bet
        bet_resp = client.post(
            "/api/place-bet/",
            json={"prediction_id": self.prediction_id, "stake": 500.0},
        )
        bet_id = bet_resp.json()["id"]

        # Transition to SUBMITTED
        resp = client.post(
            f"/api/place-bet/{bet_id}/transition", json={"status": "SUBMITTED"}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "SUBMITTED"

        # Transition to CONFIRMED
        resp = client.post(
            f"/api/place-bet/{bet_id}/transition", json={"status": "CONFIRMED"}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "CONFIRMED"

        # Transition to LIVE
        resp = client.post(
            f"/api/place-bet/{bet_id}/transition", json={"status": "LIVE"}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "LIVE"

    def test_invalid_transition(self):
        # Place bet (PENDING)
        bet_resp = client.post(
            "/api/place-bet/",
            json={"prediction_id": self.prediction_id, "stake": 500.0},
        )
        bet_id = bet_resp.json()["id"]

        # Try invalid transition PENDING -> LIVE
        resp = client.post(
            f"/api/place-bet/{bet_id}/transition", json={"status": "LIVE"}
        )
        assert resp.status_code == 400


class TestSettlement:
    """Test bet settlement."""

    def setup_method(self):
        """Setup for each test."""
        # Initialize bankroll
        client.post("/api/bankroll/initialize", json={"initial_amount": 10000.0})

        # Create prediction
        pred_resp = client.post(
            "/api/predictions/",
            json={
                "event_id": "SETTLE_TEST",
                "event_description": "Settle test",
                "outcome": "Test",
                "predicted_probability": 0.62,
                "market_probability": 0.55,
                "market_odds": 1.82,
            },
        )
        self.prediction_id = pred_resp.json()["id"]

        # Place and move to LIVE
        bet_resp = client.post(
            "/api/place-bet/",
            json={"prediction_id": self.prediction_id, "stake": 500.0},
        )
        self.bet_id = bet_resp.json()["id"]

        client.post(
            f"/api/place-bet/{self.bet_id}/transition", json={"status": "SUBMITTED"}
        )
        client.post(
            f"/api/place-bet/{self.bet_id}/transition", json={"status": "CONFIRMED"}
        )
        client.post(
            f"/api/place-bet/{self.bet_id}/transition", json={"status": "LIVE"}
        )

    def test_settle_winning_bet(self):
        response = client.post(
            f"/api/settle/{self.bet_id}",
            json={
                "actual_outcome": "Event happened",
                "is_winner": True,
                "actual_return": 910.0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_winner"] is True
        assert data["pnl"] == 410.0
        assert data["status"] == "SETTLED"

    def test_settle_losing_bet(self):
        response = client.post(
            f"/api/settle/{self.bet_id}",
            json={
                "actual_outcome": "Event did not happen",
                "is_winner": False,
                "actual_return": 0.0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_winner"] is False
        assert data["pnl"] == -500.0


class TestAudit:
    """Test audit logging."""

    def test_audit_log_created_on_action(self):
        # Perform action
        client.post("/api/bankroll/initialize", json={"initial_amount": 10000.0})

        # Check audit log
        response = client.get("/api/audit-log/?limit=10")
        assert response.status_code == 200
        logs = response.json()
        assert len(logs) > 0

    def test_audit_summary(self):
        response = client.get("/api/audit-log/summary?days=30")
        assert response.status_code == 200
        data = response.json()
        assert "period_days" in data
        assert "total_logs" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
