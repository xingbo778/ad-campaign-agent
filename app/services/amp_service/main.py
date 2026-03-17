"""
AMP Service - FastAPI app for Agent Marketing Platform publishing.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.services.amp_service.schemas import (
    PublishToAMPRequest,
    PublishToAMPResponse,
)
from app.services.amp_service.mock_data import create_mock_response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AMP Service",
    description="MCP service for publishing to the Agent Marketing Platform",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/publish_to_amp", response_model=PublishToAMPResponse)
async def publish_to_amp(request: PublishToAMPRequest) -> PublishToAMPResponse:
    """
    Publish product listings to the Agent Marketing Platform.

    This endpoint publishes structured product data to the AMP marketplace,
    making products discoverable by AI agents.

    TODO: Replace mock implementation with:
    - AMP marketplace API integration
    - Product schema validation against AMP standards
    - Verified claims submission and third-party verification triggers
    - Sandbox API registration
    - Bidding strategy configuration
    - Real-time listing status monitoring

    Args:
        request: PublishToAMPRequest with agent creatives and budget

    Returns:
        PublishToAMPResponse with campaign_id and listing details
    """
    logger.info(
        f"Publishing to AMP: {len(request.agent_creatives)} creatives, "
        f"budget=${request.budget}, bidding={request.bidding_strategy}"
    )

    # TODO: Implement real AMP integration
    response = create_mock_response(request)

    logger.info(
        f"Published AMP campaign: {response.campaign_id} "
        f"with {len(response.listings)} listings"
    )
    return response


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "amp_service"}


if __name__ == "__main__":
    import uvicorn
    from app.common.config import settings

    uvicorn.run(
        "app.services.amp_service.main:app",
        host="0.0.0.0",
        port=settings.AMP_SERVICE_PORT,
        reload=settings.DEBUG,
    )
