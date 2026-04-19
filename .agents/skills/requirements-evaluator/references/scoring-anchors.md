# Scoring Anchors And Red-Line Rules

Use this file to stabilize scoring decisions. Score with the 100-point structure from `SKILL.md`, then use the anchors and score caps here to calibrate critical dimensions.

## Operating Rules

- Check whether the current OR or DR triggers any red-line rule before finalizing the score.
- Use the anchors to judge whether the dimension is `Meets`, `Weak`, or `Missing`.
- If the anchor conflicts with first-impression judgment, prefer the anchor.
- If a red-line rule is triggered, state the score-cap reason explicitly in the report.

## Key Dimension Anchors

### OR-应用场景

- `Meets`
  - Clearly states the actor, trigger, usage environment, or business context.
  - Answers who uses the capability and under what condition.
- `Weak`
  - Describes the function but not the trigger or practical usage context.
  - Mentions a scenario, but leaves scope, preconditions, or target users incomplete.
- `Missing`
  - Gives only an abstract capability statement with no practical usage context.

### OR-用户价值

- `Meets`
  - Clearly states the user problem, business value, or compliance/market value.
  - Answers why this requirement exists.
- `Weak`
  - Value can be inferred, but the beneficiary or expected outcome is not explicit.
- `Missing`
  - Contains only functional or technical wording with no value statement.

### OR-约束和限制

- `Meets`
  - Clearly states at least one critical constraint such as scope, exclusions, compatibility, compliance, deployment, or runtime limitation.
- `Weak`
  - Mentions a constraint but does not define the boundary, condition, or acceptance rule.
- `Missing`
  - Gives no constraint or limitation at all.

### DR-技术描述

- `Meets`
  - Clearly defines behavior, inputs and outputs, key conditions, and main processing logic.
  - Engineering implementation does not depend on major hidden assumptions.
- `Weak`
  - Contains technical actions, but misses key parameters, states, boundaries, or expected results.
- `Missing`
  - Uses vague wording such as "support", "implement", or "provide" without enough detail to guide implementation.

### DR-可测试性

- `Meets`
  - Test points, acceptance conditions, or verification steps can be derived directly.
  - At least two of the following are explicit: inputs, actions, expected results.
- `Weak`
  - Test design is possible, but still depends on additional assumptions or unstated pass criteria.
- `Missing`
  - Test points cannot be derived directly and the acceptance semantics are not closed.

### DR-无歧义性

- `Meets`
  - Parameters, objects, scope, states, frequency, quantities, or results are defined clearly.
  - Different readers will usually reach the same interpretation.
- `Weak`
  - The main subject is clear, but key terms, boundaries, or result criteria still allow multiple interpretations.
- `Missing`
  - Relies on vague wording such as "support", "reasonable", "related", or "complete" without additional definition.

### 需求分解与追踪-一致性与可追踪性

- `Meets`
  - Coverage from the OR to its DRs is clear.
  - DRs do not show obvious omission, duplication, or contradiction, and each DR maps back to the OR.
- `Weak`
  - The overall mapping is mostly visible, but there are omissions, overlaps, duplicate coverage, or weak mapping quality.
- `Missing`
  - The OR-to-DR relationship is unclear, so decomposition completeness and consistency cannot be confirmed.

## Red-Line Rules

### R1 Missing User Value Cap

- If the OR does not explicitly state user value, business purpose, or compliance/market motivation, the `OR` part must not exceed `24/40`.

### R2 Untestable DR Cap

- If a DR does not directly yield test points, acceptance conditions, or verification steps, that DR must not exceed `24/40`.

### R3 Vague DR Technical Description Cap

- If a DR only uses vague wording such as "support", "implement", or "provide" and lacks key behavioral detail, that DR must not exceed `20/40`.

### R4 Incomplete Decomposition Coverage Cap

- If one OR has obviously uncovered key sub-capabilities, `Requirement Decomposition And Traceability Quality` must not exceed `10/20`.

### R5 Distorted Decomposition Mapping Cap

- If multiple DRs under one OR are obviously duplicate, conflicting, or cannot be traced back to the OR, `Requirement Decomposition And Traceability Quality` must not exceed `8/20`.
