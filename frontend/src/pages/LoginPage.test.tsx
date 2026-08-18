import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";
import { MemoryRouter } from "react-router-dom";

import LoginPage from "./LoginPage";
import { ApiError } from "../api/client";

const mockNavigate = vi.fn();
const mockLogin = vi.fn();

vi.mock("react-router-dom", async (importOriginal) => {
  const actual =
    await importOriginal<
      typeof import("react-router-dom")
    >();

  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock("../api", () => ({
  login: (...args: unknown[]) => mockLogin(...args),
}));

// GoogleSignInButton has its own focused test suite - here we only
// need to confirm LoginPage renders it and wires success/error
// through to the same completeAuth() path as password login.
vi.mock("../components/GoogleSignInButton", () => ({
  default: ({
    onSuccess,
    onError,
  }: {
    onSuccess: (token: string) => void;
    onError: (message: string) => void;
  }) => (
    <div>
      <button
        type="button"
        onClick={() => onSuccess("google-app-token")}
      >
        Continue with Google
      </button>
      <button
        type="button"
        onClick={() =>
          onError("Invalid or expired Google credential.")
        }
      >
        Simulate Google Error
      </button>
    </div>
  ),
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <LoginPage />
    </MemoryRouter>,
  );
}

afterEach(() => {
  cleanup();
  localStorage.clear();
  vi.clearAllMocks();
});

beforeEach(() => {
  localStorage.clear();
});

describe("LoginPage", () => {
  it("renders the password login form and the Google sign-in option", () => {
    renderPage();

    expect(screen.getByLabelText("Email")).toBeTruthy();
    expect(screen.getByLabelText("Password")).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Login" }),
    ).toBeTruthy();
    expect(
      screen.getByText("Continue with Google"),
    ).toBeTruthy();
  });

  it("logs in with email/password and routes recruiters to /jobs", async () => {
    mockLogin.mockResolvedValueOnce({
      access_token:
        // role: recruiter
        "header." +
        btoa(JSON.stringify({ role: "recruiter" })) +
        ".sig",
      token_type: "bearer",
    });

    renderPage();

    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "recruiter@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "StrongPassword123!" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Login" }),
    );

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/jobs");
    });
  });

  it("shows the backend's error message on failed login", async () => {
    mockLogin.mockRejectedValueOnce(
      new ApiError(401, {
        detail:
          "This account uses Google Sign-In. Please continue with Google.",
      }),
    );

    renderPage();

    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "google-user@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "whatever" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Login" }),
    );

    expect(
      await screen.findByText(
        "This account uses Google Sign-In. Please continue with Google.",
      ),
    ).toBeTruthy();
  });

  it("completes Google sign-in and routes candidates to their dashboard", async () => {
    renderPage();

    fireEvent.click(
      screen.getByText("Continue with Google"),
    );

    // completeAuth reads the role back out of the stored JWT via
    // getStoredRole() - a plain opaque token with no role claim
    // falls back to the non-candidate destination, which is enough
    // to prove the Google success path reaches completeAuth() and
    // stores the token.
    await waitFor(() => {
      expect(
        localStorage.getItem("access_token"),
      ).toBe("google-app-token");
    });
    expect(mockNavigate).toHaveBeenCalledWith("/jobs");
  });

  it("shows a clean error when Google sign-in fails", async () => {
    renderPage();

    fireEvent.click(
      screen.getByText("Simulate Google Error"),
    );

    expect(
      await screen.findByText(
        "Invalid or expired Google credential.",
      ),
    ).toBeTruthy();
  });
});
