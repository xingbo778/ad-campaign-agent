"""
Pydantic schemas for amp_service.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AgentCreative(BaseModel):
    """Agent-facing creative material (structured product data for agent consumption)."""
    creative_id: str
    product_id: str
    product_schema: Dict[str, Any] = Field(
        ..., description="Structured product schema: name, category, capabilities, pricing, integrations, metrics"
    )
    verified_claims: List[str] = Field(
        default_factory=list, description="Verified factual claims, e.g. '99.9% uptime verified by UptimeRobot'"
    )
    sandbox_api_url: Optional[str] = Field(
        None, description="URL for agents to test/interact with product sandbox"
    )
    agent_incentives: Optional[Dict[str, Any]] = Field(
        None, description="Incentives for recommending agents: commission_rate, exclusive_trial_days, discount_code"
    )
    tags: List[str] = Field(default_factory=list, description="Searchable tags for agent discovery")
    category_taxonomy: List[str] = Field(
        default_factory=list, description="Hierarchical category path, e.g. ['software', 'project-management', 'kanban']"
    )


class PublishToAMPRequest(BaseModel):
    """Request to publish product listings to the Agent Marketing Platform."""
    agent_creatives: List[AgentCreative] = Field(..., description="Agent-facing creative materials to publish")
    budget: float = Field(..., gt=0, description="AMP channel budget in USD")
    bidding_strategy: str = Field(
        default="cost_per_recommendation",
        description="Bidding model: cost_per_recommendation | cost_per_query_match | cost_per_action | flat_rate"
    )
    target_agent_categories: Optional[List[str]] = Field(
        None, description="Categories of agents to target: shopping_assistant, saas_advisor, personal_finance, etc."
    )
    start_date: Optional[datetime] = Field(None, description="Campaign start date")
    end_date: Optional[datetime] = Field(None, description="Campaign end date")


class AMPListing(BaseModel):
    """A single listing published on the AMP marketplace."""
    listing_id: str
    product_id: str
    status: str = "active"
    marketplace_url: str


class PublishToAMPResponse(BaseModel):
    """Response from AMP publishing."""
    campaign_id: str = Field(..., description="AMP campaign ID")
    listings: List[AMPListing] = Field(..., description="Published marketplace listings")
    status: str = Field(default="active", description="Campaign status")
