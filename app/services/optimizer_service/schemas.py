"""
Pydantic schemas for optimizer_service.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SummarizeRecentRunsRequest(BaseModel):
    """Request model for optimization analysis."""
    campaign_ids: List[str] = Field(..., description="List of campaign IDs to analyze")
    lookback_days: int = Field(default=30, ge=1, le=365, description="Number of days to look back")
    include_agent_metrics: bool = Field(
        default=False, description="Include AMP agent channel metrics in the analysis"
    )


class Suggestion(BaseModel):
    """Optimization suggestion."""
    type: str = Field(..., description="Type of suggestion")
    description: str = Field(..., description="Suggestion description")
    impact: str = Field(..., description="Expected impact")
    priority: str = Field(..., description="Priority: high, medium, low")


class AgentChannelMetrics(BaseModel):
    """Metrics specific to the AMP agent channel."""
    total_query_matches: int = Field(default=0, description="Times product matched agent queries")
    total_recommendations: int = Field(default=0, description="Times agents recommended the product to users")
    total_agent_referrals: int = Field(default=0, description="Conversions from agent referrals")
    query_match_rate: float = Field(default=0.0, description="Query match rate percentage")
    recommendation_rate: float = Field(default=0.0, description="Recommendation rate (recommendations / matches)")
    cost_per_recommendation: float = Field(default=0.0, description="CPR in USD")
    agent_channel_spend: float = Field(default=0.0, description="Total spend on agent channel")
    agent_channel_roas: float = Field(default=0.0, description="Return on ad spend for agent channel")


class Summary(BaseModel):
    """Campaign performance summary."""
    total_campaigns: int
    total_spend: float
    total_impressions: int
    total_clicks: int
    average_ctr: float
    average_cpc: float
    top_performing_campaigns: List[str]
    underperforming_campaigns: List[str]
    agent_channel_metrics: Optional[AgentChannelMetrics] = Field(
        None, description="AMP agent channel metrics (present when include_agent_metrics=True)"
    )


class SummarizeRecentRunsResponse(BaseModel):
    """Response model for optimization analysis."""
    summary: Summary
    suggestions: List[Suggestion]




