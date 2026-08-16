import { render, screen } from "@testing-library/react";

import App from "./App";

describe("Application", () => {
  it("renders the dashboard", async () => {
    render(<App />);

    expect(
      await screen.findByRole("heading", {
        name: "Dashboard",
      }),
    ).toBeInTheDocument();
  });
});