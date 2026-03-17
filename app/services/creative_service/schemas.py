"""
Pydantic schemas for creative_service.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Product(BaseModel):
    """Product model for creative generation."""
    product_id: str
    name: str
    category: str
    price: float
    description: Optional[str] = None


class TargetAudience(BaseModel):
    """Target audience definition."""
    demographics: Optional[Dict[str, Any]] = Field(default_factory=dict)
    interests: Optional[List[str]] = Field(default_factory=list)


class GenerateCreativesRequest(BaseModel):
    """Request model for creative generation."""
    products: List[Product] = Field(..., description="List of products to create creatives for")
    campaign_objective: str = Field(..., description="Campaign objective")
    platform: str = Field(..., description="Target platform: facebook, instagram, or meta")
    target_audience: Optional[TargetAudience] = Field(None, description="Optional audience information")


class Creative(BaseModel):
    """Creative model."""
    creative_id: str
    type: str = Field(..., description="Type: text, image, video")
    headline: Optional[str] = None
    description: Optional[str] = None
    primary_text: Optional[str] = None
    call_to_action: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    product_id: str
    platform: str


class GenerateCreativesResponse(BaseModel):
    """Response model for creative generation."""
    creatives: List[Creative] = Field(..., description="List of generated creatives")


# --- Agent Creative Models (for AMP channel) ---


class GenerateAgentCreativesRequest(BaseModel):
    """Request to generate agent-facing creative materials (structured product data, not human ad copy)."""
    products: List[Product] = Field(..., description="Products to create agent materials for")
    campaign_objective: str = Field(..., description="Campaign objective")
    target_agent_categories: Optional[List[str]] = Field(
        None, description="Types of agents to target: shopping_assistant, saas_advisor, etc."
    )


class AgentCreativeOutput(BaseModel):
    """Single agent creative output - structured data optimized for AI agent consumption."""
    creative_id: str
    product_id: str
    product_schema: Dict[str, Any] = Field(
        ..., description="Structured product data: name, category, capabilities, pricing, integrations, metrics"
    )
    verified_claims: List[str] = Field(
        default_factory=list, description="Verified factual claims about the product"
    )
    sandbox_api_url: Optional[str] = Field(
        None, description="URL for agents to test/interact with the product"
    )
    agent_incentives: Optional[Dict[str, Any]] = Field(
        None, description="Incentives for recommending agents: commission_rate, exclusive_trial_days, discount_code"
    )
    tags: List[str] = Field(default_factory=list, description="Searchable tags for agent discovery")
    category_taxonomy: List[str] = Field(
        default_factory=list, description="Hierarchical category path"
    )


class GenerateAgentCreativesResponse(BaseModel):
    """Response with generated agent creatives."""
    agent_creatives: List[AgentCreativeOutput] = Field(..., description="List of agent-facing creatives")


