import { apiRequest } from "./client";
import type { components } from "../types/api";

export type RecruiterApplicationListResponse =
  components["schemas"]["RecruiterApplicationListResponse"];
export type ApplicationResponse =
  components["schemas"]["ApplicationResponse"];
export type ApplicationStatus =
  components["schemas"]["ApplicationStatusUpdateRequest"]["status"];

export function listJobApplications(
  jobId: string,
  token: string,
) {
  return apiRequest<RecruiterApplicationListResponse>(
    `/api/jobs/${encodeURIComponent(jobId)}/applications`,
    { token },
  );
}

export function getJobApplication(
  jobId: string,
  applicationId: number,
  token: string,
) {
  return apiRequest<ApplicationResponse>(
    `/api/jobs/${encodeURIComponent(
      jobId,
    )}/applications/${applicationId}`,
    { token },
  );
}

export function updateApplicationStatus(
  applicationId: number,
  status: ApplicationStatus,
  token: string,
) {
  return apiRequest<ApplicationResponse>(
    `/api/applications/${applicationId}/status`,
    {
      method: "PATCH",
      token,
      body: JSON.stringify({ status }),
    },
  );
}
