import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from conftest import configure_runtime_env, import_app_main_module


def test_create_app_raises_when_no_model_provider_is_available(monkeypatch) -> None:
    configure_runtime_env(monkeypatch)

    with pytest.raises(RuntimeError, match="No model provider is available") as exc_info:
        import_app_main_module()

    message = str(exc_info.value)
    assert "OPENAI_API_KEY" in message
    assert "ZHIPU_API_KEY" in message
    assert "codex" in message
    assert "REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK=1" in message


def test_create_app_succeeds_with_debug_fallback_when_codex_is_unavailable(monkeypatch) -> None:
    configure_runtime_env(monkeypatch, debug_fallback_enabled=True)

    app = import_app_main_module().create_app()

    assert isinstance(app, FastAPI)
    assert app.title == "Requirements Evaluator API"


def test_app_module_serves_openapi_when_debug_fallback_enabled(monkeypatch, tmp_path) -> None:
    configure_runtime_env(
        monkeypatch,
        data_dir=str(tmp_path),
        debug_fallback_enabled=True,
    )

    app_module = import_app_main_module()
    client = TestClient(app_module.app)
    response = client.get("/openapi.json")

    assert response.status_code == 200
