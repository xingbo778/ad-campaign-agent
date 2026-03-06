"""
Shared pipeline runner for orchestrating campaign creation.

Extracts the common pipeline logic from both simple_service.py and llm_service.py
into a single reusable module.
"""

import asyncio
from typing import Dict, Any, List, Optional
from app.common.config import settings
from app.common.http_client import AsyncMCPClient
from app.common.middleware import get_logger

logger = get_logger(__name__)


class PipelineResult:
    """Result of a pipeline execution."""

    def __init__(self):
        self.products: List[Dict[str, Any]] = []
        self.strategy: Dict[str, Any] = {}
        self.creatives: List[Dict[str, Any]] = []
        self.campaign_id: Optional[str] = None
        self.log_event_id: Optional[str] = None
        self.errors: List[str] = []
        self.steps: List[Dict[str, Any]] = []

    @property
    def success(self) -> bool:
        return len(self.errors) == 0 and self.campaign_id is not None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "products": self.products,
            "strategy": self.strategy,
            "creatives": self.creatives,
            "campaign_id": self.campaign_id,
            "errors": self.errors,
            "steps": self.steps,
        }


async def run_campaign_pipeline(
    campaign_spec: Dict[str, Any],
    products_for_creatives: Optional[List[Dict[str, Any]]] = None,
    max_products: int = 10,
    max_creatives: int = 3,
    continue_on_error: bool = False,
) -> PipelineResult:
    """
    Execute the fixed campaign creation pipeline:
    1. Select products
    2. Generate strategy
    3. Generate creatives
    4. Create Meta campaign
    5. Log event

    Args:
        campaign_spec: Campaign specification dict (must match CampaignSpec schema)
        products_for_creatives: Optional pre-selected products (skip step 1)
        max_products: Max products to select
        max_creatives: Max products to generate creatives for
        continue_on_error: If True, continue pipeline even if a step fails

    Returns:
        PipelineResult with all step outputs
    """
    result = PipelineResult()
    timeout = settings.SERVICE_TIMEOUT

    async with AsyncMCPClient(settings.PRODUCT_SERVICE_URL, timeout=timeout) as product_client, \
               AsyncMCPClient(settings.STRATEGY_SERVICE_URL, timeout=timeout) as strategy_client, \
               AsyncMCPClient(settings.CREATIVE_SERVICE_URL, timeout=timeout) as creative_client, \
               AsyncMCPClient(settings.META_SERVICE_URL, timeout=timeout) as meta_client, \
               AsyncMCPClient(settings.LOGS_SERVICE_URL, timeout=timeout) as logs_client:

        # Step 1: Select products
        if products_for_creatives is None:
            try:
                logger.info("Pipeline step 1: Selecting products")
                product_request = {
                    "campaign_spec": campaign_spec,
                    "limit": max_products,
                }
                products_response = await product_client.post("/select_products", product_request)

                # Extract products from response
                if "products" in products_response:
                    result.products = products_response["products"]
                elif "groups" in products_response:
                    for group in products_response["groups"]:
                        if "products" in group:
                            result.products.extend(group["products"])

                result.steps.append({"step": 1, "action": "select_products", "status": "completed",
                                     "result": f"Selected {len(result.products)} products"})
            except Exception as e:
                result.errors.append(f"Product selection failed: {e}")
                result.steps.append({"step": 1, "action": "select_products", "status": "failed", "error": str(e)})
                if not continue_on_error:
                    return result
        else:
            result.products = products_for_creatives
            result.steps.append({"step": 1, "action": "select_products", "status": "skipped",
                                 "result": f"Using {len(result.products)} pre-selected products"})

        # Step 2: Generate strategy
        try:
            logger.info("Pipeline step 2: Generating strategy")
            strategy_request = {"campaign_spec": campaign_spec}
            result.strategy = await strategy_client.post("/generate_strategy", strategy_request)
            result.steps.append({"step": 2, "action": "generate_strategy", "status": "completed"})
        except Exception as e:
            result.errors.append(f"Strategy generation failed: {e}")
            result.steps.append({"step": 2, "action": "generate_strategy", "status": "failed", "error": str(e)})
            if not continue_on_error:
                return result

        # Step 3: Generate creatives
        try:
            logger.info("Pipeline step 3: Generating creatives")
            creative_products = result.products[:max_creatives]
            creative_request = {
                "campaign_spec": campaign_spec,
                "products": creative_products,
                "ab_config": {"variants_per_product": 2, "max_creatives": 10, "enable_image_generation": True},
            }
            creatives_response = await creative_client.post("/generate_creatives", creative_request)
            result.creatives = creatives_response.get("creatives", [])
            result.steps.append({"step": 3, "action": "generate_creatives", "status": "completed",
                                 "result": f"Generated {len(result.creatives)} creatives"})
        except Exception as e:
            result.errors.append(f"Creative generation failed: {e}")
            result.steps.append({"step": 3, "action": "generate_creatives", "status": "failed", "error": str(e)})
            if not continue_on_error:
                return result

        # Step 4: Create Meta campaign
        try:
            logger.info("Pipeline step 4: Creating Meta campaign")
            meta_request = {
                "campaign_name": f"{campaign_spec.get('objective', 'campaign')}_campaign",
                "objective": campaign_spec.get("objective", "conversions"),
                "budget": campaign_spec.get("budget", 0),
                "target_audience": campaign_spec.get("user_query", ""),
                "creatives": [c.get("creative_id", "") for c in result.creatives[:5]],
            }
            meta_response = await meta_client.post("/create_campaign", meta_request)
            result.campaign_id = meta_response.get("campaign_id")
            result.steps.append({"step": 4, "action": "create_campaign", "status": "completed",
                                 "result": f"Campaign ID: {result.campaign_id}"})
        except Exception as e:
            result.errors.append(f"Meta campaign creation failed: {e}")
            result.steps.append({"step": 4, "action": "create_campaign", "status": "failed", "error": str(e)})
            if not continue_on_error:
                return result

        # Step 5: Log event
        try:
            logger.info("Pipeline step 5: Logging event")
            log_request = {
                "event_type": "campaign_created",
                "message": f"Campaign {result.campaign_id} created",
                "metadata": {
                    "products_count": len(result.products),
                    "creatives_count": len(result.creatives),
                    "campaign_id": result.campaign_id,
                },
            }
            await logs_client.post("/append_event", log_request)
            result.steps.append({"step": 5, "action": "log_event", "status": "completed"})
        except Exception as e:
            # Logging failure is non-critical
            logger.warning(f"Logging failed (non-critical): {e}")
            result.steps.append({"step": 5, "action": "log_event", "status": "failed", "error": str(e)})

    return result
