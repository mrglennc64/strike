from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class LineCapturCreate(BaseModel):
    """Create a line capture."""
    date: str
    tag: str  # 'open' or 'close'
    event: str
    player: str
    line: float
    over_odds: float
    under_odds: float
    bookmaker: str
    sport: str = "baseball_mlb"
    market: str = "pitcher_strikeouts"


class LineCaptureResponse(BaseModel):
    """Line capture response."""
    id: int
    date: str
    captured_at: datetime
    tag: str
    event: str
    player: str
    line: float
    over_odds: float
    under_odds: float
    bookmaker: str
    sport: str
    market: str
    created_at: datetime

    class Config:
        from_attributes = True


class CLVBetCreate(BaseModel):
    """Create a CLV bet record."""
    date: str = Field(..., description="YYYY-MM-DD format")
    player: str = Field(..., description="Player name")
    your_side: str = Field(..., description="'over' or 'under'")
    your_american: float = Field(..., description="Your odds in American format")
    close_over_american: Optional[float] = Field(None, description="Close over odds")
    close_under_american: Optional[float] = Field(None, description="Close under odds")
    bookmaker: Optional[str] = None
    sport: str = "baseball_mlb"
    market: str = "pitcher_strikeouts"
    notes: Optional[str] = None


class CLVBetUpdate(BaseModel):
    """Update CLV bet with close odds."""
    close_over_american: float
    close_under_american: float


class CLVBetResponse(BaseModel):
    """CLV bet response."""
    id: int
    date: str
    player: str
    your_side: str
    your_american: float
    your_decimal: Optional[float]
    close_over_american: Optional[float]
    close_under_american: Optional[float]
    close_fair_prob: Optional[float]
    your_break_even: float
    clv_value: Optional[float]
    status: str
    sport: str
    market: str
    bookmaker: Optional[str]
    notes: Optional[str]
    created_at: datetime
    recorded_at: Optional[datetime]
    closed_at: Optional[datetime]
    analyzed_at: Optional[datetime]

    class Config:
        from_attributes = True


class LineMovementAnalysis(BaseModel):
    """Line movement for a player."""
    date: str
    player: str
    open_line: float
    close_line: float
    open_fair_prob: float
    close_fair_prob: float
    fair_prob_move: float
    direction: str  # 'OVER' or 'UNDER'


class CLVAnalysisResponse(BaseModel):
    """CLV analysis response."""
    analysis_date: datetime
    captures_count: int
    pairs_analyzed: int
    line_changed_count: int
    fair_moves: List[float]
    mean_fair_move: float
    median_fair_move: float
    max_fair_move: float
    avg_available_clv: float
    biggest_movers: List[LineMovementAnalysis]


class CLVLeaderboardEntry(BaseModel):
    """Leaderboard entry."""
    rank: int
    player: str
    date: str
    side: str
    your_odds: float
    close_odds_over: Optional[float]
    close_odds_under: Optional[float]
    clv_value: Optional[float]
    status: str


class CLVLeaderboardResponse(BaseModel):
    """Leaderboard response."""
    total_bets: int
    analyzed_bets: int
    mean_clv: Optional[float]
    median_clv: Optional[float]
    max_clv: Optional[float]
    min_clv: Optional[float]
    positive_clv_count: int
    entries: List[CLVLeaderboardEntry]


class OddsAPIResponse(BaseModel):
    """Response structure from Odds API capture."""
    timestamp: datetime
    rows_captured: int
    sport: str
    market: str
    tag: str


class CLVBatchRecordRequest(BaseModel):
    """Batch record multiple bets."""
    bets: List[CLVBetCreate]


class CLVBatchRecordResponse(BaseModel):
    """Batch record response."""
    success_count: int
    error_count: int
    recorded_ids: List[int]
    errors: List[dict]
