"""
Strategy Service - MCP microservice for generating campaign strategies.

This service is responsible for creating optimal campaign strategies including
budget allocation, platform selection, and bidding strategies.
"""

from fastapi import FastAPI, HTTPException
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.common.middleware import setup_logging, RequestIDMiddleware, get_cors_middleware_class, get_logger
from app.common.config import settings
from app.common.exceptions import register_exception_handlers

from .schemas import GenerateStrategyRequest, GenerateStrategyResponse
from .mock_data import get_mock_strategy_response

# Configure unified logging
setup_logging(level=settings.LOG_LEVEL, service_name="strategy_service")
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Strategy Service",
    description="MCP microservice for generating campaign strategies",
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
    return {"status": "healthy", "service": "strategy_service"}


@app.post("/generate_strategy", response_model=GenerateStrategyResponse)
async def generate_strategy(request: GenerateStrategyRequest):
    """
    Generate optimal campaign strategy based on objectives and constraints.
    
    Args:
        request: Strategy generation request with campaign parameters
        
    Returns:
        Campaign strategy with platform-specific recommendations
        
    TODO: Implement real strategy generation logic:
    - Use ML models to optimize budget allocation
    - Analyze historical campaign performance data
    - Consider seasonality and market trends
    - Optimize bidding strategies based on objectives
    - Provide realistic reach and conversion estimates
    """
    logger.info(f"Generating strategy: objective={request.campaign_objective}, "
                f"budget=${request.total_budget}, platforms={request.platforms}")
    
    # Return mock data for now
    response = get_mock_strategy_response(request.total_budget, request.platforms)
    
    logger.info(f"Generated strategy with {len(response.platform_strategies)} platform strategies")
    
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
