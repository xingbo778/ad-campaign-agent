"""
Pydantic schemas for the strategy service.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional, Union
from app.common.schemas import (
    CampaignSpec,
    ProductGroup,
    Creative,
    AbstractStrategy,
    PlatformStrategy,
    ErrorResponse
)


class GenerateStrategyRequest(BaseModel):
    """Request to generate campaign strategy."""
    # New API format (preferred)
    campaign_spec: Optional[CampaignSpec] = Field(None, description="Campaign specification")
    product_groups: Optional[List[ProductGroup]] = Field(None, description="Product groups with priority levels")
    creatives: Optional[List[Creative]] = Field(None, description="Generated creatives for the campaign")
    
    # Legacy API format (for backward compatibility)
    campaign_objective: Optional[str] = Field(None, description="Campaign objective (legacy)")
    total_budget: Optional[float] = Field(None, description="Total campaign budget (legacy)")
    duration_days: Optional[int] = Field(None, description="Campaign duration in days (legacy)")
    target_audience: Optional[str] = Field(None, description="Target audience description (legacy)")
    platforms: Optional[List[str]] = Field(None, description="Platforms to advertise on (legacy)")
    
    model_config = ConfigDict(from_attributes=True)


class GenerateStrategyResponse(BaseModel):
    """Response containing campaign strategy."""
    status: str = Field(..., description="Response status: 'success' or 'error'")
    abstract_strategy: Optional[AbstractStrategy] = Field(None, description="Abstract campaign strategy")
    platform_strategies: Optional[List[PlatformStrategy]] = Field(None, description="Platform-specific strategies")
    debug: Optional[Dict] = Field(None, description="Debug information including budget plan and targeting")
    
    # Legacy response fields (for backward compatibility)
    estimated_reach: Optional[int] = Field(None, description="Estimated total reach (legacy)")
    estimated_conversions: Optional[int] = Field(None, description="Estimated conversions (legacy)")
    
    model_config = ConfigDict(from_attributes=True)
