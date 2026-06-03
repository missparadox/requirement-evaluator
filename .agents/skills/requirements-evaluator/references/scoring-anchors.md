# Scoring Anchors And Red-Line Rules

Use this file to stabilize scoring decisions. Score with the 100-point structure from `SKILL.md`, then use the anchors and score caps here to calibrate critical dimensions.

## Operating Rules

- Check whether the current OR or DR triggers any red-line rule before finalizing the score.
- Use the anchors to judge whether the dimension is `Meets`, `Weak`, or `Missing`.
- If the anchor conflicts with first-impression judgment, prefer the anchor.
- If a red-line rule is triggered, state the score-cap reason explicitly in the report.

## Key Dimension Anchors

### OR-用户语言描述

- `Meets`
  - Requirement wording is understandable from a user or business perspective.
  - The description explains the desired capability without relying mainly on internal implementation terms.
- `Weak`
  - The requirement is mostly understandable, but mixes user intent with unexplained technical wording.
  - The user-facing meaning can be inferred but is not stated cleanly.
- `Missing`
  - The description is mainly implementation language or an abstract label, so non-technical readers cannot reliably understand the need.

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

### DR-安全分析

- `Meets`
  - Security constraints, red lines, authentication, authorization, audit, encryption, or safety boundaries are explicitly described where relevant.
  - The DR states how security-sensitive behavior should be handled or verified.
- `Weak`
  - Security is mentioned, but the boundary, rule, or expected handling is incomplete.
  - Security expectations require additional interpretation before implementation or testing.
- `Missing`
  - Security expectations are absent when the DR involves access, data, operations, interfaces, compliance, or other security-sensitive behavior.

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

### DR-异常描述

- `Meets`
  - Exception paths, error conditions, invalid input handling, and failure behavior are explicitly described.
  - Triggers for each exception and the expected system response are clearly stated.
  - Edge scenarios and boundary conditions are addressed.
- `Weak`
  - Some exception paths are mentioned but lack specific triggers, expected responses, or recovery behavior.
  - Error handling is partially described but incomplete or inconsistent.
- `Missing`
  - No exception or error handling is described.
  - Only the happy path is covered with no mention of failure scenarios or invalid input.

### 需求分解完整性

- `Meets`
  - The key capability points in the OR are all covered by one or more DRs.
  - The DR set is sufficient to support implementation and testing of the OR.
- `Weak`
  - The main capability is covered, but some expected sub-capabilities are missing or only partially decomposed.
- `Missing`
  - Major capability points in the OR have no clear DR coverage.

### 需求分解边界清晰度

- `Meets`
  - Each DR has a clear responsibility boundary.
  - The DR set avoids obvious overlap, duplication, or ownership ambiguity.
- `Weak`
  - Most DR boundaries are understandable, but some responsibilities overlap or are not sharply separated.
- `Missing`
  - DR boundaries are blurred, heavily overlapping, or too ambiguous to support clean implementation ownership.

### 需求映射一致性

- `Meets`
  - The OR-to-DR mapping is semantically coherent.
  - DRs do not show obvious drift, contradiction, or inconsistent interpretation of the OR.
- `Weak`
  - The overall mapping is mostly visible, but some DRs are too narrow, too broad, partially off-topic, or weakly mapped.
- `Missing`
  - The OR-to-DR relationship is inconsistent or unclear, so the decomposition cannot be trusted as an accurate implementation of the OR.

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
