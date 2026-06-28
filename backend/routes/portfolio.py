"""Portfolio engine routes - simulation, allocation, and regime control."""

from fastapi import APIRouter, HTTPException, status
import logging

from schemas.portfolio import (
    PortfolioSimulationRequest,
    PortfolioSimulationResult,
    AllocationRequest,
    AllocationResult,
    RegimeRequest,
    RegimeState,
)
from services.portfolio_service import (
    PortfolioSimulator,
    PortfolioAllocator,
    RegimeController,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.post("/simulate", response_model=PortfolioSimulationResult)
async def simulate_portfolio(request: PortfolioSimulationRequest):
    """
    Run Monte Carlo simulation for portfolio paths.

    Simulates 1000+ paths of portfolio returns given strategy parameters and correlations.
    Returns equity curve percentiles, drawdown distribution, and risk/return statistics.

    Args:
        request: Portfolio parameters including:
            - strategies: List of 5 strategy inputs (name, return, vol, Sharpe, max_dd, weight)
            - num_simulations: Number of Monte Carlo runs (default 1000)
            - time_horizon_days: Trading days to simulate (default 252)
            - initial_capital: Starting capital (default 100,000)
            - rebalance_frequency: How often to rebalance (daily/weekly/monthly/quarterly)

    Returns:
        PortfolioSimulationResult with:
            - Final capital statistics (mean, median, std, min, max)
            - Return statistics (mean, median, std)
            - Risk metrics (Sharpe, Sortino, max drawdown)
            - Equity curve percentiles (5th, 25th, 50th, 75th, 95th)
            - Drawdown distribution
            - Correlation drag and diversification ratio

    Example:
        POST /api/portfolio/simulate
        {
            "strategies": [
                {"name": "MLB", "expected_return": 15, "volatility": 12, "sharpe_ratio": 1.25, "max_drawdown": -0.15, "weight": 0.2},
                {"name": "Crypto", "expected_return": 25, "volatility": 40, "sharpe_ratio": 0.625, "max_drawdown": -0.50, "weight": 0.15},
                {"name": "Earnings", "expected_return": 18, "volatility": 18, "sharpe_ratio": 1.0, "max_drawdown": -0.20, "weight": 0.25},
                {"name": "AI", "expected_return": 22, "volatility": 32, "sharpe_ratio": 0.69, "max_drawdown": -0.35, "weight": 0.20},
                {"name": "Econ", "expected_return": 12, "volatility": 8, "sharpe_ratio": 1.5, "max_drawdown": -0.10, "weight": 0.20}
            ],
            "num_simulations": 1000,
            "time_horizon_days": 252,
            "initial_capital": 100000
        }
    """
    try:
        # Validate inputs
        if len(request.strategies) != 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must provide exactly 5 strategies (MLB, Crypto, Earnings, AI, Econ)",
            )

        # Validate weights sum to approximately 1.0
        weights_sum = sum(s.weight for s in request.strategies)
        if weights_sum < 0.99 or weights_sum > 1.01:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Weights must sum to 1.0 (got {weights_sum:.2f})",
            )

        logger.info(f"Running Monte Carlo simulation with {request.num_simulations} paths")

        # Run simulation
        result = PortfolioSimulator.simulate_paths(request)

        logger.info(
            f"Simulation complete - Sharpe: {result.sharpe_ratio:.2f}, "
            f"Sortino: {result.sortino_ratio:.2f}, "
            f"Max DD: {result.max_drawdown_worst:.1f}%"
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Simulation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation failed: {str(e)}",
        )


