# Recommended Prompt

Use this pattern when invoking the skill on a batch of requirement rows:

```text
Use $requirements-evaluator at <skill-path>.

Read the requirement review packet at <packet-path>.
Use the rubric defined in <skill-path>/SKILL.md as the primary scoring basis.
Read the report template at <skill-path>/references/report-template.md.
If needed, read the model review workflow at <skill-path>/references/model-review-workflow.md.
If a custom dimensions file exists and the user explicitly wants it considered, use it only as a supplement.

Evaluate the requirements with the model, not with deterministic scripting.
Output a Chinese Markdown report.
For each requirement:
- give a weighted score and grade
- cite concrete evidence from the row
- list red flags
- list missing items
- give prioritized revision advice

Then summarize cross-requirement weaknesses, strongest examples, and whether the set is ready for implementation and testing.
```

Shorter variant:

```text
Use $requirements-evaluator to review <packet-path> and output the final Chinese evaluation report.
Use the packet as evidence, the rubric as scoring rules, and the template as the report structure.
```
