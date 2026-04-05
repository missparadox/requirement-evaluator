# Model Configuration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic backend-only model provider selection with OpenAI, Zhipu, Codex CLI, and debug fallback, including startup validation and documentation updates.

**Architecture:** Expand `Settings` into a provider-aware configuration object, then move provider resolution into the model client layer so provider priority is enforced in one place. Keep the HTTP API unchanged while persisting the resolved `model_provider` and `model_name` in evaluation metadata and failing the service at startup when no valid runtime mode exists.

**Tech Stack:** Python, FastAPI, pytest, OpenAI Python SDK, subprocess, local environment variables

---

## File Map

- Modify: `backend/app/core/config.py`
  Parse and normalize provider-specific environment variables.
- Modify: `backend/app/clients/model_client.py`
  Add provider resolution, Zhipu/OpenAI-compatible transport reuse, Codex CLI execution, and startup validation helpers.
- Modify: `backend/app/api/routes/evaluations.py`
  Build the runner from resolved settings instead of a single global model name.
- Modify: `backend/app/services/evaluation_service.py`
  Persist the resolved provider and model metadata through the existing dedupe flow.
- Modify: `backend/app/main.py`
  Validate provider availability during application startup.
- Modify: `backend/tests/test_evaluation_service.py`
  Cover provider selection, normalization, Codex execution, and metadata persistence.
- Modify: `backend/tests/test_evaluations_api.py`
  Add API-facing startup failure coverage when no runtime mode exists.
- Create: `backend/tests/test_main.py`
  Cover startup fail-fast behavior in isolation.
- Modify: `README.md`
  Document the four runtime modes, env vars, priority order, and startup failure behavior.
- Modify: `docs/requirements-evaluator-dev-notes.md`
  Sync the model runtime notes with the new provider priority design.

### Task 1: Expand settings for provider-aware configuration

**Files:**
- Modify: `backend/app/core/config.py`
- Test: `backend/tests/test_evaluation_service.py`

- [ ] **Step 1: Write the failing normalization tests**

```python
def test_get_settings_normalizes_blank_provider_values(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("REQUIREMENTS_EVALUATOR_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("OPENAI_API_KEY", "   ")
    monkeypatch.setenv("OPENAI_MODEL", "   ")
    monkeypatch.setenv("OPENAI_BASE_URL", "   ")
    monkeypatch.setenv("ZHIPU_API_KEY", "")
    monkeypatch.setenv("ZHIPU_MODEL", "   ")
    monkeypatch.setenv("CODEX_MODEL", "   ")
    monkeypatch.setenv("REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK", "0")

    settings = get_settings()

    assert settings.openai_api_key is None
    assert settings.openai_model == "gpt-5.4"
    assert settings.zhipu_api_key is None
    assert settings.zhipu_model == "glm-5"
    assert settings.codex_model == "gpt-5.4"
    assert settings.debug_fallback_enabled is False
```

```python
def test_get_settings_reads_explicit_provider_values(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("REQUIREMENTS_EVALUATOR_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.4-mini")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://openai.example/v1")
    monkeypatch.setenv("ZHIPU_API_KEY", "zhipu-key")
    monkeypatch.setenv("ZHIPU_MODEL", "glm-5-air")
    monkeypatch.setenv("ZHIPU_BASE_URL", "https://zhipu.example/api/paas/v4")
    monkeypatch.setenv("CODEX_MODEL", "gpt-5.4-mini")
    monkeypatch.setenv("REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK", "1")

    settings = get_settings()

    assert settings.openai_api_key == "openai-key"
    assert settings.openai_model == "gpt-5.4-mini"
    assert settings.openai_base_url == "https://openai.example/v1"
    assert settings.zhipu_api_key == "zhipu-key"
    assert settings.zhipu_model == "glm-5-air"
    assert settings.zhipu_base_url == "https://zhipu.example/api/paas/v4"
    assert settings.codex_model == "gpt-5.4-mini"
    assert settings.debug_fallback_enabled is True
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `./.venv/bin/python -m pytest -q backend/tests/test_evaluation_service.py -k settings`
Expected: FAIL with missing `Settings` fields such as `openai_api_key` or `debug_fallback_enabled`

- [ ] **Step 3: Implement the expanded settings object**

```python
from dataclasses import dataclass
from pathlib import Path
import os

from app.core.paths import REPO_ROOT


def _normalized_env(name: str) -> str | None:
    value = os.environ.get(name)
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    openai_api_key: str | None
    openai_model: str
    openai_base_url: str
    zhipu_api_key: str | None
    zhipu_model: str
    zhipu_base_url: str
    codex_model: str
    debug_fallback_enabled: bool


