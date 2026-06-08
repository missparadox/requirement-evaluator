---
name: requirements-evaluator
description: Evaluate requirement or design documents stored in Excel or JSON files with a shard-only workflow. Use when Codex needs to normalize requirement rows, split OR units into independent shard prompts, validate model TSV scoring output, and aggregate validated shard results into a Chinese Markdown quality report.
---

# Requirements Evaluator

Evaluate requirement documents as evidence, not as intent. The model is the reviewer for each shard; the local script prepares evidence, validates TSV output, and aggregates the final report.

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
- empty `results/` and `repairs/` directories

Send each prompt file to the model in an independent context, and save the raw TSV output, for example:

```text
artifacts/requirements/results/shard_0001.raw.tsv
```

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

Aggregate validated results:

```bash
python3 scripts/evaluate_requirements.py aggregate \
  --packet artifacts/requirements/packet.json \
  --results-dir artifacts/requirements/results \
  --report reports/requirements.md
```

## Input Handling

The script supports:

- `.xlsx`
- `.xlsm`
- `.json`

Excel handling:

- Read only the active sheet.
- Record the actual `sheet_name` in `packet.json`.
- Expand merged-cell evidence before grouping rows.
- Preserve original field names and repeated headers.

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

The model:

- scores only the OR units in the current shard
- applies the full scoring guide and red-line rules
- outputs only the required TSV schema

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
