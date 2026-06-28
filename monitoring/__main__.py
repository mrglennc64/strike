"""
Portfolio Monitoring Service

Main entry point for portfolio monitoring.
Runs allocation monitor, correlation monitor, and regime alerter in parallel.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from allocation_monitor import AllocationMonitor, monitor_loop as allocation_monitor_loop
from correlation_monitor import CorrelationMonitor
from regime_alerter import RegimeAlerter

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def correlation_monitor_loop(monitor: CorrelationMonitor, check_interval: int = 3600):
    """
    Correlation monitoring loop (runs hourly by default).

    Args:
        monitor: CorrelationMonitor instance
        check_interval: Check interval in seconds (default 1 hour)
    """
    logger.info(f"Starting correlation monitor (check interval: {check_interval}s)")

    while True:
        try:
            snapshot = monitor.generate_snapshot()
            if snapshot:
                monitor.record_snapshot(snapshot)

                # Alert on high clustering
                if snapshot.alert_level.value in ["HIGH", "CRITICAL"]:
                    logger.warning(f"CORRELATION ALERT: {snapshot.alert_message}")

        except Exception as e:
            logger.error(f"Correlation monitor loop error: {str(e)}")

        await asyncio.sleep(check_interval)


async def regime_alerter_loop(alerter: RegimeAlerter, check_interval: int = 300):
    """
    Regime monitoring loop (runs every 5 minutes by default).

    Args:
        alerter: RegimeAlerter instance
        check_interval: Check interval in seconds (default 5 minutes)
    """
    logger.info(f"Starting regime alerter (check interval: {check_interval}s)")

    while True:
        try:
            state = alerter.assess_regime()
            if state:
                alerter.record_regime_state(state)
                alerter.send_alert(state)

        except Exception as e:
            logger.error(f"Regime alerter loop error: {str(e)}")

        await asyncio.sleep(check_interval)


async def main():
    """Run all monitoring services in parallel"""
    logger.info("=" * 70)
    logger.info("Portfolio Monitoring Service Starting")
    logger.info("=" * 70)

    # Initialize monitors
    allocation_monitor = AllocationMonitor()
    correlation_monitor = CorrelationMonitor()
    regime_alerter = RegimeAlerter()

    # Check intervals from environment
    allocation_interval = int(os.getenv("ALLOCATION_CHECK_INTERVAL", "300"))  # 5 min
    correlation_interval = int(os.getenv("CORRELATION_CHECK_INTERVAL", "3600"))  # 1 hour
    regime_interval = int(os.getenv("REGIME_CHECK_INTERVAL", "300"))  # 5 min

    logger.info(f"Allocation monitor interval: {allocation_interval}s")
    logger.info(f"Correlation monitor interval: {correlation_interval}s")
    logger.info(f"Regime alerter interval: {regime_interval}s")

    # Run all monitors concurrently
    try:
        await asyncio.gather(
            allocation_monitor_loop(allocation_monitor, allocation_interval),
            correlation_monitor_loop(correlation_monitor, correlation_interval),
            regime_alerter_loop(regime_alerter, regime_interval)
        )
    except KeyboardInterrupt:
        logger.info("Monitoring service stopped by user")
    except Exception as e:
        logger.error(f"Monitoring service error: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
