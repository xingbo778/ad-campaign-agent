"""
Optimizer Service - MCP microservice for campaign optimization.

This service analyzes campaign performance and provides optimization suggestions
to improve ROI and achieve campaign objectives.
"""

from fastapi import FastAPI, HTTPException
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.common.middleware import setup_logging, RequestIDMiddleware, get_cors_middleware_class, get_logger
from app.common.config import settings
from app.common.exceptions import register_exception_handlers

from .schemas import SummarizeRecentRunsRequest, SummarizeRecentRunsResponse
from .mock_data import get_mock_optimization_response

# Configure unified logging
setup_logging(level=settings.LOG_LEVEL, service_name="optimizer_service")
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Optimizer Service",
    description="MCP microservice for campaign optimization",
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
    return {"status": "healthy", "service": "optimizer_service"}


@app.post("/summarize_recent_runs", response_model=SummarizeRecentRunsResponse)
async def summarize_recent_runs(request: SummarizeRecentRunsRequest):
    """
    Summarize recent campaign performance and provide optimization suggestions.
    
    Args:
        request: Request with campaign IDs and time range
        
    Returns:
        Performance summary and actionable optimization suggestions
        
    TODO: Implement real optimization logic:
    - Query campaign performance data from analytics database
    - Calculate key metrics (ROAS, CPA, CTR, etc.)
    - Use ML models to identify optimization opportunities
    - Compare against industry benchmarks
    - Provide prioritized, actionable recommendations
    - Estimate expected impact of each suggestion
    """
    logger.info(f"Summarizing campaigns: ids={request.campaign_ids}, days={request.days}")
    
    # Return mock data for now
    response = get_mock_optimization_response()
    
    logger.info(f"Generated summary with {len(response.suggestions)} optimization suggestions")
    
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
