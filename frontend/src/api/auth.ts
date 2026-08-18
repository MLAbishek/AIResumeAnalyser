import { apiRequest } from "./client";
import type { components } from "../types/api";

type LoginRequest = components["schemas"]["LoginRequest"];
type TokenResponse = components["schemas"]["TokenResponse"];
type RegisterRequest = components["schemas"]["RegisterRequest"];
type UserResponse = components["schemas"]["UserResponse"];

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
