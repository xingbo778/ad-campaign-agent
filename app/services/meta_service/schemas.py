"""
Pydantic schemas for meta_service.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class Creative(BaseModel):
    """Creative model for campaign creation."""
    creative_id: str
    type: str
    headline: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    product_id: str
    platform: str


class PlatformStrategy(BaseModel):
    """Platform-specific strategy."""
    platform: str
    budget_allocation: float
    bidding_strategy: str
    targeting_rules: Dict[str, Any]


class Strategy(BaseModel):
    """Strategy model for campaign creation."""
    abstract_strategy: Dict[str, Any]
    platform_strategies: List[PlatformStrategy]


class CreateCampaignRequest(BaseModel):
    """Request model for campaign creation."""
    strategy: Strategy = Field(..., description="Campaign strategy")
    creatives: List[Creative] = Field(..., description="List of creatives")
    budget: float = Field(..., gt=0, description="Campaign budget")
    start_date: Optional[datetime] = Field(None, description="Campaign start date")
    end_date: Optional[datetime] = Field(None, description="Campaign end date")


class CreateCampaignResponse(BaseModel):
    """Response model for campaign creation."""
    campaign_id: str = Field(..., description="Created campaign ID")
    ad_ids: List[str] = Field(..., description="List of created ad IDs")
    status: str = Field(default="active", description="Campaign status")




