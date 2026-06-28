import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Production-ready application configuration from environment variables.

    All variables can be overridden via environment or .env file.
    """

    # ============================================================================
    # Application Settings
    # ============================================================================
    APP_NAME: str = "Betting Framework API - Production"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    WORKERS: int = int(os.getenv("WORKERS", "4"))

    # ============================================================================
    # Database Configuration
    # ============================================================================
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://betting_user:betting_password@localhost:5432/betting_db"
    )
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "20"))
    DATABASE_POOL_RECYCLE: int = int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))
    DATABASE_POOL_PRE_PING: bool = True

    # ============================================================================
    # Authentication & Security
    # ============================================================================
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "change-me-in-production-at-least-32-characters-long"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # ============================================================================
    # Risk Management
    # ============================================================================
    MAX_SINGLE_BET_FRACTION: float = float(os.getenv("MAX_SINGLE_BET_FRACTION", "0.05"))
    MAX_DAILY_LOSS_FRACTION: float = float(os.getenv("MAX_DAILY_LOSS_FRACTION", "0.10"))
    MAX_KELLY_FRACTION: float = float(os.getenv("MAX_KELLY_FRACTION", "0.25"))
    MIN_KELLY_FRACTION: float = float(os.getenv("MIN_KELLY_FRACTION", "0.01"))
    MAX_CONCURRENT_BETS: int = int(os.getenv("MAX_CONCURRENT_BETS", "50"))

    # ============================================================================
    # External APIs - Odds & Markets
    # ============================================================================
    ODDS_API_KEY: str = os.getenv("ODDS_API_KEY", "")
    ODDS_API_BASE_URL: str = "https://api.the-odds-api.com/v4"
    ODDS_API_TIMEOUT: int = int(os.getenv("ODDS_API_TIMEOUT", "30"))

    # ============================================================================
    # Prediction Markets
    # ============================================================================
    POLYMARKET_KEY: str = os.getenv("POLYMARKET_KEY", "")
    POLYMARKET_SECRET: str = os.getenv("POLYMARKET_SECRET", "")
    KALSHI_API_KEY: str = os.getenv("KALSHI_API_KEY", "")
    KALSHI_API_SECRET: str = os.getenv("KALSHI_API_SECRET", "")

    # ============================================================================
    # Data Sources
    # ============================================================================
    STATCAST_API_KEY: str = os.getenv("STATCAST_API_KEY", "")
    FRED_API_KEY: str = os.getenv("FRED_API_KEY", "")
    ALPHA_VANTAGE_KEY: str = os.getenv("ALPHA_VANTAGE_KEY", "")
    FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "")

    # ============================================================================
    # Middleware Configuration
    # ============================================================================
    ENABLE_RATE_LIMITING: bool = os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true"
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
    CORS_ORIGINS: list = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:8080,https://example.com"
    ).split(",")

    # ============================================================================
    # Logging Configuration
    # ============================================================================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/betting_framework.log")
    LOG_FILE_MAX_BYTES: int = int(os.getenv("LOG_FILE_MAX_BYTES", "10485760"))
    LOG_FILE_BACKUPS: int = int(os.getenv("LOG_FILE_BACKUPS", "10"))

    # ============================================================================
    # Cache Configuration
    # ============================================================================
    ENABLE_CACHE: bool = os.getenv("ENABLE_CACHE", "true").lower() == "true"
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # ============================================================================
    # Model Configuration
    # ============================================================================
    MLB_MODEL_PATH: str = os.getenv("MLB_MODEL_PATH", "./models/mlb_strikeout_model.pkl")
    ECONOMICS_MODEL_PATH: str = os.getenv("ECONOMICS_MODEL_PATH", "./models/economics_model.pkl")
    EARNINGS_MODEL_PATH: str = os.getenv("EARNINGS_MODEL_PATH", "./models/earnings_model.pkl")

    # ============================================================================
    # Feature Flags
    # ============================================================================
    ENABLE_MLB_EDGE: bool = os.getenv("ENABLE_MLB_EDGE", "true").lower() == "true"
    ENABLE_TENNIS_EDGE: bool = os.getenv("ENABLE_TENNIS_EDGE", "true").lower() == "true"
    ENABLE_CRICKET_EDGE: bool = os.getenv("ENABLE_CRICKET_EDGE", "true").lower() == "true"
    ENABLE_HORSE_EDGE: bool = os.getenv("ENABLE_HORSE_EDGE", "true").lower() == "true"
    ENABLE_HOCKEY_EDGE: bool = os.getenv("ENABLE_HOCKEY_EDGE", "true").lower() == "true"
    ENABLE_ECONOMICS_EDGE: bool = os.getenv("ENABLE_ECONOMICS_EDGE", "true").lower() == "true"
    ENABLE_EARNINGS_EDGE: bool = os.getenv("ENABLE_EARNINGS_EDGE", "true").lower() == "true"

    # ============================================================================
    # Monitoring & Observability
    # ============================================================================
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
    ENABLE_METRICS: bool = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    METRICS_PORT: int = int(os.getenv("METRICS_PORT", "8001"))

    # ============================================================================
    # Email Configuration (for alerts)
    # ============================================================================
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    ALERT_EMAIL: str = os.getenv("ALERT_EMAIL", "admin@example.com")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
