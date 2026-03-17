"""
Meta Service - FastAPI app for Meta (Facebook/Instagram) campaign creation.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.services.meta_service.schemas import (
    CreateCampaignRequest,
    CreateCampaignResponse
)
from app.services.meta_service.mock_data import create_mock_response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Meta Service",
    description="MCP service for Meta platform campaign creation",
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


@app.post("/create_campaign", response_model=CreateCampaignResponse)
async def create_campaign(request: CreateCampaignRequest) -> CreateCampaignResponse:
    """
    Create and deploy campaigns to Meta platforms.
    
    This endpoint creates campaigns on Facebook and Instagram using the
    provided strategy and creatives.
    
    TODO: Replace mock implementation with:
    - Meta Marketing API integration
    - Real campaign creation via Facebook Graph API
    - Ad set and ad creation
    - Budget and scheduling configuration
    - Error handling and retry logic
    - Campaign status monitoring
    
    Args:
        request: CreateCampaignRequest with strategy, creatives, and budget
        
    Returns:
        CreateCampaignResponse with campaign_id and ad_ids
    """
    logger.info(f"Creating campaign with budget: ${request.budget}, {len(request.creatives)} creatives")
    
    # TODO: Implement real Meta API integration
    # - Authenticate with Meta Marketing API
    # - Create campaign via Graph API
    # - Create ad sets for each platform strategy
    # - Create ads for each creative
    # - Set budget and scheduling
    # - Handle API errors and retries
    
    # For now, return mock data
    response = create_mock_response(request)
    
    logger.info(f"Created campaign: {response.campaign_id} with {len(response.ad_ids)} ads")
    return response


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "meta_service"}


if __name__ == "__main__":
    import uvicorn
    from app.common.config import settings
    
    uvicorn.run(
        "app.services.meta_service.main:app",
        host="0.0.0.0",
        port=settings.META_SERVICE_PORT,
        reload=settings.DEBUG
    )




