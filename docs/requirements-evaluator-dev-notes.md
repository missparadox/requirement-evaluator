# Requirements Evaluator Notes

## Goal

Build a requirement evaluation capability where:

- the skill defines the review standard
- a preprocessing script normalizes uploaded files into a review packet
- the model produces the final Chinese evaluation report

## Final Architecture

The current intended structure is:

- `.agents/skills/requirements-evaluator/SKILL.md`
- `.agents/skills/requirements-evaluator/references/report-template.md`
- `.agents/skills/requirements-evaluator/references/dependencies.md`
- `.agents/skills/requirements-evaluator/scripts/evaluate_requirements.py`

Responsibilities:

- `SKILL.md`
  Contains the review rubric, scoring rules, review workflow, and recommended invocation pattern.
- `report-template.md`
  Defines the target Chinese report structure.
- `dependencies.md`
  Documents script runtime dependencies and installation commands.
- `evaluate_requirements.py`
  Parses input files and builds a review packet for the model.

## Review Principles

The evaluator should treat requirement documents as evidence, not intent.

Core review principles:

- score from explicit document evidence
- use a weighted 100-point rubric
- prefer implementation readiness and test readiness while still checking OR quality
- mark genuinely non-applicable dimensions as `N/A`
- separate evidence, judgment, and recommendation
- avoid vague conclusions without field-level support

## Default Rubric

The default rubric is embedded in `SKILL.md`.

Main dimensions:

- OR user language
- OR scenario
- OR user value
- OR constraints
- DR security
- DR technical detail
- DR testability
- DR ambiguity
- DR performance
- DR hardware
- cross-layer scope and boundaries
- cross-layer assumptions and dependencies
- cross-layer traceability and consistency
- cross-layer exceptions and edge cases

The rubric is self-contained and should be treated as the source of truth.

## Packet Builder Design

The preprocessing script is intentionally not a scorer.

Its job is to normalize input and preserve evidence for the model.

Current packet structure includes:

- `raw_fields`
  Original field evidence
- `core_fields`
  Useful high-signal extracted fields such as IDs, names, descriptions, parameters, test points, and security notes
- `dimension_view`
  A field-to-dimension mapping that shows:
  - which source fields are relevant to each evaluation dimension
  - which of those fields contain evidence
  - which important fields are missing

Important rule:

- field importance is determined by evaluation value, not by whether a sample file frequently leaves that field empty

## Supported Input Types

The packet builder supports:

- `.csv`
- `.xlsx`
- `.xlsm`
- `.json`

## Dependencies

Current runtime dependency rule:

- `.csv` and `.json`: no extra Python package required
- `.xlsx` and `.xlsm`: require `openpyxl`

Current install command:

```bash
python3 -m pip install openpyxl
```

The script should detect missing runtime dependencies before reading the file and return a clear install command.

## Current Usage Flow

### CLI flow

1. User provides a requirement file.
2. Build a review packet:

```bash
python3 .agents/skills/requirements-evaluator/scripts/evaluate_requirements.py \
  --input /path/to/input-file.csv \
  --output /path/to/review-packet.md
```

3. The model reads:
   - the review packet
   - `SKILL.md`
   - `references/report-template.md`

4. The model outputs the final Chinese evaluation report.

### Prompt shape

Recommended prompt pattern:

```text
Use $requirements-evaluator at <skill-path>.

Read the requirement review packet at <packet-path>.
Use the rubric defined in <skill-path>/SKILL.md as the scoring basis.
Read the report template at <skill-path>/references/report-template.md.

Evaluate the requirements with the model.
Output a Chinese Markdown report.
```

## Frontend / Backend Notes

This section is for the future session that builds a UI and service around the evaluator.

### Backend flow

Recommended backend flow:

1. accept file upload
2. store the original file temporarily
3. run the packet builder
4. call the model with:
   - `SKILL.md`
   - `report-template.md`
   - packet content
5. store:
   - original file metadata
   - packet artifact
   - final report
   - status and errors

### Suggested API shape

- `POST /api/evaluations`
  upload file and start evaluation
- `GET /api/evaluations/:id`
  get evaluation status and metadata
- `GET /api/evaluations/:id/report`
  get final report
- `GET /api/evaluations/:id/packet`
  get review packet

Optional:

- `GET /api/evaluations`
  list evaluation history
- `DELETE /api/evaluations/:id`
  delete evaluation artifacts

### Suggested frontend screens

- upload page
- evaluation detail page
- history page

Useful UI behaviors:

- clear upload validation
- readable Markdown report rendering
- long-running status display
- optional packet inspection for debugging
- download or copy final report

## Current Boundaries

These boundaries should hold unless there is a strong reason to change them:

- final scoring belongs to the model, not the Python script
- the script is a packet builder, not a scoring engine
- the rubric lives in `SKILL.md`
- the output template stays in `report-template.md`
- packet and final report are separate artifacts

## Service Development Progress

### Current branch and workflow

- active implementation branch: `feature/requirements-evaluator-service`
- implementation is being executed from a git worktree under `.worktrees/`
- development is following the superpowers flow:
  - brainstorming
  - written spec
  - written implementation plan
  - subagent-driven task execution

### Scope locked for phase 1

Phase 1 currently includes only:

