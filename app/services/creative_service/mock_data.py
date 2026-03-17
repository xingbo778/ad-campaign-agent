"""
Mock data generators for creative_service.
"""
from typing import List, Optional
from app.services.creative_service.schemas import (
    Creative,
    GenerateCreativesResponse,
    Product,
    AgentCreativeOutput,
    GenerateAgentCreativesResponse,
)


def generate_mock_creatives(products: List[Product], platform: str) -> List[Creative]:
    """
    Generate mock creatives for given products and platform.
    
    Args:
        products: List of products
        platform: Target platform
        
    Returns:
        List of Creative objects
    """
    creatives = []
    
    for idx, product in enumerate(products):
        # Text creative
        creatives.append(Creative(
            creative_id=f"creative_text_{idx + 1}",
            type="text",
            headline=f"Discover {product.name}",
            description=product.description or f"Amazing {product.name} for you",
            primary_text=f"Get {product.name} now! Only ${product.price:.2f}",
            call_to_action="Shop Now",
            product_id=product.product_id,
            platform=platform
        ))
        
        # Image creative
        creatives.append(Creative(
            creative_id=f"creative_image_{idx + 1}",
            type="image",
            headline=f"{product.name} - Special Offer",
            description=f"Premium {product.category} product",
            primary_text=f"Transform your experience with {product.name}",
            call_to_action="Learn More",
            image_url=f"https://example.com/images/{product.product_id}.jpg",
            product_id=product.product_id,
            platform=platform
        ))
        
        # Video creative (only for first product)
        if idx == 0:
            creatives.append(Creative(
                creative_id=f"creative_video_{idx + 1}",
                type="video",
                headline=f"Introducing {product.name}",
                description="Watch how it works",
                primary_text=f"See {product.name} in action",
                call_to_action="Watch Video",
                video_url=f"https://example.com/videos/{product.product_id}.mp4",
                product_id=product.product_id,
                platform=platform
            ))
    
    return creatives


def create_mock_response(products: List[Product], platform: str) -> GenerateCreativesResponse:
    """
    Create a mock response for creative generation.
    
    Args:
        products: List of products
        platform: Target platform
        
    Returns:
        GenerateCreativesResponse with mock creatives
    """
    creatives = generate_mock_creatives(products, platform)
    return GenerateCreativesResponse(creatives=creatives)


def generate_mock_agent_creatives(
    products: List[Product],
    target_agent_categories: Optional[List[str]] = None,
) -> List[AgentCreativeOutput]:
    """
    Generate mock agent-facing creatives for given products.

    Unlike human creatives (text/image/video), agent creatives are structured
    product data optimized for AI agent consumption and recommendation.

    Args:
        products: List of products
        target_agent_categories: Optional agent categories to target

    Returns:
        List of AgentCreativeOutput objects
    """
    agent_creatives = []

    for idx, product in enumerate(products):
        agent_creatives.append(AgentCreativeOutput(
            creative_id=f"agent_creative_{idx + 1}",
            product_id=product.product_id,
            product_schema={
                "name": product.name,
                "category": product.category,
                "price": {"amount": product.price, "currency": "USD", "model": "one-time"},
                "description": product.description or f"Premium {product.category} product",
                "capabilities": [
                    f"{product.category}-core-feature",
                    "api-access",
                    "analytics-dashboard",
                ],
                "integrations": [
                    {"service": "slack", "type": "bidirectional", "verified": True},
                    {"service": "zapier", "type": "outbound", "verified": True},
                ],
                "metrics": {
                    "active_users": 12000 + idx * 5000,
                    "avg_rating": round(4.5 - idx * 0.1, 1),
                    "uptime_sla": "99.9%",
                },
            },
            verified_claims=[
                f"99.9% uptime verified by UptimeRobot (last checked 2026-03-01)",
                f"Average rating {round(4.5 - idx * 0.1, 1)}/5 on G2 ({800 + idx * 200} reviews)",
                f"SOC2 Type 2 certified (verified by Vanta)",
            ],
            sandbox_api_url=f"https://sandbox.example.com/api/v1/{product.product_id}",
            agent_incentives={
                "commission_rate": 0.05,
                "exclusive_trial_days": 60,
                "discount_code": f"AMP-{product.product_id.upper()}-20OFF",
            },
            tags=[
                product.category,
                "verified",
                "sandbox-available",
                "api-ready",
            ],
            category_taxonomy=[
                "software",
                product.category,
                f"{product.category}-professional",
            ],
        ))

    return agent_creatives


def create_agent_mock_response(
    products: List[Product],
    target_agent_categories: Optional[List[str]] = None,
) -> GenerateAgentCreativesResponse:
    """
    Create a mock response for agent creative generation.

    Args:
        products: List of products
        target_agent_categories: Optional agent categories

    Returns:
        GenerateAgentCreativesResponse with mock agent creatives
    """
    agent_creatives = generate_mock_agent_creatives(products, target_agent_categories)
    return GenerateAgentCreativesResponse(agent_creatives=agent_creatives)


