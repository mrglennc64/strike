"""
CLV-Tracker Routes

Endpoints for capturing lines, recording bets, analyzing CLV, and viewing leaderboards.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from services import CLVTracker
from schemas import (
    LineCapturCreate,
    LineCaptureResponse,
    CLVBetCreate,
    CLVBetUpdate,
    CLVBetResponse,
    CLVAnalysisResponse,
    CLVLeaderboardResponse,
    OddsAPIResponse,
    CLVBatchRecordRequest,
    CLVBatchRecordResponse,
)

router = APIRouter(prefix="/api/clv", tags=["clv"])


# ========== Line Capture Endpoints ==========


@router.post("/capture", response_model=OddsAPIResponse)
async def capture_odds(
    tag: str = Query(..., description="'open' or 'close'"),
    sport: str = Query("baseball_mlb"),
    market: str = Query("pitcher_strikeouts"),
    regions: str = Query("us"),
    db: Session = Depends(get_db),
):
    """
    Capture player prop lines from Odds API.

    Called at open (1pm) and close (10pm) to track line movement.

    Args:
        tag: 'open' for morning capture, 'close' for evening
        sport: sport slug (default: baseball_mlb)
        market: market slug (default: pitcher_strikeouts)
        regions: comma-separated regions (default: us)

    Returns:
        Capture summary with timestamp and row count
    """
    try:
        tracker = CLVTracker(db)
        rows_captured = tracker.capture_from_odds_api(tag, sport, market, regions)

        return OddsAPIResponse(
            timestamp=datetime.utcnow(),
            rows_captured=rows_captured,
            sport=sport,
            market=market,
            tag=tag,
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )


@router.post("/capture/manual", response_model=LineCaptureResponse)
async def capture_manual(
    request: LineCapturCreate,
    db: Session = Depends(get_db),
):
    """
    Manually record a line capture (for testing/fallback).

    Args:
        request: Line capture details

    Returns:
        Created capture record
    """
    tracker = CLVTracker(db)
    capture = tracker.record_line_capture(
        date=request.date,
        tag=request.tag,
        event=request.event,
        player=request.player,
        line=request.line,
        over_odds=request.over_odds,
        under_odds=request.under_odds,
        bookmaker=request.bookmaker,
        sport=request.sport,
        market=request.market,
    )
    return capture


# ========== CLV Bet Recording Endpoints ==========


@router.post("/record-bet", response_model=CLVBetResponse)
async def record_bet(
    request: CLVBetCreate,
    db: Session = Depends(get_db),
):
    """
    Record a CLV bet.

    If close odds provided, CLV is calculated immediately.
    Otherwise, bet is marked PENDING until closed.

    Args:
        request: Bet details (player, date, your_side, your_odds, optional close odds)

    Returns:
        Recorded bet with CLV if calculated
    """
    tracker = CLVTracker(db)

    # Validate side
    if request.your_side.lower() not in ("over", "under"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="your_side must be 'over' or 'under'",
        )

    try:
        bet = tracker.record_bet(
            date=request.date,
            player=request.player,
            your_side=request.your_side.lower(),
            your_american=request.your_american,
            close_over_american=request.close_over_american,
            close_under_american=request.close_under_american,
            bookmaker=request.bookmaker,
            sport=request.sport,
            market=request.market,
            notes=request.notes,
        )
        return bet
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/record-bet/batch", response_model=CLVBatchRecordResponse)
async def record_bets_batch(
    request: CLVBatchRecordRequest,
    db: Session = Depends(get_db),
):
    """
    Record multiple CLV bets in batch.

    Args:
        request: List of bet details

    Returns:
        Summary of success/error counts and recorded IDs
    """
    tracker = CLVTracker(db)
    success_count = 0
    error_count = 0
    recorded_ids = []
    errors = []

    for idx, bet_req in enumerate(request.bets):
        try:
            if bet_req.your_side.lower() not in ("over", "under"):
                errors.append({
                    "index": idx,
                    "player": bet_req.player,
                    "error": "your_side must be 'over' or 'under'",
                })
                error_count += 1
                continue

            bet = tracker.record_bet(
                date=bet_req.date,
                player=bet_req.player,
                your_side=bet_req.your_side.lower(),
                your_american=bet_req.your_american,
                close_over_american=bet_req.close_over_american,
                close_under_american=bet_req.close_under_american,
                bookmaker=bet_req.bookmaker,
                sport=bet_req.sport,
                market=bet_req.market,
                notes=bet_req.notes,
            )
            recorded_ids.append(bet.id)
            success_count += 1
        except Exception as e:
            errors.append({
                "index": idx,
                "player": bet_req.player,
                "error": str(e),
            })
            error_count += 1

    return CLVBatchRecordResponse(
        success_count=success_count,
        error_count=error_count,
        recorded_ids=recorded_ids,
        errors=errors,
    )


@router.put("/close-bet/{bet_id}", response_model=CLVBetResponse)
async def close_bet(
    bet_id: int,
    request: CLVBetUpdate,
    db: Session = Depends(get_db),
):
    """
    Close an open bet with closing odds.

    Calculates CLV based on close odds.

    Args:
        bet_id: ID of bet to close
        request: Close odds (over and under)

    Returns:
        Updated bet with calculated CLV
    """
    tracker = CLVTracker(db)
    try:
        bet = tracker.close_bet(
            bet_id=bet_id,
            close_over_american=request.close_over_american,
            close_under_american=request.close_under_american,
        )
        return bet
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ========== Analysis Endpoints ==========


@router.get("/analysis", response_model=CLVAnalysisResponse)
async def get_analysis(
    sport: str = Query("baseball_mlb"),
    market: str = Query("pitcher_strikeouts"),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Analyze line movement open->close.

    Returns line changes, fair probability moves, and biggest movers.

    Args:
        sport: sport slug (default: baseball_mlb)
        market: market slug (default: pitcher_strikeouts)
        limit: number of biggest movers to return (default: 10)

    Returns:
        Analysis with mean/median/max fair moves and top movers
    """
    tracker = CLVTracker(db)
    analysis = tracker.analyze_line_movement(sport, market, limit)

    return CLVAnalysisResponse(
        analysis_date=analysis["analysis_date"],
        captures_count=analysis["captures_count"],
        pairs_analyzed=analysis["pairs_analyzed"],
        line_changed_count=analysis["line_changed_count"],
        fair_moves=analysis["fair_moves"],
        mean_fair_move=analysis["mean_fair_move"],
        median_fair_move=analysis["median_fair_move"],
        max_fair_move=analysis["max_fair_move"],
        avg_available_clv=analysis["avg_available_clv"],
        biggest_movers=analysis["biggest_movers"],
    )


