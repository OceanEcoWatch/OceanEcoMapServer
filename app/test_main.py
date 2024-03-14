from fastapi.testclient import TestClient

from .main import app

client = TestClient(app)


def test_health_status():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"message": "Application running"}
