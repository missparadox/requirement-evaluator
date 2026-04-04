# Requirements Evaluator

## Overview

Requirements Evaluator is a hybrid project with two closely related modes:

- service mode:
  a frontend-backend application for uploading requirement files, creating evaluation jobs, and reading generated reports
- standalone skill mode:
  a model-driven workflow that reads requirement packets, applies the rubric in `.agents/skills/requirements-evaluator`, and produces a Chinese Markdown evaluation report

The repository keeps the scoring rubric in the skill, uses the existing packet builder script to normalize evidence, and stores phase 1 service artifacts on the local filesystem.

## Service Mode

Service mode is split into:

- `backend/`
  FastAPI service, local artifact storage, packet generation, model client integration, and job lifecycle
- `frontend/`
  React + TypeScript + Vite application for the upload flow and evaluation detail flow

Current phase 1 status:

- backend scaffold is in place
- create-or-reuse evaluation flow is implemented
- background runner flow is implemented
- evaluation API endpoints are implemented
- frontend upload page and detail page shells are implemented

## Frontend Setup

Requirements:

- Node.js 22 or newer
- `corepack` available so `pnpm` can be used without a global install

Install dependencies:

```bash
cd frontend
corepack pnpm install
```

Run the frontend tests:

```bash
cd frontend
corepack pnpm exec vitest run
```

Start the frontend dev server:

```bash
cd frontend
corepack pnpm dev
```

## Backend Setup

Requirements:

- Python 3.11+
- a virtual environment

Install backend dependencies into the worktree-local environment:

```bash
cd backend
../.venv/bin/pip install -e .
```

Run backend tests:

```bash
cd backend
../.venv/bin/python -m pytest -q
```

Start the backend dev server:

```bash
cd backend
../.venv/bin/python -m uvicorn app.main:app --reload
```

## Environment Configuration

Backend configuration currently uses these environment variables:

- `REQUIREMENTS_EVALUATOR_DATA_DIR`
  local directory for runtime artifacts; defaults to `<repo>/data`
- `REQUIREMENTS_EVALUATOR_MODEL`
  model name used by the configurable model client; defaults to `gpt-5.4`
- `OPENAI_API_KEY`
  when present, the backend can build the OpenAI-backed model client instead of the static fallback client

## Running the Service

Start the backend in one terminal:

```bash
cd backend
../.venv/bin/python -m uvicorn app.main:app --reload
```

Start the frontend in another terminal:

```bash
cd frontend
corepack pnpm dev
```

Current HTTP endpoints:

- `POST /api/evaluations`
- `GET /api/evaluations/{evaluation_id}`

## Local Artifact Storage Behavior

Phase 1 stores artifacts on disk under the configured data directory.

Each evaluation directory contains:

- the original uploaded file
- `metadata.json`
- a generated review packet after runner execution
- a generated Markdown report after successful execution

Dedupe behavior is based on:

- uploaded file content fingerprint
- skill version
- report template version
- model name
- app version

Matching `pending`, `running`, and `succeeded` tasks are reusable. Matching `failed` tasks are not reused.

## Standalone Skill Mode

You can use the repository without the service by invoking the requirement evaluator skill directly.

The packet builder script is:

```bash
python3 .agents/skills/requirements-evaluator/scripts/evaluate_requirements.py \
  --input /path/to/input-file.csv \
  --output /path/to/review-packet.md
```

The model should then read:

- `.agents/skills/requirements-evaluator/SKILL.md`
- `.agents/skills/requirements-evaluator/references/report-template.md`
- the generated review packet

Expected output:

- a Chinese Markdown evaluation report

## Integrating the Skill

The repository keeps the evaluator rubric and template in the skill directory so coding agents can invoke the same review standard both inside and outside service mode.

### OpenCode

Use the requirement evaluator skill path directly and point the model at:

- `.agents/skills/requirements-evaluator/SKILL.md`
- `.agents/skills/requirements-evaluator/references/report-template.md`
- a generated packet file

### Codex

Use the same skill assets from the repo workspace. The recommended pattern is:

- build a packet with the script
- instruct Codex to use the rubric in `SKILL.md`
- instruct Codex to structure the output with `references/report-template.md`

### Claude Code

Invoke the repository skill from the local `.agents/skills/requirements-evaluator` directory and pass the generated packet as the review input. The final model output should remain a Chinese Markdown report rather than raw scoring data.
