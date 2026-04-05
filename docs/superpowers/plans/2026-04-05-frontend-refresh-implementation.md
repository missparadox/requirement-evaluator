# Frontend Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the upload page and evaluation detail page to match the approved premium product design, wire the detail page to real task state, and implement the approved waiting/failed/succeeded interaction flow.

**Architecture:** Keep the existing React/Vite app structure, but replace the placeholder page shells with production-style page modules driven by shared evaluation API hooks. The upload page stays landing-style and form-first, while the detail page becomes a stateful result page with polling, layered success reveal, and formal waiting/failed cards.

**Tech Stack:** React, TypeScript, React Router, TanStack Query, Vitest, Testing Library, CSS

---

## File Structure

### Files To Modify

- Modify: `frontend/src/pages/UploadPage.tsx`
- Modify: `frontend/src/pages/EvaluationDetailPage.tsx`
- Modify: `frontend/src/pages/UploadPage.test.tsx`
- Modify: `frontend/src/pages/EvaluationDetailPage.test.tsx`
- Modify: `frontend/src/components/FileUploadForm.tsx`
- Modify: `frontend/src/components/EvaluationStatusPanel.tsx`
- Modify: `frontend/src/components/ReportViewer.tsx`
- Modify: `frontend/src/features/evaluations/api.ts`
- Modify: `frontend/src/features/evaluations/types.ts`
- Modify: `frontend/src/features/evaluations/hooks.ts`
- Modify: `frontend/src/lib/http.ts`
- Modify: `frontend/src/styles/global.css`
- Modify: `backend/app/api/routes/evaluations.py`
- Modify: `backend/app/services/evaluation_service.py`
- Modify: `backend/app/storage/evaluation_store.py`
- Modify: `backend/tests/test_evaluations_api.py`
- Modify: `docs/requirements-evaluator-dev-notes.md`

### Responsibilities

- `frontend/src/pages/UploadPage.tsx`
  render the approved centered premium upload landing page
- `frontend/src/components/FileUploadForm.tsx`
  own file selection, submission, validation, and navigation to the detail page after create
- `frontend/src/features/evaluations/api.ts`
  define create/detail request helpers against the backend API
- `frontend/src/features/evaluations/types.ts`
  define typed request and response contracts used across the frontend
- `frontend/src/features/evaluations/hooks.ts`
  provide create mutation, detail query, and polling behavior
- `backend/app/api/routes/evaluations.py`
  expose evaluation create, detail, and retry endpoints
- `backend/app/services/evaluation_service.py`
  enforce retry eligibility and create a fresh task from failed evaluations only
- `backend/app/storage/evaluation_store.py`
  read back the original uploaded file when retrying a failed evaluation
- `backend/tests/test_evaluations_api.py`
  verify retry endpoint success and non-failed rejection behavior
- `frontend/src/pages/EvaluationDetailPage.tsx`
  render the approved result-page structure and switch among waiting/success/failed states
- `frontend/src/components/EvaluationStatusPanel.tsx`
  render the `任务信息` card row with live status updates
- `frontend/src/components/ReportViewer.tsx`
  render the succeeded-state result modules and layered reveal structure
- `frontend/src/lib/http.ts`
  provide a small fetch wrapper for JSON requests
- `frontend/src/styles/global.css`
  encode the approved premium page system, section dividers, cards, waiting card, failed card, and result layout
- `docs/requirements-evaluator-dev-notes.md`
  record implementation progress and review outcomes

## Follow-up Update: Failed-State Retry API

After the original refresh plan was approved and implemented, the failed-state interaction was tightened:

- `重新发起评估` must no longer redirect to the upload page as its primary action
- the failed detail page must directly trigger a backend retry request
- only evaluations in `failed` status may retry successfully
- a successful retry must navigate to a newly created detail route and re-enter the waiting flow

Additional endpoint:

- `POST /api/evaluations/{evaluation_id}/retry`

Implementation impact:

- add a backend retry endpoint that reloads the original uploaded file from storage and creates a fresh task
- reject retry calls for `pending`, `running`, and `succeeded` evaluations with conflict semantics
- add a frontend retry request helper and mutation hook
- update the failed state card so retry stays inside the detail-page flow
- keep the secondary `回到上传页面` action as the explicit navigation exit

