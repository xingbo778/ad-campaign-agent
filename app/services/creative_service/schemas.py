"""
Pydantic schemas for the creative service.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional
from app.common.schemas import CampaignSpec, Product, Creative, ErrorResponse


class ABConfig(BaseModel):
    """A/B testing configuration for creative generation."""
    variants_per_product: int = Field(default=2, ge=1, le=5, description="Number of variants per product (A, B, C, etc.)")
    max_creatives: int = Field(default=10, ge=1, le=50, description="Maximum total number of creatives to generate")
    enable_image_generation: bool = Field(default=True, description="Whether to attempt image generation via API")
    enable_video_generation: bool = Field(default=False, description="Whether to attempt video generation from images via Replicate API")
    enable_storyline_video: bool = Field(default=False, description="Whether to generate multi-segment storyline-based videos (15 seconds)")
    num_video_segments: int = Field(default=3, ge=1, le=10, description="Number of video segments for storyline videos")


class GenerateCreativesRequest(BaseModel):
    """Request to generate creative content."""
    campaign_spec: CampaignSpec = Field(..., description="Campaign specification")
    products: List[Product] = Field(..., description="List of products to generate creatives for")
    ab_config: Optional[ABConfig] = Field(default=None, description="A/B testing configuration (optional)")


class GenerateCreativesResponse(BaseModel):
    """Response containing generated creatives with debug information."""
    status: str = Field(..., description="Response status: 'success' or 'error'")
    creatives: List[Creative] = Field(default_factory=list, description="List of generated creative assets")
    debug: Optional[Dict] = Field(None, description="Debug information including prompts and LLM responses")
    
    model_config = ConfigDict(
        from_attributes=True,  # Pydantic v2: Allow creating from ORM objects
        arbitrary_types_allowed=False
    )
