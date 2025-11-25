"""
Integration tests for product selection endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from app.services.product_service.main import app
from app.common.schemas import CampaignSpec, Product

client = TestClient(app)


@pytest.fixture
def valid_campaign_spec():
    """Valid campaign specification."""
    return CampaignSpec(
        user_query="Create a campaign for electronics",
        platform="meta",
        budget=2000.0,
        objective="conversions",
        category="electronics",
        metadata={}
    )


@pytest.fixture
def valid_request(valid_campaign_spec):
    """Valid select products request."""
    return {
        "campaign_spec": valid_campaign_spec.model_dump(),
        "limit": 10
    }


class TestSelectProductsEndpoint:
    """Test select_products endpoint."""
    
    def test_select_products_success(self, valid_request):
        """Test successful product selection."""
        response = client.post("/select_products", json=valid_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert "products" in data
        assert "groups" in data
        assert "debug" in data
        
        # Verify products list
        assert isinstance(data["products"], list)
        assert len(data["products"]) > 0
        
        # Verify groups
        assert isinstance(data["groups"], list)
        assert len(data["groups"]) > 0
        
        # Verify debug info
        debug = data["debug"]
        assert "scoring_details" in debug
        assert "selected_ids" in debug
        assert "rules_applied" in debug
    
    def test_select_products_with_limit(self, valid_campaign_spec):
        """Test product selection with custom limit."""
        request = {
            "campaign_spec": valid_campaign_spec.model_dump(),
            "limit": 5
        }
        
        response = client.post("/select_products", json=request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert len(data["products"]) <= 5
    
    def test_select_products_category_filter(self, valid_campaign_spec):
        """Test product selection filters by category."""
        request = {
            "campaign_spec": valid_campaign_spec.model_dump(),
            "limit": 10
        }
        
        response = client.post("/select_products", json=request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        
        # Verify products match category
        for product in data["products"]:
            assert "electronics" in product["category"].lower() or "accessories" in product["category"].lower()
    
    def test_select_products_invalid_budget(self, valid_campaign_spec):
        """Test product selection with invalid budget."""
        invalid_spec = CampaignSpec(
            user_query="Test",
            platform="meta",
            budget=-100.0,  # Invalid budget
            objective="conversions",
            category="electronics"
        )
        
        request = {
            "campaign_spec": invalid_spec.model_dump(),
            "limit": 10
        }
        
        response = client.post("/select_products", json=request)
        assert response.status_code == 200  # Returns 200 with error response
        
        data = response.json()
        assert data["status"] == "error"
        assert data["error_code"] == "INVALID_BUDGET"
    
    def test_select_products_invalid_limit(self, valid_campaign_spec):
        """Test product selection with invalid limit."""
        request = {
            "campaign_spec": valid_campaign_spec.model_dump(),
            "limit": -5  # Invalid limit
        }
        
        response = client.post("/select_products", json=request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "error"
        assert data["error_code"] == "INVALID_LIMIT"
    
    def test_select_products_groups_structure(self, valid_request):
        """Test product groups have correct structure."""
        response = client.post("/select_products", json=valid_request)
        assert response.status_code == 200
        
        data = response.json()
        groups = data["groups"]
        
        for group in groups:
            assert "group" in group
            assert group["group"] in ["high", "medium", "low"]
            assert "products" in group
            assert isinstance(group["products"], list)
            assert len(group["products"]) > 0
    
    def test_select_products_debug_info(self, valid_request):
        """Test debug information is complete."""
        response = client.post("/select_products", json=valid_request)
        assert response.status_code == 200
        
        data = response.json()
        debug = data["debug"]
        
        # Verify scoring details
        assert "scoring_details" in debug
        scoring_details = debug["scoring_details"]
        assert isinstance(scoring_details, dict)
        
        # Verify each product has scoring details
        for product in data["products"]:
            product_id = product["product_id"]
            assert product_id in scoring_details
            assert "score" in scoring_details[product_id]
            assert "breakdown" in scoring_details[product_id]
        
        # Verify rules applied
        assert "rules_applied" in debug
        assert isinstance(debug["rules_applied"], list)
        assert len(debug["rules_applied"]) > 0
    
    def test_select_products_legacy_fields(self, valid_request):
        """Test legacy response fields for backward compatibility."""
        response = client.post("/select_products", json=valid_request)
        assert response.status_code == 200
        
        data = response.json()
        
        # Legacy fields should be present
        assert "product_groups" in data
        assert "total_products" in data
        
        # Should match new fields
        assert data["product_groups"] == data["groups"]
        assert data["total_products"] == len(data["products"])
    
    def test_select_products_different_categories(self):
        """Test product selection for different categories."""
        categories = ["electronics", "accessories", "fashion", "toys"]
        
        for category in categories:
            campaign_spec = CampaignSpec(
                user_query=f"Campaign for {category}",
                platform="meta",
                budget=2000.0,
                objective="conversions",
                category=category
            )
            
            request = {
                "campaign_spec": campaign_spec.model_dump(),
                "limit": 5
            }
            
            response = client.post("/select_products", json=request)
            assert response.status_code == 200
            
            data = response.json()
            # Should return success (may have 0 products if category doesn't exist)
            assert data["status"] in ["success", "error"]
    
    def test_select_products_no_category(self):
        """Test product selection without category filter."""
        campaign_spec = CampaignSpec(
            user_query="General campaign",
            platform="meta",
            budget=2000.0,
            objective="conversions",
            category=""  # No category
        )
        
        request = {
            "campaign_spec": campaign_spec.model_dump(),
            "limit": 10
        }
        
        response = client.post("/select_products", json=request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert len(data["products"]) > 0

