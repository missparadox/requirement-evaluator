# Requirements Evaluator Service Design

## Overview

This document defines the first production-oriented service architecture for the requirements evaluator project.

The repository already contains the evaluation core:
- a requirement-review skill
- a report template
- a packet builder script

The goal of this phase is to wrap that evaluation core in a frontend-backend separated application with a minimal but complete user flow:
- upload a requirement file
- create an asynchronous evaluation job
- poll job status
- render the final Markdown report
- download the final Markdown report

This design intentionally keeps the first release small. It does not include history, delete operations, packet inspection, authentication, or database-backed metadata yet.

## Goals

The first release must:
- accept supported requirement files from a web UI
- generate review packets with the existing Python packet builder
- call a real model to generate the final Chinese Markdown report
- persist artifacts on local disk
- deduplicate repeated uploads safely
- expose a small HTTP API for asynchronous job creation and status polling
- provide a frontend with an upload flow and a detail page
- support Markdown report download from the detail page

## Non-Goals

The first release must not include:
- evaluation history page
- delete API
- packet download or packet inspection UI
- authentication or user accounts
- multi-tenant support
- object storage
- database-backed metadata storage
- advanced job queues or distributed workers

These can be added in later phases if needed.

## Existing Core Capabilities

The current repository already contains the review engine inputs and preprocessing logic:
- `.agents/skills/requirements-evaluator/SKILL.md`
- `.agents/skills/requirements-evaluator/references/report-template.md`
- `.agents/skills/requirements-evaluator/scripts/evaluate_requirements.py`

These existing boundaries remain unchanged:
- the Python script is a packet builder, not a scorer
- final scoring belongs to the model
- the review rubric lives in `SKILL.md`
- the report structure lives in `report-template.md`

The new service layer must reuse these assets rather than re-implement them elsewhere.

## Architecture

### High-Level Structure

The project will use frontend-backend separation:

- `frontend/`
  React + TypeScript + Vite application
- `backend/`
  FastAPI service
- `.agents/skills/requirements-evaluator/`
  evaluation skill, template, and packet builder
- `data/`
  local runtime artifact storage

The backend will expose HTTP APIs. The frontend will only communicate with the backend over HTTP.

### Selected Stack

#### Frontend

- React
- TypeScript
- Vite
- React Router
- TanStack Query
- pnpm

#### Backend

- Python
- FastAPI
- in-process background execution for asynchronous jobs
- local filesystem storage for runtime artifacts

This stack is chosen to maximize reuse of the existing Python packet builder and keep the first release maintainable.

## Core User Flow

### Upload Flow

1. User opens the upload page.
2. User selects a supported file.
3. Frontend submits the file to `POST /api/evaluations`.
4. Backend computes fingerprints and dedupe state.
5. Backend returns an `evaluation_id`.
6. Frontend navigates to the evaluation detail page.

### Evaluation Flow

1. Backend stores the original file in the task directory.
2. Backend creates a metadata record with `pending` status.
3. Backend starts a background job.
4. The job updates status to `running`.
5. The job generates a review packet.
6. The job reads:
   - `SKILL.md`
   - `report-template.md`
   - generated packet
7. The job calls the model and requests a Chinese Markdown report.
8. The job stores the final report.
9. The job updates status to `succeeded` or `failed`.

### Detail Flow

1. Frontend opens `/evaluations/:id`.
2. Frontend calls `GET /api/evaluations/:id`.
3. If status is `pending` or `running`, frontend polls.
4. If status is `failed`, frontend shows the error.
5. If status is `succeeded`, frontend renders the Markdown report.
6. User can download the report as a `.md` file from the browser.

## Backend Design

### Service Boundaries

The backend should be decomposed into a few focused units:

- API layer
  request validation and response shaping
- evaluation service
  task creation, dedupe decisions, and lifecycle coordination
- storage layer
  local metadata and artifact persistence
- runner layer
  background job execution
- model client layer
  LLM invocation wrapper
- packet builder adapter
  integration point for the existing Python packet builder

### Task Lifecycle

The first release will use this status model:
- `pending`
- `running`
- `succeeded`
- `failed`

Lifecycle rules:
- newly created tasks start at `pending`
- background execution moves them to `running`
- completed tasks end in `succeeded` or `failed`
- repeated upload of a failed input creates a new evaluation task

### File Storage Layout

Use one directory per `evaluation_id` under `data/evaluations/`.

Each task directory should store:
- original uploaded file
- generated review packet
- final report Markdown
- `metadata.json`

`metadata.json` should store:
- `evaluation_id`
- status
- original filename
- content type when available
- timestamps
- error details when failed
- `input_fingerprint`
- `skill_version`
- `report_template_version`
- `model_name`
- `app_version`
- `dedupe_key`
- local artifact paths

## API Design

The first release exposes only two endpoints.

### `POST /api/evaluations`

Purpose:
- upload a file
- create or reuse an evaluation task

Request:
- `multipart/form-data`
- file field

Behavior:
- validate file presence and supported type
- compute fingerprints
- reuse existing `pending` or `running` task on dedupe hit
- reuse existing `succeeded` task on dedupe hit
- create a new task if there is no reusable task
- create a new task if the matching previous task is `failed`

Response fields:
- `evaluation_id`
- `status`
- `filename`
- `created_at`
- `dedupe_hit`

### `GET /api/evaluations/:id`

Purpose:
- return task status and final report content

Response fields:
- `evaluation_id`
- `status`
- `filename`
- `created_at`
- `started_at`
- `finished_at`
- `error_message`
- `report_markdown`

This endpoint replaces the need for a separate `/report` endpoint in the first release.

