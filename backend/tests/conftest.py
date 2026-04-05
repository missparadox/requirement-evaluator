import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK", "1")

from app.main import app


def test_app_health_routes_module_loads() -> None:
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200
