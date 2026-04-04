from fastapi.testclient import TestClient

from app.main import create_app


def test_post_evaluations_returns_pending_task(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("REQUIREMENTS_EVALUATOR_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    response = client.post(
        "/api/evaluations",
        files={
            "file": (
                "requirements.csv",
                "OR需求编号,OR需求名称*,OR需求描述*\nD1,N,D\n".encode("utf-8"),
                "text/csv",
            )
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "pending"


def test_get_evaluation_returns_detail(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("REQUIREMENTS_EVALUATOR_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = TestClient(create_app())
    create = client.post(
        "/api/evaluations",
        files={
            "file": (
                "requirements.csv",
                "OR需求编号,OR需求名称*,OR需求描述*\nD1,N,D\n".encode("utf-8"),
                "text/csv",
            )
        },
    )
    evaluation_id = create.json()["evaluation_id"]
    detail = client.get(f"/api/evaluations/{evaluation_id}")
    assert detail.status_code == 200
    assert detail.json()["evaluation_id"] == evaluation_id
    assert detail.json()["status"] == "succeeded"
    assert detail.json()["report_markdown"].startswith("# Mock Report")


def test_get_evaluation_returns_404_for_missing_id(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("REQUIREMENTS_EVALUATOR_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())

    response = client.get("/api/evaluations/eval_missing")

    assert response.status_code == 404
