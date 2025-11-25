"""
Pydantic schemas for the creative service.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from common.schemas import CampaignSpec, Product, Creative, ErrorResponse


class GenerateCreativesRequest(BaseModel):
    """Request to generate creative content."""
    campaign_spec: CampaignSpec = Field(..., description="Campaign specification")
    products: List[Product] = Field(..., description="List of products to generate creatives for")


class GenerateCreativesResponse(BaseModel):
    """Response containing generated creatives with debug information."""
    status: str = Field(..., description="Response status: 'success' or 'error'")
    creatives: List[Creative] = Field(default_factory=list, description="List of generated creative assets")
    debug: Optional[Dict] = Field(None, description="Debug information including prompts and LLM responses")
