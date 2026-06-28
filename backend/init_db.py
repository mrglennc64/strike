#!/usr/bin/env python
"""
Database initialization script.

Creates all database tables and initializes schema.
Run this script before starting the application for the first time.

Usage:
    python init_db.py
    python init_db.py --drop-all  # Drop existing tables (CAUTION)
    python init_db.py --seed      # Populate with sample data
"""

import os
import sys
import argparse
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_database(drop_all: bool = False):
    """
    Initialize database schema.

    Args:
        drop_all: If True, drop all existing tables first
    """
    try:
        from database import Base, engine
        from models import (
            User, Bankroll, Prediction, Bet, AuditLog,
            EarningsPredictionRecord, EarningsHistoryRecord,
            CLVBet, LineCapture
        )

        logger.info("=" * 60)
        logger.info("Starting Database Initialization")
        logger.info("=" * 60)

        if drop_all:
            logger.warning("DROPPING ALL EXISTING TABLES...")
            Base.metadata.drop_all(bind=engine)
            logger.warning("All tables dropped")

        logger.info("Creating database schema...")

        # Create all tables
        Base.metadata.create_all(bind=engine)

        logger.info("Database schema created successfully")

        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(
                __import__('sqlalchemy').text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public' ORDER BY table_name"
                )
            )
            tables = [row[0] for row in result.fetchall()]

            logger.info(f"Created {len(tables)} tables:")
            for table in tables:
                logger.info(f"  - {table}")

        logger.info("=" * 60)
        logger.info("Database initialization completed successfully!")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        return False


def seed_database():
    """
    Populate database with sample data for testing.
    """
    try:
        from database import SessionLocal
        from models import User
        from passlib.context import CryptContext

        logger.info("=" * 60)
        logger.info("Seeding Database with Sample Data")
        logger.info("=" * 60)

        db = SessionLocal()
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        # Check if test user already exists
        existing_user = db.query(User).filter(
            User.email == "test@example.com"
        ).first()

        if existing_user:
            logger.info("Test user already exists, skipping seed")
            db.close()
            return True

        # Create test user
        hashed_password = pwd_context.hash("testpassword123")
        test_user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=hashed_password,
            is_active=True
        )

        db.add(test_user)
        db.commit()

        logger.info(f"Created test user: testuser (test@example.com)")
        logger.info("Password: testpassword123")

        db.close()

        logger.info("=" * 60)
        logger.info("Database seeding completed successfully!")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"Database seeding failed: {e}", exc_info=True)
        return False


def verify_database():
    """
    Verify database is properly configured and accessible.
    """
    try:
        from database import engine
        from sqlalchemy import text

        logger.info("=" * 60)
        logger.info("Verifying Database Connection")
        logger.info("=" * 60)

        with engine.connect() as conn:
            # Test connection
            result = conn.execute(text("SELECT 1"))
            logger.info("✓ Database connection successful")

            # Check table count
            result = conn.execute(text("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """))
            table_count = result.scalar()
            logger.info(f"✓ Found {table_count} tables in database")

            # Check pool settings
            logger.info(f"✓ Connection pool size: {engine.pool.size()}")
            logger.info(f"✓ Connection pool overflow: {engine.pool.overflow}")

        logger.info("=" * 60)
        logger.info("Database verification completed successfully!")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"Database verification failed: {e}", exc_info=True)
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Initialize and manage Betting Framework database"
    )

    parser.add_argument(
        "--drop-all",
        action="store_true",
        help="Drop all existing tables before creating schema (CAUTION)"
    )

    parser.add_argument(
        "--seed",
        action="store_true",
        help="Populate database with sample data for testing"
    )

    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify database connection and schema"
    )

    args = parser.parse_args()

    success = True

    # Initialize database
    if not args.verify:
        success = init_database(drop_all=args.drop_all) and success

    # Seed database if requested
    if args.seed and success:
        success = seed_database() and success

    # Verify database
    if args.verify or success:
        success = verify_database() and success

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
