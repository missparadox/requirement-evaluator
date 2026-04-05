from fastapi.testclient import TestClient

from app.main import create_app


def _enable_debug_startup(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ZHIPU_API_KEY", raising=False)
    monkeypatch.setenv("REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK", "1")
    monkeypatch.setenv("PATH", "")


def test_post_evaluations_returns_pending_task(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("REQUIREMENTS_EVALUATOR_DATA_DIR", str(tmp_path))
    _enable_debug_startup(monkeypatch)
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
    _enable_debug_startup(monkeypatch)
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
    _enable_debug_startup(monkeypatch)
    client = TestClient(create_app())

    response = client.get("/api/evaluations/eval_missing")

    assert response.status_code == 404


def test_retry_evaluation_creates_new_pending_task(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("REQUIREMENTS_EVALUATOR_DATA_DIR", str(tmp_path))
    _enable_debug_startup(monkeypatch)
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
    original_evaluation_id = create.json()["evaluation_id"]
    metadata_path = tmp_path / "evaluations" / original_evaluation_id / "metadata.json"
    metadata = __import__("json").loads(metadata_path.read_text(encoding="utf-8"))
    metadata["status"] = "failed"
    metadata["error_message"] = "forced failure"
    metadata_path.write_text(__import__("json").dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    retry = client.post(f"/api/evaluations/{original_evaluation_id}/retry")

    assert retry.status_code == 200
    assert retry.json()["evaluation_id"] != original_evaluation_id
    assert retry.json()["status"] in {"pending", "succeeded"}


def test_retry_evaluation_rejects_non_failed_task(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("REQUIREMENTS_EVALUATOR_DATA_DIR", str(tmp_path))
    _enable_debug_startup(monkeypatch)
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

    retry = client.post(f"/api/evaluations/{evaluation_id}/retry")

    assert retry.status_code == 409
