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

- `OR-用户语言描述`: 12
- `OR-应用场景`: 12
- `OR-用户价值`: 10
- `OR-约束和限制`: 6

DR part, 40 points:

- `DR-安全分析`: 5
- `DR-技术描述`: 10
- `DR-可测试性`: 10
- `DR-无歧义性`: 8
- `DR-异常描述`: 7

Requirement decomposition and traceability part, 20 points:

- `需求分解完整性`: 7
- `需求分解边界清晰度`: 6
- `需求映射一致性`: 7

## Dimension Intent

- `OR-用户语言描述`: Check whether the requirement is understandable in user or business language rather than only implementation language.
- `OR-应用场景`: Check whether usage context, trigger condition, and operating environment are explicit.
- `OR-用户价值`: Check whether the user problem and expected value are explicit.
- `OR-约束和限制`: Check whether deployment, compliance, compatibility, or operational limits are explicit.
- `DR-安全分析`: Check whether security constraints, red lines, authentication, authorization, audit, encryption, or safety boundaries are explicit.
- `DR-技术描述`: Check whether the technical behavior is concrete, complete, and operationally meaningful.
- `DR-可测试性`: Check whether test cases or verification steps can be derived directly.
- `DR-无歧义性`: Check whether parameters, states, and expected behavior are precise rather than vague.
- `DR-异常描述`: Check whether exception paths, error conditions, invalid input handling, failure behavior, and edge scenarios are explicit with clear triggers and expected responses.
- `需求分解完整性`: Check whether the key capability points in the OR are covered by the linked DR set.
- `需求分解边界清晰度`: Check whether each DR has a clear responsibility boundary and avoids overlap or duplicate ownership.
- `需求映射一致性`: Check whether OR, DR, and DS align semantically without drift or contradiction.

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
- no scenario but detailed technical action
- no user value but heavy technical wording
- no test points, acceptance criteria, or verification method
- no edge cases, invalid input handling, or failure behavior
- references to standards without mapping requirement-to-standard behavior

## Common Positive Signals

- explicit actor, trigger, and scenario
- user problem and business value are stated
- parameters, allowed ranges, units, defaults, and requiredness are explicit
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

### OR-约束和限制

- `Meets`: Clearly states at least one critical constraint such as scope, exclusions, compatibility, compliance, deployment, or runtime limitation.
- `Weak`: Mentions a constraint but does not define the boundary, condition, or acceptance rule.
- `Missing`: Gives no constraint or limitation.

### DR-技术描述

- `Meets`: Clearly defines behavior, inputs and outputs, key conditions, and main processing logic.
- `Weak`: Contains technical actions, but misses key parameters, states, boundaries, or expected results.
- `Missing`: Uses vague wording such as "support", "implement", or "provide" without enough detail to guide implementation.

### DR-可测试性

- `Meets`: Test points, acceptance conditions, or verification steps can be derived directly. At least two of inputs, actions, and expected results are explicit.
- `Weak`: Test design is possible, but still depends on assumptions or unstated pass criteria.
- `Missing`: Test points cannot be derived directly and acceptance semantics are not closed.

### DR-无歧义性

- `Meets`: Parameters, objects, scope, states, frequency, quantities, or results are clearly defined.
- `Weak`: The main subject is clear, but key terms, boundaries, or result criteria allow multiple interpretations.
- `Missing`: Relies on vague wording such as "support", "reasonable", "related", or "complete" without additional definition.

### DR-异常描述

- `Meets`: Exception paths, error conditions, invalid input handling, failure behavior, and edge scenarios are explicitly described.
- `Weak`: Some exception handling is mentioned but lacks triggers, expected responses, or recovery behavior.
- `Missing`: No exception or error handling is described; only the happy path is covered.

### 需求分解完整性

- `Meets`: The key capability points in the OR are covered by one or more DRs.
- `Weak`: Main capability is covered, but some expected sub-capabilities are missing or partially decomposed.
- `Missing`: Major capability points in the OR have no clear DR coverage.

### 需求分解边界清晰度

- `Meets`: Each DR has a clear responsibility boundary and the DR set avoids obvious overlap.
- `Weak`: Most DR boundaries are understandable, but some responsibilities overlap or are not sharply separated.
- `Missing`: DR boundaries are blurred, heavily overlapping, or ambiguous.

### 需求映射一致性

- `Meets`: OR-to-DR mapping is semantically coherent and DRs do not drift or contradict the OR.
- `Weak`: Overall mapping is visible, but some DRs are too narrow, too broad, partially off-topic, or weakly mapped.
- `Missing`: OR-to-DR relationship is inconsistent or unclear.

## Red-Line Rules

Apply these caps after initial scoring:

- `R1 Missing User Value Cap`: If the OR does not explicitly state user value, business purpose, compliance motivation, or market motivation, `or_score` must not exceed 24/40.
- `R2 Untestable DR Cap`: If a DR does not directly yield test points, acceptance conditions, or verification steps, that DR must not exceed 24/40 before averaging.
- `R3 Vague DR Technical Description Cap`: If a DR only uses vague wording such as "support", "implement", or "provide" and lacks key behavioral detail, that DR must not exceed 20/40 before averaging.
- `R4 Incomplete Decomposition Coverage Cap`: If one OR has obviously uncovered key sub-capabilities, `traceability_score` must not exceed 10/20.
- `R5 Distorted Decomposition Mapping Cap`: If multiple DRs under one OR are duplicate, conflicting, or cannot be traced back to the OR, `traceability_score` must not exceed 8/20.

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
