# Requirement Scoring Guide

Use this guide for every shard evaluation. Score from explicit document evidence only.

## Default 100-Point Structure

- OR part: 40 points
- DR average part: 40 points
- Requirement decomposition and traceability part: 20 points

Final OR total score:

```text
total_score = or_score + dr_average_score + traceability_score
```

When one OR has multiple DRs, score each DR separately out of 40, then compute `dr_average_score` as the arithmetic average.

## Dimension Weights

OR part, 40 points:

- `OR-用户语言描述`: 14
- `OR-应用场景`: 14
- `OR-用户价值`: 12

DR part, 40 points:

- `DR-安全分析`: 6
- `DR-可测试性`: 16
- `DR-无歧义性`: 10
- `DR-异常描述`: 8

Requirement decomposition and traceability part, 20 points:

- `需求分解完整性`: 7
- `需求分解边界清晰度`: 6
- `需求映射一致性`: 7

## Dimension Intent

- `OR-用户语言描述`: Check whether the requirement is understandable in user or business language rather than only implementation language.
- `OR-应用场景`: Check whether usage context, trigger condition, and operating environment are explicit.
- `OR-用户价值`: Check whether the user problem and expected value are explicit.
- `DR-安全分析`: Check whether the DR identifies which business parts touch applicable security red lines and states what security requirements, restrictions, or compliance obligations those parts must satisfy.
- `DR-可测试性`: Check whether the DR uses technical language to define behavior, inputs, outputs, conditions, boundaries, and expected results clearly enough to derive test cases and acceptance criteria directly. When quantitative claims are present, require explicit values, ranges, thresholds, units, or frequencies rather than vague adjectives.
- `DR-无歧义性`: Check whether terms, parameters, scope, states, and expected behavior allow only one reasonable interpretation rather than multiple competing readings.
- `DR-异常描述`: Check whether exception paths, error conditions, invalid input handling, failure behavior, and edge scenarios are explicit with clear triggers and expected responses.
- `需求分解完整性`: Check whether the OR's explicit key goals, sub-goals, critical constraints, or critical scenarios are each clearly carried by one or more DRs. Focus on whether any core goal is left uncovered.
- `需求分解边界清晰度`: Check whether each DR has a clear responsibility boundary and whether core-goal DRs are distinguishable from supporting DRs such as parameter, platform-reuse, release-scope, or format-definition items. Avoid overlap, mixed ownership, or background information masquerading as requirement decomposition.
- `需求映射一致性`: Check whether each DR semantically and directly responds to the OR's goals, objects, conditions, or expected results rather than being only topically related or linked by numbering.

## Evidence Tiers

Apply these tiers within each dimension:

- `Excellent`: 90% to 100% of the dimension weight
- `Good`: 70% to 89%
- `Fair`: 40% to 69%
- `Poor`: 10% to 39%
- `Missing`: 0%

Mark a dimension as missing or weak when evidence is not explicit. Do not assume intent. Mark `N/A` only when the dimension is genuinely not applicable, and explain the basis in your internal reasoning before scoring.
Do not treat a blank or omitted spreadsheet column as evidence of a requirement gap by itself. If the same meaning is stated in OR, DR, or DS text, use that substantive text as evidence instead of marking a missing item only because a dedicated Excel field is blank.

## Common Negative Signals

- slogan-like statements with no conditions or scope
- broad "支持" wording without behavior detail
- "etc.", "相关", "完整", "合理", or similar vague wording without enumeration
- adjectives such as "较大", "较好", "性能高", or "响应快" without explicit data, thresholds, ranges, or units
- performance, capacity, latency, throughput, frequency, or success-rate claims without a measurable target
- security wording such as "符合安全规范" or "满足安全红线" without pointing to the affected business part
- mentions authentication, audit, or encryption without mapping them to a concrete business requirement
- no scenario but detailed technical action
- no user value but heavy technical wording
- no explicit inputs, outputs, conditions, or result criteria
- no test points, acceptance criteria, or verification method
- no edge cases, invalid input handling, or failure behavior
- references to standards without mapping requirement-to-standard behavior

## Common Positive Signals

- explicit actor, trigger, and scenario
- user problem and business value are stated
- parameters, allowed ranges, units, defaults, and requiredness are explicit
- the business part that touches a security red line is explicitly identified
- the required security obligation is stated for that business part
- inputs, outputs, preconditions, boundary conditions, and result criteria are explicit
- quantitative targets include concrete values, ranges, thresholds, units, or frequencies
- normal flow and exceptional flow are both stated
- acceptance criteria or test points are directly derivable
- security, logging, compliance, and audit expectations are written down
- assumptions and dependencies are explicit
- OR and DR content reinforce rather than contradict each other

## Anchors

### OR-应用场景

- `Meets`: Clearly states the actor, trigger, usage environment, or business context.
- `Weak`: Describes the function but leaves trigger, scope, preconditions, or target users incomplete.
- `Missing`: Gives only an abstract capability statement with no practical usage context.

### OR-用户价值

- `Meets`: Clearly states the user problem, business value, compliance value, or market value.
- `Weak`: Value can be inferred, but the beneficiary or expected outcome is not explicit.
- `Missing`: Contains only functional or technical wording with no value statement.

### DR-安全分析

- `Meets`: Clearly identifies which business part touches a security red line and states what security requirement, restriction, or compliance obligation that part must satisfy.
- `Weak`: Mentions security, compliance, or red-line requirements, but does not clearly point to the affected business part or does not state the corresponding requirement concretely.
- `Missing`: Gives no security analysis, or only states broad wording such as "符合安全规范" or "满足安全红线要求" without mapping it to a specific business part and requirement.

### DR-可测试性

