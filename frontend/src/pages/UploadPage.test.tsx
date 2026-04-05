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

  fireEvent.change(screen.getByLabelText("Requirement File"), {
    target: { files: [file] },
  });
  fireEvent.click(screen.getByRole("button", { name: "Start Evaluation" }));

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