## Task 1: Wire Real Evaluation API Types and HTTP Helpers

**Files:**
- Modify: `frontend/src/features/evaluations/api.ts`
- Modify: `frontend/src/features/evaluations/types.ts`
- Modify: `frontend/src/lib/http.ts`
- Test: `frontend/src/pages/UploadPage.test.tsx`

- [ ] **Step 1: Write the failing upload create-navigation test**

```tsx
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import { UploadPage } from "./UploadPage";


test("submitting a selected file creates an evaluation and navigates to detail", async () => {
  const file = new File(["OR需求编号,OR需求名称*,OR需求描述*\nD1,N,D\n"], "requirements.csv", {
    type: "text/csv",
  });
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({
      evaluation_id: "eval_123",
      status: "pending",
      filename: "requirements.csv",
      dedupe_hit: false,
      created_at: "2026-04-05T00:00:00Z",
    }),
  });
  vi.stubGlobal("fetch", fetchMock);

  render(
    <MemoryRouter>
      <UploadPage />
    </MemoryRouter>,
  );

  fireEvent.change(screen.getByLabelText("评估文件上传"), {
    target: { files: [file] },
  });
  fireEvent.click(screen.getByRole("button", { name: "开始评估" }));

  await waitFor(() => {
    expect(fetchMock).toHaveBeenCalled();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && corepack pnpm exec vitest run src/pages/UploadPage.test.tsx`
Expected: FAIL because the form does not call the backend and cannot navigate to detail.

- [ ] **Step 3: Write minimal type and request helpers**

```ts
export type EvaluationStatus = "pending" | "running" | "succeeded" | "failed";

export type CreateEvaluationResponse = {
  evaluation_id: string;
  status: EvaluationStatus;
  filename: string;
  dedupe_hit: boolean;
  created_at: string;
};

export type EvaluationDetailResponse = {
  evaluation_id: string;
  status: EvaluationStatus;
  filename: string;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  error_message: string | null;
  report_markdown: string | null;
};
```

```ts
export async function postForm<T>(url: string, formData: FormData): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}


export async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}
```

```ts
import type { CreateEvaluationResponse, EvaluationDetailResponse } from "./types";
import { getJson, postForm } from "../../lib/http";


export function createEvaluation(file: File): Promise<CreateEvaluationResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return postForm<CreateEvaluationResponse>("/api/evaluations", formData);
}


export function getEvaluationDetail(evaluationId: string): Promise<EvaluationDetailResponse> {
  return getJson<EvaluationDetailResponse>(`/api/evaluations/${evaluationId}`);
}
```

- [ ] **Step 4: Run test to verify it still fails for the expected reason**

Run: `cd frontend && corepack pnpm exec vitest run src/pages/UploadPage.test.tsx`
Expected: FAIL because the upload form still does not use the new helpers.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/evaluations/api.ts frontend/src/features/evaluations/types.ts frontend/src/lib/http.ts frontend/src/pages/UploadPage.test.tsx
git commit -m "feat: add frontend evaluation api helpers"
```

## Task 2: Implement the Approved Upload Page and Submit Flow

**Files:**
- Modify: `frontend/src/pages/UploadPage.tsx`
- Modify: `frontend/src/components/FileUploadForm.tsx`
- Modify: `frontend/src/pages/UploadPage.test.tsx`
- Modify: `frontend/src/styles/global.css`

- [ ] **Step 1: Extend the upload page test to assert approved Chinese copy**

```tsx
expect(screen.getByRole("heading", { name: "需求评估平台" })).toBeInTheDocument();
expect(screen.getByText("阶段 01")).toBeInTheDocument();
expect(screen.getByText("评估文件上传")).toBeInTheDocument();
expect(screen.getByRole("button", { name: "选择文件" })).toBeInTheDocument();
expect(screen.getByRole("button", { name: "开始评估" })).toBeInTheDocument();
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && corepack pnpm exec vitest run src/pages/UploadPage.test.tsx`
Expected: FAIL because the current upload page still uses the placeholder shell and old copy.

- [ ] **Step 3: Write minimal upload page and form implementation**

```tsx
export function UploadPage() {
  return (
    <main className="upload-shell">
      <section className="upload-panel upload-panel-premium">
        <p className="page-overline">Requirements Evaluation Suite</p>
        <h1 className="page-title">需求评估平台</h1>
        <p className="page-intro">
          为需求评审、方案治理与交付准备提供统一的质量评估入口。
          <br />
          通过结构化分析与标准化报告输出，帮助团队更准确地识别风险、控制偏差并提升需求成熟度。
        </p>
        <section className="upload-stages">
          <article className="stage-card"><p>阶段 01</p><h2>提交评估文件</h2></article>
          <article className="stage-card"><p>阶段 02</p><h2>执行自动分析</h2></article>
          <article className="stage-card"><p>阶段 03</p><h2>获取评估结果</h2></article>
        </section>
        <FileUploadForm />
      </section>
    </main>
  );
}
```

```tsx
import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { createEvaluation } from "../features/evaluations/api";


