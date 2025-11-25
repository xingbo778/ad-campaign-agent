"""
Product Service - MCP microservice for product selection.

This service is responsible for selecting products for ad campaigns
based on campaign objectives, target audience, and budget.
"""

from fastapi import FastAPI, HTTPException
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.common.middleware import setup_logging, RequestIDMiddleware, get_cors_middleware_class, get_logger
from app.common.config import settings
from app.common.exceptions import register_exception_handlers

from .schemas import SelectProductsRequest, SelectProductsResponse
from .mock_data import get_mock_products_response

# Configure unified logging
setup_logging(level=settings.LOG_LEVEL, service_name="product_service")
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Product Service",
    description="MCP microservice for product selection in ad campaigns",
    version="1.0.0"
)

# Add middleware
app.add_middleware(RequestIDMiddleware)
cors_middleware = get_cors_middleware_class()
cors_middleware(app)

# Register exception handlers
register_exception_handlers(app)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "product_service"}


@app.post("/select_products", response_model=SelectProductsResponse)
async def select_products(request: SelectProductsRequest):
    """
    Select products for an ad campaign based on objectives and constraints.
    
    Args:
        request: Product selection request with campaign details
        
    Returns:
        Selected products grouped by priority level
        
    TODO: Implement real product selection logic:
    - Query product database based on campaign_objective and target_audience
    - Apply ML-based ranking algorithm
    - Filter by budget and stock availability
    - Return dynamically selected products instead of mock data
    """
    logger.info(f"Selecting products for campaign: objective={request.campaign_objective}, "
                f"audience={request.target_audience}, budget={request.budget}")
    
    # Return mock data for now
    response = get_mock_products_response()
    
    logger.info(f"Selected {response.total_products} products across "
                f"{len(response.product_groups)} priority groups")
    
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
