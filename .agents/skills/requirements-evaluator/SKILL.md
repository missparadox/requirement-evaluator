---
name: requirements-evaluator
description: Evaluate requirement or design documents stored in CSV, Excel, or JSON files and produce a structured Chinese quality report with per-item scores, red flags, missing information, and prioritized revision advice. Use when Codex needs to review one or many requirement rows, score them against strong design standards, reconcile user-provided dimensions with file headers, or judge whether the documents are ready for detailed design, implementation, or testing.
---

# Requirements Evaluator

Evaluate requirement documents as evidence, not as intent. Score only what the file actually states.

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

3. Score each requirement row.
   Use the rubric in [references/rubric.md](references/rubric.md).
   Base every score on explicit evidence in the row.
   If a dimension is not clearly addressed, score it as missing or weak instead of assuming intent.
   If a dimension is genuinely not applicable, say why. Do not silently award full credit.

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
  --output /path/to/report.md
```

Behavior:
- reads CSV directly
- reads Excel with `openpyxl` when available
- reads JSON arrays or objects with a top-level list field
- handles repeated column names by keeping ordered occurrences
- writes a Chinese Markdown report

## Notes

- Keep this skill body concise. Put detailed criteria in references.
- If the user asks for only a review and no file changes, you may run the script and return the report without editing the input files.
- If you manually review a few rows in addition to the scripted output, use that review to sharpen recommendations, not to override evidence blindly.
