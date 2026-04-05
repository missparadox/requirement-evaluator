import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
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

  expect(await screen.findByText("评估进行中")).toBeInTheDocument();
  expect(screen.getByText("系统将在 20 秒后刷新最新状态")).toBeInTheDocument();
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

  expect(await screen.findByText("评估失败")).toBeInTheDocument();
  expect(screen.getByText("后端服务不可用")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "重新发起评估" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "返回首页" })).toBeInTheDocument();
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

  expect(await screen.findByText("评估已完成")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "下载评估报告" }));
  expect(downloadMarkdown).toHaveBeenCalledWith("eval_123.md", "# 标题\n\n总体评分：92\n\n报告内容");
  expect(screen.getByText("总体评分")).toBeInTheDocument();
  expect(screen.getAllByText("摘要结论").length).toBeGreaterThan(0);
  expect(screen.getByText("详细报告").closest("section")).toHaveTextContent("报告内容");
  expect(screen.getByText("92")).toBeInTheDocument();
});
