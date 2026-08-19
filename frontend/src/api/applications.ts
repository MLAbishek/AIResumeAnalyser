import { apiRequest, apiRequestBlob } from "./client";
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

/**
 * Fetch the candidate's actual uploaded resume file as a Blob, for
 * an authorized recruiter. The caller is responsible for turning
 * this into an object URL (and revoking it on cleanup).
 */
export function getApplicationResumeBlob(
  jobId: string,
  applicationId: number,
  token: string,
) {
  return apiRequestBlob(
    `/api/jobs/${encodeURIComponent(
      jobId,
    )}/applications/${applicationId}/resume`,
    { token },
  );
}
