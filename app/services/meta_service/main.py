"""
Meta Service - MCP microservice for Meta (Facebook/Instagram) platform integration.

This service handles campaign creation and management on Meta platforms.
"""

from fastapi import FastAPI, HTTPException
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.common.middleware import setup_logging, RequestIDMiddleware, get_cors_middleware_class, get_logger
from app.common.config import settings
from app.common.exceptions import register_exception_handlers

from .schemas import CreateCampaignRequest, CreateCampaignResponse
from .mock_data import get_mock_campaign_response

# Configure unified logging
setup_logging(level=settings.LOG_LEVEL, service_name="meta_service")
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Meta Service",
    description="MCP microservice for Meta platform integration",
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
    return {"status": "healthy", "service": "meta_service"}


@app.post("/create_campaign", response_model=CreateCampaignResponse)
async def create_campaign(request: CreateCampaignRequest):
    """
    Create a campaign on Meta platforms (Facebook/Instagram).
    
    Args:
        request: Campaign creation request with targeting and creatives
        
    Returns:
        Created campaign, ad set, and ad IDs
        
    TODO: Implement real Meta API integration:
    - Authenticate with Facebook Marketing API
    - Create campaign with proper objectives
    - Create ad sets with targeting
    - Upload creatives and create ads
    - Handle API rate limits and errors
    - Implement campaign status monitoring
    """
    logger.info(f"Creating Meta campaign: {request.campaign_name}, "
                f"budget=${request.daily_budget}, creatives={len(request.creatives)}")
    
    # Return mock data for now
    response = get_mock_campaign_response(request.creatives)
    
    logger.info(f"Created campaign {response.campaign_id} with {len(response.ad_ids)} ads")
    
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
