import {
  cleanup,
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

import GoogleSignInButton from "./GoogleSignInButton";
import { ApiError } from "../api/client";

const mockGoogleAuth = vi.fn();

vi.mock("../api", () => ({
  googleAuth: (...args: unknown[]) => mockGoogleAuth(...args),
}));

let configured = true;

vi.mock("../lib/googleIdentity", () => ({
  GOOGLE_CLIENT_ID: "test-client-id.apps.googleusercontent.com",
  isGoogleSignInConfigured: () => configured,
  loadGoogleIdentityScript: () => Promise.resolve(),
}));

function setupWindowGoogle() {
  let capturedCallback:
    | ((response: { credential: string }) => void)
    | null = null;

  window.google = {
    accounts: {
      id: {
        initialize: vi.fn((config) => {
          capturedCallback = config.callback;
        }),
        renderButton: vi.fn((container) => {
          const btn = document.createElement("button");
          btn.textContent = "Sign in with Google";
          container.appendChild(btn);
        }),
        prompt: vi.fn(),
        cancel: vi.fn(),
        disableAutoSelect: vi.fn(),
      },
    },
  };

  return {
    triggerCredential: (credential: string) => {
      capturedCallback?.({ credential });
    },
  };
}

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  configured = true;
  delete (window as { google?: unknown }).google;
});

beforeEach(() => {
  configured = true;
});

describe("GoogleSignInButton", () => {
  it("renders the official Google button once the script loads", async () => {
    setupWindowGoogle();

    render(
      <GoogleSignInButton
        onSuccess={vi.fn()}
        onError={vi.fn()}
      />,
    );

    await waitFor(() => {
      expect(
        screen.getByText("Sign in with Google"),
      ).toBeTruthy();
    });
  });

  it("shows an unavailable notice when no client ID is configured", () => {
    configured = false;

    render(
      <GoogleSignInButton
        onSuccess={vi.fn()}
        onError={vi.fn()}
      />,
    );

    expect(
      screen.getByText(
        "Google Sign-In is not configured for this environment.",
      ),
    ).toBeTruthy();
  });

  it("exchanges the Google credential and calls onSuccess with the app access token", async () => {
    const { triggerCredential } = setupWindowGoogle();
    mockGoogleAuth.mockResolvedValueOnce({
      access_token: "app-jwt-token",
      token_type: "bearer",
    });

    const onSuccess = vi.fn();

    render(
      <GoogleSignInButton
        role="candidate"
        onSuccess={onSuccess}
        onError={vi.fn()}
      />,
    );

    await waitFor(() => {
      expect(
        screen.getByText("Sign in with Google"),
      ).toBeTruthy();
    });

    triggerCredential("fake-google-id-token");

    await waitFor(() => {
      expect(mockGoogleAuth).toHaveBeenCalledWith({
        credential: "fake-google-id-token",
        role: "candidate",
      });
    });

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledWith(
        "app-jwt-token",
      );
    });
  });

  it("reports a clean error message when the backend rejects the credential", async () => {
    const { triggerCredential } = setupWindowGoogle();
    mockGoogleAuth.mockRejectedValueOnce(
      new ApiError(401, {
        detail: "Invalid or expired Google credential.",
      }),
    );

    const onError = vi.fn();

    render(
      <GoogleSignInButton
        onSuccess={vi.fn()}
        onError={onError}
      />,
    );

    await waitFor(() => {
      expect(
        screen.getByText("Sign in with Google"),
      ).toBeTruthy();
    });

    triggerCredential("bad-token");

    await waitFor(() => {
      expect(onError).toHaveBeenCalledWith(
        "Invalid or expired Google credential.",
      );
    });
  });
});
