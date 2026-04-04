import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { EvaluationDetailPage } from "./EvaluationDetailPage";


test("renders loading status shell", () => {
  render(
    <MemoryRouter initialEntries={["/evaluations/eval_123"]}>
      <Routes>
        <Route path="/evaluations/:evaluationId" element={<EvaluationDetailPage />} />
      </Routes>
    </MemoryRouter>,
  );
  expect(screen.getByText(/evaluation status/i)).toBeInTheDocument();
});