def get_settings() -> Settings:
    data_dir = Path(os.environ.get("REQUIREMENTS_EVALUATOR_DATA_DIR", REPO_ROOT / "data"))
    return Settings(
        data_dir=data_dir,
        openai_api_key=_normalized_env("OPENAI_API_KEY"),
        openai_model=_normalized_env("OPENAI_MODEL") or "gpt-5.4",
        openai_base_url=_normalized_env("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        zhipu_api_key=_normalized_env("ZHIPU_API_KEY"),
        zhipu_model=_normalized_env("ZHIPU_MODEL") or "glm-5",
        zhipu_base_url=_normalized_env("ZHIPU_BASE_URL") or "https://open.bigmodel.cn/api/paas/v4",
        codex_model=_normalized_env("CODEX_MODEL") or "gpt-5.4",
        debug_fallback_enabled=_normalized_env("REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK") == "1",
    )
```

- [ ] **Step 4: Run the settings tests to verify they pass**

Run: `./.venv/bin/python -m pytest -q backend/tests/test_evaluation_service.py -k settings`
Expected: PASS with `2 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/config.py backend/tests/test_evaluation_service.py
git commit -m "feat: add provider-aware backend settings"
```

### Task 2: Implement provider resolution priority and hosted-provider clients

**Files:**
- Modify: `backend/app/clients/model_client.py`
- Modify: `backend/app/services/evaluation_service.py`
- Test: `backend/tests/test_evaluation_service.py`

- [ ] **Step 1: Write the failing provider-resolution tests**

```python
def test_build_model_client_prefers_openai_over_all_other_modes(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("ZHIPU_API_KEY", "zhipu-key")
    monkeypatch.setenv("REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK", "1")
    monkeypatch.setattr("app.clients.model_client.shutil.which", lambda _: "/usr/local/bin/codex")

    settings = get_settings()
    client = build_model_client(settings)

    assert isinstance(client, OpenAIModelClient)
    assert model_provider_name(settings) == "openai"
```

```python
def test_build_model_client_uses_zhipu_when_openai_is_unavailable(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("ZHIPU_API_KEY", "zhipu-key")
    monkeypatch.setattr("app.clients.model_client.OpenAI", Mock(return_value=Mock()))

    settings = get_settings()
    client = build_model_client(settings)

    assert isinstance(client, OpenAIModelClient)
    assert client.model_name == "glm-5"
    assert model_provider_name(settings) == "zhipu"
```

```python
def test_create_makes_new_evaluation_when_model_provider_changes_to_zhipu(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ZHIPU_API_KEY", raising=False)
    monkeypatch.setenv("REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK", "1")
    service = EvaluationService(store=EvaluationStore(tmp_path))
    first = service.create_or_reuse(filename="requirements.csv", file_bytes=b"abc")

    monkeypatch.delenv("REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK", raising=False)
    monkeypatch.setenv("ZHIPU_API_KEY", "zhipu-key")
    second = EvaluationService(store=EvaluationStore(tmp_path)).create_or_reuse(
        filename="requirements.csv",
        file_bytes=b"abc",
    )

    assert second.evaluation_id != first.evaluation_id
    assert second.dedupe_hit is False
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `./.venv/bin/python -m pytest -q backend/tests/test_evaluation_service.py -k "prefers_openai or uses_zhipu or model_provider_changes_to_zhipu"`
Expected: FAIL because `build_model_client()` still accepts a single model name and cannot resolve `zhipu`

- [ ] **Step 3: Implement provider resolution and hosted-provider construction**

```python
import shutil
from dataclasses import dataclass
from typing import Literal, Protocol

from openai import OpenAI

from app.core.config import Settings

ProviderName = Literal["openai", "zhipu", "codex", "static"]


@dataclass(frozen=True)
class ResolvedModelRuntime:
    provider: ProviderName
    model_name: str
    base_url: str | None = None
    api_key: str | None = None


def resolve_model_runtime(settings: Settings) -> ResolvedModelRuntime:
    if settings.openai_api_key:
        return ResolvedModelRuntime(
            provider="openai",
            model_name=settings.openai_model,
            base_url=settings.openai_base_url,
            api_key=settings.openai_api_key,
        )
    if settings.zhipu_api_key:
        return ResolvedModelRuntime(
            provider="zhipu",
            model_name=settings.zhipu_model,
            base_url=settings.zhipu_base_url,
            api_key=settings.zhipu_api_key,
        )
    if shutil.which("codex"):
        return ResolvedModelRuntime(provider="codex", model_name=settings.codex_model)
    if settings.debug_fallback_enabled:
        return ResolvedModelRuntime(provider="static", model_name=settings.codex_model)
    raise RuntimeError("No model provider is available. Checked OpenAI API key, Zhipu API key, local codex binary, and REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK=1.")


def model_provider_name(settings: Settings) -> ProviderName:
    return resolve_model_runtime(settings).provider


def build_model_client(settings: Settings) -> ModelClient:
    runtime = resolve_model_runtime(settings)
    if runtime.provider in {"openai", "zhipu"}:
        return OpenAIModelClient(
            model_name=runtime.model_name,
            client=OpenAI(api_key=runtime.api_key, base_url=runtime.base_url),
        )
    if runtime.provider == "codex":
        return CodexModelClient(model_name=runtime.model_name)
    return StaticModelClient()
```

```python
class EvaluationService:
    def __init__(self, *, store: EvaluationStore) -> None:
        settings = get_settings()
        runtime = resolve_model_runtime(settings)
        self.store = store
        self.model_name = runtime.model_name
        self.model_provider = runtime.provider
```

- [ ] **Step 4: Run the provider-resolution tests to verify they pass**

Run: `./.venv/bin/python -m pytest -q backend/tests/test_evaluation_service.py -k "prefers_openai or uses_zhipu or model_provider_changes_to_zhipu"`
Expected: PASS with `3 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/app/clients/model_client.py backend/app/services/evaluation_service.py backend/tests/test_evaluation_service.py
git commit -m "feat: add prioritized hosted model resolution"
```

### Task 3: Add Codex CLI execution and failure handling

**Files:**
- Modify: `backend/app/clients/model_client.py`
- Test: `backend/tests/test_evaluation_service.py`

- [ ] **Step 1: Write the failing Codex tests**

```python
def test_build_model_client_uses_codex_when_no_api_key_provider_exists(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ZHIPU_API_KEY", raising=False)
    monkeypatch.delenv("REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK", raising=False)
    monkeypatch.setattr("app.clients.model_client.shutil.which", lambda _: "/usr/local/bin/codex")

    settings = get_settings()
    client = build_model_client(settings)

    assert isinstance(client, CodexModelClient)
    assert client.model_name == "gpt-5.4"
```

```python
def test_codex_model_client_runs_exec_and_returns_stdout(monkeypatch) -> None:
    completed = Mock(return_value=Mock(returncode=0, stdout="# Codex Report\n", stderr=""))
    monkeypatch.setattr("app.clients.model_client.subprocess.run", completed)
    client = CodexModelClient(model_name="gpt-5.4")

    report = client.generate_report(skill_text="skill", template_text="template", packet_text="packet")

    assert report == "# Codex Report"
    completed.assert_called_once()
```

```python
def test_codex_model_client_raises_when_stdout_is_empty(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.clients.model_client.subprocess.run",
        Mock(return_value=Mock(returncode=0, stdout="   ", stderr="")),
    )
    client = CodexModelClient(model_name="gpt-5.4")

    with pytest.raises(RuntimeError, match="did not produce output"):
        client.generate_report(skill_text="skill", template_text="template", packet_text="packet")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `./.venv/bin/python -m pytest -q backend/tests/test_evaluation_service.py -k codex`
Expected: FAIL because `CodexModelClient` does not exist yet

- [ ] **Step 3: Implement the Codex client**

```python
import subprocess


@dataclass
class CodexModelClient:
    model_name: str

    def generate_report(self, *, skill_text: str, template_text: str, packet_text: str) -> str:
        prompt = (
            "You are a requirements evaluation assistant. "
            "Follow the rubric and produce the final answer in Chinese Markdown using the template.\n\n"
            "[SKILL]\n"
            f"{skill_text}\n\n"
            "[TEMPLATE]\n"
            f"{template_text}\n\n"
            "[PACKET]\n"
            f"{packet_text}\n"
        )
        completed = subprocess.run(
            ["codex", "exec", "--model", self.model_name, prompt],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"Codex execution failed: {completed.stderr.strip() or 'unknown error'}")
        report = completed.stdout.strip()
        if not report:
            raise RuntimeError("Codex execution did not produce output.")
        return report
```

- [ ] **Step 4: Run the Codex tests to verify they pass**

Run: `./.venv/bin/python -m pytest -q backend/tests/test_evaluation_service.py -k codex`
Expected: PASS with `3 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/app/clients/model_client.py backend/tests/test_evaluation_service.py
git commit -m "feat: add codex cli model client"
```

### Task 4: Fail fast on startup and update API wiring

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/api/routes/evaluations.py`
- Create: `backend/tests/test_main.py`
- Modify: `backend/tests/test_evaluations_api.py`

- [ ] **Step 1: Write the failing startup tests**

```python
import pytest

from app.main import create_app


def test_create_app_raises_when_no_model_runtime_is_available(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("REQUIREMENTS_EVALUATOR_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ZHIPU_API_KEY", raising=False)
    monkeypatch.delenv("REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK", raising=False)
    monkeypatch.setattr("app.clients.model_client.shutil.which", lambda _: None)

    with pytest.raises(RuntimeError, match="No model provider is available"):
        create_app()
```

```python
def test_create_app_allows_debug_fallback_when_explicitly_enabled(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("REQUIREMENTS_EVALUATOR_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK", "1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ZHIPU_API_KEY", raising=False)
    monkeypatch.setattr("app.clients.model_client.shutil.which", lambda _: None)

    app = create_app()

    assert app.title == "Requirements Evaluator API"
```

- [ ] **Step 2: Run the startup tests to verify they fail**

Run: `./.venv/bin/python -m pytest -q backend/tests/test_main.py`
Expected: FAIL because `create_app()` does not validate model runtime availability yet

- [ ] **Step 3: Implement startup validation and settings-based API wiring**

```python
from app.clients.model_client import build_model_client, resolve_model_runtime
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    resolve_model_runtime(settings)

    app = FastAPI(title="Requirements Evaluator API")
    app.include_router(evaluations_router)
    return app
```

```python
def get_runner() -> EvaluationRunner:
    settings = get_settings()
    return EvaluationRunner(
        store=get_store(),
        model_client=build_model_client(settings),
    )
```

- [ ] **Step 4: Run the startup and API tests to verify they pass**

Run: `./.venv/bin/python -m pytest -q backend/tests/test_main.py backend/tests/test_evaluations_api.py`
Expected: PASS with all startup and API tests green

- [ ] **Step 5: Commit**

```bash
git add backend/app/main.py backend/app/api/routes/evaluations.py backend/tests/test_main.py backend/tests/test_evaluations_api.py
git commit -m "feat: fail fast when no model runtime is available"
```

### Task 5: Update docs and run full verification

**Files:**
- Modify: `README.md`
- Modify: `docs/requirements-evaluator-dev-notes.md`

- [ ] **Step 1: Update the runtime configuration docs**

```md
## Model Runtime Priority

The backend chooses the first available runtime in this order:

1. OpenAI: enabled by `OPENAI_API_KEY`
2. Zhipu: enabled by `ZHIPU_API_KEY`
3. Codex CLI: enabled when `codex` is available on `PATH`
4. Debug fallback: enabled by `REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK=1`

If none of the above is available, backend startup fails with a configuration error.
```

```md
### Environment Variables

- `OPENAI_API_KEY`
- `OPENAI_MODEL` default `gpt-5.4`
- `OPENAI_BASE_URL` default `https://api.openai.com/v1`
- `ZHIPU_API_KEY`
- `ZHIPU_MODEL` default `glm-5`
- `ZHIPU_BASE_URL` default `https://open.bigmodel.cn/api/paas/v4`
- `CODEX_MODEL` default `gpt-5.4`
- `REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK=1` to explicitly enable the static fallback path
```

- [ ] **Step 2: Run the full backend verification**

Run: `./.venv/bin/python -m pytest -q backend/tests/test_evaluations_api.py backend/tests/test_evaluation_service.py backend/tests/test_evaluation_store.py backend/tests/test_versioning.py backend/tests/test_main.py`
Expected: PASS with all backend tests green

- [ ] **Step 3: Run the frontend regression verification**

Run: `cd frontend && corepack pnpm exec vitest run`
Expected: PASS with all frontend tests green and only the existing React Router future-flag warnings on stderr

- [ ] **Step 4: Commit**

```bash
git add README.md docs/requirements-evaluator-dev-notes.md
git commit -m "docs: document model runtime configuration"
```

- [ ] **Step 5: Final integration commit if doc changes were squashed locally**

```bash
git status --short
```

Expected: no modified tracked files remain; only optional local untracked inputs such as `dimensions.txt` and `requirements.csv`

## Self-Review

- Spec coverage: the plan covers provider priority, default env vars, Codex CLI execution, startup fail-fast behavior, metadata persistence, and documentation updates.
- Placeholder scan: no `TODO` or open placeholders remain; provider defaults are explicit, including `glm-5` and `gpt-5.4`.
- Type consistency: the plan standardizes on `Settings`, `ResolvedModelRuntime`, `build_model_client(settings)`, and `resolve_model_runtime(settings)` across tasks.
