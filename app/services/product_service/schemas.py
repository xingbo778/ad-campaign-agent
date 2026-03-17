"""
Pydantic schemas for product_service.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TargetAudience(BaseModel):
    """Target audience definition."""
    demographics: Optional[Dict[str, Any]] = Field(default_factory=dict)
    interests: Optional[List[str]] = Field(default_factory=list)
    behaviors: Optional[List[str]] = Field(default_factory=list)


class BudgetRange(BaseModel):
    """Budget range constraints."""
    min: float = Field(ge=0, description="Minimum budget")
    max: float = Field(ge=0, description="Maximum budget")


class SelectProductsRequest(BaseModel):
    """Request model for product selection."""
    campaign_objective: str = Field(..., description="Campaign objective: awareness, conversions, or engagement")
    target_audience: TargetAudience = Field(..., description="Target audience information")
    budget_range: Optional[BudgetRange] = Field(None, description="Optional budget constraints")


class Product(BaseModel):
    """Product model."""
    product_id: str
    name: str
    category: str
    price: float
    description: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)


class ProductGroupsResponse(BaseModel):
    """Response model for product selection."""
    product_groups: Dict[str, List[Product]] = Field(
        ...,
        description="Products grouped by priority: high, medium, low"
    )




