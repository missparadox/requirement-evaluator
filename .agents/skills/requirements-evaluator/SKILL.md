---
name: requirements-evaluator
description: Evaluate requirement or design documents stored in CSV, Excel, or JSON files by having the model review the document content directly against a structured rubric and then produce a Chinese quality report with per-item scores, red flags, missing information, and prioritized revision advice. Use when Codex needs to review one or many requirement rows, reconcile user-provided dimensions with file headers, judge whether the documents are ready for implementation or testing, or prepare a model-driven review packet from tabular requirement data.
---

# Requirements Evaluator

Evaluate requirement documents as evidence, not as intent. The model is the reviewer. Local scripts may normalize the input, but they must not replace model judgment.

## Workflow

1. Inspect the input format.
   Support `.csv`, `.xlsx`, `.xlsm`, and `.json`.
   Treat each row or object as one requirement document.
   Preserve the original field names and note repeated headers instead of silently dropping them.

2. Build the rubric before scoring.
   Start with any user-provided dimension file such as `dimensions.txt`.
   Then inspect the input headers to infer what the author expects to provide, such as scenario, customer problem, value, parameter specification, test points, security constraints, assumptions, and verification method.
   Then supplement with strong design standards drawn from superpowers-style requirement writing: clear scope, low ambiguity, internal consistency, explicit constraints, error handling, and testability.
   If a user explicitly asks for outside references or local evidence is insufficient, browse authoritative sources. Otherwise prefer local evidence.

3. Review each requirement row with the model.
   Use the rubric in [references/rubric.md](references/rubric.md).
   Base every score on explicit evidence in the row.
   If a dimension is not clearly addressed, score it as missing or weak instead of assuming intent.
   If a dimension is genuinely not applicable, say why. Do not silently award full credit.
   Do not delegate the final score to a deterministic script.

4. Produce a Chinese report.
   Follow [references/report-template.md](references/report-template.md).
   Include:
   - methodology and data source
   - overall distribution and average score
   - per-requirement scorecards
   - recurring weak dimensions
   - prioritized recommendations
   - a final judgment on whether the set reaches excellent-design quality

## Scoring Rules

Read [references/rubric.md](references/rubric.md) when:
- the user supplies a custom dimensions file
- the input has OR/DR/DS/TDR/TDS style staged requirements
- you need to justify why a requirement is weak or not implementation-ready

Apply these rules:
- Prefer weighted scoring out of 100.
- Keep user-supplied dimensions whenever they are coherent.
- Add missing dimensions only when needed to reflect strong requirement-writing standards.
- Separate evidence, judgment, and recommendation in the write-up.
- Flag vague statements such as "support", "complete", "reasonable", "etc." when they are not backed by parameters, conditions, or acceptance criteria.

## Local Script

Use the bundled script when possible:

```bash
python3 scripts/evaluate_requirements.py \
  --input /path/to/requirements.csv \
  --dimensions /path/to/dimensions.txt \
  --output /path/to/review-packet.md
```

Behavior:
- reads CSV directly
- reads Excel with `openpyxl` when available
- reads JSON arrays or objects with a top-level list field
- handles repeated column names by keeping ordered occurrences
- writes a review packet for the model
- does not generate the final scores or the final report on its own

## Notes

- Keep this skill body concise. Put detailed criteria in references.
- If the user asks for only a review and no file changes, you may run the script to prepare the packet and then perform the final evaluation in the model response.
- Treat the script output as context assembly, not as the verdict.
