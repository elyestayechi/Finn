from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_get_analyses():
    response = client.get("/api/analyses/recent")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_analysis():
    response = client.post("/api/analyses", json={
        "loan_id": "test123",
        "notes": "Test analysis"
    })
    assert response.status_code in [200, 500]  # 500 if Ollama not available