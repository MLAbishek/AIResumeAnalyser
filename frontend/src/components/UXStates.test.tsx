import {
  cleanup,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import {
  afterEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";
import {
  EmptyState,
  ErrorState,
  LoadingState,
  ValidationMessage,
} from "./UXStates";

afterEach(()=>{
    cleanup()
});

describe("Global UX States", () => {
  it("renders loading state", () => {
    render(
      <LoadingState message="Loading candidates..." />,
    );

    expect(
      screen.getByRole("status")
        .textContent,
    ).toContain("Loading candidates...");
  });

  it("renders empty state", () => {
    render(
      <EmptyState
        title="No candidates"
        message="No candidates were found."
      />,
    );

    expect(
      screen.getByRole("status")
        .textContent,
    ).toContain("No candidates were found.");
  });

  it("renders error state and retries", () => {
    const retry = vi.fn();

    render(
      <ErrorState
        message="Failed to load candidates."
        onRetry={retry}
      />,
    );

    expect(
      screen.getByRole("alert")
        .textContent,
    ).toContain("Failed to load candidates.");

    fireEvent.click(
      screen.getByRole("button", {
        name: "Retry",
      }),
    );

    expect(retry).toHaveBeenCalledTimes(1);
  });

  it("renders validation message", () => {
    render(
      <ValidationMessage message="Please select a job." />,
    );

    expect(
      screen.getByRole("alert")
        .textContent,
    ).toContain("Please select a job.");
  });
});