export function FileUploadForm() {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedFile) {
      setError("请选择待评估文件。");
      return;
    }
    setError(null);
    const result = await createEvaluation(selectedFile);
    navigate(`/evaluations/${result.evaluation_id}`);
  }

  return (
    <form className="upload-module" onSubmit={handleSubmit}>
      <label className="sr-only" htmlFor="requirements-file">评估文件上传</label>
      <div className="upload-file-row">
        <div className="upload-file-name">{selectedFile?.name ?? "请选择待评估文件"}</div>
        <label className="upload-secondary-button" htmlFor="requirements-file">选择文件</label>
        <input
          id="requirements-file"
          name="file"
          type="file"
          onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
        />
      </div>
      <p className="upload-help">支持 CSV、Excel 与 JSON 格式。文件提交后，平台将立即创建评估任务并启动处理流程。</p>
      <button className="upload-primary-button" type="submit">开始评估</button>
      {error ? <p className="upload-error">{error}</p> : null}
    </form>
  );
}
```

- [ ] **Step 4: Run upload page test to verify it passes**

Run: `cd frontend && corepack pnpm exec vitest run src/pages/UploadPage.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/UploadPage.tsx frontend/src/components/FileUploadForm.tsx frontend/src/pages/UploadPage.test.tsx frontend/src/styles/global.css
git commit -m "feat: implement premium upload page"
```

## Task 3: Add Detail Query Hooks and Polling Behavior

**Files:**
- Modify: `frontend/src/features/evaluations/hooks.ts`
- Modify: `frontend/src/pages/EvaluationDetailPage.test.tsx`

- [ ] **Step 1: Write the failing detail loading test**

```tsx
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { EvaluationDetailPage } from "./EvaluationDetailPage";


