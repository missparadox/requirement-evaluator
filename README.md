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
- frontend upload experience matches the approved premium landing design
- frontend detail page now renders live pending, running, failed, and succeeded states from the backend
- frontend detail view includes polling, task metadata, report download, and structured result sections

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
- `OPENAI_API_KEY`
  when present, the backend builds the OpenAI-backed model client and calls the OpenAI Responses API
- `OPENAI_MODEL`
  OpenAI model name; defaults to `gpt-5.4`
- `OPENAI_BASE_URL`
  OpenAI API base URL; defaults to `https://api.openai.com/v1`
- `ZHIPU_API_KEY`
  when present and OpenAI is unavailable, the backend builds the Zhipu-backed model client
- `ZHIPU_MODEL`
  Zhipu model name; defaults to `glm-5`
- `ZHIPU_BASE_URL`
  Zhipu API base URL; defaults to `https://open.bigmodel.cn/api/paas/v4`
- `CODEX_MODEL`
  Codex CLI model name; defaults to `gpt-5.4`
- `REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK`
  set to `1` to enable the local debug fallback mode

Current backend behavior:

- runtime priority is `OPENAI_API_KEY` first, then `ZHIPU_API_KEY`, then local `codex` on `PATH`, then `REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK=1`
- if none of those modes is available, backend startup fails fast instead of silently falling back to a placeholder runtime
- OpenAI uses `OPENAI_MODEL` and `OPENAI_BASE_URL`, which default to `gpt-5.4` and `https://api.openai.com/v1`
- Zhipu uses `ZHIPU_MODEL` and `ZHIPU_BASE_URL`, which default to `glm-5` and `https://open.bigmodel.cn/api/paas/v4`
- Codex CLI uses `CODEX_MODEL`, which defaults to `gpt-5.4`, and the exec call has timeout protection
- the debug fallback is only enabled when `REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK=1`

Example backend environment setup for real OpenAI-backed evaluations:

```bash
export OPENAI_API_KEY=your-api-key
export OPENAI_MODEL=gpt-5.4
export OPENAI_BASE_URL=https://api.openai.com/v1
```

## Running the Service

Start the backend in one terminal:

```bash
export OPENAI_API_KEY=your-api-key
export OPENAI_MODEL=gpt-5.4
export OPENAI_BASE_URL=https://api.openai.com/v1
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
- `POST /api/evaluations/{evaluation_id}/retry`

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
- model provider (`openai`, `zhipu`, `codex`, or `debug`)
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

### Full Automatic Evaluation

For large inputs or limited-context models, use the full sharded automation pipeline instead of loading one full packet into the model at once.

The full pipeline script is:

```bash
./.venv/bin/python .agents/skills/requirements-evaluator/scripts/run_evaluation.py \
  --input /path/to/input-file.xlsx \
  --report-output /path/to/report.md
```

What it does:

- reads the input file and expands merged Excel cells
- builds a packet manifest plus multiple shard packets
- sends each shard to the configured model provider
- writes one structured `partial-review-*.json` per shard
- aggregates shard outputs into one `aggregate.json`
- generates the final Chinese Markdown report automatically

Typical outputs inside the working directory:

- `packets/manifest.json`
- `packets/shard-001.json`, `packets/shard-002.json`, ...
- `partials/partial-review-shard-001.json`, ...
- `aggregate.json`
- final report file

Example using this repository's sample input:

```bash
./.venv/bin/python .agents/skills/requirements-evaluator/scripts/run_evaluation.py \
  --input requirements.xlsm \
  --report-output reports/requirements.md
```

For local dry-runs without calling a remote model, force the static provider:

```bash
./.venv/bin/python .agents/skills/requirements-evaluator/scripts/run_evaluation.py \
  --input requirements.xlsm \
  --report-output reports/requirements.md \
  --provider static
```

Useful options:

- `--work-dir`
  choose where manifest, shard packets, partial reviews, and aggregate output are written
- `--shard-size`
  maximum OR units per shard, default `8`
- `--max-chars-per-shard`
  approximate shard size cap, default `120000`
- `--provider`
  `auto` or `static`; `auto` uses the runtime selection rules below

### Provider Selection

The standalone automation script reuses the backend model client selection logic.

Current priority in `--provider auto` mode:

- `OPENAI_API_KEY` present -> OpenAI Responses API
- otherwise `ZHIPU_API_KEY` present -> Zhipu via OpenAI-compatible client
- otherwise `codex` available on `PATH` -> `codex exec`
- otherwise fall back only when `--provider static` is explicitly selected

Practical consequence:

- if `codex` is installed locally and no API key is configured, automatic runs will use `codex exec`
- if you want a deterministic local no-network run, pass `--provider static`
- if you want a real remote run, set `OPENAI_API_KEY` or `ZHIPU_API_KEY`

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
