# Model Review Workflow

Use this workflow after loading the review packet. The goal is consistent model judgment, not mechanical checkbox filling.

## 1. Read Before Scoring

For each requirement row:

1. Identify the requirement identity first.
   Capture row index, requirement ID, and requirement name.

2. Read the staged fields together.
   Read OR, DR, DS, TDR, and TDS as one chain when present.
   Do not score OR and DR in isolation if they obviously describe the same requirement at different levels.

3. Build a short evidence view.
   Extract the few lines that most strongly support or weaken the requirement.
   Prefer explicit statements over inferred intent.

## 2. Score Dimensions

For each dimension:

1. Decide whether the dimension is applicable.
   Mark `N/A` only when the requirement genuinely does not call for that dimension.
   Do not use `N/A` to avoid hard judgment on weak writing.

2. Assign a score based on evidence.
   Use the rubric weights and evidence tiers from `rubric.md`.

3. Write one short reason.
   Keep the reason concrete.
   Example: "写了参数范围和失败提示，但没有验证方法，因此可测试性中等。"

## 3. Judge Readiness

After dimension scoring, make a second-pass judgment on readiness:

- Can an engineer implement this without making major assumptions?
- Can a tester derive meaningful test cases from it?
- Are failure paths, limits, and dependencies visible enough to reduce rework?

If the answer is mostly yes, the requirement should not be buried only because OR framing is weak.
If the answer is no, the report should say the document is not implementation-ready even if the requirement sounds directionally reasonable.

## 4. Write Requirement Findings

For each requirement, output:

- score and grade
- 2 to 4 key evidence bullets
- 1 to 3 red flags
- 1 to 4 missing items
- 2 to 5 revision actions

Keep findings evidence-first:

- First say what the document states.
- Then say what that means for quality.
- Then say what to change.

## 5. Write Cross-Requirement Summary

After row-level review:

1. Identify repeated weak dimensions.
2. Separate structural issues from row-specific issues.
3. Call out the best-written rows as candidate templates.
4. Summarize whether the whole set is ready for:
   - design review
   - implementation
   - system test design

## 6. Avoid These Failure Modes

- Do not reward a requirement for information that exists only in neighboring rows unless traceability is explicit.
- Do not infer user value from technical detail unless the document actually states the value or problem.
- Do not over-penalize business framing if technical readiness is strong; explain the imbalance instead.
- Do not produce generic recommendations like "完善需求" or "补充细节"; name the missing field or behavior.
- Do not let the packet structure force shallow review. The packet is only context assembly.
