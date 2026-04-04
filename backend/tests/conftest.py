from fastapi.testclient import TestClient

from app.main import app


def test_app_health_routes_module_loads() -> None:
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200
