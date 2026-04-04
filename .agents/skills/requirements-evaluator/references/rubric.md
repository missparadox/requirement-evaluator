# Requirements Evaluation Rubric

Use this rubric to evaluate whether a requirement document meets strong design standards.

## Dimension Sources

Build the final rubric from three sources in this order:

1. User-provided dimensions, if present.
2. The input schema itself.
3. Strong design-writing standards from superpowers-style specs.

For the common OR/DR/DS/TDR/TDS schema, use the default 100-point rubric below.

## Default 100-Point Rubric

### OR dimensions: 35 points

1. `OR-用户语言描述` - 10
   Check whether the requirement is understandable in user or business language rather than only implementation language.

2. `OR-应用场景` - 10
   Check whether the usage context, trigger condition, and operating environment are clear.

3. `OR-用户价值` - 10
   Check whether the user problem and expected value are explicit.

4. `OR-约束和限制` - 5
   Check whether constraints such as deployment, compliance, compatibility, or limits are explicit.

### DR dimensions: 35 points

5. `DR-安全分析` - 8
   Check whether security constraints, red lines, authentication, audit, encryption, or safety boundaries are explicit.

6. `DR-技术描述` - 8
   Check whether the technical requirement is concrete, complete, and includes important operational detail.

7. `DR-可测试性` - 8
   Check whether the text can be turned into direct test cases or verification steps.

8. `DR-无歧义性` - 4
   Check whether parameters, states, and expected behavior are precise rather than vague.

9. `DR-性能需求` - 4
   Check whether performance expectations or explicit "not applicable" statements are present when relevant.

10. `DR-硬件分析` - 3
    Check whether hardware or resource assumptions are stated when relevant, or whether the document clearly indicates that hardware impact is not applicable.

### Cross-layer dimensions: 30 points

11. `跨层-范围与边界` - 8
    Derived from strong spec-writing standards.
    Check whether the requirement defines what is included, what is excluded, and the main behavior boundaries.

12. `跨层-假设与依赖` - 8
    Derived from DS/TDS-style fields and from implementation readiness.
    Check whether assumptions, dependencies, upstream inputs, and external conditions are visible.

13. `跨层-一致性与可追踪` - 7
    Check whether OR, DR, DS, TDR, and TDS descriptions align and trace cleanly to one another without contradiction.

14. `跨层-异常处理与边界条件` - 7
    Derived from superpowers emphasis on ambiguity control, error handling, and testing.
    Check whether invalid input, failures, edge cases, rollback, timeout, conflict, or logging expectations are covered.

## Scoring Guidance

Use evidence-based tiering:

- `Excellent`: 90% to 100% of the dimension weight
  The document addresses the dimension directly, concretely, and with little ambiguity.

- `Good`: 70% to 89%
  The document addresses the dimension but still leaves moderate gaps.

- `Fair`: 40% to 69%
  The document partially addresses the dimension or implies it weakly.

- `Poor`: 10% to 39%
  The document barely addresses the dimension.

- `Missing`: 0%
  No reliable evidence.

## Common Negative Signals

- only slogan-like statements with no conditions or scope
- broad "support X" language without behavior detail
- "etc." or "相关" or "完整" without enumeration
- no scenario but detailed technical action
- no user value but heavy technical wording
- no test points or verification method
- no edge cases, invalid input handling, or failure behavior
- references to standards without mapping requirement-to-standard behavior

## Common Positive Signals

- explicit actor, trigger, and scenario
- user problem and business value are stated
- parameters, allowed ranges, units, defaults, and requiredness are explicit
- system behavior is broken into normal flow and exceptional flow
- acceptance criteria or test points are directly derivable
- security, logging, compliance, and audit expectations are written down
- assumptions and dependencies are explicit
- OR and DR content reinforce rather than contradict each other
