# Detail Page State Interaction Design

## Scope

This document finalizes the status-driven interaction rules for the evaluation detail page.

In scope:

- first-load state behavior
- pending, running, succeeded, and failed state presentation
- polling cadence and stop conditions
- success-state reveal order
- failure-state recovery entry points

Out of scope:

- visual redesign of page structure
- backend task orchestration changes
- exact implementation details for React hooks or API adapters

## Shared Principles

The detail page is a result page with stable structure.

Rules:

- the page skeleton should remain stable across status changes
- `任务信息` remains visible in every state
- `评估结论` section title remains visible in every state
- the page should not jump between unrelated layouts while the task progresses

The detail page should feel calm, formal, and predictable rather than animated for its own sake.

## Status Labels

Approved Chinese status labels:

- `pending` → `评估准备中`
- `running` → `评估进行中`
- `succeeded` → `评估已完成`
- `failed` → `评估失败`

These labels should be used consistently in the result page UI.

## Initial Load Behavior

When the user enters the detail page immediately after task creation, the default visible status is:

- `pending`
- label: `评估准备中`

This is the expected first state before the system transitions to running or completion.

## Pending and Running States

### Structure

`pending` and `running` share the same waiting-card layout.

Visible elements:

- page header
- `任务信息`
- `评估结论` divider title
- a single waiting card inside the conclusion area

Hidden or not yet expanded:

- main conclusion content
- score and suggested-state cards
- risk, action, and explanation cards
- final summary block
- report download action

### Waiting Card Rules

The waiting card keeps the same layout for both states and only changes:

- status title
- supporting message

Approved state-specific copy:

#### Pending

- title: `评估准备中`
- message: `评估任务已创建，系统正在准备分析所需内容。结果将自动刷新，请稍候。`

#### Running

- title: `评估进行中`
- message: `评估依赖模型处理，系统正在生成分析结果。页面将每 20 秒自动刷新，请耐心等待。`

The message may mention the current state, but the layout must remain the same.

## Polling Rules

The detail page polls every:

- `20s`

Polling starts when the page is in:

- `pending`
- `running`

Polling stops when the page reaches:

- `succeeded`
- `failed`

No shorter cadence should be used unless the interaction design is revisited.

## Succeeded State

### General Rule

When the task reaches `succeeded`, the waiting card is replaced by the full result content.

### Reveal Pattern

Success content should reveal in layers rather than appearing all at once.

Approved reveal order:

1. main conclusion card
2. `总体评分` and `建议状态`
3. `核心风险`、`优先动作`、`评估说明`
4. `摘要结论`

This sequence ensures the user sees the most important judgment first, then the supporting signals, then the detailed summary structure.

### Download Action

The report download action belongs to the conclusion module, not the page header.

Approved placement:

- inside the main conclusion card
- top-right position within that card

Reason:

- it is a result-consumption action, not a page-level navigation action
- it should remain visually attached to the result content
- it should not create an empty gap between the section divider and the main conclusion card

## Failed State

### Structure

When the task reaches `failed`:

- keep the overall detail page structure
- keep `任务信息` visible
- keep the `评估结论` section visible
- do not expand the normal success content

Instead, show a failure card in the conclusion area.

### Failure Card Content

The failure card contains:

- status title: `评估失败`
- error explanation
- `重新发起评估` entry
- `回到上传页面` entry

The upload page is treated as the service homepage.

### Recovery Entry Rules

`重新发起评估` should clearly represent a fresh evaluation action.

`回到上传页面` should navigate the user back to the homepage upload screen.

## Content Stability Rules

The detail page should not behave like a report viewer before the result exists.

Rules:

- pending/running states keep the structure but suppress result modules
- succeeded state reveals the result progressively
- failed state replaces the result modules with a recovery-oriented failure card

This creates clear expectations:

- before completion: waiting
- after success: result
- after failure: recovery

## Final Approved Decisions

- initial visible state after task creation is `评估准备中`
- `pending` and `running` use the same waiting-card layout
- waiting-card copy changes with the current state
- the detail page polls every `20s`
- polling stops on `succeeded` or `failed`
- pending/running do not expand report modules
- success content reveals in four layers
- the download button belongs inside the main conclusion card
- failed state shows a failure card with error details and two actions
- the upload page is the homepage return target
