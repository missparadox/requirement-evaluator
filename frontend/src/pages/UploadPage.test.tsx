import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useParams } from "react-router-dom";
import { afterEach } from "vitest";
import { vi } from "vitest";

import { UploadPage } from "./UploadPage";


function EvaluationDestination() {
  const { evaluationId } = useParams();

  return <p>evaluation destination: {evaluationId}</p>;
}


afterEach(() => {
  vi.unstubAllGlobals();
});

test("submitting a selected file posts an evaluation request", async () => {
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
      <Routes>
        <Route path="/" element={<UploadPage />} />
        <Route path="/evaluations/:evaluationId" element={<EvaluationDestination />} />
      </Routes>
    </MemoryRouter>,
  );

  expect(screen.getByRole("heading", { name: "需求评估平台" })).toBeInTheDocument();
  expect(screen.getByText("Requirements Evaluation Suite")).toBeInTheDocument();
  expect(screen.getByText("阶段 01")).toBeInTheDocument();
  expect(screen.getByText("阶段 02")).toBeInTheDocument();
  expect(screen.getByText("阶段 03")).toBeInTheDocument();
  expect(screen.getByText("评估文件上传")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "选择文件" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "开始评估" })).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText("评估文件上传"), {
    target: { files: [file] },
  });
  fireEvent.click(screen.getByRole("button", { name: "开始评估" }));

  await waitFor(() => {
    expect(fetchMock).toHaveBeenCalled();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/evaluations",
      expect.objectContaining({
        method: "POST",
        body: expect.any(FormData),
      }),
    );
  });

  expect(await screen.findByText("evaluation destination: eval_123")).toBeInTheDocument();
});
