"""
Health check module for comprehensive system diagnostics.

Provides health status of all components:
- Database connectivity
- External APIs
- Cache systems
- Model availability
- Verticals operational status
"""

from datetime import datetime
from typing import Dict, Any
import logging
from sqlalchemy import text

from config import settings
from database import engine

logger = logging.getLogger(__name__)


class HealthChecker:
    """Comprehensive health check for all system components."""

    @staticmethod
    def check_database() -> Dict[str, Any]:
        """
        Check database connectivity and performance.

        Returns:
            Dict with database status and metrics
        """
        try:
            with engine.connect() as conn:
                # Basic connectivity
                conn.execute(text("SELECT 1"))

                # Check tables exist
                result = conn.execute(text("""
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                """))
                table_count = result.scalar()

                return {
                    "status": "ok",
                    "type": "PostgreSQL",
                    "table_count": table_count,
                    "message": f"{table_count} tables found"
                }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Database connection failed"
            }

    @staticmethod
    def check_apis() -> Dict[str, Any]:
        """
        Check external API configurations and availability.

        Returns:
            Dict with API status
        """
        apis = {}

        # Odds API
        if settings.ODDS_API_KEY:
            apis["odds_api"] = {
                "configured": True,
                "status": "ready",
                "provider": "The Odds API"
            }
        else:
            apis["odds_api"] = {
                "configured": False,
                "status": "not_configured",
                "provider": "The Odds API"
            }

        # Polymarket
        if settings.POLYMARKET_KEY:
            apis["polymarket"] = {
                "configured": True,
                "status": "ready",
                "provider": "Polymarket"
            }
        else:
            apis["polymarket"] = {
                "configured": False,
                "status": "not_configured",
                "provider": "Polymarket"
            }

        # Kalshi
        if settings.KALSHI_API_KEY:
            apis["kalshi"] = {
                "configured": True,
                "status": "ready",
                "provider": "Kalshi"
            }
        else:
            apis["kalshi"] = {
                "configured": False,
                "status": "not_configured",
                "provider": "Kalshi"
            }

        # Data sources
        if settings.FRED_API_KEY:
            apis["fred"] = {
                "configured": True,
                "status": "ready",
                "provider": "Federal Reserve Economic Data"
            }
        else:
            apis["fred"] = {
                "configured": False,
                "status": "not_configured",
                "provider": "Federal Reserve Economic Data"
            }

        return apis

    @staticmethod
    def check_cache() -> Dict[str, Any]:
        """
        Check Redis/cache system status.

        Returns:
            Dict with cache status
        """
        if not settings.ENABLE_CACHE:
            return {
                "enabled": False,
                "status": "disabled",
                "message": "Cache disabled in configuration"
            }

        try:
            import redis
            r = redis.from_url(settings.REDIS_URL)
            r.ping()

            return {
                "enabled": True,
                "status": "ok",
                "provider": "Redis",
                "ttl_seconds": settings.CACHE_TTL_SECONDS
            }
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                "enabled": True,
                "status": "error",
                "error": str(e),
                "message": "Cache connection failed"
            }

    @staticmethod
    def check_models() -> Dict[str, Any]:
        """
        Check model availability and paths.

        Returns:
            Dict with model status
        """
        import os

        models = {}

        # MLB Model
        models["mlb"] = {
            "enabled": settings.ENABLE_MLB_EDGE,
            "path": settings.MLB_MODEL_PATH,
            "exists": os.path.exists(settings.MLB_MODEL_PATH) if settings.ENABLE_MLB_EDGE else False
        }

        # Economics Model
        models["economics"] = {
            "enabled": settings.ENABLE_ECONOMICS_EDGE,
            "path": settings.ECONOMICS_MODEL_PATH,
            "exists": os.path.exists(settings.ECONOMICS_MODEL_PATH) if settings.ENABLE_ECONOMICS_EDGE else False
        }

        # Earnings Model
        models["earnings"] = {
            "enabled": settings.ENABLE_EARNINGS_EDGE,
            "path": settings.EARNINGS_MODEL_PATH,
            "exists": os.path.exists(settings.EARNINGS_MODEL_PATH) if settings.ENABLE_EARNINGS_EDGE else False
        }

        return models

    @staticmethod
    def check_verticals() -> Dict[str, Any]:
        """
        Check all 5 sports verticals status.

        Returns:
            Dict with vertical status
        """
        return {
            "mlb": {
                "name": "MLB Strikeout Edge",
                "enabled": settings.ENABLE_MLB_EDGE,
                "status": "operational" if settings.ENABLE_MLB_EDGE else "disabled"
            },
            "tennis": {
                "name": "Tennis Elo+Markov",
                "enabled": settings.ENABLE_TENNIS_EDGE,
                "status": "operational" if settings.ENABLE_TENNIS_EDGE else "disabled"
            },
            "cricket": {
                "name": "Cricket LBW Edge",
                "enabled": settings.ENABLE_CRICKET_EDGE,
                "status": "operational" if settings.ENABLE_CRICKET_EDGE else "disabled"
            },
            "horse": {
                "name": "Horse Racing Benter",
                "enabled": settings.ENABLE_HORSE_EDGE,
                "status": "operational" if settings.ENABLE_HORSE_EDGE else "disabled"
            },
            "hockey": {
                "name": "NHL SOG Model",
                "enabled": settings.ENABLE_HOCKEY_EDGE,
                "status": "operational" if settings.ENABLE_HOCKEY_EDGE else "disabled"
            }
        }

    @staticmethod
    def check_configuration() -> Dict[str, Any]:
        """
        Check application configuration status.

        Returns:
            Dict with configuration details
        """
        return {
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "rate_limiting": settings.ENABLE_RATE_LIMITING,
            "rate_limit_per_minute": settings.RATE_LIMIT_PER_MINUTE,
            "cache_enabled": settings.ENABLE_CACHE,
            "cors_origins": len(settings.CORS_ORIGINS),
            "port": settings.PORT,
            "workers": settings.WORKERS
        }

    @classmethod
    def full_check(cls) -> Dict[str, Any]:
        """
        Perform comprehensive health check of all systems.

        Returns:
            Dict with complete health status
        """
        database_status = cls.check_database()
        overall_healthy = database_status["status"] == "ok"

        return {
            "status": "healthy" if overall_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,

            "components": {
                "database": database_status,
                "apis": cls.check_apis(),
                "cache": cls.check_cache(),
                "models": cls.check_models(),
                "configuration": cls.check_configuration(),
            },

            "verticals": cls.check_verticals(),

            "summary": {
                "database_ok": database_status["status"] == "ok",
                "apis_configured": sum(1 for api in cls.check_apis().values() if api.get("configured")),
                "verticals_enabled": sum(1 for v in cls.check_verticals().values() if v["enabled"]),
                "all_critical_ok": overall_healthy
            }
        }


def get_health_status() -> Dict[str, Any]:
    """
    Get full health status (convenience function).

    Returns:
        Dict with complete health status
    """
    return HealthChecker.full_check()


def get_database_status() -> Dict[str, Any]:
    """Get database-only status."""
    return HealthChecker.check_database()


def get_api_status() -> Dict[str, Any]:
    """Get external APIs status."""
    return HealthChecker.check_apis()


def get_verticals_status() -> Dict[str, Any]:
    """Get all verticals status."""
    return HealthChecker.check_verticals()
