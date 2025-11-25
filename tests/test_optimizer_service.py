"""
Tests for Optimizer Service
"""

import pytest
from fastapi.testclient import TestClient
from app.services.optimizer_service.main import app

client = TestClient(app)


class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check(self):
        """Test basic health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "optimizer_service"


class TestSummarizeRecentRuns:
    """Test optimization summary endpoint"""
    
    def test_summarize_recent_runs_success(self):
        """Test successful optimization summary"""
        payload = {
            "campaign_ids": ["campaign_1", "campaign_2", "campaign_3"],
            "days": 7
        }
        response = client.post("/summarize_recent_runs", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "suggestions" in data
        assert len(data["suggestions"]) > 0
        # Metrics are at top level (average_cpa, total_campaigns, etc.)
        assert "average_cpa" in data or "total_campaigns" in data
    
    def test_summarize_recent_runs_empty_campaigns(self):
        """Test optimization summary with empty campaign list"""
        payload = {
            "campaign_ids": [],
            "days": 7
        }
        response = client.post("/summarize_recent_runs", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
    
    def test_summarize_recent_runs_validation_error(self):
        """Test optimization summary with invalid payload"""
        payload = {
            "campaign_ids": "not_a_list",  # Invalid type
            "days": -1  # Invalid days
        }
        response = client.post("/summarize_recent_runs", json=payload)
        assert response.status_code == 422

