"""
Mock data generators for optimizer_service.
"""
from app.services.optimizer_service.schemas import (
    SummarizeRecentRunsResponse,
    Summary,
    Suggestion,
    SummarizeRecentRunsRequest,
    AgentChannelMetrics,
)


def create_mock_response(request: SummarizeRecentRunsRequest) -> SummarizeRecentRunsResponse:
    """
    Create a mock response for optimization analysis.
    
    Args:
        request: SummarizeRecentRunsRequest with campaign IDs
        
    Returns:
        SummarizeRecentRunsResponse with mock summary and suggestions
    """
    # Build agent channel metrics if requested
    agent_metrics = None
    if request.include_agent_metrics:
        agent_metrics = AgentChannelMetrics(
            total_query_matches=8500,
            total_recommendations=2720,
            total_agent_referrals=340,
            query_match_rate=12.5,
            recommendation_rate=32.0,
            cost_per_recommendation=0.45,
            agent_channel_spend=1224.0,
            agent_channel_roas=4.2,
        )

    summary = Summary(
        total_campaigns=len(request.campaign_ids),
        total_spend=15000.0,
        total_impressions=500000,
        total_clicks=25000,
        average_ctr=5.0,
        average_cpc=0.60,
        top_performing_campaigns=request.campaign_ids[:2] if len(request.campaign_ids) >= 2 else request.campaign_ids,
        underperforming_campaigns=request.campaign_ids[-1:] if len(request.campaign_ids) >= 3 else [],
        agent_channel_metrics=agent_metrics,
    )

    suggestions = [
        Suggestion(
            type="budget_reallocation",
            description="Reallocate budget from underperforming campaigns to top performers",
            impact="Expected 15-20% increase in ROI",
            priority="high"
        ),
        Suggestion(
            type="creative_refresh",
            description="Refresh creatives for campaigns with declining CTR",
            impact="Expected 10-15% improvement in engagement",
            priority="medium"
        ),
        Suggestion(
            type="audience_expansion",
            description="Expand targeting to lookalike audiences for top campaigns",
            impact="Expected 25-30% increase in reach",
            priority="medium"
        ),
        Suggestion(
            type="bidding_optimization",
            description="Adjust bidding strategy for campaigns with high CPC",
            impact="Expected 20% reduction in cost per conversion",
            priority="high"
        ),
    ]

    # Add AMP-specific suggestions when agent metrics are included
    if request.include_agent_metrics:
        suggestions.extend([
            Suggestion(
                type="agent_creative_refresh",
                description="Update product schemas with latest features and certifications to improve query match rate",
                impact="Expected 20-25% increase in agent query matches",
                priority="high"
            ),
            Suggestion(
                type="agent_incentive_adjustment",
                description="Increase agent commission rate from 5% to 8% for top-performing product categories",
                impact="Expected 15-20% increase in agent recommendation rate",
                priority="medium"
            ),
        ])

    return SummarizeRecentRunsResponse(
        summary=summary,
        suggestions=suggestions,
    )




