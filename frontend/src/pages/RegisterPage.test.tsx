import {
  cleanup,
  fireEvent,
  render,
  screen,
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

import RegisterPage from "./RegisterPage";
import { ApiError } from "../api/client";

const mockNavigate = vi.fn();
const mockRegisterUser = vi.fn();

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
  registerUser: (
    ...args: unknown[]
  ) => mockRegisterUser(...args),
}));

// GoogleSignInButton has its own focused test suite - here we only
// need to confirm RegisterPage renders it, passes the selected role
// through, and wires its success/error callbacks correctly.
vi.mock("../components/GoogleSignInButton", () => ({
  default: ({
    role,
    onSuccess,
    onError,
  }: {
    role?: string;
    onSuccess: (token: string) => void;
    onError: (message: string) => void;
  }) => (
    <div>
      <button
        type="button"
        onClick={() => onSuccess("google-app-token")}
      >
        Sign up with Google ({role ?? "no role"})
      </button>
      <button
        type="button"
        onClick={() =>
          onError(
            "An account with this email already exists. " +
              "Please sign in with your password instead.",
          )
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
      <RegisterPage />
    </MemoryRouter>,
  );
}

function fillForm({
  email = "new-user@example.com",
  password = "StrongPassword123!",
  confirmPassword = "StrongPassword123!",
}: {
  email?: string;
  password?: string;
  confirmPassword?: string;
} = {}) {
  fireEvent.change(
    screen.getByLabelText("Email"),
    { target: { value: email } },
  );

  fireEvent.change(
    screen.getByLabelText("Password"),
    { target: { value: password } },
  );

  fireEvent.change(
    screen.getByLabelText("Confirm Password"),
    { target: { value: confirmPassword } },
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

describe("RegisterPage", () => {
  it("renders the registration form", () => {
    renderPage();

    expect(
      screen.getByRole("heading", {
        name: "Create your account",
      }),
    ).toBeTruthy();

    expect(
      screen.getByLabelText("Email"),
    ).toBeTruthy();
    expect(
      screen.getByLabelText("Password"),
    ).toBeTruthy();
    expect(
      screen.getByLabelText("Confirm Password"),
    ).toBeTruthy();
    expect(
      screen.getByRole("button", {
        name: "Create Account",
      }),
    ).toBeTruthy();
  });

  it("rejects a password shorter than 8 characters without calling the API", () => {
    renderPage();

    fillForm({
      password: "short1",
      confirmPassword: "short1",
    });

    fireEvent.click(
      screen.getByRole("button", {
        name: "Create Account",
      }),
    );

    expect(
      screen.getByText(
        "Password must contain at least 8 characters.",
      ),
    ).toBeTruthy();

    expect(mockRegisterUser).not.toHaveBeenCalled();
  });

  it("rejects mismatched passwords without calling the API", () => {
    renderPage();

    fillForm({
      password: "StrongPassword123!",
      confirmPassword: "DifferentPassword123!",
    });

    fireEvent.click(
      screen.getByRole("button", {
        name: "Create Account",
      }),
    );

    expect(
      screen.getByText("Passwords do not match."),
    ).toBeTruthy();

    expect(mockRegisterUser).not.toHaveBeenCalled();
  });

  it("submits only email and password to the API and redirects to /login on success", async () => {
    mockRegisterUser.mockResolvedValueOnce({
      id: 1,
      email: "new-user@example.com",
      role: "recruiter",
      is_active: true,
    });

    renderPage();

    fillForm();

    fireEvent.click(
      screen.getByRole("button", {
        name: "Create Account",
      }),
    );

    await vi.waitFor(() => {
      expect(mockRegisterUser).toHaveBeenCalledTimes(1);
    });

    expect(mockRegisterUser).toHaveBeenCalledWith({
      email: "new-user@example.com",
      password: "StrongPassword123!",
      role: "recruiter",
    });

    await vi.waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith(
        "/login",
        { state: { registered: true } },
      );
    });
  });

  it("shows a clean error message when the email is already registered", async () => {
    mockRegisterUser.mockRejectedValueOnce(
      new ApiError(409, {
        detail:
          "An account with this email already exists.",
      }),
    );

    renderPage();

    fillForm();

    fireEvent.click(
      screen.getByRole("button", {
        name: "Create Account",
      }),
    );

    await vi.waitFor(() => {
      expect(
        screen.getByText(
          "An account with this email already exists.",
        ),
      ).toBeTruthy();
    });

    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it("never writes the password to localStorage", async () => {
    mockRegisterUser.mockResolvedValueOnce({
      id: 1,
      email: "new-user@example.com",
      role: "recruiter",
      is_active: true,
    });

    renderPage();

    fillForm();

    fireEvent.click(
      screen.getByRole("button", {
        name: "Create Account",
      }),
    );

    await vi.waitFor(() => {
      expect(mockRegisterUser).toHaveBeenCalledTimes(1);
    });

    const storedValues = Object.values(
      localStorage,
    ).join(" ");

    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);

      if (key) {
        expect(
          localStorage.getItem(key),
        ).not.toContain("StrongPassword123!");
      }
    }

    expect(storedValues).not.toContain(
      "StrongPassword123!",
    );
  });

  it("defaults to the recruiter role and offers a candidate toggle", () => {
    renderPage();

    expect(
      screen.getByRole("radio", { name: /Recruiter/i }),
    ).toHaveProperty("ariaChecked", "true");
    expect(
      screen.getByRole("radio", { name: /Candidate/i }),
    ).toHaveProperty("ariaChecked", "false");
  });

  it("passes the selected role into the Google sign-up button", () => {
    renderPage();

    fireEvent.click(
      screen.getByRole("radio", { name: /Candidate/i }),
    );

    expect(
      screen.getByText("Sign up with Google (candidate)"),
    ).toBeTruthy();
  });

  it("stores the token and redirects after a successful Google sign-up", async () => {
    renderPage();

    fireEvent.click(
      screen.getByText(/Sign up with Google/),
    );

    await vi.waitFor(() => {
      expect(
        localStorage.getItem("access_token"),
      ).toBe("google-app-token");
    });

    // No role claim in this opaque test token, so completeAuth()
    // falls back to the non-candidate destination - proving the
    // Google success path reaches the same redirect logic as
    // password registration's login handoff.
    expect(mockNavigate).toHaveBeenCalledWith("/jobs");
  });

  it("shows a clean error when Google sign-up reports an existing account", async () => {
    renderPage();

    fireEvent.click(
      screen.getByText("Simulate Google Error"),
    );

    expect(
      await screen.findByText(
        "An account with this email already exists. " +
          "Please sign in with your password instead.",
      ),
    ).toBeTruthy();
  });
});
