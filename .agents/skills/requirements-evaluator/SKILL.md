---
name: requirements-evaluator
description: Evaluate requirement or design documents stored in Excel or JSON files with a shard-only workflow. Use when Codex needs to normalize requirement rows, split OR units into independent shard prompts, validate model TSV scoring output, and aggregate validated shard results into a Chinese Markdown quality report.
---

# Requirements Evaluator

Evaluate requirement documents as evidence, not as intent. The model is the reviewer for each shard; the local script prepares evidence, validates TSV output, and aggregates the final report.

## Single-Project Closed Loop

When the user asks to use this skill for one requirement document, the skill must execute the full single-project workflow end-to-end and return the final deliverables. The user should not need to handle shard prompts, raw TSV files, repair prompts, or intermediate validation artifacts manually.

Default single-project deliverables:

- final Chinese Markdown report
- matching machine-readable `*.summary.json`

## Mandatory Shard Workflow

Formal evaluations must use the shard pipeline. Do not evaluate a full packet in one model call.

Rules:

- Build a structured `packet.json` first.
- Split the packet into OR shards. The default shard size is 2 OR units.
- Evaluate every shard in a fresh model context. Do not continue from a previous shard conversation.
- Each shard prompt must include:
  - `references/scoring-guide.md`
  - `references/output-tsv-schema.md`
  - the current `shard_XXXX.json`
- The model output for a shard must be TSV only.
- Validate every raw TSV output with the script before aggregation.
- Aggregate only validated result JSON files. Do not aggregate prior chat history, raw model prose, or full shard prompts.
- Generate the final Chinese Markdown report with the script. Do not ask the model to write the final report from the full raw packet.
- In normal skill usage, do not ask the user to forward shard prompts or manage TSV formatting manually.

## Command Flow

Prepare a complete shard workspace:

```bash
python3 scripts/evaluate_requirements.py prepare \
  --input /path/to/requirements.xlsx \
  --out-dir /path/to/artifacts/requirements \
  --shard-size 2
```

This writes:

- `packet.json`
- `shards/shard_0001.json`, `shards/shard_0002.json`, ...
- `prompts/shard_0001.prompt.txt`, `prompts/shard_0002.prompt.txt`, ...
- `run_state.json`
- empty `results/` and `repairs/` directories

The agent must evaluate each prompt file in an independent model context, and save the raw TSV output, for example:

```text
artifacts/requirements/results/shard_0001.raw.tsv
```

Closed-loop requirement:

- Do not stop after `prepare` unless the user explicitly asked for a partial workflow.
- Run every shard through evaluation, validation, and if needed repair or rerun, before aggregation.
- Use `run_state.json` as the machine-readable source of truth for shard status progression.

Validate a raw shard output:

```bash
python3 scripts/evaluate_requirements.py validate-result \
  --shard artifacts/requirements/shards/shard_0001.json \
  --raw-output artifacts/requirements/results/shard_0001.raw.tsv \
  --output artifacts/requirements/results/shard_0001.valid.json \
  --repair-prompt artifacts/requirements/repairs/shard_0001.repair_prompt.txt
```

Validation statuses:

- `valid`: the TSV is accepted and a validated JSON result is written.
- `repairable`: the output appears to contain scoring content but is not valid TSV; use the generated repair prompt.
- `rerun_required`: the output is missing required ORs, scores, or identifiers; rerun the original shard prompt.

Closed-loop retry policy:

- If `repairable`, immediately evaluate the generated repair prompt in a fresh model context and validate the repaired TSV again.
- If `rerun_required`, rerun the original shard prompt in a fresh model context and validate again.
- Do not aggregate until every shard is `valid`, or the agent has exhausted explicit retry handling and can report the failure clearly.

Aggregate validated results:

```bash
python3 scripts/evaluate_requirements.py aggregate \
  --packet artifacts/requirements/packet.json \
  --results-dir artifacts/requirements/results \
  --report reports/requirements.md
```

This also writes a machine-readable sidecar summary by default:

```text
reports/requirements.summary.json
```

## Input Handling

The script supports:

- `.xlsx`
- `.xlsm`
- `.json`

Excel handling:

- Read only `Sheet1`.
- Record the actual `sheet_name` in `packet.json`.
- Expand merged-cell evidence before grouping rows.
- Preserve original field names and repeated headers, except `TDR/TDS` fields which are excluded from processing.

Evaluation scope:

- Only OR units whose requirement category is exactly `功能` participate in scoring.
- Category counts for all OR categories are preserved in `packet.json` and reported during aggregation.

## Responsibility Boundaries

The script:

- reads Excel/JSON input
- builds `packet.json`
- splits OR shards
- generates shard prompts
- validates model TSV output
- generates repair prompts for format-only failures
- aggregates validated results
- renders the final Chinese Markdown report
- writes the machine-readable single-project summary JSON

The model:

- scores only the OR units in the current shard
- applies the full scoring guide and red-line rules
- outputs only the required TSV schema

The main agent:

- owns orchestration of the single-project closed loop
- evaluates each shard in a fresh model context
- handles repair or rerun automatically when validation fails
- returns the final report location and summary location to the user

The script must not assign final scores by itself. It may reject, normalize, and aggregate model scores only after validation.

## References

- `references/scoring-guide.md`: full rubric, anchors, and red-line score caps.
- `references/output-tsv-schema.md`: the only accepted shard output format.

## Dependencies

JSON input uses the Python standard library.

Excel input requires `openpyxl`. If it is missing, the script returns an install hint:

```bash
python3 -m pip install openpyxl
```
