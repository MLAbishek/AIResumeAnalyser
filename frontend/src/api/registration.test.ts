import { describe, expect, it } from "vitest";
import { ApiError } from "./client";
import { login, registerUser } from "./auth";

describe("Registration API", () => {
  it("registers a recruiter with the recruiter role and no password in the response", async () => {
    const email = `frontend-register-${Date.now()}@example.com`;

    const user = await registerUser({
      email,
      password: "StrongPassword123!",
      role: "recruiter",
    });

    expect(user.email).toBe(email);
    expect(user.role).toBe("recruiter");
    expect(user.is_active).toBe(true);
    expect(
      Object.keys(user),
    ).not.toContain("password");
    expect(
      Object.keys(user),
    ).not.toContain("password_hash");
  });

  it("registers a candidate with the candidate role", async () => {
    const email = `frontend-register-candidate-${Date.now()}@example.com`;

    const user = await registerUser({
      email,
      password: "StrongPassword123!",
      role: "candidate",
    });

    expect(user.role).toBe("candidate");
  });

  it("rejects a duplicate email with a clean 409 error", async () => {
    const email = `frontend-register-dup-${Date.now()}@example.com`;

    await registerUser({
      email,
      password: "StrongPassword123!",
      role: "recruiter",
    });

    await expect(
      registerUser({
        email,
        password: "AnotherPassword123!",
        role: "recruiter",
      }),
    ).rejects.toMatchObject({
      status: 409,
    });

    try {
      await registerUser({
        email,
        password: "AnotherPassword123!",
        role: "recruiter",
      });

      throw new Error(
        "Expected duplicate registration to be rejected.",
      );
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);

      const apiError = err as ApiError;

      expect(apiError.status).toBe(409);

      const detail = (
        apiError.data as { detail?: unknown }
      )?.detail;

      expect(typeof detail).toBe("string");
      expect(detail as string).toContain(
        "already exists",
      );
    }
  });

  it("rejects registration attempting to set a privileged role", async () => {
    const email = `frontend-register-escalate-${Date.now()}@example.com`;

    // RegisterRequest.role is a closed
    // Literal["recruiter", "candidate"] - "admin" is not a
    // representable value at all, so the request is rejected
    // outright by the backend's schema validation (422), not
    // silently downgraded.
    await expect(
      registerUser({
        email,
        password: "StrongPassword123!",
        // @ts-expect-error - "admin" is intentionally not a valid
        // RegisterRequest role; verifying the server rejects it
        // even if a malicious client sends it anyway.
        role: "admin",
      }),
    ).rejects.toMatchObject({
      status: 422,
    });
  });

  it("allows a newly registered user to log in through the existing login endpoint", async () => {
    const email = `frontend-register-login-${Date.now()}@example.com`;
    const password = "StrongPassword123!";

    await registerUser({
      email,
      password,
      role: "recruiter",
    });

    const session = await login({ email, password });

    expect(typeof session.access_token).toBe("string");
    expect(session.access_token.length).toBeGreaterThan(
      0,
    );
    expect(session.token_type).toBe("bearer");
  });
});
