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
- message: `评估依赖模型处理，系统正在生成分析结果。页面将每 30 秒自动刷新，请耐心等待。`

The message may mention the current state, but the layout must remain the same.

### Waiting Card Visual Rules

The waiting card is a formal centered status card inside the `评估结论` area.

Required elements:

- light status mark
- status title
- one-paragraph processing explanation
- integrated refresh-countdown module

The refresh countdown module belongs inside the waiting card rather than in a separate floating overlay.

It should contain:

- a circular countdown indicator
- remaining seconds in the center
- a short status-refresh label
- a short explanation that the platform will refresh automatically

This card should feel calm and premium rather than technical or dashboard-like.

## Polling Rules

The detail page polls every:

- `30s`

Polling starts when the page is in:

- `pending`
- `running`

Polling stops when the page reaches:

- `succeeded`
- `failed`

No shorter cadence should be used unless the interaction design is revisited.

### Polling Update Scope

When a polling response returns a new task state, all state-dependent areas on the page must update together.

This includes at least:

- the `任务信息` section status card
- the `评估结论` section waiting card, success content, or failure card
- report download action visibility
- success-state layered reveal trigger

The page must not update only the conclusion area while leaving the task-information status stale.

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

### Failure Card Visual Rules

The failure card is shown in the same `评估结论` position as the waiting card.

Required elements:

- failure status mark
- failure title
- brief recovery-oriented explanation
- structured error-description block
- primary retry entry
- secondary return-home entry

The failure card should remain formal and product-oriented. It should explain the failure without turning the page into a raw technical error dump.

### Recovery Entry Rules

`重新发起评估` should clearly represent a fresh evaluation action.

Approved behavior:

- it does not navigate the user back to the upload page first
- it sends a retry request from the detail page context
- it is only valid for evaluations whose current backend status is `failed`
- on success, the frontend navigates directly to the newly created evaluation detail route
- the page then re-enters the waiting state flow with the same stable result-page skeleton

Approved backend integration:

- `POST /api/evaluations/{evaluation_id}/retry`

The retry endpoint creates a new evaluation task from the original uploaded file associated with the failed task. It must reject non-failed tasks rather than silently reusing or restarting active/completed work.

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

## State Card Consistency

The waiting card and failure card should use closely matched outer dimensions and spacing.

Required consistency:

- similar outer width
- similar padding
- similar corner radius
- similar visual weight

Reason:

- reduce visible layout jump when switching between waiting and failed states
- preserve page stability during state changes

## Final Approved Decisions

- the detail page polls every `30s`
- the waiting card countdown reflects the active polling interval
- the waiting card uses an explicit waiting indicator rather than an ambiguous decorative mark
- `重新发起评估` calls a dedicated retry API from the failed detail page
- only `failed` evaluations are allowed to use the retry API successfully

- initial visible state after task creation is `评估准备中`
- `pending` and `running` use the same waiting-card layout
- waiting-card copy changes with the current state
- the waiting card integrates the countdown module inside the card
- polling stops on `succeeded` or `failed`
- pending/running do not expand report modules
- success content reveals in four layers
- the download button belongs inside the main conclusion card
- failed state shows a failure card with error details and two actions
- waiting and failure cards use closely matched dimensions to reduce layout jump
- the upload page is the homepage return target
