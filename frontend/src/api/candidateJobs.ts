import { apiRequest } from "./client";
import type { components } from "../types/api";

export type CandidateJobSummary =
  components["schemas"]["CandidateJobSummary"];
export type CandidateJobDetail =
  components["schemas"]["CandidateJobDetail"];
export type ResumeResponse =
  components["schemas"]["ResumeResponse"];
export type ScreeningResultResponse =
  components["schemas"]["ScreeningResultResponse"];
export type ApplicationResponse =
  components["schemas"]["ApplicationResponse"];

export function listAvailableJobs(token: string) {
  return apiRequest<CandidateJobSummary[]>(
    "/api/candidate/jobs",
    { token },
  );
}

export function getAvailableJob(
  jobId: string,
  token: string,
) {
  return apiRequest<CandidateJobDetail>(
    `/api/candidate/jobs/${encodeURIComponent(jobId)}`,
    { token },
  );
}

export function uploadResume(
  file: File,
  token: string,
) {
  const formData = new FormData();
  formData.append("file", file);

  return apiRequest<ResumeResponse>(
    "/api/candidate/resumes/upload",
    {
      method: "POST",
      token,
      body: formData,
    },
  );
}

export function listMyResumes(token: string) {
  return apiRequest<ResumeResponse[]>(
    "/api/candidate/resumes",
    { token },
  );
}

export function previewMatch(
  jobId: string,
  resumeId: string,
  token: string,
) {
  return apiRequest<ScreeningResultResponse>(
    `/api/candidate/jobs/${encodeURIComponent(jobId)}/preview`,
    {
      method: "POST",
      token,
      body: JSON.stringify({ resume_id: resumeId }),
    },
  );
}

export function applyToJob(
  jobId: string,
  resumeId: string,
  token: string,
) {
  return apiRequest<ApplicationResponse>(
    `/api/candidate/jobs/${encodeURIComponent(jobId)}/apply`,
    {
      method: "POST",
      token,
      body: JSON.stringify({ resume_id: resumeId }),
    },
  );
}

export function listMyApplications(token: string) {
  return apiRequest<ApplicationResponse[]>(
    "/api/candidate/applications",
    { token },
  );
}

export function getMyApplication(
  applicationId: number,
  token: string,
) {
  return apiRequest<ApplicationResponse>(
    `/api/candidate/applications/${applicationId}`,
    { token },
  );
}
