"""
Tests for Strategy Service
"""

import pytest
from fastapi.testclient import TestClient
from app.services.strategy_service.main import app

client = TestClient(app)


class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check(self):
        """Test basic health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "strategy_service"


class TestGenerateStrategy:
    """Test strategy generation endpoint"""
    
    def test_generate_strategy_success(self):
        """Test successful strategy generation"""
        payload = {
            "campaign_objective": "sales",
            "total_budget": 10000,
            "duration_days": 30,
            "target_audience": "young professionals",
            "platforms": ["facebook", "instagram"]
        }
        response = client.post("/generate_strategy", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "platform_strategies" in data
        assert len(data["platform_strategies"]) > 0
        # Budget allocation is in platform_strategies, not top level
        assert "abstract_strategy" in data
    
    def test_generate_strategy_single_platform(self):
        """Test strategy generation for single platform"""
        payload = {
            "campaign_objective": "brand_awareness",
            "total_budget": 5000,
            "duration_days": 14,
            "target_audience": "tech enthusiasts",
            "platforms": ["facebook"]
        }
        response = client.post("/generate_strategy", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data["platform_strategies"]) == 1
    
    def test_generate_strategy_validation_error(self):
        """Test strategy generation with invalid payload"""
        payload = {
            "campaign_objective": "invalid",
            "total_budget": -100  # Invalid budget
        }
        response = client.post("/generate_strategy", json=payload)
        assert response.status_code == 422
    
    def test_generate_strategy_missing_fields(self):
        """Test strategy generation with missing required fields"""
        payload = {
            "campaign_objective": "sales"
            # Missing other required fields
        }
        response = client.post("/generate_strategy", json=payload)
        assert response.status_code == 422

