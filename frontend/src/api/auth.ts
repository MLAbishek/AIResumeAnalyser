import { apiRequest } from "./client";
import type { components } from "../types/api";

type LoginRequest = components["schemas"]["LoginRequest"];
type TokenResponse = components["schemas"]["TokenResponse"];

export function login(request: LoginRequest) {
  return apiRequest<TokenResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(request),
  });
}