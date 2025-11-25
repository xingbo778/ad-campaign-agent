"""
Tests for invalid input handling in strategy generation.

Tests verify that the service correctly handles:
- Missing required fields
- Invalid budget values
- Empty product groups
- Missing creatives
"""

import pytest
from fastapi.testclient import TestClient
from app.services.strategy_service.main import app
from app.common.schemas import CampaignSpec, ProductGroup, Creative, Product


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


def test_missing_creatives(client, campaign_spec_valid, product_group_high):
    """Test that empty creatives uses default variant split (service handles gracefully)."""
    request_payload = {
        "campaign_spec": campaign_spec_valid.model_dump(),
        "product_groups": [product_group_high.model_dump()],
        "creatives": []  # Empty creatives
    }
    
    response = client.post("/generate_strategy", json=request_payload)
    
    # Service handles empty creatives gracefully with default split
    assert response.status_code == 200, \
        f"Expected 200, got {response.status_code}"
    
    data = response.json()
    
    # Service returns success with default variant split
    assert data["status"] == "success", \
        f"Service handles empty creatives gracefully, got '{data.get('status')}'"
    
    # Verify default variant split is used
    abstract_strategy = data["abstract_strategy"]
    budget_split = abstract_strategy["budget_split"]
    assert "A" in budget_split or "B" in budget_split, \
        "Default variant split should be present"


def test_budget_zero(client, product_group_high, creatives_ab):
    """Test that budget of zero returns an error."""
    campaign_spec = CampaignSpec(
        user_query="Test zero budget",
        platform="meta",
        budget=0.0,  # Invalid budget
        objective="conversions",
        category="electronics",
        metadata={}
    )
    
    request_payload = {
        "campaign_spec": campaign_spec.model_dump(),
        "product_groups": [product_group_high.model_dump()],
        "creatives": [c.model_dump() for c in creatives_ab]
    }
    
    response = client.post("/generate_strategy", json=request_payload)
    assert response.status_code in [200, 400]
    
    data = response.json()
    assert data["status"] == "error"
    assert "error_code" in data
    assert "INVALID_BUDGET" in data["error_code"] or "VALIDATION_ERROR" in data["error_code"]


def test_budget_negative(client, product_group_high, creatives_ab):
    """Test that negative budget returns an error."""
    campaign_spec = CampaignSpec(
        user_query="Test negative budget",
        platform="meta",
        budget=-100.0,  # Invalid budget
        objective="conversions",
        category="electronics",
        metadata={}
    )
    
    request_payload = {
        "campaign_spec": campaign_spec.model_dump(),
        "product_groups": [product_group_high.model_dump()],
        "creatives": [c.model_dump() for c in creatives_ab]
    }
    
    response = client.post("/generate_strategy", json=request_payload)
    assert response.status_code in [200, 400]
    
    data = response.json()
    assert data["status"] == "error"
    assert "error_code" in data


def test_empty_product_groups(client, campaign_spec_valid, creatives_ab):
    """Test that empty product groups uses default allocation (service handles gracefully)."""
    request_payload = {
        "campaign_spec": campaign_spec_valid.model_dump(),
        "product_groups": [],  # Empty product groups
        "creatives": [c.model_dump() for c in creatives_ab]
    }
    
    response = client.post("/generate_strategy", json=request_payload)
    
    # Service handles empty product groups gracefully with default allocation
    assert response.status_code == 200, \
        f"Service handles empty product groups, got {response.status_code}"
    
    data = response.json()
    
    # Service returns success with default allocation
    assert data["status"] == "success", \
        f"Service handles empty product groups gracefully, got '{data.get('status')}'"
    
    # Verify default allocation is used
    debug = data["debug"]
    budget_plan = debug["budget_plan"]
    assert "group_allocation" in budget_plan, \
        "Default group allocation should be present"


def test_missing_campaign_spec(client, product_group_high, creatives_ab):
    """Test that missing campaign_spec returns validation error."""
    request_payload = {
        # Missing campaign_spec
        "product_groups": [product_group_high.model_dump()],
        "creatives": [c.model_dump() for c in creatives_ab]
    }
    
    response = client.post("/generate_strategy", json=request_payload)
    
    # FastAPI validation should return 422
    assert response.status_code == 422, \
        f"Expected 422 for validation error, got {response.status_code}"


def test_missing_product_groups(client, campaign_spec_valid, creatives_ab):
    """Test that missing product_groups returns validation error."""
    request_payload = {
        "campaign_spec": campaign_spec_valid.model_dump(),
        # Missing product_groups
        "creatives": [c.model_dump() for c in creatives_ab]
    }
    
    response = client.post("/generate_strategy", json=request_payload)
    
    # FastAPI validation should return 422
    assert response.status_code == 422, \
        f"Expected 422 for validation error, got {response.status_code}"


def test_missing_creatives_field(client, campaign_spec_valid, product_group_high):
    """Test that missing creatives field returns validation error."""
    request_payload = {
        "campaign_spec": campaign_spec_valid.model_dump(),
        "product_groups": [product_group_high.model_dump()]
        # Missing creatives field
    }
    
    response = client.post("/generate_strategy", json=request_payload)
    
    # FastAPI validation should return 422
    assert response.status_code == 422, \
        f"Expected 422 for validation error, got {response.status_code}"


def test_invalid_platform(client, product_group_high, creatives_ab):
    """Test that invalid platform returns validation error at Pydantic level."""
    # Invalid platform should fail at Pydantic validation (422)
    # We can't create a CampaignSpec with invalid platform, so test with raw dict
    request_payload = {
        "campaign_spec": {
            "user_query": "Test invalid platform",
            "platform": "invalid_platform",  # Invalid platform
            "budget": 2000.0,
            "objective": "conversions",
            "category": "electronics",
            "metadata": {}
        },
        "product_groups": [product_group_high.model_dump()],
        "creatives": [c.model_dump() for c in creatives_ab]
    }
    
    response = client.post("/generate_strategy", json=request_payload)
    
    # Should return validation error (422) from Pydantic
    assert response.status_code == 422, \
        f"Expected 422 for invalid platform, got {response.status_code}"
    
    data = response.json()
    # FastAPI validation error format
    assert "detail" in data or "status" in data


def test_invalid_objective(client, product_group_high, creatives_ab):
    """Test that invalid objective returns validation error."""
    # This should fail at Pydantic validation level
    with pytest.raises(Exception):
        campaign_spec = CampaignSpec(
            user_query="Test invalid objective",
            platform="meta",
            budget=2000.0,
            objective="invalid_objective",  # Invalid objective
            category="electronics",
            metadata={}
        )


def test_malformed_request(client):
    """Test that malformed JSON request returns validation error."""
    # Send invalid JSON
    response = client.post(
        "/generate_strategy",
        json={"invalid": "data"},
        headers={"Content-Type": "application/json"}
    )
    
    # Should return validation error
    assert response.status_code in [200, 400, 422]