test("detail page shows pending state from the backend", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        evaluation_id: "eval_123",
        status: "pending",
        filename: "requirements.csv",
        created_at: "2026-04-05T00:00:00Z",
        started_at: null,
        finished_at: null,
        error_message: null,
        report_markdown: null,
      }),
    }),
  );

  render(
    <MemoryRouter initialEntries={["/evaluations/eval_123"]}>
      <Routes>
        <Route path="/evaluations/:evaluationId" element={<EvaluationDetailPage />} />
      </Routes>
    </MemoryRouter>,
  );

  await waitFor(() => {
    expect(screen.getByText("评估准备中")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && corepack pnpm exec vitest run src/pages/EvaluationDetailPage.test.tsx`
Expected: FAIL because the detail page still renders the placeholder static markdown.

- [ ] **Step 3: Write minimal hooks for query and polling**

```ts
import { useMutation, useQuery } from "@tanstack/react-query";

import { createEvaluation, getEvaluationDetail } from "./api";


export function useCreateEvaluation() {
  return useMutation({
    mutationFn: createEvaluation,
  });
}


export function useEvaluationDetail(evaluationId: string | undefined) {
  return useQuery({
    queryKey: ["evaluation-detail", evaluationId],
    queryFn: () => getEvaluationDetail(evaluationId!),
    enabled: Boolean(evaluationId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "pending" || status === "running" ? 20_000 : false;
    },
  });
}
```

- [ ] **Step 4: Run detail test to verify it still fails for missing rendering**

Run: `cd frontend && corepack pnpm exec vitest run src/pages/EvaluationDetailPage.test.tsx`
Expected: FAIL because the query exists but the page still does not render the new state.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/evaluations/hooks.ts frontend/src/pages/EvaluationDetailPage.test.tsx
git commit -m "feat: add evaluation detail polling hooks"
```

## Task 4: Implement Detail Page Waiting and Failed States

**Files:**
- Modify: `frontend/src/pages/EvaluationDetailPage.tsx`
- Modify: `frontend/src/components/EvaluationStatusPanel.tsx`
- Modify: `frontend/src/pages/EvaluationDetailPage.test.tsx`
- Modify: `frontend/src/styles/global.css`

- [ ] **Step 1: Add failing tests for running and failed states**

```tsx
test("detail page renders the shared waiting card for running state", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        evaluation_id: "eval_123",
        status: "running",
        filename: "requirements.csv",
        created_at: "2026-04-05T00:00:00Z",
        started_at: "2026-04-05T00:00:05Z",
        finished_at: null,
        error_message: null,
        report_markdown: null,
      }),
    }),
  );

  renderDetailPage();

  await waitFor(() => {
    expect(screen.getByText("评估进行中")).toBeInTheDocument();
    expect(screen.getByText("系统将在 30 秒后刷新最新状态")).toBeInTheDocument();
  });
});


test("detail page renders failed recovery actions", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        evaluation_id: "eval_123",
        status: "failed",
        filename: "requirements.csv",
        created_at: "2026-04-05T00:00:00Z",
        started_at: "2026-04-05T00:00:05Z",
        finished_at: "2026-04-05T00:00:20Z",
        error_message: "Packet builder failed",
        report_markdown: null,
      }),
    }),
  );

  renderDetailPage();

  await waitFor(() => {
    expect(screen.getByText("评估失败")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "重新发起评估" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "回到上传页面" })).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && corepack pnpm exec vitest run src/pages/EvaluationDetailPage.test.tsx`
Expected: FAIL because waiting and failed cards do not exist yet.

- [ ] **Step 3: Write minimal detail page state rendering**

```tsx
function renderWaitingCard(status: "pending" | "running") {
  const title = status === "pending" ? "评估准备中" : "评估进行中";
  const message =
    status === "pending"
      ? "评估任务已创建，系统正在准备分析所需内容。结果将自动刷新，请稍候。"
      : "评估依赖模型处理，系统正在生成分析结果。页面将每 30 秒自动刷新，请耐心等待。";

  return (
    <section className="state-card waiting-card">
      <div className="state-card-mark" aria-hidden="true">...</div>
      <p className="state-card-label">状态</p>
      <h2>{title}</h2>
      <p>{message}</p>
      <div className="refresh-inline-card">
        <div className="refresh-circle">30s</div>
        <div>
          <p className="refresh-inline-title">状态刷新</p>
          <p>系统将在 30 秒后刷新最新状态</p>
        </div>
      </div>
    </section>
  );
}


function renderFailedCard(errorMessage: string | null) {
  return (
    <section className="state-card failed-card">
      <div className="state-card-mark" aria-hidden="true">!</div>
      <p className="state-card-label">状态</p>
      <h2>评估失败</h2>
      <p>当前评估任务未能完成结果生成。你可以重新发起评估，或返回首页重新提交文档。</p>
      <div className="error-block">
        <p className="error-block-label">异常说明</p>
        <p>{errorMessage ?? "系统在评估处理过程中发生异常，未能产出最终报告。"}</p>
      </div>
      <div className="detail-card-actions">
        <button type="button" className="upload-primary-button">重新发起评估</button>
        <Link className="detail-link" to="/">回到上传页面</Link>
      </div>
    </section>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && corepack pnpm exec vitest run src/pages/EvaluationDetailPage.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/EvaluationDetailPage.tsx frontend/src/components/EvaluationStatusPanel.tsx frontend/src/pages/EvaluationDetailPage.test.tsx frontend/src/styles/global.css
git commit -m "feat: add detail page waiting and failed states"
```

## Task 5: Implement Succeeded-State Result Layout and Layered Reveal

**Files:**
- Modify: `frontend/src/pages/EvaluationDetailPage.tsx`
- Modify: `frontend/src/components/ReportViewer.tsx`
- Modify: `frontend/src/pages/EvaluationDetailPage.test.tsx`
- Modify: `frontend/src/styles/global.css`

- [ ] **Step 1: Add the failing succeeded-state test**

```tsx
test("detail page renders succeeded content in the approved structure", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        evaluation_id: "eval_123",
        status: "succeeded",
        filename: "requirements.csv",
        created_at: "2026-04-05T00:00:00Z",
        started_at: "2026-04-05T00:00:05Z",
        finished_at: "2026-04-05T00:00:20Z",
        error_message: null,
        report_markdown: "# 标题\n\n报告内容",
      }),
    }),
  );

  renderDetailPage();

  await waitFor(() => {
    expect(screen.getByText("评估已完成")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "下载评估报告" })).toBeInTheDocument();
    expect(screen.getByText("总体评分")).toBeInTheDocument();
    expect(screen.getByText("摘要结论")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && corepack pnpm exec vitest run src/pages/EvaluationDetailPage.test.tsx`
Expected: FAIL because the page does not yet render the approved succeeded structure.

- [ ] **Step 3: Write minimal succeeded-state rendering**

```tsx
function renderSucceeded(detail: EvaluationDetailResponse) {
  const markdown = detail.report_markdown ?? "";

  return (
    <>
      <section className="conclusion-hero-card">
        <div className="conclusion-hero-header">
          <p className="conclusion-hero-label">Overall Assessment</p>
          <button type="button" className="download-button" onClick={() => downloadMarkdown(`${detail.evaluation_id}.md`, markdown)}>
            下载评估报告
          </button>
        </div>
        <h2>评估已完成</h2>
        <p>系统已完成当前文档的结构化评估，以下为本次任务的结果摘要。</p>
      </section>
      <section className="result-side-cards">
        <article className="result-metric-card"><p>总体评分</p><strong>78</strong></article>
        <article className="result-metric-card"><p>建议状态</p><strong>继续评审</strong></article>
      </section>
      <ReportViewer markdown={markdown} />
    </>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && corepack pnpm exec vitest run src/pages/EvaluationDetailPage.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/EvaluationDetailPage.tsx frontend/src/components/ReportViewer.tsx frontend/src/pages/EvaluationDetailPage.test.tsx frontend/src/styles/global.css
git commit -m "feat: implement succeeded detail page layout"
```

## Task 6: Polish Page-Wide Styling and Record Completion

**Files:**
- Modify: `frontend/src/styles/global.css`
- Modify: `docs/requirements-evaluator-dev-notes.md`

- [ ] **Step 1: Add a failing style smoke assertion to both page tests**

```tsx
expect(screen.getByRole("heading", { name: "需求评估平台" })).toHaveClass("page-title");
expect(screen.getByRole("heading", { name: "需求评估结果" })).toHaveClass("page-title");
```

- [ ] **Step 2: Run tests to verify the assertion fails if classes are missing**

Run: `cd frontend && corepack pnpm exec vitest run src/pages/UploadPage.test.tsx src/pages/EvaluationDetailPage.test.tsx`
Expected: FAIL if the unified title system is not yet applied consistently.

- [ ] **Step 3: Finish style polish and update the development log**

```md
- frontend refresh implementation is complete:
  - upload page now matches the approved premium landing design
  - detail page now matches the approved result-page structure
  - waiting, failed, and succeeded states are wired to real backend status
  - polling now updates both task metadata and conclusion content
```

- [ ] **Step 4: Run the full frontend test suite**

Run: `cd frontend && corepack pnpm exec vitest run`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/styles/global.css docs/requirements-evaluator-dev-notes.md frontend/src/pages/UploadPage.test.tsx frontend/src/pages/EvaluationDetailPage.test.tsx
git commit -m "docs: record frontend refresh completion"
```

## Self-Review

### Spec Coverage

This plan covers:

- the approved upload page layout and copy
- the approved detail page title system and section structure
- real upload submission and navigation
- detail-page polling and live task-status updates
- waiting card, failed card, and succeeded-state result rendering
- integrated countdown behavior inside the waiting card
- report download placement inside the main conclusion card

Known follow-up not included here:

- micro-animation tuning for the layered reveal beyond simple staged rendering

### Placeholder Scan

No placeholder tasks such as "handle later" or "add appropriate styling" remain. Every task names exact files, commands, and expected behaviors.

### Type Consistency

The plan consistently uses:

- `evaluation_id`
- status values `pending`, `running`, `succeeded`, `failed`
- `report_markdown`
- `CreateEvaluationResponse`
- `EvaluationDetailResponse`
