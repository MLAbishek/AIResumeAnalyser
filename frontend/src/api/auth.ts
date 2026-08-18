import { apiRequest } from "./client";
import type { components } from "../types/api";

type LoginRequest = components["schemas"]["LoginRequest"];
type TokenResponse = components["schemas"]["TokenResponse"];
type RegisterRequest = components["schemas"]["RegisterRequest"];
type UserResponse = components["schemas"]["UserResponse"];
type GoogleAuthRequest =
  components["schemas"]["GoogleAuthRequest"];

export function login(request: LoginRequest) {
  return apiRequest<TokenResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export function registerUser(request: RegisterRequest) {
  return apiRequest<UserResponse>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

/**
 * Exchange a verified Google ID token for the application's own JWT
 * (see POST /api/auth/google). `role` only matters the first time a
 * given Google account signs in - the backend ignores it for an
 * already-linked account and always keeps that account's original
 * role.
 */
export function googleAuth(request: GoogleAuthRequest) {
  return apiRequest<TokenResponse>("/api/auth/google", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
