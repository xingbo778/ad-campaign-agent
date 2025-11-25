"""
Pydantic schemas for the product service.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Union
from app.common.schemas import CampaignSpec, Product, ProductGroup, ErrorResponse


class SelectProductsRequest(BaseModel):
    """Request to select products for ad campaign."""
    # New API format (preferred)
    campaign_spec: Optional[CampaignSpec] = Field(None, description="Campaign specification")
    limit: Optional[int] = Field(default=10, description="Maximum number of products to select")
    
    # Legacy API format (for backward compatibility)
    campaign_objective: Optional[str] = Field(None, description="Campaign objective (legacy)")
    target_audience: Optional[str] = Field(None, description="Target audience description (legacy)")
    budget: Optional[float] = Field(None, description="Campaign budget (legacy)")
    max_products: Optional[int] = Field(None, description="Maximum number of products (legacy)")
    
    model_config = ConfigDict(from_attributes=True)


class SelectProductsResponse(BaseModel):
    """Response containing selected products grouped by priority."""
    status: str = Field(..., description="Response status: 'success' or 'error'")
    products: Optional[List[Product]] = Field(None, description="Selected products (flat list)")
    groups: Optional[List[ProductGroup]] = Field(None, description="Products grouped by priority level")
    debug: Optional[Dict] = Field(None, description="Debug information including scoring details")
    
    # Legacy fields for backward compatibility
    product_groups: Optional[List[ProductGroup]] = Field(None, description="Legacy: Products grouped by priority level")
    total_products: Optional[int] = Field(None, description="Legacy: Total number of products selected")
    
    model_config = ConfigDict(from_attributes=True)