@router.post("/allocation", response_model=AllocationResult)
async def calculate_allocation(request: AllocationRequest):
    """
    Calculate optimal portfolio allocation given strategy metrics.

    Uses correlation matrix (MLB 0.1-0.2, AI-Earnings 0.65-0.85) and betas
    to find optimal weights via Kelly criterion, maximum Sharpe ratio, or minimum variance.

    Args:
        request: Strategy metrics and optimization method:
            - strategies: List of strategies with return, vol, Sharpe
            - optimization_method: "kelly" (growth), "sharpe" (risk-adjusted), "min_variance", or "equal_weight"
            - kelly_fraction: Fraction of full Kelly to apply (default 0.25)

    Returns:
        AllocationResult with:
            - Optimal weights for each strategy
            - Kelly fractions per strategy
            - Portfolio expected return, volatility, Sharpe ratio
            - Concentration metrics (Herfindahl index)

    Example:
        POST /api/portfolio/allocation
        {
            "strategies": [
                {"name": "MLB", "expected_return": 15, "volatility": 12, "sharpe_ratio": 1.25, "max_drawdown": -0.15, "weight": 0.2},
                ...
            ],
            "optimization_method": "kelly",
            "kelly_fraction": 0.25
        }
    """
    try:
        if len(request.strategies) != 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must provide exactly 5 strategies",
            )

        if request.optimization_method not in ["kelly", "sharpe", "min_variance", "equal_weight"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="optimization_method must be kelly, sharpe, min_variance, or equal_weight",
            )

        logger.info(f"Calculating allocation using {request.optimization_method} method")

        # Calculate allocation
        result = PortfolioAllocator.allocate(request)

        logger.info(
            f"Allocation complete - Expected return: {result.portfolio_expected_return:.1f}%, "
            f"Volatility: {result.portfolio_volatility:.1f}%, "
            f"Sharpe: {result.portfolio_sharpe_ratio:.2f}"
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Allocation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Allocation failed: {str(e)}",
        )


@router.post("/regime", response_model=RegimeState)
async def assess_regime(request: RegimeRequest):
    """
    Assess current market regime and adjust portfolio weights.

    Evaluates VIX, funding rates, and sentiment to classify regime (Low Vol, Normal, High Vol, Stress)
    and recommends weight adjustments.

    Args:
        request: Current market conditions:
            - current_vix: Current VIX level
            - vix_percentile_30d: VIX percentile over 30 days
            - crypto_funding_rate: Current crypto funding rate (%)
            - market_sentiment: Sentiment score (-1 to +1)
            - base_weights: Current allocation weights
            - strategies: Strategy info for context

    Returns:
        RegimeState with:
            - Regime name (Low Vol, Normal, High Vol, Stress)
            - VIX level and percentile
            - Crypto funding regime
            - Regime-adjusted weights
            - Adjustment factors applied per strategy
            - Recommended action (Hold, Reduce Risk, Increase Risk, Rebalance)
            - Explanation of recommendation

    Example:
        POST /api/portfolio/regime
        {
            "current_vix": 18.5,
            "vix_percentile_30d": 60,
            "crypto_funding_rate": 0.01,
            "market_sentiment": 0.3,
            "base_weights": {
                "MLB": 0.2,
                "Crypto": 0.15,
                "Earnings": 0.25,
                "AI": 0.20,
                "Econ": 0.20
            },
            "strategies": [...]
        }
    """
    try:
        if len(request.strategies) != 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must provide exactly 5 strategies",
            )

        if len(request.base_weights) != 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must provide weights for all 5 strategies",
            )

        # Validate weight sum
        weights_sum = sum(request.base_weights.values())
        if weights_sum < 0.99 or weights_sum > 1.01:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Base weights must sum to 1.0 (got {weights_sum:.2f})",
            )

        logger.info(f"Assessing regime - VIX: {request.current_vix:.1f}, Sentiment: {request.market_sentiment:.2f}")

        # Assess regime
        result = RegimeController.assess_regime(request)

        logger.info(
            f"Regime: {result.regime_name}, "
            f"Recommendation: {result.recommended_action}"
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Regime assessment failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Regime assessment failed: {str(e)}",
        )


@router.get("/health")
async def portfolio_health():
    """Health check for portfolio engine."""
    return {
        "status": "ok",
        "service": "portfolio_engine",
        "endpoints": [
            "POST /api/portfolio/simulate - Monte Carlo simulation",
            "POST /api/portfolio/allocation - Optimal allocation",
            "POST /api/portfolio/regime - Regime assessment",
        ],
    }
