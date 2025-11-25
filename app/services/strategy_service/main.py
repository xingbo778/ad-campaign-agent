"""
Strategy Service - MCP microservice for generating campaign strategies.

This service implements real strategy generation logic including:
- Budget allocation across product groups and creatives
- Audience targeting for Meta platform
- Strategy optimization (bidding, adset structure)
"""

from fastapi import FastAPI
from typing import Union
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.common.middleware import setup_logging, RequestIDMiddleware, get_cors_middleware_class, get_logger
from app.common.config import settings
from app.common.exceptions import register_exception_handlers, ValidationError, ServiceException
from app.common.schemas import ErrorResponse

from .schemas import GenerateStrategyRequest, GenerateStrategyResponse
from .strategy_logic import (
    allocate_budget_by_groups,
    build_meta_targeting,
    choose_bidding_strategy,
    design_adset_structure,
    estimate_reach_and_conversions,
    generate_abstract_strategy,
    generate_platform_strategy,
    BUDGET_ALLOCATION_RULES
)

# Configure unified logging
setup_logging(level=settings.LOG_LEVEL, service_name="strategy_service")
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Strategy Service",
    description="MCP microservice for generating campaign strategies",
    version="2.0.0"
)

# Add middleware
app.add_middleware(RequestIDMiddleware)
cors_middleware = get_cors_middleware_class(settings.ENVIRONMENT)
app.add_middleware(cors_middleware)

# Register exception handlers
register_exception_handlers(app)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "strategy_service"}