# ========== Leaderboard Endpoints ==========


@router.get("/leaderboard", response_model=CLVLeaderboardResponse)
async def get_leaderboard(
    sport: str = Query("baseball_mlb"),
    market: str = Query("pitcher_strikeouts"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """
    Get CLV leaderboard sorted by CLV value (descending).

    Only includes bets with calculated CLV.

    Args:
        sport: sport slug (default: baseball_mlb)
        market: market slug (default: pitcher_strikeouts)
        limit: max entries to return (default: 100)

    Returns:
        Leaderboard with stats and ranked entries
    """
    tracker = CLVTracker(db)
    leaderboard = tracker.get_leaderboard(sport, market, limit)

    return CLVLeaderboardResponse(
        total_bets=leaderboard["total_bets"],
        analyzed_bets=leaderboard["analyzed_bets"],
        mean_clv=leaderboard["mean_clv"],
        median_clv=leaderboard["median_clv"],
        max_clv=leaderboard["max_clv"],
        min_clv=leaderboard["min_clv"],
        positive_clv_count=leaderboard["positive_clv_count"],
        entries=leaderboard["entries"],
    )


@router.get("/leaderboard/player/{player}", response_model=list[CLVBetResponse])
async def get_player_history(
    player: str,
    db: Session = Depends(get_db),
):
    """
    Get all CLV bets for a player.

    Args:
        player: player name

    Returns:
        List of bets for player, sorted by date descending
    """
    tracker = CLVTracker(db)
    bets = tracker.get_player_history(player)

    if not bets:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No bets found for player {player}",
        )

    return bets


@router.get("/bets/date-range", response_model=list[CLVBetResponse])
async def get_bets_date_range(
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """
    Get CLV bets in a date range.

    Args:
        start_date: start date (YYYY-MM-DD)
        end_date: end date (YYYY-MM-DD)

    Returns:
        List of bets in range, sorted by date descending
    """
    tracker = CLVTracker(db)
    bets = tracker.get_bets_by_date_range(start_date, end_date)

    return bets


# ========== Health/Info Endpoints ==========


@router.get("/info")
async def clv_info():
    """
    CLV-Tracker API info and usage guide.

    Returns:
        API endpoint reference and examples
    """
    return {
        "service": "CLV-Tracker",
        "description": "Closing Line Value tracking for sports betting edge detection",
        "endpoints": {
            "capture": {
                "POST /api/clv/capture": "Capture lines from Odds API",
                "POST /api/clv/capture/manual": "Manually record a line capture",
            },
            "bets": {
                "POST /api/clv/record-bet": "Record a single CLV bet",
                "POST /api/clv/record-bet/batch": "Record multiple bets",
                "PUT /api/clv/close-bet/{bet_id}": "Close bet with close odds",
            },
            "analysis": {
                "GET /api/clv/analysis": "Analyze line movement open->close",
            },
            "leaderboard": {
                "GET /api/clv/leaderboard": "CLV leaderboard sorted by CLV",
                "GET /api/clv/leaderboard/player/{player}": "Player history",
                "GET /api/clv/bets/date-range": "Bets in date range",
            },
        },
        "cron_tasks": {
            "capture_open": "Call @ 1pm: capture_open()",
            "capture_close": "Call @ 10pm: capture_close()",
            "calculate_clv": "Call @ 11pm: calculate_clv()",
        },
        "env_vars": [
            "ODDS_API_KEY: The Odds API key (required for API captures)",
        ],
        "clv_formula": "CLV = fair_prob(close) - break_even_prob(your_odds)",
    }
