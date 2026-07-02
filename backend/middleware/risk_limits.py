import logging

from fastapi import Request
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from services import RiskManager
from database import SessionLocal
from config import settings

logger = logging.getLogger(__name__)


class RiskLimitsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to check risk limits before executing bet-related operations.

    Defense-in-depth: the place-bet route also enforces auth and risk limits
    directly. This middleware independently blocks over-limit stakes and fails
    CLOSED — if the risk check cannot be completed, the request is rejected
    rather than allowed through.

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
        # Only enforce on the stake-carrying place-bet POST. Other matched paths
        # are gated by their own route-level auth dependency.
        if not (request.method == "POST" and "/place-bet" in request.url.path):
            return await call_next(request)

        # Resolve the authenticated user from the verified bearer token. If the
        # caller is unauthenticated, let the route's own auth dependency return
        # 401 rather than duplicating that response here.
        user_id = self._user_id_from_token(request)
        if user_id is None:
            return await call_next(request)

        try:
            body = await request.json()
            stake = body.get("stake", 0)

            db = SessionLocal()
            try:
                is_valid, errors = RiskManager.check_all_limits(user_id, stake, db)
            finally:
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
            # Fail closed: a risk control that cannot verify the stake must not
            # let the bet through.
            logger.error("Risk check failed; rejecting request: %s", e)
            return JSONResponse(
                status_code=503,
                content={"detail": "Risk check unavailable; request rejected"},
            )

        return await call_next(request)

    @staticmethod
    def _user_id_from_token(request: Request):
        """Return the user id from a valid bearer token, or None if absent/invalid."""
        auth = request.headers.get("authorization", "")
        if not auth.lower().startswith("bearer "):
            return None
        token = auth[7:].strip()
        if not token:
            return None
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            sub = payload.get("sub")
            return int(sub) if sub is not None else None
        except (JWTError, ValueError):
            return None
