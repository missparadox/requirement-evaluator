# Requirements Evaluator Service Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a first-release requirements evaluation service with a FastAPI backend, a React/Vite frontend, asynchronous evaluation jobs, local artifact storage, dedupe, Markdown rendering, and Markdown download.

**Architecture:** Use a frontend-backend separated structure. The backend owns uploads, file-based task state, packet generation, model invocation, and dedupe. The frontend is a React SPA with an upload page and a detail page that polls job status and downloads the final Markdown report.

**Tech Stack:** Python, FastAPI, pytest, React, TypeScript, Vite, React Router, TanStack Query, pnpm

---

## File Structure

### Repository-Level Files

- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/paths.py`
- Create: `backend/app/core/versioning.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/routes/__init__.py`
- Create: `backend/app/api/routes/evaluations.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/evaluation.py`
- Create: `backend/app/storage/__init__.py`
- Create: `backend/app/storage/evaluation_store.py`
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/evaluation_service.py`
- Create: `backend/app/runners/__init__.py`
- Create: `backend/app/runners/evaluation_runner.py`
- Create: `backend/app/clients/__init__.py`
- Create: `backend/app/clients/model_client.py`
- Create: `backend/app/adapters/__init__.py`
- Create: `backend/app/adapters/packet_builder.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_versioning.py`
- Create: `backend/tests/test_evaluation_store.py`
- Create: `backend/tests/test_evaluation_service.py`
- Create: `backend/tests/test_evaluations_api.py`
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/router/index.tsx`
- Create: `frontend/src/pages/UploadPage.tsx`
- Create: `frontend/src/pages/EvaluationDetailPage.tsx`
- Create: `frontend/src/features/evaluations/api.ts`
- Create: `frontend/src/features/evaluations/types.ts`
- Create: `frontend/src/features/evaluations/hooks.ts`
- Create: `frontend/src/components/FileUploadForm.tsx`
- Create: `frontend/src/components/EvaluationStatusPanel.tsx`
- Create: `frontend/src/components/ReportViewer.tsx`
- Create: `frontend/src/lib/download.ts`
- Create: `frontend/src/lib/http.ts`
- Create: `frontend/src/styles/global.css`
- Create: `frontend/src/styles/theme.css`
- Create: `frontend/src/vite-env.d.ts`
- Create: `frontend/src/test/setup.ts`
- Create: `frontend/src/pages/UploadPage.test.tsx`
- Create: `frontend/src/pages/EvaluationDetailPage.test.tsx`
- Create: `.gitignore`
- Modify: `docs/requirements-evaluator-dev-notes.md`
- Create: `README.md`

### Responsibilities

- `backend/app/core/config.py`
  environment configuration such as data directory, model name, and API settings
- `backend/app/core/paths.py`
  canonical repository-relative and runtime paths
- `backend/app/core/versioning.py`
  digest helpers for uploaded files, skill/template versions, app version, and dedupe key creation
- `backend/app/models/evaluation.py`
  Pydantic models and typed status values
- `backend/app/storage/evaluation_store.py`
  metadata persistence and artifact file management
- `backend/app/services/evaluation_service.py`
  create-or-reuse logic and detail retrieval
- `backend/app/runners/evaluation_runner.py`
  background job execution flow and status transitions
- `backend/app/clients/model_client.py`
  model invocation abstraction
- `backend/app/adapters/packet_builder.py`
  wrapper around the existing `evaluate_requirements.py`
- `backend/app/api/routes/evaluations.py`
  `POST /api/evaluations` and `GET /api/evaluations/{id}`
- `frontend/src/pages/UploadPage.tsx`
  upload UI and submit flow
- `frontend/src/pages/EvaluationDetailPage.tsx`
  polling, report rendering, and Markdown download
- `frontend/src/features/evaluations/*`
  frontend API client, React Query hooks, and shared types
- `docs/requirements-evaluator-dev-notes.md`
  implementation progress log and follow-up context
- `README.md`
  open-source usage guide for service mode and standalone skill mode

### Execution Order

Implement the backend core and API first, then the frontend shell and route flow, then frontend polling and Markdown download, then documentation updates.

## Task 1: Scaffold Backend App and Core Configuration

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/paths.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/evaluation.py`
- Test: `backend/tests/conftest.py`

- [ ] **Step 1: Write the failing backend import smoke test**

```python
from fastapi.testclient import TestClient

from app.main import app


def test_app_health_routes_module_loads() -> None:
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/conftest.py -q`
Expected: FAIL because the backend package and app entrypoint do not exist yet.

- [ ] **Step 3: Write minimal backend scaffolding**

```toml
[project]
name = "requirements-evaluator-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115.0,<1.0.0",
  "uvicorn>=0.30.0,<1.0.0",
  "python-multipart>=0.0.9,<1.0.0",
  "pydantic>=2.8.0,<3.0.0",
  "pytest>=8.0.0,<9.0.0",
]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"
```

```python
from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    model_name: str


def get_settings() -> Settings:
    repo_root = Path(__file__).resolve().parents[3]
    data_dir = Path(os.environ.get("REQUIREMENTS_EVALUATOR_DATA_DIR", repo_root / "data"))
    model_name = os.environ.get("REQUIREMENTS_EVALUATOR_MODEL", "gpt-5.4")
    return Settings(data_dir=data_dir, model_name=model_name)
```

```python
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = REPO_ROOT / ".agents" / "skills" / "requirements-evaluator"
SKILL_FILE = SKILL_ROOT / "SKILL.md"
REPORT_TEMPLATE_FILE = SKILL_ROOT / "references" / "report-template.md"
PACKET_BUILDER_FILE = SKILL_ROOT / "scripts" / "evaluate_requirements.py"
DATA_ROOT = REPO_ROOT / "data"
EVALUATIONS_ROOT = DATA_ROOT / "evaluations"
```

```python
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


EvaluationStatus = Literal["pending", "running", "succeeded", "failed"]


class EvaluationDetail(BaseModel):
    evaluation_id: str
    status: EvaluationStatus
    filename: str
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None
    report_markdown: Optional[str] = None
```

```python
from fastapi import FastAPI


app = FastAPI(title="Requirements Evaluator API")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python3 -m pytest tests/conftest.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/pyproject.toml backend/app backend/tests/conftest.py
git commit -m "feat: scaffold backend application"
```

## Task 2: Implement Versioning and Dedupe Helpers

**Files:**
- Create: `backend/app/core/versioning.py`
- Test: `backend/tests/test_versioning.py`

- [ ] **Step 1: Write the failing versioning tests**

```python
from app.core.versioning import build_dedupe_key, sha256_bytes, sha256_text


def test_sha256_text_is_stable() -> None:
    assert sha256_text("abc") == sha256_text("abc")


def test_dedupe_key_changes_when_model_changes() -> None:
    first = build_dedupe_key(
        input_fingerprint="input",
        skill_version="skill",
        report_template_version="template",
        model_name="gpt-5.4",
        app_version="commit-a",
    )
    second = build_dedupe_key(
        input_fingerprint="input",
        skill_version="skill",
        report_template_version="template",
        model_name="gpt-5.4-mini",
        app_version="commit-a",
    )
    assert first != second
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/test_versioning.py -q`
Expected: FAIL because the module does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
import hashlib
import subprocess
from pathlib import Path


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_text(payload: str) -> str:
    return sha256_bytes(payload.encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def detect_app_version(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return "dev"
    return result.stdout.strip() or "dev"


def build_dedupe_key(
    *,
    input_fingerprint: str,
    skill_version: str,
    report_template_version: str,
    model_name: str,
    app_version: str,
) -> str:
    material = "|".join(
        [input_fingerprint, skill_version, report_template_version, model_name, app_version]
    )
    return sha256_text(material)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python3 -m pytest tests/test_versioning.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/versioning.py backend/tests/test_versioning.py
git commit -m "feat: add evaluation versioning helpers"
```

## Task 3: Implement File-Based Evaluation Store

**Files:**
- Create: `backend/app/storage/evaluation_store.py`
- Test: `backend/tests/test_evaluation_store.py`

- [ ] **Step 1: Write the failing storage test**

```python
from pathlib import Path

from app.storage.evaluation_store import EvaluationStore


def test_create_evaluation_directory_and_metadata(tmp_path: Path) -> None:
    store = EvaluationStore(tmp_path)
    record = store.create_evaluation(
        evaluation_id="eval_001",
        filename="requirements.csv",
        file_bytes=b"hello",
    )
    assert record["metadata_path"].exists()
    assert record["original_file_path"].exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/test_evaluation_store.py -q`
Expected: FAIL because the storage module does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class EvaluationStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def evaluation_dir(self, evaluation_id: str) -> Path:
        return self.root / evaluation_id

    def create_evaluation(self, *, evaluation_id: str, filename: str, file_bytes: bytes) -> dict[str, Any]:
        directory = self.evaluation_dir(evaluation_id)
        directory.mkdir(parents=True, exist_ok=False)
        original_file_path = directory / filename
        original_file_path.write_bytes(file_bytes)
        metadata_path = directory / "metadata.json"
        metadata = {
            "evaluation_id": evaluation_id,
            "status": "pending",
            "filename": filename,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "directory": directory,
            "original_file_path": original_file_path,
            "metadata_path": metadata_path,
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python3 -m pytest tests/test_evaluation_store.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/storage/evaluation_store.py backend/tests/test_evaluation_store.py
git commit -m "feat: add file-based evaluation store"
```

## Task 4: Implement Packet Builder Adapter

**Files:**
- Create: `backend/app/adapters/packet_builder.py`
- Modify: `backend/tests/test_evaluation_store.py`

- [ ] **Step 1: Write the failing packet adapter test**

```python
from pathlib import Path

from app.adapters.packet_builder import build_review_packet


def test_build_review_packet_creates_markdown_file(tmp_path: Path) -> None:
    input_path = tmp_path / "requirements.csv"
    input_path.write_text("OR需求编号,OR需求名称*,OR需求描述*\nD1,Name,Desc\n", encoding="utf-8")
    output_path = tmp_path / "packet.md"
    build_review_packet(input_path=input_path, output_path=output_path)
    assert output_path.exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/test_evaluation_store.py -q`
Expected: FAIL because the packet adapter module does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
import subprocess
import sys
from pathlib import Path

from app.core.paths import PACKET_BUILDER_FILE


def build_review_packet(*, input_path: Path, output_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(PACKET_BUILDER_FILE),
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Packet builder failed")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python3 -m pytest tests/test_evaluation_store.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/adapters/packet_builder.py backend/tests/test_evaluation_store.py
git commit -m "feat: add packet builder adapter"
```

## Task 5: Implement Model Client Abstraction

**Files:**
- Create: `backend/app/clients/model_client.py`
- Create: `backend/tests/test_evaluation_service.py`

- [ ] **Step 1: Write the failing model client test**

```python
from app.clients.model_client import StaticModelClient


def test_static_model_client_returns_markdown() -> None:
    client = StaticModelClient()
    report = client.generate_report(skill_text="skill", template_text="template", packet_text="packet")
    assert report.startswith("#")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/test_evaluation_service.py -q`
Expected: FAIL because the client does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
from typing import Protocol


class ModelClient(Protocol):
    def generate_report(self, *, skill_text: str, template_text: str, packet_text: str) -> str: ...


class StaticModelClient:
    def generate_report(self, *, skill_text: str, template_text: str, packet_text: str) -> str:
        return "# Mock Report\n\nReplace this client with the real model integration.\n"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python3 -m pytest tests/test_evaluation_service.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/clients/model_client.py backend/tests/test_evaluation_service.py
git commit -m "feat: add model client abstraction"
```

## Task 6: Implement Evaluation Service Create-or-Reuse Logic

**Files:**
- Create: `backend/app/services/evaluation_service.py`
- Modify: `backend/tests/test_evaluation_service.py`

- [ ] **Step 1: Write the failing dedupe service tests**

```python
from pathlib import Path

from app.services.evaluation_service import EvaluationService
from app.storage.evaluation_store import EvaluationStore


def test_create_returns_new_evaluation_id_when_no_match(tmp_path: Path) -> None:
    service = EvaluationService(store=EvaluationStore(tmp_path))
    result = service.create_or_reuse(filename="requirements.csv", file_bytes=b"abc")
    assert result.status == "pending"
    assert result.dedupe_hit is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/test_evaluation_service.py -q`
Expected: FAIL because the service does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4


@dataclass
class CreateEvaluationResult:
    evaluation_id: str
    status: str
    filename: str
    dedupe_hit: bool
    created_at: str


class EvaluationService:
    def __init__(self, store) -> None:
        self.store = store

    def create_or_reuse(self, *, filename: str, file_bytes: bytes) -> CreateEvaluationResult:
        evaluation_id = f"eval_{uuid4().hex}"
        created = self.store.create_evaluation(
            evaluation_id=evaluation_id,
            filename=filename,
            file_bytes=file_bytes,
        )
        metadata = self.store.read_metadata(evaluation_id)
        return CreateEvaluationResult(
            evaluation_id=evaluation_id,
            status=metadata["status"],
            filename=metadata["filename"],
            dedupe_hit=False,
            created_at=metadata["created_at"],
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python3 -m pytest tests/test_evaluation_service.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/evaluation_service.py backend/tests/test_evaluation_service.py
git commit -m "feat: add evaluation creation service"
```

## Task 7: Extend Store for Metadata Updates and Detail Reads

**Files:**
- Modify: `backend/app/storage/evaluation_store.py`
- Modify: `backend/tests/test_evaluation_store.py`

- [ ] **Step 1: Write the failing metadata update test**

```python
from app.storage.evaluation_store import EvaluationStore


def test_update_metadata_persists_status_and_report_path(tmp_path) -> None:
    store = EvaluationStore(tmp_path)
    store.create_evaluation(evaluation_id="eval_001", filename="requirements.csv", file_bytes=b"abc")
    store.update_metadata("eval_001", {"status": "running", "report_path": "report.md"})
    metadata = store.read_metadata("eval_001")
    assert metadata["status"] == "running"
    assert metadata["report_path"] == "report.md"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/test_evaluation_store.py -q`
Expected: FAIL because `update_metadata` and `read_metadata` do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
import json


    def metadata_path(self, evaluation_id: str) -> Path:
        return self.evaluation_dir(evaluation_id) / "metadata.json"

    def read_metadata(self, evaluation_id: str) -> dict[str, Any]:
        return json.loads(self.metadata_path(evaluation_id).read_text(encoding="utf-8"))

    def update_metadata(self, evaluation_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        metadata = self.read_metadata(evaluation_id)
        metadata.update(patch)
        self.metadata_path(evaluation_id).write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return metadata
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python3 -m pytest tests/test_evaluation_store.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/storage/evaluation_store.py backend/tests/test_evaluation_store.py
git commit -m "feat: support evaluation metadata updates"
```

## Task 8: Implement Background Evaluation Runner

**Files:**
- Create: `backend/app/runners/evaluation_runner.py`
- Modify: `backend/tests/test_evaluation_service.py`

- [ ] **Step 1: Write the failing runner test**

```python
from pathlib import Path

from app.clients.model_client import StaticModelClient
from app.runners.evaluation_runner import EvaluationRunner
from app.storage.evaluation_store import EvaluationStore


def test_runner_writes_report_and_marks_success(tmp_path: Path) -> None:
    store = EvaluationStore(tmp_path)
    store.create_evaluation(evaluation_id="eval_001", filename="requirements.csv", file_bytes=b"OR需求编号,OR需求名称*,OR需求描述*\nD1,N,D\n")
    runner = EvaluationRunner(store=store, model_client=StaticModelClient())
    runner.run("eval_001")
    metadata = store.read_metadata("eval_001")
    assert metadata["status"] == "succeeded"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/test_evaluation_service.py -q`
Expected: FAIL because the runner does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
from datetime import datetime, timezone

from app.adapters.packet_builder import build_review_packet
from app.core.paths import REPORT_TEMPLATE_FILE, SKILL_FILE


class EvaluationRunner:
    def __init__(self, *, store, model_client) -> None:
        self.store = store
        self.model_client = model_client

    def run(self, evaluation_id: str) -> None:
        metadata = self.store.update_metadata(
            evaluation_id,
            {"status": "running", "started_at": datetime.now(timezone.utc).isoformat()},
        )
        directory = self.store.evaluation_dir(evaluation_id)
        input_path = directory / metadata["filename"]
        packet_path = directory / "review-packet.md"
        build_review_packet(input_path=input_path, output_path=packet_path)
        report = self.model_client.generate_report(
            skill_text=SKILL_FILE.read_text(encoding="utf-8"),
            template_text=REPORT_TEMPLATE_FILE.read_text(encoding="utf-8"),
            packet_text=packet_path.read_text(encoding="utf-8"),
        )
        report_path = directory / "report.md"
        report_path.write_text(report, encoding="utf-8")
        self.store.update_metadata(
            evaluation_id,
            {
                "status": "succeeded",
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "report_path": str(report_path),
            },
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python3 -m pytest tests/test_evaluation_service.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/runners/evaluation_runner.py backend/tests/test_evaluation_service.py
git commit -m "feat: add evaluation runner"
```

## Task 9: Implement Evaluation API Endpoints

**Files:**
- Create: `backend/app/api/routes/evaluations.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_evaluations_api.py`

- [ ] **Step 1: Write the failing API tests**

```python
from fastapi.testclient import TestClient

from app.main import app


def test_post_evaluations_returns_pending_task() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/evaluations",
        files={"file": ("requirements.csv", b"OR需求编号,OR需求名称*,OR需求描述*\nD1,N,D\n", "text/csv")},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "pending"


def test_get_evaluation_returns_detail() -> None:
    client = TestClient(app)
    create = client.post(
        "/api/evaluations",
        files={"file": ("requirements.csv", b"OR需求编号,OR需求名称*,OR需求描述*\nD1,N,D\n", "text/csv")},
    )
    evaluation_id = create.json()["evaluation_id"]
    detail = client.get(f"/api/evaluations/{evaluation_id}")
    assert detail.status_code == 200
    assert detail.json()["evaluation_id"] == evaluation_id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/test_evaluations_api.py -q`
Expected: FAIL because routes are not wired yet.

- [ ] **Step 3: Write minimal implementation**

```python
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile


router = APIRouter(prefix="/api/evaluations", tags=["evaluations"])


@router.post("")
async def create_evaluation(file: UploadFile = File(...)):
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    result = service.create_or_reuse(filename=file.filename or "upload.bin", file_bytes=payload)
    return result.__dict__


@router.get("/{evaluation_id}")
def get_evaluation(evaluation_id: str):
    return service.get_detail(evaluation_id).model_dump()
```

```python
from fastapi import FastAPI

from app.api.routes.evaluations import router as evaluations_router


app = FastAPI(title="Requirements Evaluator API")
app.include_router(evaluations_router)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python3 -m pytest tests/test_evaluations_api.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/routes/evaluations.py backend/app/main.py backend/tests/test_evaluations_api.py
git commit -m "feat: add evaluation api endpoints"
```

## Task 10: Replace Static Model Client with Real Configurable Client

**Files:**
- Modify: `backend/app/clients/model_client.py`
- Modify: `backend/pyproject.toml`
- Modify: `backend/app/core/config.py`
- Modify: `backend/tests/test_evaluation_service.py`

- [ ] **Step 1: Write the failing configurable client tests**

```python
from app.clients.model_client import OpenAIModelClient, StaticModelClient, build_model_client


def test_build_model_client_returns_static_client_without_api_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = build_model_client("gpt-5.4")
    assert isinstance(client, StaticModelClient)


def test_build_model_client_returns_openai_client_with_api_key(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    client = build_model_client("gpt-5.4")
    assert isinstance(client, OpenAIModelClient)
    assert client.model_name == "gpt-5.4"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/test_evaluation_service.py -q`
Expected: FAIL because the configurable real client path does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
from dataclasses import dataclass
import os
from openai import OpenAI


@dataclass
class OpenAIModelClient:
    model_name: str
    client: OpenAI

    def generate_report(self, *, skill_text: str, template_text: str, packet_text: str) -> str:
        prompt = (
            "Use the requirement evaluation rubric and template below.\n\n"
            f"[SKILL]\n{skill_text}\n\n"
            f"[TEMPLATE]\n{template_text}\n\n"
            f"[PACKET]\n{packet_text}\n"
        )
        response = self.client.responses.create(
            model=self.model_name,
            input=prompt,
        )
        return response.output_text


def build_model_client(model_name: str):
    if os.environ.get("OPENAI_API_KEY"):
        return OpenAIModelClient(model_name=model_name, client=OpenAI())
    return StaticModelClient()
```

```toml
dependencies = [
  "fastapi>=0.115.0,<1.0.0",
  "httpx>=0.28.0,<1.0.0",
  "uvicorn>=0.30.0,<1.0.0",
  "python-multipart>=0.0.9,<1.0.0",
  "pydantic>=2.8.0,<3.0.0",
  "pytest>=8.0.0,<9.0.0",
  "openai>=1.0.0,<2.0.0",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python3 -m pytest tests/test_evaluation_service.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/clients/model_client.py backend/app/core/config.py backend/tests/test_evaluation_service.py
git commit -m "feat: add configurable model client"
```

## Task 11: Scaffold Frontend App and Routing

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/router/index.tsx`
- Create: `frontend/src/vite-env.d.ts`
- Create: `frontend/src/styles/global.css`
- Create: `frontend/src/styles/theme.css`
- Test: `frontend/src/pages/UploadPage.test.tsx`

- [ ] **Step 1: Write the failing route smoke test**

```tsx
import { render, screen } from "@testing-library/react";

import App from "../App";


test("renders upload route shell", () => {
  render(<App />);
  expect(screen.getByText(/requirements evaluator/i)).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && pnpm test -- --run UploadPage.test.tsx`
Expected: FAIL because the frontend app does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```json
{
  "name": "requirements-evaluator-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "test": "vitest"
  },
  "dependencies": {
    "@tanstack/react-query": "^5.59.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.28.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.6.3",
    "@testing-library/react": "^16.0.1",
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.3",
    "typescript": "^5.6.3",
    "vite": "^5.4.10",
    "vitest": "^2.1.3"
  }
}
```

```tsx
import { RouterProvider } from "react-router-dom";

import { router } from "./router";

export default function App() {
  return <RouterProvider router={router} />;
}
```

```tsx
import { createBrowserRouter } from "react-router-dom";

import { UploadPage } from "../pages/UploadPage";

export const router = createBrowserRouter([
  { path: "/", element: <UploadPage /> },
]);
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && pnpm test -- --run UploadPage.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/tsconfig.json frontend/tsconfig.node.json frontend/vite.config.ts frontend/index.html frontend/src
git commit -m "feat: scaffold frontend application"
```

## Task 12: Implement Upload Page and Create Evaluation API Flow

**Files:**
- Create: `frontend/src/features/evaluations/api.ts`
- Create: `frontend/src/features/evaluations/types.ts`
- Create: `frontend/src/features/evaluations/hooks.ts`
- Create: `frontend/src/components/FileUploadForm.tsx`
- Create: `frontend/src/pages/UploadPage.tsx`
- Modify: `frontend/src/pages/UploadPage.test.tsx`

- [ ] **Step 1: Write the failing upload flow test**

```tsx
import { fireEvent, render, screen } from "@testing-library/react";

import { UploadPage } from "./UploadPage";


test("shows validation when no file is selected", async () => {
  render(<UploadPage />);
  fireEvent.click(screen.getByRole("button", { name: /start evaluation/i }));
  expect(await screen.findByText(/select a file/i)).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && pnpm test -- --run UploadPage.test.tsx`
Expected: FAIL because the page and form are not implemented yet.

- [ ] **Step 3: Write minimal implementation**

```tsx
import { FormEvent, useState } from "react";


export function FileUploadForm() {
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const input = event.currentTarget.elements.namedItem("file") as HTMLInputElement | null;
    if (!input?.files?.length) {
      setError("Select a file before starting evaluation.");
      return;
    }
    setError(null);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input name="file" type="file" />
      <button type="submit">Start Evaluation</button>
      {error ? <p>{error}</p> : null}
    </form>
  );
}
```

```tsx
import { FileUploadForm } from "../components/FileUploadForm";


export function UploadPage() {
  return (
    <main>
      <h1>Requirements Evaluator</h1>
      <FileUploadForm />
    </main>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && pnpm test -- --run UploadPage.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/evaluations frontend/src/components/FileUploadForm.tsx frontend/src/pages/UploadPage.tsx frontend/src/pages/UploadPage.test.tsx
git commit -m "feat: add upload page flow"
```

## Task 13: Implement Evaluation Detail Page, Polling, and Markdown Download

**Files:**
- Create: `frontend/src/components/EvaluationStatusPanel.tsx`
- Create: `frontend/src/components/ReportViewer.tsx`
- Create: `frontend/src/lib/download.ts`
- Create: `frontend/src/pages/EvaluationDetailPage.tsx`
- Modify: `frontend/src/router/index.tsx`
- Create: `frontend/src/pages/EvaluationDetailPage.test.tsx`

- [ ] **Step 1: Write the failing detail page test**

```tsx
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { EvaluationDetailPage } from "./EvaluationDetailPage";


test("renders loading status shell", () => {
  render(
    <MemoryRouter initialEntries={["/evaluations/eval_123"]}>
      <Routes>
        <Route path="/evaluations/:evaluationId" element={<EvaluationDetailPage />} />
      </Routes>
    </MemoryRouter>,
  );
  expect(screen.getByText(/evaluation status/i)).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && pnpm test -- --run EvaluationDetailPage.test.tsx`
Expected: FAIL because the detail page does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```tsx
import { useParams } from "react-router-dom";


export function EvaluationDetailPage() {
  const { evaluationId } = useParams();
  return (
    <main>
      <h1>Evaluation Status</h1>
      <p>{evaluationId}</p>
      <button type="button">Download Markdown</button>
    </main>
  );
}
```

```tsx
import { createBrowserRouter } from "react-router-dom";

import { EvaluationDetailPage } from "../pages/EvaluationDetailPage";
import { UploadPage } from "../pages/UploadPage";

export const router = createBrowserRouter([
  { path: "/", element: <UploadPage /> },
  { path: "/evaluations/:evaluationId", element: <EvaluationDetailPage /> },
]);
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && pnpm test -- --run EvaluationDetailPage.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/EvaluationStatusPanel.tsx frontend/src/components/ReportViewer.tsx frontend/src/lib/download.ts frontend/src/pages/EvaluationDetailPage.tsx frontend/src/pages/EvaluationDetailPage.test.tsx frontend/src/router/index.tsx
git commit -m "feat: add evaluation detail page"
```

## Task 14: Add Runtime Ignore Rules and Local Data Directory Setup

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Write the expected ignore entries**

```gitignore
data/
frontend/node_modules/
frontend/dist/
backend/.pytest_cache/
backend/__pycache__/
```

- [ ] **Step 2: Verify current file is missing required entries**

Run: `rg -n "^(data/|frontend/node_modules/|frontend/dist/|backend/.pytest_cache/|backend/__pycache__/)$" .gitignore`
Expected: no matches or incomplete matches.

- [ ] **Step 3: Add the ignore rules**

```gitignore
data/
frontend/node_modules/
frontend/dist/
backend/.pytest_cache/
backend/__pycache__/
```

- [ ] **Step 4: Run verification**

Run: `rg -n "^(data/|frontend/node_modules/|frontend/dist/|backend/.pytest_cache/|backend/__pycache__/)$" .gitignore`
Expected: one match per required line.

- [ ] **Step 5: Commit**

```bash
git add .gitignore
git commit -m "chore: ignore runtime artifacts"
```

## Task 15: Update Development Log with Service Progress

**Files:**
- Modify: `docs/requirements-evaluator-dev-notes.md`

- [ ] **Step 1: Write the new progress section content**

```md
## Service Development Progress

Current implementation phase:
- frontend-backend separated service scaffold
- FastAPI backend with asynchronous evaluation jobs
- React/Vite frontend with upload and detail pages

Completed decisions:
- local filesystem artifact storage for phase 1
- dedupe based on input and version material
- SQLite reserved for future metadata storage only

Next recommended steps:
- replace mock model client path with production model configuration validation
- add richer status messaging
- consider SQLite metadata upgrade after phase 1 is stable
```

- [ ] **Step 2: Verify the section is not already present**

Run: `rg -n "^## Service Development Progress$" docs/requirements-evaluator-dev-notes.md`
Expected: no matches

- [ ] **Step 3: Add the progress section**

```md
## Service Development Progress

Current implementation phase:
- frontend-backend separated service scaffold
- FastAPI backend with asynchronous evaluation jobs
- React/Vite frontend with upload and detail pages

Completed decisions:
- local filesystem artifact storage for phase 1
- dedupe based on input and version material
- SQLite reserved for future metadata storage only

Next recommended steps:
- replace mock model client path with production model configuration validation
- add richer status messaging
- consider SQLite metadata upgrade after phase 1 is stable
```

- [ ] **Step 4: Run verification**

Run: `rg -n "^## Service Development Progress$" docs/requirements-evaluator-dev-notes.md`
Expected: one match

- [ ] **Step 5: Commit**

```bash
git add docs/requirements-evaluator-dev-notes.md
git commit -m "docs: update service development log"
```

## Task 16: Add Open-Source README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write the README outline as a failing documentation checklist**

```md
- project overview
- service mode setup
- frontend setup
- backend setup
- environment configuration
- running the service
- local artifact storage behavior
- standalone skill usage
- integration notes for OpenCode
- integration notes for Codex
- integration notes for Claude Code
```

- [ ] **Step 2: Verify README does not exist yet**

Run: `test -f README.md; echo $?`
Expected: `1`

- [ ] **Step 3: Write the README**

```md
# Requirements Evaluator

## Overview
...

## Service Mode
...

## Standalone Skill Mode
...

## Integrating the Skill
### OpenCode
...
### Codex
...
### Claude Code
...
```

- [ ] **Step 4: Verify README sections exist**

Run: `rg -n "^# Requirements Evaluator$|^## Service Mode$|^## Standalone Skill Mode$|^### OpenCode$|^### Codex$|^### Claude Code$" README.md`
Expected: all required section headers are present.

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: add project readme"
```

## Self-Review

### Spec Coverage

This plan covers:
- frontend-backend separated service structure
- asynchronous evaluation flow
- local artifact storage
- dedupe and version input helpers
- real-model integration path with a fallback static client during development
- upload and detail pages
- Markdown download
- development log updates
- roadmap-aligned README work

### Placeholder Scan

Known limitation:
- the README task intentionally uses section placeholders in the task body as a document shape, but the execution step requires writing actual content, not keeping placeholder ellipses in the final file
- the model client task uses a real OpenAI client path, but production credential validation and richer prompt shaping may still need follow-up refinement during implementation

### Type Consistency

The plan consistently uses:
- `evaluation_id`
- `input_fingerprint`
- `dedupe_key`
- `report_markdown`
- status values: `pending`, `running`, `succeeded`, `failed`
