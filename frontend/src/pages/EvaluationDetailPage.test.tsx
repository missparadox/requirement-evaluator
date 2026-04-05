import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, vi } from "vitest";

import { downloadMarkdown } from "../lib/download";
import { EvaluationDetailPage } from "./EvaluationDetailPage";

vi.mock("../lib/download", () => ({
  downloadMarkdown: vi.fn(),
}));


afterEach(() => {
  vi.unstubAllGlobals();
});

function renderEvaluationDetailPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/evaluations/eval_123"]}>
        <Routes>
          <Route path="/evaluations/:evaluationId" element={<EvaluationDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

test("shows pending backend state for a pending evaluation", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      expect(String(input)).toBe("/api/evaluations/eval_123");

      return new Response(
        JSON.stringify({
          evaluation_id: "eval_123",
          status: "pending",
          filename: "requirements.csv",
          created_at: "2026-04-05T09:00:00Z",
          started_at: null,
          finished_at: null,
          error_message: null,
          report_markdown: null,
        }),
        {
          status: 200,
          headers: {
            "Content-Type": "application/json",
          },
        },
      );
    }),
  );

  renderEvaluationDetailPage();

  expect(await screen.findByText("评估准备中")).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "需求评估结果" })).toHaveClass("page-title");
  expect(screen.getByText("任务信息")).toBeInTheDocument();
  expect(screen.getByText("评估结论")).toBeInTheDocument();
  expect(screen.getByRole("region", { name: "结果概览" })).toBeInTheDocument();
  expect(screen.getByRole("region", { name: "任务信息概览" })).toHaveClass("detail-page-section");
  expect(screen.getByRole("region", { name: "结果概览" })).toHaveClass("detail-page-section");
  expect(screen.getByText("评估编号")).toBeInTheDocument();
  expect(screen.getByText("文件名称")).toBeInTheDocument();
  expect(screen.getByText("任务状态")).toBeInTheDocument();
});

test("shows running backend state for an in-progress evaluation", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => {
      return new Response(
        JSON.stringify({
          evaluation_id: "eval_123",
          status: "running",
          filename: "requirements.csv",
          created_at: "2026-04-05T09:00:00Z",
          started_at: "2026-04-05T09:00:10Z",
          finished_at: null,
          error_message: null,
          report_markdown: null,
        }),
        {
          status: 200,
          headers: {
            "Content-Type": "application/json",
          },
        },
      );
    }),
  );

  renderEvaluationDetailPage();

  expect((await screen.findAllByText("评估进行中")).length).toBeGreaterThan(0);
  expect(screen.getByText("评估依赖模型处理，系统正在生成分析结果。页面将每 20 秒自动刷新，请耐心等待。")).toBeInTheDocument();
});

test("shows failed backend state with retry actions", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => {
      return new Response(
        JSON.stringify({
          evaluation_id: "eval_123",
          status: "failed",
          filename: "requirements.csv",
          created_at: "2026-04-05T09:00:00Z",
          started_at: "2026-04-05T09:00:10Z",
          finished_at: "2026-04-05T09:00:30Z",
          error_message: "后端服务不可用",
          report_markdown: null,
        }),
        {
          status: 200,
          headers: {
            "Content-Type": "application/json",
          },
        },
      );
    }),
  );

  renderEvaluationDetailPage();

  expect((await screen.findAllByText("评估失败")).length).toBeGreaterThan(0);
  expect(screen.getByText("后端服务不可用")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "重新发起评估" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "回到上传页面" })).toBeInTheDocument();
});

test("keeps the page skeleton visible when detail loading fails", async () => {
  vi.stubGlobal("fetch", vi.fn(async () => new Response("boom", { status: 500 })));

  renderEvaluationDetailPage();

  expect(await screen.findByRole("heading", { name: "需求评估结果" })).toBeInTheDocument();
  expect(screen.getByText("任务信息")).toBeInTheDocument();
  expect(screen.getByText("评估结论")).toBeInTheDocument();
  expect(screen.getByText("评估编号")).toBeInTheDocument();
  expect(screen.getByText("任务状态")).toBeInTheDocument();
  expect(await screen.findByRole("button", { name: "重新发起评估" })).toBeInTheDocument();
});

test("shows succeeded backend state in the approved result structure", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => {
      return new Response(
        JSON.stringify({
          evaluation_id: "eval_123",
          status: "succeeded",
          filename: "requirements.csv",
          created_at: "2026-04-05T09:00:00Z",
          started_at: "2026-04-05T09:00:10Z",
          finished_at: "2026-04-05T09:00:30Z",
          error_message: null,
          report_markdown: "# 标题\n\n总体评分：92\n\n报告内容",
        }),
        {
          status: 200,
          headers: {
            "Content-Type": "application/json",
          },
        },
      );
    }),
  );

  renderEvaluationDetailPage();

  expect((await screen.findAllByText("评估已完成")).length).toBeGreaterThan(0);
  fireEvent.click(screen.getByRole("button", { name: "下载评估报告" }));
  expect(downloadMarkdown).toHaveBeenCalledWith("eval_123.md", "# 标题\n\n总体评分：92\n\n报告内容");
  expect(screen.getByText("总体评分")).toBeInTheDocument();
  expect(screen.getByText("建议状态")).toBeInTheDocument();
  expect(screen.queryByText("核心风险")).not.toBeInTheDocument();
  expect(screen.queryByText("优先动作")).not.toBeInTheDocument();
  expect(screen.queryByText("评估说明")).not.toBeInTheDocument();
  expect(screen.queryAllByText("摘要结论")).toHaveLength(0);

  await waitFor(() => {
    expect(screen.getByText("核心风险")).toBeInTheDocument();
    expect(screen.getByText("优先动作")).toBeInTheDocument();
    expect(screen.getByText("评估说明")).toBeInTheDocument();
    expect(screen.getAllByText("摘要结论").length).toBeGreaterThan(0);
  });

  expect(screen.getAllByText("详细报告")[0]?.closest("section")).toHaveTextContent("报告内容");
  expect(screen.getByText("92")).toBeInTheDocument();
});
