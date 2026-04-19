---
name: requirements-evaluator
description: Evaluate requirement or design documents stored in Excel or JSON files by having the model review the document content directly against a structured rubric and then produce a Chinese quality report with per-item scores, red flags, missing information, and prioritized revision advice. Use when Codex needs to review one or many requirement rows, reconcile user-provided dimensions with file headers, judge whether the documents are ready for implementation or testing, or prepare a model-driven review packet from structured requirement data.
---

# Requirements Evaluator

Evaluate requirement documents as evidence, not as intent. The model is the reviewer. Local scripts may normalize the input, but they must not replace model judgment.

This skill is self-contained. The default evaluation framework is fully defined in this file and should be used directly in future reviews.

## Workflow

1. Inspect the input format.
   Support `.xlsx`, `.xlsm`, and `.json`.
   Excel rows may represent one OR with multiple DR rows because merged cells are common.
   For Excel workbooks, read only the default active sheet.
   Ignore all other sheets unless the user explicitly asks for a different sheet.
   Expand merged-cell evidence before review so that blank follower rows still inherit the OR fields they belong to.
   Preserve the original field names and note repeated headers instead of silently dropping them.

2. Build the rubric before scoring.
   Start with the default rubric defined in this file.
   If the input headers clearly provide additional useful fields, incorporate them as evidence, not as new mandatory dimensions by default.
   Bias judgment toward implementation readiness and test readiness, while still checking OR quality and business clarity.
   Read [references/scoring-anchors.md](references/scoring-anchors.md) before final scoring to apply anchor definitions and red-line score caps.
   If a user explicitly asks for outside references or local evidence is insufficient, browse authoritative sources. Otherwise prefer local evidence.

3. Review each OR unit with the model.
   Use the rubric in this file as the primary standard.
   Base every score on explicit evidence in the OR and its linked DR rows.
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

### Default 100-Point Rubric

Default weight profile:

- `OR-用户语言描述`: 12
- `OR-应用场景`: 12
- `OR-用户价值`: 10
- `OR-约束和限制`: 6
- `DR-安全分析`: 10
- `DR-技术描述`: 10
- `DR-可测试性`: 10
- `DR-无歧义性`: 5
- `DR-性能需求`: 3
- `DR-硬件分析`: 2
- `需求分解与追踪-范围与边界`: 6
- `需求分解与追踪-假设与依赖`: 6
- `需求分解与追踪-一致性与可追踪性`: 4
- `需求分解与追踪-异常与边界场景`: 4

Dimension intent:

- `OR-用户语言描述`
  Check whether the requirement is understandable in user or business language rather than only implementation language.
- `OR-应用场景`
  Check whether usage context, trigger condition, and operating environment are explicit.
- `OR-用户价值`
  Check whether the user problem and expected value are explicit.
- `OR-约束和限制`
  Check whether deployment, compliance, compatibility, or operational limits are explicit.
- `DR-安全分析`
  Check whether security constraints, red lines, authentication, authorization, audit, encryption, or safety boundaries are explicit.
- `DR-技术描述`
  Check whether the technical behavior is concrete, complete, and operationally meaningful.
- `DR-可测试性`
  Check whether test cases or verification steps can be derived directly.
- `DR-无歧义性`
  Check whether parameters, states, and expected behavior are precise rather than vague.
- `DR-性能需求`
  Check whether relevant performance expectations are stated.
- `DR-硬件分析`
  Check whether hardware or resource assumptions are stated when relevant.
- `需求分解与追踪-范围与边界`
  Check whether the OR-to-DR decomposition defines inclusions, exclusions, and main behavior boundaries.
- `需求分解与追踪-假设与依赖`
  Check whether decomposition assumptions, dependencies, upstream inputs, or external conditions are visible.
- `需求分解与追踪-一致性与可追踪性`
  Check whether OR, DR, DS, TDR, and TDS align and trace cleanly, and whether each DR clearly maps back to the OR.
- `需求分解与追踪-异常与边界场景`
  Check whether invalid input, failures, rollback, timeout, conflict, logging, or edge conditions are covered in the decomposition result.

Apply these rules:
- Prefer weighted scoring out of 100.
- Score one OR unit at a time.
- `OR` part is scored once out of 40 for the OR statement itself.
- Each linked `DR` is scored separately out of 40.
- When one OR has multiple DRs, compute the `DR` part as the arithmetic average of all DR scores.
- `需求分解与追踪质量` part is scored once out of 20 by analyzing the relationship between the OR and all of its linked DRs together.
- Final OR total score = `OR部分得分 + DR平均分 + 需求分解与追踪质量得分`.
- Final document score = the arithmetic average of all OR total scores.
- Always start from the rubric above.
- Add missing dimensions only when needed to reflect strong requirement-writing standards.
- Separate evidence, judgment, and recommendation in the write-up.
- Flag vague statements such as "support", "complete", "reasonable", "etc." when they are not backed by parameters, conditions, or acceptance criteria.
- Prefer quoting or paraphrasing concrete field evidence over broad subjective summaries.
- When implementation and testing readiness conflict with OR completeness, explain the tradeoff explicitly instead of hiding it in the score.
- Mark clearly non-applicable dimensions as `N/A` and exclude them from the denominator instead of scoring them as missing.
- Apply the anchor definitions and red-line rules from [references/scoring-anchors.md](references/scoring-anchors.md) before finalizing any score.
- If any red-line rule is triggered, explicitly state the rule id and the score-cap basis in the final report.

Evidence tiering:

- `Excellent`: 90% to 100% of the dimension weight
- `Good`: 70% to 89%
- `Fair`: 40% to 69%
- `Poor`: 10% to 39%
- `Missing`: 0%

Common negative signals:

- slogan-like statements with no conditions or scope
- broad "支持" wording without behavior detail
- "etc." or "相关" or "完整" without enumeration
- no scenario but detailed technical action
- no user value but heavy technical wording
- no test points or verification method
- no edge cases, invalid input handling, or failure behavior
- references to standards without mapping requirement-to-standard behavior

Common positive signals:

- explicit actor, trigger, and scenario
- user problem and business value are stated
- parameters, allowed ranges, units, defaults, and requiredness are explicit
- normal flow and exceptional flow are both stated
- acceptance criteria or test points are directly derivable
- security, logging, compliance, and audit expectations are written down
- assumptions and dependencies are explicit
- OR and DR content reinforce rather than contradict each other

## Review Procedure

For each OR unit:

1. Identify the OR first.
   Capture the OR row range, OR ID, and OR name.

2. Identify all linked DRs.
   Use the expanded packet rather than the raw merged layout.
   Collect every DR that belongs to the OR before scoring.

3. Read staged fields together.
   Read OR, each DR, and DS/TDR/TDS fields as one chain when present.
   Score OR once, each DR once, and cross-layer consistency once.

4. Build a short evidence view.
   Extract the few lines that most strongly support or weaken the OR and each DR.
   Prefer explicit statements over inferred intent.

5. Score each dimension.
   Decide whether the dimension is applicable.
   Mark `N/A` only when the OR or DR genuinely does not call for that dimension.
   Write one short reason per dimension.

6. Make a readiness judgment.
   Ask whether an engineer can implement every DR without major assumptions, whether a tester can derive meaningful test cases, and whether the OR-to-DR mapping is complete enough to reduce rework.

7. Write per-OR findings.
   Output:
   - OR total score
   - OR part score
   - each DR score
   - DR average score
   - requirement decomposition and traceability score
   - triggered red-line rules and score-cap basis when applicable
   - 2 to 4 key evidence bullets
   - 1 to 3 red flags
   - 1 to 4 missing items
   - 2 to 5 revision actions

8. Write cross-OR findings.
   Identify repeated weak dimensions, separate structural issues from OR-specific issues, call out the best-written OR units as templates, and summarize whether the whole set is ready for design review, implementation, and system test design.

Avoid these failure modes:

- do not reward a requirement for information that exists only in neighboring rows unless traceability is explicit
- do not infer user value from technical detail unless the document states the value or problem
- do not over-penalize business framing if technical readiness is strong; explain the imbalance instead
- do not produce generic recommendations like “完善需求”; name the missing field or behavior
- do not let the packet structure force shallow review
- do not collapse multiple DRs under one OR into a single DR score

## Local Script

Use the bundled script when possible:

```bash
python3 scripts/evaluate_requirements.py \
  --input /path/to/input-file.xlsx \
  --output /path/to/review-packet.md
```

Behavior:
- reads Excel with `openpyxl` when available
- for Excel workbooks, reads only the default active sheet and records the actual `sheet_name` in the review packet `source_info`
- expands merged cells so OR fields remain visible on follower DR rows
- reads JSON arrays or objects with a top-level list field
- groups the packet by OR and nests all linked DR entries under that OR
- writes a review packet for the model
- does not generate the final scores or the final report on its own

## Dependencies

Check runtime dependencies before using the script.
Use [references/dependencies.md](references/dependencies.md) for the concrete package list and install command.

Current rule:

- `.json` does not need extra Python packages
- `.xlsx` and `.xlsm` require `openpyxl`

If a dependency is missing:

1. Detect it before continuing.
2. Tell the user which package is missing.
3. Use the bash tool to run the install command when appropriate.
4. Re-run the script after installation.

## Recommended Invocation

If the input is tabular, generate a review packet first, then ask the model to perform the final review.

Preferred flow:

1. Run the script to build a review packet.
2. Load the packet, this `SKILL.md`, and the report template.
3. Ask the model to produce the final Chinese evaluation report.
4. State the actual `sheet_name` from the packet when the input is Excel.
5. Report scores by OR unit, not by raw row.

Recommended prompt pattern:

```text
Use $requirements-evaluator at <skill-path>.

Read the requirement review packet at <packet-path>.
Use the rubric defined in <skill-path>/SKILL.md as the scoring basis.
Read the scoring anchors at <skill-path>/references/scoring-anchors.md.
Read the report template at <skill-path>/references/report-template.md.

Evaluate the requirements with the model, not with deterministic scripting.
Output a Chinese Markdown report.
When the input is Excel, state the actual `sheet_name` from the review packet before scoring.
For each OR:
- give the OR total score
- give the OR part score
- give each DR score
- give the DR average score
- give the requirement decomposition and traceability score
- cite concrete evidence from the OR and DR rows
- list red flags
- list missing items
- give prioritized revision advice
- state any triggered red-line rule as explicit score-cap evidence when applicable

Then summarize cross-OR weaknesses, strongest examples, the overall average score across all OR totals, and whether the set is ready for implementation and testing.
```

## Notes

- Keep this skill body concise. Put detailed criteria in references.
- If the user asks for only a review and no file changes, you may run the script to prepare the packet and then perform the final evaluation in the model response.
- Treat the script output as context assembly, not as the verdict.
- If the input is large, summarize repetitive low-signal rows and spend more space on the highest-risk or highest-value requirements.
