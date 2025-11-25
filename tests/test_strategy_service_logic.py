"""
Tests for Strategy Service logic implementation.
"""

import pytest
from fastapi.testclient import TestClient
from app.services.strategy_service.main import app
from app.common.schemas import (
    CampaignSpec,
    Product,
    ProductGroup,
    Creative
)
from app.services.strategy_service.strategy_logic import (
    allocate_budget_by_groups,
    build_meta_targeting,
    choose_bidding_strategy,
    design_adset_structure,
    estimate_reach_and_conversions
)

client = TestClient(app)


@pytest.fixture
def sample_campaign_spec():
    """Sample campaign specification."""
    return CampaignSpec(
        user_query="Create a campaign for electronics",
        platform="meta",
        budget=5000.0,
        objective="conversions",
        category="electronics",
        time_range={"start": "2025-01-01", "end": "2025-01-31"},
        metadata={"locale": "en_US"}
    )


@pytest.fixture
def sample_product_groups():
    """Sample product groups."""
    return [
        ProductGroup(
            group="high",
            products=[
                Product(
                    product_id="PROD-001",
                    title="Wireless Headphones",
                    description="Premium headphones",
                    price=199.99,
                    category="electronics",
                    image_url="https://example.com/image1.jpg",
                    metadata={"age_range": "25-45"}
                )
            ]
        ),
        ProductGroup(
            group="medium",
            products=[
                Product(
                    product_id="PROD-002",
                    title="Bluetooth Speaker",
                    description="Portable speaker",
                    price=79.99,
                    category="electronics",
                    image_url="https://example.com/image2.jpg",
                    metadata={}
                )
            ]
        )
    ]


@pytest.fixture
def sample_creatives():
    """Sample creatives."""
    return [
        Creative(
            creative_id="CREATIVE-001",
            product_id="PROD-001",
            platform="meta",
            variant_id="A",
            primary_text="Experience premium sound quality",
            headline="Amazing Headphones",
            image_url="https://example.com/creative1.jpg"
        ),
        Creative(
            creative_id="CREATIVE-002",
            product_id="PROD-001",
            platform="meta",
            variant_id="B",
            primary_text="Wireless freedom for your music",
            headline="Premium Audio",
            image_url="https://example.com/creative2.jpg"
        )
    ]


class TestBudgetAllocation:
    """Test budget allocation logic."""
    
    def test_allocate_budget_by_groups(self, sample_product_groups, sample_creatives):
        """Test budget allocation across groups."""
        budget_plan = allocate_budget_by_groups(
            total_budget=1000.0,
            product_groups=sample_product_groups,
            creatives=sample_creatives
        )
        
        assert budget_plan["total_budget"] == 1000.0
        assert "group_allocation" in budget_plan
        assert "creative_allocation" in budget_plan
        
        # Check group allocation
        group_alloc = budget_plan["group_allocation"]
        assert "high" in group_alloc
        assert "medium" in group_alloc
        
        # High should get more than medium
        assert group_alloc["high"] > group_alloc["medium"]
        
        # Check creative allocation
        creative_alloc = budget_plan["creative_allocation"]
        assert len(creative_alloc) == 2
        assert sum(creative_alloc.values()) <= 1000.0
    
    def test_budget_allocation_no_creatives(self, sample_product_groups):
        """Test budget allocation with no creatives."""
        budget_plan = allocate_budget_by_groups(
            total_budget=1000.0,
            product_groups=sample_product_groups,
            creatives=[]
        )
        
        assert budget_plan["total_budget"] == 1000.0
        assert "group_allocation" in budget_plan


class TestTargeting:
    """Test targeting logic."""
    
    def test_build_meta_targeting_electronics(self, sample_campaign_spec, sample_product_groups, sample_creatives):
        """Test Meta targeting for electronics category."""
        targeting = build_meta_targeting(
            campaign_spec=sample_campaign_spec,
            product_groups=sample_product_groups,
            creatives=sample_creatives
        )
        
        assert "age_min" in targeting
        assert "age_max" in targeting
        assert "interests" in targeting
        assert "locations" in targeting
        
        # Electronics should have tech interests
        assert "technology" in targeting["interests"] or "electronics" in targeting["interests"]
    
    def test_build_meta_targeting_toys(self, sample_product_groups, sample_creatives):
        """Test Meta targeting for toys category."""
        campaign_spec = CampaignSpec(
            user_query="Create a campaign for toys",
            platform="meta",
            budget=2000.0,
            objective="conversions",
            category="toys",
            metadata={}
        )
        
        targeting = build_meta_targeting(
            campaign_spec=campaign_spec,
            product_groups=sample_product_groups,
            creatives=sample_creatives
        )
        
        # Toys should target parents
        assert targeting["age_min"] >= 25
        assert "parenting" in targeting["interests"] or "children" in targeting["interests"]