## Dedupe Strategy

The system must distinguish between task identity and dedupe identity.

- `evaluation_id`
  unique per task instance
- `input_fingerprint`
  identifies the uploaded file content
- `dedupe_key`
  identifies whether a previous result can be safely reused

### Version Inputs

The first release should derive version inputs automatically:

- `input_fingerprint`
  `sha256(file_bytes)`
- `skill_version`
  `sha256(SKILL.md contents)`
- `report_template_version`
  `sha256(report-template.md contents)`
- `model_name`
  configured model identifier string
- `app_version`
  current git commit hash if available, otherwise `dev`

### Dedupe Key

Compute:

`dedupe_key = sha256(input_fingerprint + skill_version + report_template_version + model_name + app_version)`

### Dedupe Rules

- if a matching `dedupe_key` exists with `pending` or `running`, return the existing task
- if a matching `dedupe_key` exists with `succeeded`, return the existing task
- if a matching `dedupe_key` exists with `failed`, create a new task

Neither `dedupe_key` nor `input_fingerprint` need to be exposed to the frontend in the first release. They are internal metadata.

## Model Invocation Strategy

The service will not "load the skill" in the same way an interactive coding agent does.

Instead, the backend will treat the skill as input context for the model call.

Each evaluation job must:
- read `.agents/skills/requirements-evaluator/SKILL.md`
- read `.agents/skills/requirements-evaluator/references/report-template.md`
- read the generated review packet
- construct a prompt that instructs the model to use the rubric and template
- request a Chinese Markdown report

This preserves the same review logic while moving it into a service execution flow.

## Frontend Design

### Pages

The first release includes only two pages:

#### Upload Page

Responsibilities:
- choose a file
- validate basic file constraints
- submit the upload
- handle submission errors
- navigate to the evaluation detail page after task creation

#### Evaluation Detail Page

Responsibilities:
- show task metadata
- show `pending`, `running`, `failed`, or `succeeded`
- poll the backend while work is incomplete
- render final Markdown on success
- expose a Markdown download button

### Detail Page Download

The detail page should support a `Download Markdown` action.

Implementation approach:
- use `report_markdown` returned by `GET /api/evaluations/:id`
- create a browser `Blob`
- download as `<original-filename>-evaluation-report.md`

This avoids adding an extra backend download endpoint in the first release.

### Visual Direction

The UI should avoid dashboard-card overload.

Recommended visual direction:
- upload page: clear, minimal, trustworthy
- detail page: editorial or analysis-console feel with strong reading ergonomics

The UI should feel deliberate and polished while remaining readable and maintainable.

## Error Handling

The backend should classify errors into at least these groups:

- upload errors
  - missing file
  - unsupported file type
  - empty file
- preprocessing errors
  - packet builder failure
  - missing runtime dependency
  - parse failure
- model invocation errors
  - timeout
  - missing credentials or configuration
  - malformed output
- storage errors
  - artifact write failure
  - metadata persistence failure

Failure responses and metadata should include explicit error messages. The frontend should never show a blank failed state.

## Testing Strategy

### Backend

Cover:
- dedupe decisions
- file-based metadata storage
- evaluation task lifecycle transitions
- packet builder integration
- API responses for create and detail endpoints

### Frontend

Cover:
- upload submission flow
- detail polling behavior
- success and failure rendering
- Markdown download behavior

### End-to-End Validation

Use `requirements.csv` as the first end-to-end validation input for the full service workflow.

## Runtime Artifact Policy

`data/` is a runtime directory and must not be treated as source content.

It should be ignored in git and should be safe to inspect locally during development for debugging.

## Roadmap

### Phase 1

Implement the first release defined in this document:
- file upload
- asynchronous evaluation
- local artifact storage
- dedupe
- status polling
- Markdown rendering
- Markdown download

### Phase 2

Introduce SQLite for metadata only.

SQLite should store:
- evaluation identity
- status
- timestamps
- filename
- fingerprints and dedupe data
- model and version metadata
- local artifact path references
- error messages

Even after SQLite is introduced:
- original uploaded files remain in local storage
- generated packet files remain in local storage
- generated report files remain in local storage

This keeps metadata queryable without storing large artifacts in the database.

Possible later additions:
- evaluation history
- delete flow
- packet inspection
- more robust worker model

## Documentation Requirements

The implementation phase must also produce user-facing documentation.

### Development Log Updates

After each meaningful implementation phase, update:
- `docs/requirements-evaluator-dev-notes.md`

The updates should record:
- architecture decisions
- completed work
- current limitations
- known issues
- next recommended steps

The purpose is to preserve project context for future sessions.

### Open-Source README

After the service is implemented, add a README suitable for open-source users.

It must explain:
- project purpose and capabilities
- frontend and backend setup
- installation steps
- configuration and model setup
- local development workflow
- deployment basics
- runtime artifact storage behavior

It must also explain the standalone offline evaluation workflow:
- how to use the evaluation skill without the web service
- how to integrate the evaluation skill into OpenCode
- how to integrate the evaluation skill into Codex
- how to integrate the evaluation skill into Claude Code

This repository should remain useful both as:
- a service application
- a reusable offline requirement-evaluation skill package

## Acceptance Criteria

The first release is complete when:
- a user can upload `requirements.csv`
- the backend creates or reuses an evaluation task correctly
- asynchronous task execution works
- dedupe behavior matches the defined rules
- the detail page shows live task status
- the final Markdown report renders in the detail page
- the final Markdown report can be downloaded
- artifacts are stored on local disk in a clear structure
- the development log is updated
- the README documents both service mode and standalone skill mode