- `Meets`: Uses technical language to define behavior, inputs, outputs, conditions, boundaries, and expected results clearly enough to derive test cases and pass criteria directly. When quantitative statements are present, they include explicit values, ranges, thresholds, units, or frequencies.
- `Weak`: Contains some technical detail, but inputs, outputs, state changes, boundary conditions, or measurable pass criteria are incomplete. Quantitative expectations may exist but still rely on vague wording or unstated thresholds.
- `Missing`: Relies on broad wording such as "support", "provide", "optimize", "性能高", or "响应快" without concrete behavior definitions or measurable criteria. Test cases and acceptance rules cannot be derived directly.

### DR-无歧义性

- `Meets`: Parameters, objects, scope, states, frequency, quantities, or results are clearly defined.
- `Weak`: The main subject is clear, but key terms, boundaries, or result criteria allow multiple interpretations.
- `Missing`: Relies on vague wording such as "support", "reasonable", "related", or "complete" without additional definition.

### DR-异常描述

- `Meets`: Exception paths, error conditions, invalid input handling, failure behavior, and edge scenarios are explicitly described.
- `Weak`: Some exception handling is mentioned but lacks triggers, expected responses, or recovery behavior.
- `Missing`: No exception or error handling is described; only the happy path is covered.

### 需求分解完整性

- `Meets`: The OR's explicit key goals and sub-goals are each carried by one or more DRs. Core goals are directly decomposed, and supporting DRs are only supplementary rather than substitutes.
- `Weak`: Main capability is covered, but one or more explicit sub-goals, critical constraints, or critical scenarios are only indirectly supported or only partially decomposed.
- `Missing`: Multiple key goals or explicit sub-goals in the OR have no clear DR coverage, so the DR set cannot support implementation or acceptance with confidence.

### 需求分解边界清晰度

- `Meets`: Each DR has a single and clear responsibility boundary. Core-goal DRs and supporting DRs are clearly distinguishable, and the DR set avoids obvious overlap, duplication, or mixed goal-and-background writing.
- `Weak`: Most DR boundaries are understandable, but some DRs mix core goals with platform reuse, product parameters, release scope, format definition, or other supporting context. Some responsibilities overlap or are not sharply separated.
- `Missing`: DR boundaries are blurred or heavily mixed. It is hard to tell which DRs directly carry the OR's core goals and which are only background, scope, or implementation-support information.

### 需求映射一致性

- `Meets`: Each DR directly and semantically responds to an explicit OR goal, object, condition, or expected result. Supporting DRs, when present, reinforce the OR's explicit scope, constraints, or implementation preconditions rather than substituting for core-goal DRs.
- `Weak`: OR-to-DR mapping is broadly visible, but some DRs only address side content, supporting context, or implementation background instead of directly answering the OR's core goals. Some mappings are too narrow, too broad, or only partially on target.
- `Missing`: OR-to-DR relationship is inconsistent, indirect, or unclear. The DR set is mostly composed of topically related or supporting DRs while the OR's core goals are not directly carried.

### 支撑型DR说明

- `Valid`: Product parameters, platform reuse, release scope, format definitions, and similar items may be independent DRs when they directly carry explicit OR scope, constraints, or implementation preconditions.
- `Invalid As Primary Evidence`: Such supporting DRs must not be treated as high-quality mapping evidence when the OR's core business goals still lack directly corresponding DRs.

## Red-Line Rules

Apply these caps after initial scoring:

- `R1 Missing User Value Cap`: If the OR does not explicitly state user value, business purpose, compliance motivation, or market motivation, `or_score` must not exceed 24/40.
- `R2 Missing Usage Context Cap`: If the OR does not explicitly state the actor, trigger, usage condition, or business context, `or_score` must not exceed 26/40.
- `R3 Unmapped Security Red-Line Cap`: If a DR mentions security, compliance, or red-line requirements but does not identify which business part is affected and what requirement it must satisfy, `DR-安全分析` must not exceed 2/6.
- `R4 Untestable DR Cap`: If a DR does not clearly define behavior, inputs, outputs, conditions, expected results, or acceptance criteria, so that direct test cases cannot be derived, that DR must not exceed 24/40 before averaging.
- `R5 Vague Quantification Cap`: If a DR makes performance, capacity, latency, success-rate, frequency, or similar claims using wording such as "较大", "较好", "性能高", or "响应快" without explicit measurable targets, that DR must not exceed 20/40 before averaging.
- `R6 Happy-Path-Only DR Cap`: If a DR materially involves state changes, external dependencies, security decisions, data processing, or invalid-input risk but only describes the happy path and omits failure, rejection, invalid input, or recovery behavior, that DR must not exceed 30/40 before averaging.
- `R7 Incomplete Decomposition Coverage Cap`: If one OR has obviously uncovered key sub-capabilities, explicit sub-goals, or critical scenarios, `traceability_score` must not exceed 10/20.
- `R8 Distorted Decomposition Mapping Cap`: If multiple DRs under one OR are duplicate, conflicting, only weakly related, or mostly supporting DRs without directly carrying the OR's core goals, `traceability_score` must not exceed 8/20.

If any red-line rule affects the result, include it in `red_flags` or `missing_items` in the TSV output.

## Review Procedure Per OR

1. Identify the OR ID, name, row range, and category.
2. Collect all linked DRs under the OR before scoring.
3. Read OR, DR, and DS evidence as one requirement chain when present.
4. Score the OR part once.
5. Score each DR separately, then average DR scores.
6. Score decomposition and traceability once across the OR and all linked DRs.
7. Assign a numeric score to every scoring dimension and make sure the dimension sums equal `or_score`, `dr_average_score`, and `traceability_score`.
8. Apply red-line caps.
9. Output exactly one TSV row for the OR.
