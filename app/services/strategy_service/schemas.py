"""
Pydantic schemas for strategy_service.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Creative(BaseModel):
    """Creative model for strategy generation."""
    creative_id: str
    type: str
    headline: Optional[str] = None
    description: Optional[str] = None
    product_id: str
    platform: str


class TargetAudience(BaseModel):
    """Target audience definition."""
    demographics: Optional[Dict[str, Any]] = Field(default_factory=dict)
    interests: Optional[List[str]] = Field(default_factory=list)


class GenerateStrategyRequest(BaseModel):
    """Request model for strategy generation."""
    creatives: List[Creative] = Field(..., description="List of creatives")
    campaign_objective: str = Field(..., description="Campaign objective")
    budget: float = Field(..., gt=0, description="Campaign budget")
    target_audience: Optional[TargetAudience] = Field(None, description="Optional audience information")
    include_agent_channel: bool = Field(
        default=False, description="Whether to include AMP agent channel in strategy"
    )


class PlatformStrategy(BaseModel):
    """Platform-specific strategy."""
    platform: str
    budget_allocation: float
    bidding_strategy: str
    targeting_rules: Dict[str, Any]
    ad_scheduling: Optional[Dict[str, Any]] = None
    optimization_goals: List[str] = Field(default_factory=list)


class AbstractStrategy(BaseModel):
    """Abstract/high-level strategy."""
    overall_approach: str
    key_messaging: str
    target_segments: List[str]
    budget_distribution: Dict[str, float]
    timeline: Dict[str, Any]


class AgentChannelStrategy(BaseModel):
    """Strategy for the AMP agent channel."""
    budget_allocation: float = Field(..., description="Budget allocated to agent channel in USD")
    bidding_strategy: str = Field(
        default="cost_per_recommendation",
        description="AMP bidding: cost_per_recommendation | cost_per_query_match | cost_per_action"
    )
    target_agent_categories: List[str] = Field(
        default_factory=list, description="Agent categories to target"
    )
    optimization_goals: List[str] = Field(
        default_factory=list, description="e.g. query_match_rate, recommendation_rate, agent_referral_conversion"
    )


class ChannelDistribution(BaseModel):
    """Budget split between human and agent channels."""
    human_channel_pct: float = Field(default=0.75, ge=0, le=1, description="Percentage of budget for human channels")
    agent_channel_pct: float = Field(default=0.25, ge=0, le=1, description="Percentage of budget for AMP agent channel")


class GenerateStrategyResponse(BaseModel):
    """Response model for strategy generation."""
    abstract_strategy: AbstractStrategy
    platform_strategies: List[PlatformStrategy]
    agent_channel_strategy: Optional[AgentChannelStrategy] = Field(
        None, description="Strategy for AMP agent channel (present when include_agent_channel=True)"
    )
    channel_distribution: Optional[ChannelDistribution] = Field(
        None, description="Human vs agent budget split (present when include_agent_channel=True)"
    )


