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
