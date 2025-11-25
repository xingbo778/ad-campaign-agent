"""
Tests for Logs Service
"""

import pytest
from fastapi.testclient import TestClient
from app.services.logs_service.main import app

client = TestClient(app)


class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check(self):
        """Test basic health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "logs_service"


class TestAppendEvent:
    """Test event logging endpoint"""
    
    def test_append_event_success(self):
        """Test successful event logging"""
        from datetime import datetime
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "stage": "product",
            "service": "product_service",
            "success": True,
            "request": {"campaign_spec": {"category": "electronics"}},
            "response": {"status": "success", "products": []},
            "metadata": {
                "message": "Campaign created successfully",
                "campaign_id": "campaign_123",
                "user_id": "user_456",
                "platform": "meta"
            }
        }
        response = client.post("/append_event", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "event_id" in data
    
    def test_append_event_minimal(self):
        """Test event logging with minimal required fields"""
        from datetime import datetime
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "stage": "orchestrator",
            "service": "orchestrator_agent",
            "success": True,
            "metadata": {"message": "Test message"}
        }
        response = client.post("/append_event", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "event_id" in data
    
    def test_append_event_validation_error(self):
        """Test event logging with invalid payload"""
        payload = {
            "event_type": ""  # Empty event type
        }
        response = client.post("/append_event", json=payload)
        assert response.status_code == 422

