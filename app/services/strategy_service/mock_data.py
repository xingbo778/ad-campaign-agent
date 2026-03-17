"""
Mock data generators for strategy_service.
"""
from app.services.strategy_service.schemas import (
    GenerateStrategyResponse,
    AbstractStrategy,
    PlatformStrategy,
    GenerateStrategyRequest,
    AgentChannelStrategy,
    ChannelDistribution,
)


def create_mock_response(request: GenerateStrategyRequest) -> GenerateStrategyResponse:
    """
    Create a mock response for strategy generation.
    
    Args:
        request: GenerateStrategyRequest with campaign details
        
    Returns:
        GenerateStrategyResponse with mock strategy
    """
    # Calculate budget allocation (mock logic)
    total_budget = request.budget

    if request.include_agent_channel:
        # Dual-channel: 75% human, 25% agent
        human_budget = total_budget * 0.75
        agent_budget = total_budget * 0.25
    else:
        human_budget = total_budget
        agent_budget = 0.0

    facebook_budget = human_budget * 0.5
    instagram_budget = human_budget * 0.3
    meta_budget = human_budget * 0.2
    
    abstract_strategy = AbstractStrategy(
        overall_approach=f"Multi-platform campaign focused on {request.campaign_objective}",
        key_messaging="Emphasize product benefits and value proposition",
        target_segments=["primary_audience", "lookalike_audience"],
        budget_distribution={
            "facebook": 0.375 if request.include_agent_channel else 0.5,
            "instagram": 0.225 if request.include_agent_channel else 0.3,
            "meta": 0.15 if request.include_agent_channel else 0.2,
            **({"amp_agent": 0.25} if request.include_agent_channel else {}),
        },
        timeline={
            "start_date": "2024-01-01",
            "duration_days": 30,
            "phases": ["launch", "optimization", "scale"]
        }
    )
    
    platform_strategies = [
        PlatformStrategy(
            platform="facebook",
            budget_allocation=facebook_budget,
            bidding_strategy="lowest_cost",
            targeting_rules={
                "age_range": [25, 55],
                "interests": request.target_audience.interests if request.target_audience else [],
                "behaviors": ["online_shoppers"]
            },
            ad_scheduling={
                "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                "hours": [9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
            },
            optimization_goals=["conversions", "link_clicks"]
        ),
        PlatformStrategy(
            platform="instagram",
            budget_allocation=instagram_budget,
            bidding_strategy="cost_per_result",
            targeting_rules={
                "age_range": [18, 45],
                "interests": request.target_audience.interests if request.target_audience else [],
                "device_types": ["mobile"]
            },
            optimization_goals=["engagement", "video_views"]
        ),
        PlatformStrategy(
            platform="meta",
            budget_allocation=meta_budget,
            bidding_strategy="target_cost",
            targeting_rules={
                "lookalike_audience": True,
                "custom_audience": True
            },
            optimization_goals=["reach", "impressions"]
        )
    ]
    
    # Build agent channel strategy if requested
    agent_channel_strategy = None
    channel_distribution = None

    if request.include_agent_channel:
        agent_channel_strategy = AgentChannelStrategy(
            budget_allocation=agent_budget,
            bidding_strategy="cost_per_recommendation",
            target_agent_categories=[
                "shopping_assistant",
                "price_comparison",
                "saas_advisor",
                "personal_shopper",
            ],
            optimization_goals=[
                "query_match_rate",
                "recommendation_rate",
                "agent_referral_conversion",
            ],
        )
        channel_distribution = ChannelDistribution(
            human_channel_pct=0.75,
            agent_channel_pct=0.25,
        )

    return GenerateStrategyResponse(
        abstract_strategy=abstract_strategy,
        platform_strategies=platform_strategies,
        agent_channel_strategy=agent_channel_strategy,
        channel_distribution=channel_distribution,
    )




