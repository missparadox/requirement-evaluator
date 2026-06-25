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

### DR-安全分析

- `Meets`
  - Clearly identifies which business part touches a security red line.
  - States what security requirement, restriction, or compliance obligation that part must satisfy.
- `Weak`
  - Mentions security, compliance, or red-line requirements, but does not clearly point to the affected business part or does not state the corresponding requirement concretely.
- `Missing`
  - Gives no security analysis, or only states broad wording such as "符合安全规范" or "满足安全红线要求" without mapping it to a specific business part and requirement.

### DR-可测试性

- `Meets`
  - Uses technical language to define behavior, inputs, outputs, conditions, boundaries, and expected results clearly enough to derive test cases and pass criteria directly.
  - When quantitative statements are present, they include explicit values, ranges, thresholds, units, or frequencies.
- `Weak`
  - Contains some technical detail, but inputs, outputs, state changes, boundary conditions, or measurable pass criteria are incomplete.
  - Quantitative expectations may exist but still rely on vague wording or unstated thresholds.
- `Missing`
  - Relies on broad wording such as "support", "provide", "optimize", "性能高", or "响应快" without concrete behavior definitions or measurable criteria.
  - Test cases and acceptance rules cannot be derived directly.

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
  - The OR's explicit key goals and sub-goals are each carried by one or more DRs.
  - Core goals are directly decomposed, and supporting DRs are only supplementary rather than substitutes.
- `Weak`
  - Main capability is covered, but one or more explicit sub-goals, critical constraints, or critical scenarios are only indirectly supported or only partially decomposed.
- `Missing`
  - Multiple key goals or explicit sub-goals in the OR have no clear DR coverage, so the DR set cannot support implementation or acceptance with confidence.

### 需求分解边界清晰度

- `Meets`
  - Each DR has a single and clear responsibility boundary.
  - Core-goal DRs and supporting DRs are clearly distinguishable, and the DR set avoids obvious overlap, duplication, or mixed goal-and-background writing.
- `Weak`
  - Most DR boundaries are understandable, but some DRs mix core goals with platform reuse, product parameters, release scope, format definition, or other supporting context.
  - Some responsibilities overlap or are not sharply separated.
- `Missing`
  - DR boundaries are blurred or heavily mixed.
  - It is hard to tell which DRs directly carry the OR's core goals and which are only background, scope, or implementation-support information.

### 需求映射一致性

- `Meets`
  - Each DR directly and semantically responds to an explicit OR goal, object, condition, or expected result.
  - Supporting DRs, when present, reinforce the OR's explicit scope, constraints, or implementation preconditions rather than substituting for core-goal DRs.
- `Weak`
  - OR-to-DR mapping is broadly visible, but some DRs only address side content, supporting context, or implementation background instead of directly answering the OR's core goals.
  - Some mappings are too narrow, too broad, or only partially on target.
- `Missing`
  - OR-to-DR relationship is inconsistent, indirect, or unclear.
  - The DR set is mostly composed of topically related or supporting DRs while the OR's core goals are not directly carried.

### 支撑型DR说明

- `Valid`
  - Product parameters, platform reuse, release scope, format definitions, and similar items may be independent DRs when they directly carry explicit OR scope, constraints, or implementation preconditions.
- `Invalid As Primary Evidence`
  - Such supporting DRs must not be treated as high-quality mapping evidence when the OR's core business goals still lack directly corresponding DRs.

### 需求追踪与异常覆盖

- `Meets`
  - The OR-to-DR trace is clear.
  - Exception paths, invalid input, failure behavior, or key edge scenarios are explicitly represented in the decomposition result.
- `Weak`
  - The trace is mostly visible, but exception or edge-case handling is incomplete or only weakly represented.
- `Missing`
  - The trace is unclear and exception or edge-case handling has no clear decomposition landing point.

## Red-Line Rules

### R1 Missing User Value Cap

- If the OR does not explicitly state user value, business purpose, or compliance/market motivation, the `OR` part must not exceed `24/40`.

### R2 Missing Usage Context Cap

- If the OR does not explicitly state the actor, trigger, usage condition, or business context, the `OR` part must not exceed `26/40`.

### R3 Unmapped Security Red-Line Cap

- If a DR mentions security, compliance, or red-line requirements but does not identify which business part is affected and what requirement it must satisfy, `DR-安全分析` must not exceed `2/6`.

### R4 Untestable DR Cap

- If a DR does not clearly define behavior, inputs, outputs, conditions, expected results, or acceptance criteria, so that direct test cases cannot be derived, that DR must not exceed `24/40`.

### R5 Vague Quantification Cap

- If a DR makes performance, capacity, latency, success-rate, frequency, or similar claims using wording such as "较大", "较好", "性能高", or "响应快" without explicit measurable targets, that DR must not exceed `20/40`.

### R6 Happy-Path-Only DR Cap

- If a DR materially involves state changes, external dependencies, security decisions, data processing, or invalid-input risk but only describes the happy path and omits failure, rejection, invalid input, or recovery behavior, that DR must not exceed `30/40`.

### R7 Incomplete Decomposition Coverage Cap

- If one OR has obviously uncovered key sub-capabilities, explicit sub-goals, or critical scenarios, `Requirement Decomposition And Traceability Quality` must not exceed `10/20`.

### R8 Distorted Decomposition Mapping Cap

- If multiple DRs under one OR are duplicate, conflicting, only weakly related, or mostly supporting DRs without directly carrying the OR's core goals, `Requirement Decomposition And Traceability Quality` must not exceed `8/20`.
