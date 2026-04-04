import { render, screen } from "@testing-library/react";

import App from "../App";


test("renders upload route shell", () => {
  render(<App />);
  expect(screen.getByText(/requirements evaluator/i)).toBeInTheDocument();
});
