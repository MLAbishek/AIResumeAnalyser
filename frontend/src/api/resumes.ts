import { apiRequest } from "./client";
import type { components } from "../types/api";

type ResumeCreateRequest =
  components["schemas"]["ResumeCreateRequest"];

type ResumeResponse =
  components["schemas"]["ResumeResponse"];

export function createResume(
  data: ResumeCreateRequest,
  token: string,
) {
  return apiRequest<ResumeResponse>("/api/resumes", {
    method: "POST",
    token,
    body: JSON.stringify(data),
  });
}

export function getResumes(
  token: string,
  offset = 0,
  limit = 100,
) {
  return apiRequest<ResumeResponse[]>(
    `/api/resumes?offset=${offset}&limit=${limit}`,
    {
      token,
    },
  );
}

export function getResume(
  resumeId: string,
  token: string,
) {
  return apiRequest<ResumeResponse>(
    `/api/resumes/${resumeId}`,
    {
      token,
    },
  );
}