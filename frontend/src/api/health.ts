import { apiRequest } from "./client";

export interface HealthResponse {
  [key: string]: unknown;
}

export function checkHealth() {
  return apiRequest<HealthResponse>("/api/health");
}