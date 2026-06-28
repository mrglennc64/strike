from pydantic import BaseModel, Field


class KellyRequest(BaseModel):
    """Request schema for Kelly calculator."""
    bankroll: float = Field(..., gt=0, description="Current bankroll")
    win_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Probability of winning"
    )
    odds: float = Field(..., gt=1.0, description="Decimal odds")
    loss_probability: float = Field(None, description="Probability of loss (1 - win_probability)")

    @property
    def loss_prob(self) -> float:
        """Calculate loss probability if not provided."""
        if self.loss_probability is not None:
            return self.loss_probability
        return 1.0 - self.win_probability


class KellyResponse(BaseModel):
    """Response schema for Kelly calculation."""
    kelly_fraction: float  # Raw Kelly percentage
    suggested_stake: float  # Fractional Kelly stake (default 25%)
    win_probability: float
    odds: float
    edge: float  # Calculated edge
    has_positive_edge: bool

    class Config:
        from_attributes = True
