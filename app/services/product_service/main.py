"""
Product Service - MCP microservice for product selection.

This service implements real product selection logic including:
- Product data loading from database or CSV
- Rule-based product scoring
- Product grouping by priority
- Campaign-aligned product selection
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
from app.common.db import init_db, is_db_available

from .schemas import SelectProductsRequest, SelectProductsResponse
from .loaders import load_products, get_products_by_category
from .scoring import score_products
from .grouping import group_products

# Configure unified logging
setup_logging()
logger = get_logger(__name__)

# Initialize database connection (if available)
db_available = init_db()
if db_available:
    logger.info("Database connection initialized")
else:
    logger.info("Using CSV fallback mode for product data")

# Initialize FastAPI app
app = FastAPI(
    title="Product Service",
    description="MCP microservice for product selection in ad campaigns",
    version="2.0.0"
)

# Add middleware
app.add_middleware(RequestIDMiddleware)
cors_middleware = get_cors_middleware_class(settings.ENVIRONMENT)
cors_middleware(app)

# Register exception handlers
register_exception_handlers(app)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "product_service",
        "data_source": "database" if is_db_available() else "csv"
    }


@app.post("/select_products", response_model=Union[SelectProductsResponse, ErrorResponse])
async def select_products(request: SelectProductsRequest) -> Union[SelectProductsResponse, ErrorResponse]:
    """
    Select products for an ad campaign based on campaign specification.
    
    This endpoint implements real product selection logic:
    - Loads products from database or CSV
    - Scores products based on campaign alignment
    - Groups products by priority (high/medium/low)
    - Returns top N products
    
    Args:
        request: Product selection request with campaign_spec and optional limit
        
    Returns:
        Selected products grouped by priority with debug information
        or ErrorResponse if selection fails
    """
    try:
        campaign_spec = request.campaign_spec
        limit = request.limit or 10
        
        logger.info(
            f"Selecting products: category={campaign_spec.category}, "
            f"budget=${campaign_spec.budget}, limit={limit}"
        )
        
        # Validation
        if campaign_spec.budget <= 0:
            logger.error(f"Invalid budget: {campaign_spec.budget}")
            return ErrorResponse(
                status="error",
                error_code="INVALID_BUDGET",
                message="Budget must be greater than 0",
                details={"budget": campaign_spec.budget}
            )
        
        if limit <= 0:
            logger.error(f"Invalid limit: {limit}")
            return ErrorResponse(
                status="error",
                error_code="INVALID_LIMIT",
                message="Limit must be greater than 0",
                details={"limit": limit}
            )
        
        # Step 1: Load products
        logger.info("Loading products from data source")
        if campaign_spec.category:
            all_products = get_products_by_category(campaign_spec.category)
        else:
            all_products = load_products()
        
        if not all_products:
            logger.warning("No products found in data source")
            return ErrorResponse(
                status="error",
                error_code="NO_PRODUCTS_FOUND",
                message=f"No products found" + (f" for category '{campaign_spec.category}'" if campaign_spec.category else ""),
                details={"category": campaign_spec.category}
            )
        
        logger.info(f"Loaded {len(all_products)} products from data source")
        
        # Step 2: Score products
        logger.info("Scoring products based on campaign alignment")
        scored_products = score_products(all_products, campaign_spec)
        
        if not scored_products:
            logger.error("No products scored successfully")
            return ErrorResponse(
                status="error",
                error_code="SCORING_FAILED",
                message="Failed to score products",
                details={}
            )
        
        # Step 3: Apply limit and select top products
        logger.info(f"Selecting top {limit} products")
        selected_scored = scored_products[:limit]
        selected_products = [product for product, score, _ in selected_scored]
        
        # Step 4: Group selected products
        logger.info("Grouping selected products by priority")
        product_groups = group_products(selected_scored)
        
        # Step 5: Build debug information
        scoring_details = {}
        for product, score, debug_info in selected_scored:
            scoring_details[product.product_id] = {
                "score": score,
                "breakdown": debug_info
            }
        
        rules_applied = [
            f"Category alignment: +0.4 (exact), +0.2 (similar)",
            f"Price fit: Based on budget ratio (prefer products in budget/40 to budget/20 range)",
            f"Description quality: +0.1 (length), +0.1 (keyword match)",
            f"Metadata features: +0.1 (popularity, brand, features)",
            f"Grouping thresholds: high >= 0.75, medium >= 0.45, low < 0.45"
        ]
        
        debug_info = {
            "scoring_details": scoring_details,
            "selected_ids": [p.product_id for p in selected_products],
            "rules_applied": rules_applied,
            "total_products_loaded": len(all_products),
            "total_products_selected": len(selected_products),
            "data_source": "database" if is_db_available() else "csv"
        }
        
        # Step 6: Build response
        total_products = len(selected_products)
        logger.info(
            f"Selected {total_products} products: "
            f"{sum(1 for g in product_groups if g.group == 'high')} high, "
            f"{sum(1 for g in product_groups if g.group == 'medium')} medium, "
            f"{sum(1 for g in product_groups if g.group == 'low')} low"
        )
        
        return SelectProductsResponse(
            status="success",
            products=selected_products,
            groups=product_groups,
            debug=debug_info,
            # Legacy fields for backward compatibility
            product_groups=product_groups,
            total_products=total_products
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
        logger.error(f"Unexpected error in select_products: {e}", exc_info=True)
        return ErrorResponse(
            status="error",
            error_code="INTERNAL_ERROR",
            message=f"Internal server error: {str(e)}",
            details={"error_type": type(e).__name__}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
