import { fireEvent, render, screen } from "@testing-library/react";

import App from "../App";


test("renders upload route shell", () => {
  render(<App />);
  expect(screen.getByText(/requirements evaluator/i)).toBeInTheDocument();
});


test("shows validation when no file is selected", async () => {
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: /start evaluation/i }));
  expect(await screen.findByText(/select a file/i)).toBeInTheDocument();
});
