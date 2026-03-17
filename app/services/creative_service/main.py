"""
Creative Service - FastAPI app for ad creative generation.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.services.creative_service.schemas import (
    GenerateCreativesRequest,
    GenerateCreativesResponse,
    GenerateAgentCreativesRequest,
    GenerateAgentCreativesResponse,
)
from app.services.creative_service.mock_data import create_mock_response, create_agent_mock_response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Creative Service",
    description="MCP service for ad creative generation",
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


@app.post("/generate_creatives", response_model=GenerateCreativesResponse)
async def generate_creatives(request: GenerateCreativesRequest) -> GenerateCreativesResponse:
    """
    Generate ad creatives (text, images, videos) for campaigns.
    
    This endpoint creates multiple creative variations for each product,
    optimized for the target platform.
    
    TODO: Replace mock implementation with:
    - Gemini API integration for text generation
    - Image generation API (DALL-E, Midjourney, etc.)
    - Video generation/editing pipeline
    - Platform-specific creative optimization
    - A/B testing variant generation
    - Brand guideline compliance checks
    
    Args:
        request: GenerateCreativesRequest with products and campaign details
        
    Returns:
        GenerateCreativesResponse with generated creatives
    """
    logger.info(f"Generating creatives for {len(request.products)} products on {request.platform}")
    
    # TODO: Implement real creative generation logic
    # - Call Gemini API for text generation
    # - Generate images using image generation API
    # - Create video creatives
    # - Apply platform-specific optimizations
    # - Ensure brand compliance
    
    # For now, return mock data
    response = create_mock_response(request.products, request.platform)
    
    logger.info(f"Generated {len(response.creatives)} creatives")
    return response


@app.post("/generate_agent_creatives", response_model=GenerateAgentCreativesResponse)
async def generate_agent_creatives(request: GenerateAgentCreativesRequest) -> GenerateAgentCreativesResponse:
    """
    Generate agent-facing creative materials (structured product data for AMP).

    Unlike human creatives (text/image/video designed to appeal to emotions),
    agent creatives are structured, verifiable product data optimized for
    AI agent consumption, comparison, and recommendation.

    TODO: Replace mock implementation with:
    - AI-powered product schema generation from raw product data
    - Automated claim verification via third-party APIs
    - Sandbox API provisioning
    - Agent incentive optimization based on category benchmarks

    Args:
        request: GenerateAgentCreativesRequest with products and agent targeting

    Returns:
        GenerateAgentCreativesResponse with structured agent creatives
    """
    logger.info(
        f"Generating agent creatives for {len(request.products)} products, "
        f"target categories: {request.target_agent_categories}"
    )

    response = create_agent_mock_response(request.products, request.target_agent_categories)

    logger.info(f"Generated {len(response.agent_creatives)} agent creatives")
    return response


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "creative_service"}


if __name__ == "__main__":
    import uvicorn
    from app.common.config import settings
    
    uvicorn.run(
        "app.services.creative_service.main:app",
        host="0.0.0.0",
        port=settings.CREATIVE_SERVICE_PORT,
        reload=settings.DEBUG
    )




