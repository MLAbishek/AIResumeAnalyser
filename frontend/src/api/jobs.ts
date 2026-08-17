import { apiRequest } from "./client";
import type { components } from "../types/api";

type JobCreateRequest = components["schemas"]["JobCreateRequest"];
type JobResponse = components["schemas"]["JobResponse"];

export function createJob(
  data: JobCreateRequest,
  token: string,
) {
  return apiRequest<JobResponse>("/api/jobs", {
    method: "POST",
    token,
    body: JSON.stringify(data),
  });
}

export function getJobs(
  token: string,
  offset = 0,
  limit = 100,
) {
  return apiRequest<JobResponse[]>(
    `/api/jobs?offset=${offset}&limit=${limit}`,
    {
      token,
    },
  );
}

export function getJob(
  jobId: string,
  token: string,
) {
  return apiRequest<JobResponse>(
    `/api/jobs/${jobId}`,
    {
      token,
    },
  );
}