"""
Product Service - FastAPI app for product selection and grouping.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.services.product_service.schemas import SelectProductsRequest, ProductGroupsResponse
from app.services.product_service.mock_data import create_mock_response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Product Service",
    description="MCP service for product selection and grouping",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/select_products", response_model=ProductGroupsResponse)
async def select_products(request: SelectProductsRequest) -> ProductGroupsResponse:
    """
    Select and group products based on campaign requirements.
    
    This endpoint analyzes campaign objectives, target audience, and budget
    to return products grouped by priority (high, medium, low).
    
    TODO: Replace mock implementation with:
    - Real product database queries
    - ML-based product recommendation algorithm
    - Budget-aware product filtering
    - Audience matching logic
    
    Args:
        request: SelectProductsRequest with campaign details
        
    Returns:
        ProductGroupsResponse with products grouped by priority
    """
    logger.info(f"Selecting products for objective: {request.campaign_objective}")
    
    # TODO: Implement real product selection logic
    # - Query product database
    # - Apply ML recommendation model
    # - Filter by budget constraints
    # - Match audience preferences
    
    # For now, return mock data
    response = create_mock_response()
    
    logger.info(f"Returning {len(response.product_groups)} product groups")
    return response


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "product_service"}


if __name__ == "__main__":
    import uvicorn
    from app.common.config import settings
    
    uvicorn.run(
        "app.services.product_service.main:app",
        host="0.0.0.0",
        port=settings.PRODUCT_SERVICE_PORT,
        reload=settings.DEBUG
    )




