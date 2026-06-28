from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from services import RiskManager
from database import SessionLocal


class RiskLimitsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to check risk limits before executing bet-related operations.

    Intercepts requests to /api/place-bet and /api/predictions endpoints.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Process request and check risk limits.

        Args:
            request: HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response
        """
        # Only check limits for bet/prediction endpoints
        if not self._should_check_limits(request.url.path):
            return await call_next(request)

        # Extract user_id from request (would come from JWT token)
        user_id = getattr(request.state, "user_id", None)
        if not user_id:
            return await call_next(request)

        # For place-bet, check stake against limits
        if request.method == "POST" and "/place-bet" in request.url.path:
            try:
                body = await request.json()
                stake = body.get("stake", 0)

                db = SessionLocal()
                is_valid, errors = RiskManager.check_all_limits(user_id, stake, db)
                db.close()

                if not is_valid:
                    return JSONResponse(
                        status_code=429,  # Too Many Requests
                        content={
                            "detail": "Risk limits exceeded",
                            "errors": errors,
                        },
                    )
            except Exception as e:
                # Log error but allow request to proceed
                print(f"Risk check error: {e}")

        return await call_next(request)

    @staticmethod
    def _should_check_limits(path: str) -> bool:
        """
        Determine if path requires risk limit checking.

        Args:
            path: Request path

        Returns:
            True if limits should be checked
        """
        risk_paths = [
            "/api/place-bet",
            "/api/predictions",
        ]
        return any(risk_path in path for risk_path in risk_paths)
