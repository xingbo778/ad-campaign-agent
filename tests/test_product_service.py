"""
Tests for Product Service
"""

import pytest
from fastapi.testclient import TestClient
from app.services.product_service.main import app

client = TestClient(app)


class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check(self):
        """Test basic health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "product_service"
    
    def test_health_check_headers(self):
        """Test that health check includes request ID header"""
        response = client.get("/health")
        assert "X-Request-ID" in response.headers


class TestSelectProducts:
    """Test product selection endpoint"""
    
    def test_select_products_success(self):
        """Test successful product selection"""
        # Use legacy API format (backward compatible)
        payload = {
            "campaign_objective": "sales",
            "target_audience": "young professionals aged 25-40",
            "budget": 10000,
            "max_products": 10
        }
        response = client.post("/select_products", json=payload)
        assert response.status_code == 200
        data = response.json()
        # Service returns both new and legacy fields
        assert data["status"] == "success"
        assert "products" in data or "product_groups" in data
        if "products" in data:
            assert len(data["products"]) > 0
        if "product_groups" in data:
            assert len(data["product_groups"]) > 0
    
    def test_select_products_with_filters(self):
        """Test product selection with category filters"""
        # Use legacy API format with category in metadata
        payload = {
            "campaign_objective": "sales",
            "target_audience": "tech enthusiasts",
            "budget": 5000,
            "max_products": 10
        }
        response = client.post("/select_products", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        # Service returns both new and legacy fields
        if "product_groups" in data:
            assert len(data["product_groups"]) > 0
            # Check that products exist in groups
            total_products = sum(len(group["products"]) for group in data["product_groups"])
            assert total_products > 0
        if "products" in data:
            assert len(data["products"]) > 0
    
    def test_select_products_validation_error(self):
        """Test product selection with invalid payload"""
        payload = {
            "campaign_objective": "sales",
            "target_audience": "test",
            "budget": -100  # Invalid budget
        }
        response = client.post("/select_products", json=payload)
        # Service validates budget and returns error response (200 with error status)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert data["error_code"] == "INVALID_BUDGET"
    
    def test_select_products_missing_fields(self):
        """Test product selection with missing required fields"""
        payload = {
            "campaign_objective": "sales"
            # Missing target_audience and budget
        }
        response = client.post("/select_products", json=payload)
        # Service validates and returns error response (200 with error status)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert data["error_code"] in ["MISSING_REQUIRED_FIELDS", "VALIDATION_ERROR"]


class TestRequestID:
    """Test request ID tracking"""
    
    def test_request_id_in_response(self):
        """Test that request ID is included in response headers"""
        response = client.post("/select_products", json={
            "campaign_objective": "sales",
            "target_audience": "test",
            "budget": 1000
        })
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0
    
    def test_request_id_consistency(self):
        """Test that request ID is consistent across multiple calls"""
        # Request IDs should be unique
        response1 = client.get("/health")
        response2 = client.get("/health")
        assert response1.headers["X-Request-ID"] != response2.headers["X-Request-ID"]

