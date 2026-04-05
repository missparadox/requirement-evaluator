import importlib
import shutil
from unittest.mock import patch

import pytest
from fastapi import FastAPI

import app.main as main_module


def test_create_app_raises_when_no_model_provider_is_available(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ZHIPU_API_KEY", raising=False)
    monkeypatch.delenv("REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK", raising=False)

    with patch.object(shutil, "which", return_value=None):
        with pytest.raises(RuntimeError, match="No model provider is available") as exc_info:
            importlib.reload(main_module)

    message = str(exc_info.value)
    assert "OPENAI_API_KEY" in message
    assert "ZHIPU_API_KEY" in message
    assert "codex" in message
    assert "REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK=1" in message


def test_create_app_succeeds_with_debug_fallback_when_codex_is_unavailable(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ZHIPU_API_KEY", raising=False)
    monkeypatch.setenv("REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK", "1")

    with patch.object(shutil, "which", return_value=None):
        app = importlib.reload(main_module).create_app()

    assert isinstance(app, FastAPI)
    assert app.title == "Requirements Evaluator API"
