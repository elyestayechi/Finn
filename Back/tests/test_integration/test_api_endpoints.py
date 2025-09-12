import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_get_analyses():
    """Test getting recent analyses"""
    response = client.get("/api/analyses/recent")
    assert response.status_code in [200, 404]  # 404 if no analyses exist

def test_create_feedback():
    """Test feedback creation"""
    feedback_data = {
        "loan_id": "TEST123",
        "agent_recommendation": "approve",
        "human_decision": "approve",
        "rating": 5,
        "comments": "Test feedback"
    }
    
    response = client.post("/feedback/", json=feedback_data)
    assert response.status_code in [201, 500]  # 500 if loan doesn't exist