@app.post("/generate_strategy", response_model=Union[GenerateStrategyResponse, ErrorResponse])
async def generate_strategy(request: GenerateStrategyRequest) -> Union[GenerateStrategyResponse, ErrorResponse]:
    """
    Generate optimal campaign strategy based on objectives, products, and creatives.
    
    This endpoint implements real strategy generation logic:
    - Budget allocation across product groups (high/medium/low priority)
    - Budget allocation to individual creatives
    - Audience targeting for Meta platform
    - Bidding strategy selection based on objective
    - Adset structure design based on budget size
    
    Supports two API formats:
    1. New format: campaign_spec, product_groups, creatives
    2. Legacy format: campaign_objective, total_budget, duration_days, target_audience, platforms
    
    Args:
        request: Strategy generation request (new or legacy format)
        
    Returns:
        Campaign strategy with abstract strategy, platform strategies, and debug information
        or ErrorResponse if validation fails
    """
    try:
        # Step 1: Normalize input - support both new and legacy API formats
        from app.common.schemas import CampaignSpec, ProductGroup, Creative
        
        if request.campaign_spec:
            # New API format
            campaign_spec = request.campaign_spec
            product_groups = request.product_groups or []
            creatives = request.creatives or []
        else:
            # Legacy API format - convert to new format
            if not request.campaign_objective or not request.total_budget:
                return ErrorResponse(
                    status="error",
                    error_code="MISSING_REQUIRED_FIELDS",
                    message="Either new format (campaign_spec) or legacy format (campaign_objective, total_budget) is required",
                    details={}
                )
            
            # Create CampaignSpec from legacy fields
            platform = "meta"  # Default to meta
            if request.platforms:
                # Map legacy platform names to new format
                platform_map = {
                    "facebook": "meta",
                    "instagram": "meta",
                    "meta": "meta",
                    "tiktok": "tiktok",
                    "google_ads": "google",
                    "google": "google"
                }
                platform = platform_map.get(request.platforms[0].lower(), "meta")
            
            # Calculate time range from duration_days
            time_range = None
            if request.duration_days:
                from datetime import datetime, timedelta
                start_date = datetime.now()
                end_date = start_date + timedelta(days=request.duration_days)
                time_range = {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            
            campaign_spec = CampaignSpec(
                user_query=request.target_audience or f"Campaign for {request.campaign_objective}",
                platform=platform,
                budget=request.total_budget,
                objective=request.campaign_objective,
                category="general",
                time_range=time_range,
                metadata={}
            )
            
            # Create empty product groups and creatives for legacy format
            product_groups = []
            creatives = []
            
            logger.info("Using legacy API format, creating minimal CampaignSpec")
        
        logger.info(
            f"Generating strategy: platform={campaign_spec.platform}, "
            f"objective={campaign_spec.objective}, budget=${campaign_spec.budget}, "
            f"product_groups={len(product_groups)}, creatives={len(creatives)}"
        )
        
        # Validation: budget must be positive
        if campaign_spec.budget <= 0:
            logger.error(f"Invalid budget: {campaign_spec.budget}")
            return ErrorResponse(
                status="error",
                error_code="INVALID_BUDGET",
                message="Budget must be greater than 0",
                details={"budget": campaign_spec.budget}
            )
        
        # Validation: product groups and creatives are optional for legacy API
        # But if provided, they enable more sophisticated budget allocation
        if not product_groups:
            logger.warning("No product groups provided, using default allocation")
            # Create a default product group for budget allocation
            product_groups = []
        
        if not creatives:
            logger.warning("No creatives provided, using default variant split")
            # Will use default variant split in abstract strategy
        
        # Validation: platform must be supported
        if campaign_spec.platform not in ["meta", "tiktok", "google"]:
            logger.error(f"Unsupported platform: {campaign_spec.platform}")
            return ErrorResponse(
                status="error",
                error_code="UNSUPPORTED_PLATFORM",
                message=f"Platform '{campaign_spec.platform}' is not supported. Supported platforms: meta, tiktok, google",
                details={"platform": campaign_spec.platform}
            )
        
        # Step 2: Allocate budget
        if product_groups and creatives:
            logger.info("Allocating budget across product groups and creatives")
            budget_plan = allocate_budget_by_groups(
                total_budget=campaign_spec.budget,
                product_groups=product_groups,
                creatives=creatives
            )
            
            logger.info(
                f"Budget allocated: high=${budget_plan['group_allocation'].get('high', 0):.2f}, "
                f"medium=${budget_plan['group_allocation'].get('medium', 0):.2f}, "
                f"low=${budget_plan['group_allocation'].get('low', 0):.2f}"
            )
        else:
            # Legacy mode: simple budget allocation
            logger.info("Using simple budget allocation (legacy mode)")
            budget_plan = {
                "total_budget": campaign_spec.budget,
                "group_allocation": {
                    "high": campaign_spec.budget * 0.65,
                    "medium": campaign_spec.budget * 0.25,
                    "low": campaign_spec.budget * 0.10
                },
                "creative_allocation": {},
                "group_weights": BUDGET_ALLOCATION_RULES
            }
        
        # Step 3: Build targeting (for Meta platform)
        logger.info("Building audience targeting")
        targeting = {}
        if campaign_spec.platform == "meta":
            targeting = build_meta_targeting(
                campaign_spec=campaign_spec,
                product_groups=product_groups,
                creatives=creatives
            )
            logger.info(
                f"Targeting: age={targeting.get('age_min')}-{targeting.get('age_max')}, "
                f"interests={len(targeting.get('interests', []))}, "
                f"locations={targeting.get('locations', [])}"
            )
        else:
            # For other platforms, use basic targeting
            targeting = {
                "age_min": 25,
                "age_max": 45,
                "locations": ["US"]
            }
        
        # Step 4: Choose bidding strategy
        logger.info("Selecting bidding strategy")
        bidding_strategy = choose_bidding_strategy(campaign_spec)
        logger.info(f"Selected bidding strategy: {bidding_strategy}")
        
        # Step 5: Design adset structure
        logger.info("Designing adset structure")
        adset_structure = design_adset_structure(
            campaign_spec=campaign_spec,
            product_groups=product_groups,
            budget_plan=budget_plan
        )
        logger.info(f"Created {len(adset_structure['adsets'])} adsets")
        
        # Step 6: Generate abstract strategy
        logger.info("Generating abstract strategy")
        abstract_strategy = generate_abstract_strategy(
            campaign_spec=campaign_spec,
            budget_plan=budget_plan,
            bidding_strategy=bidding_strategy,
            creatives=creatives
        )
        
        # Step 7: Generate platform strategy
        logger.info("Generating platform-specific strategy")
        platform_strategy = generate_platform_strategy(
            campaign_spec=campaign_spec,
            budget_plan=budget_plan,
            targeting=targeting,
            adset_structure=adset_structure,
            bidding_strategy=bidding_strategy
        )
        
        # Step 8: Estimate reach and conversions
        logger.info("Estimating reach and conversions")
        estimated_reach, estimated_conversions = estimate_reach_and_conversions(
            campaign_spec=campaign_spec,
            budget_plan=budget_plan,
            targeting=targeting
        )
        
        # Step 9: Build debug information
        debug_info = {
            "budget_plan": budget_plan,
            "targeting_plan": targeting,
            "rules_applied": [
                f"Budget allocation: high={BUDGET_ALLOCATION_RULES['high']*100}%, "
                f"medium={BUDGET_ALLOCATION_RULES['medium']*100}%, "
                f"low={BUDGET_ALLOCATION_RULES['low']*100}%",
                f"Bidding strategy: {bidding_strategy} (based on objective: {campaign_spec.objective})",
                f"Adset structure: {len(adset_structure['adsets'])} adsets (budget-based design)"
            ],
            "score_details": {
                "group_weights": budget_plan.get("group_weights", {}),
                "creative_count": len(creatives),
                "product_group_count": len(product_groups)
            },
            "estimated_metrics": {
                "reach": estimated_reach,
                "conversions": estimated_conversions,
                "cpa": campaign_spec.budget / estimated_conversions if estimated_conversions > 0 else 0
            }
        }
        
        # Step 10: Build response
        logger.info(
            f"Strategy generated successfully: "
            f"reach={estimated_reach:,}, conversions={estimated_conversions:,}"
        )
        
        return GenerateStrategyResponse(
            status="success",
            abstract_strategy=abstract_strategy,
            platform_strategies=[platform_strategy],
            debug=debug_info,
            # Legacy fields for backward compatibility
            estimated_reach=estimated_reach,
            estimated_conversions=estimated_conversions
        )
        
    except ValidationError as e:
        logger.error(f"Validation error: {e.message}", extra={"error_code": e.error_code})
        return ErrorResponse(
            status="error",
            error_code=e.error_code,
            message=e.message,
            details=e.details
        )
    except Exception as e:
        logger.error(f"Unexpected error in generate_strategy: {e}", exc_info=True)
        return ErrorResponse(
            status="error",
            error_code="INTERNAL_ERROR",
            message=f"Internal server error: {str(e)}",
            details={"error_type": type(e).__name__}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