- frontend-backend separated architecture
- FastAPI backend
- React + TypeScript + Vite frontend
- local filesystem artifact storage
- asynchronous evaluation jobs
- dedupe based on input and version material
- upload page
- evaluation detail page
- Markdown report rendering
- Markdown report download

Phase 1 explicitly excludes:

- history page
- delete API
- packet inspection UI
- database-backed metadata storage

### Design decisions confirmed

- frontend stack:
  - React
  - TypeScript
  - Vite
  - React Router
  - TanStack Query
  - pnpm
- backend stack:
  - Python
  - FastAPI
  - in-process asynchronous job execution
- storage:
  - metadata and artifacts stored on local filesystem in phase 1
- future roadmap:
  - SQLite will be introduced later for metadata only
  - original upload, packet, and report files remain on local disk

### Completed implementation work

As of the current session, the following implementation tasks are complete on the feature branch:

- Task 1: backend scaffold and core configuration
  - FastAPI app entrypoint created
  - backend package scaffold created
  - config and repository path helpers created
  - initial evaluation model created
  - backend smoke test added
- Task 2: versioning and dedupe helpers
  - SHA-256 helper functions added
  - app version detection helper added
  - dedupe key builder added
  - regression coverage added for hashing and missing-git fallback
- Task 3: file-based evaluation store
  - file-backed `EvaluationStore` added
  - evaluation directory creation implemented
  - original upload persistence implemented
  - metadata.json persistence implemented
  - filename normalization added to prevent path traversal
  - regression coverage added for metadata contents and traversal-style input
- Task 4: packet builder adapter
  - thin backend adapter added around the existing packet builder script
  - adapter shells out with `sys.executable`
  - subprocess failures now include input and output paths
  - regression coverage added for both success and failure paths

Related commits on the feature branch:

- `be23f45` `feat: scaffold backend application`
- `805af3d` `fix: align backend scaffold dependencies and paths`
- `8903409` `feat: add evaluation versioning helpers`
- `066b657` `fix: align versioning test import`
- `8feecf6` `fix: harden versioning helpers`
- `1d23682` `feat: add file-based evaluation store`
- `a867a50` `fix: harden evaluation store filenames`
- `a2fa028` `feat: add packet builder adapter`
- `304ffdf` `fix: improve packet builder adapter errors`

### Work in progress

- Task 5 review is complete:
  - spec compliance review result:
    - approved
  - code quality review result:
    - approved with one minor package-structure follow-up
  - review note:
    - `backend/app/clients/__init__.py` was missing relative to the planned package layout and has now been added while starting Task 6
- Task 6 is complete:
  - evaluation service create path and dedupe reuse behavior have been implemented
  - service now computes and persists:
    - `input_fingerprint`
    - `skill_version`
    - `report_template_version`
    - `model_name`
    - `app_version`
    - `dedupe_key`
  - matching `pending`, `running`, and `succeeded` tasks are now reusable through the service path
  - matching `failed` tasks are intentionally not reused
  - `EvaluationStore.update_metadata()` was added early because the service now needs to persist dedupe metadata during task creation
  - completed files:
    - `backend/app/services/evaluation_service.py`
    - `backend/tests/test_evaluation_service.py`
    - `backend/app/storage/evaluation_store.py`
    - `backend/tests/test_evaluation_store.py`
- Task 7 is complete:
  - `EvaluationStore.read_detail()` now returns the backend detail model with optional report Markdown content
  - Task 7 plan note:
    - `read_metadata()` and `update_metadata()` were already implemented in Task 6 because the create-or-reuse service needed metadata persistence before Task 7
    - this task completed the remaining detail-read capability without changing later task boundaries
  - completed files:
    - `backend/app/storage/evaluation_store.py`
    - `backend/tests/test_evaluation_store.py`
- Task 8 is complete:
  - background runner now updates task status, builds a review packet, generates a mock report, and persists the final report path
  - review follow-up:
    - initial Task 8 review found that exceptions left tasks stuck in `running`
    - runner now records `failed` status, `finished_at`, and `error_message` before re-raising
  - spec compliance review result:
    - approved after failure-path fix
  - code quality review result:
    - approved
  - completed files:
    - `backend/app/runners/evaluation_runner.py`
    - `backend/tests/test_evaluation_service.py`

### Known implementation notes

- local Python test execution currently relies on a worktree-local virtual environment rather than the host interpreter
- review and implementation are being done task-by-task with subagents, and each completed task is checked with:
  - spec compliance review
  - code quality review
- there are pre-existing untracked `__pycache__` directories under `.agents/skills/requirements-evaluator/...`
  - they are not part of the service implementation work
  - they have been intentionally left untouched

### Next recommended steps

After Task 8, continue in this order:

- API endpoints
- frontend scaffold
- upload flow
- detail page and Markdown download
- development log refresh
- README for service mode and standalone skill mode

### Controller Summary

Use this section as the short resume point for future sessions:

- branch:
  - `feature/requirements-evaluator-service`
- completed tasks:
  - Task 1
  - Task 2
  - Task 3
  - Task 4
  - Task 5
  - Task 6
  - Task 7
  - Task 8
- latest task-completion commits:
  - `8feecf6` for Task 2 hardening
  - `a867a50` for Task 3 hardening
  - `304ffdf` for Task 4 hardening
  - `e52b3a5` for Task 5 implementation
- current working state:
  - Task 8 files are modified in the worktree and ready to commit
- next task:
  - Task 9 evaluation API endpoints