class TestBiddingStrategy:
    """Test bidding strategy selection."""
    
    def test_choose_bidding_strategy_conversions(self, sample_campaign_spec):
        """Test bidding strategy for conversions objective."""
        strategy = choose_bidding_strategy(sample_campaign_spec)
        assert strategy == "LOWEST_COST_WITH_CAP"
    
    def test_choose_bidding_strategy_traffic(self):
        """Test bidding strategy for traffic objective."""
        campaign_spec = CampaignSpec(
            user_query="Create a campaign",
            platform="meta",
            budget=1000.0,
            objective="traffic",
            category="general"
        )
        strategy = choose_bidding_strategy(campaign_spec)
        assert strategy == "LOWEST_COST"


class TestAdsetStructure:
    """Test adset structure design."""
    
    def test_design_adset_structure_small_budget(self, sample_campaign_spec, sample_product_groups):
        """Test adset structure for small budget."""
        campaign_spec = CampaignSpec(
            user_query="Create a campaign",
            platform="meta",
            budget=500.0,  # Small budget
            objective="conversions",
            category="general"
        )
        
        budget_plan = {
            "total_budget": 500.0,
            "group_allocation": {"high": 325.0, "medium": 125.0, "low": 50.0}
        }
        
        structure = design_adset_structure(
            campaign_spec=campaign_spec,
            product_groups=sample_product_groups,
            budget_plan=budget_plan
        )
        
        assert "adsets" in structure
        assert len(structure["adsets"]) == 1  # Single adset for small budget
    
    def test_design_adset_structure_large_budget(self, sample_campaign_spec, sample_product_groups):
        """Test adset structure for large budget."""
        campaign_spec = CampaignSpec(
            user_query="Create a campaign",
            platform="meta",
            budget=10000.0,  # Large budget
            objective="conversions",
            category="general"
        )
        
        budget_plan = {
            "total_budget": 10000.0,
            "group_allocation": {"high": 6500.0, "medium": 2500.0, "low": 1000.0}
        }
        
        structure = design_adset_structure(
            campaign_spec=campaign_spec,
            product_groups=sample_product_groups,
            budget_plan=budget_plan
        )
        
        assert len(structure["adsets"]) >= 2  # Multiple adsets for large budget


class TestGenerateStrategyEndpoint:
    """Test generate_strategy endpoint."""
    
    def test_generate_strategy_success(self, sample_campaign_spec, sample_product_groups, sample_creatives):
        """Test successful strategy generation."""
        request = {
            "campaign_spec": sample_campaign_spec.model_dump(),
            "product_groups": [pg.model_dump() for pg in sample_product_groups],
            "creatives": [c.model_dump() for c in sample_creatives]
        }
        
        response = client.post("/generate_strategy", json=request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "abstract_strategy" in data
        assert "platform_strategies" in data
        assert "debug" in data
    
    def test_generate_strategy_legacy_format(self):
        """Test strategy generation with legacy API format."""
        request = {
            "campaign_objective": "conversions",
            "total_budget": 5000.0,
            "duration_days": 30,
            "target_audience": "tech enthusiasts",
            "platforms": ["facebook", "instagram"]
        }
        
        response = client.post("/generate_strategy", json=request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "abstract_strategy" in data
        assert "platform_strategies" in data
    
    def test_generate_strategy_invalid_budget(self, sample_campaign_spec, sample_product_groups, sample_creatives):
        """Test strategy generation with invalid budget."""
        campaign_spec = CampaignSpec(
            user_query="Create a campaign",
            platform="meta",
            budget=-100.0,  # Invalid budget
            objective="conversions",
            category="general"
        )
        
        request = {
            "campaign_spec": campaign_spec.model_dump(),
            "product_groups": [pg.model_dump() for pg in sample_product_groups],
            "creatives": [c.model_dump() for c in sample_creatives]
        }
        
        response = client.post("/generate_strategy", json=request)
        assert response.status_code == 200  # Returns 200 with error response
        
        data = response.json()
        assert data["status"] == "error"
        assert data["error_code"] == "INVALID_BUDGET"
    
    def test_generate_strategy_missing_fields(self):
        """Test strategy generation with missing required fields."""
        request = {
            "campaign_objective": "conversions"
            # Missing total_budget
        }
        
        response = client.post("/generate_strategy", json=request)
        assert response.status_code == 200  # Returns 200 with error response
        
        data = response.json()
        assert data["status"] == "error"

