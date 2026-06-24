# Shard Output TSV Schema

The model must output TSV only. Do not output Markdown, explanations, bullet lists, JSON, CSV, code fences, or a summary paragraph.

The first line must be this exact header:

```tsv
or_id	or_name	total_score	or_score	dr_average_score	traceability_score	or_user_language_score	or_scenario_score	or_user_value_score	or_constraints_score	dr_security_score	dr_technical_score	dr_testability_score	dr_ambiguity_score	dr_exception_score	cross_scope_score	cross_dependencies_score	cross_traceability_score	grade	weak_dimensions	red_flags	missing_items	revision_actions	evidence_summary
```

Each following line must evaluate exactly one OR from the current shard.

## Columns

- `or_id`: OR identifier. Must exactly match one `expected_or_ids` value in the shard JSON.
- `or_name`: OR name from the shard.
- `total_score`: integer or decimal from 0 to 100.
- `or_score`: integer or decimal from 0 to 40.
- `dr_average_score`: integer or decimal from 0 to 40.
- `traceability_score`: integer or decimal from 0 to 20.
- `or_user_language_score`: integer or decimal from 0 to 12.
- `or_scenario_score`: integer or decimal from 0 to 12.
- `or_user_value_score`: integer or decimal from 0 to 10.
- `or_constraints_score`: integer or decimal from 0 to 6.
- `dr_security_score`: integer or decimal from 0 to 5.
- `dr_technical_score`: integer or decimal from 0 to 10.
- `dr_testability_score`: integer or decimal from 0 to 10.
- `dr_ambiguity_score`: integer or decimal from 0 to 8.
- `dr_exception_score`: integer or decimal from 0 to 7.
- `cross_scope_score`: integer or decimal from 0 to 7.
- `cross_dependencies_score`: integer or decimal from 0 to 6.
- `cross_traceability_score`: integer or decimal from 0 to 7.
- `grade`: one of `excellent`, `good`, `fair`, `poor`.
- `weak_dimensions`: weak dimensions separated by semicolons. Use `无` when none.
- `red_flags`: red-flag issues separated by semicolons. Use `无` when none.
- `missing_items`: missing items separated by semicolons. Use `无` when none.
- `revision_actions`: concrete revision actions separated by semicolons. Use `无` when none.
- `evidence_summary`: concise Chinese evidence summary. Keep it under 200 Chinese characters.

## Score Rules

- `total_score` must equal `or_score + dr_average_score + traceability_score`.
- `or_score` must equal `or_user_language_score + or_scenario_score + or_user_value_score + or_constraints_score`.
- `dr_average_score` must equal `dr_security_score + dr_technical_score + dr_testability_score + dr_ambiguity_score + dr_exception_score`.
- `traceability_score` must equal `cross_scope_score + cross_dependencies_score + cross_traceability_score`.
- `or_score` must be within 0-40.
- `dr_average_score` must be within 0-40.
- `traceability_score` must be within 0-20.
- `total_score` must be within 0-100.
- Use `excellent` for scores >= 90.
- Use `good` for scores >= 75 and < 90.
- Use `fair` for scores >= 60 and < 75.
- Use `poor` for scores < 60.

## Example

```tsv
or_id	or_name	total_score	or_score	dr_average_score	traceability_score	or_user_language_score	or_scenario_score	or_user_value_score	or_constraints_score	dr_security_score	dr_technical_score	dr_testability_score	dr_ambiguity_score	dr_exception_score	cross_scope_score	cross_dependencies_score	cross_traceability_score	grade	weak_dimensions	red_flags	missing_items	revision_actions	evidence_summary
OR-001	登录认证	72	28	31	13	9	7	8	4	4	8	7	6	6	5	4	4	fair	DR-异常描述;DR-可测试性	缺少异常路径	验收条件;边界条件	补充失败场景;补充验收标准	需求有基本技术描述，但缺少异常和验收闭环。
OR-002	权限校验	81	32	34	15	10	9	8	5	4	9	8	7	6	5	5	5	good	OR-约束和限制	无	边界条件	补充权限边界和失败响应	权限行为较清楚，但约束边界仍不完整。
```
