import { apiRequest } from "./client";
import type { components } from "../types/api";

export type CandidateMatchProfile =
  components["schemas"]["ScreeningResultResponse"];

export async function getCandidateMatchProfile(
  jobId: string,
  resumeId: string,
  token: string,
): Promise<CandidateMatchProfile> {
  return apiRequest<CandidateMatchProfile>(
    `/api/screenings/${encodeURIComponent(
      jobId,
    )}/${encodeURIComponent(resumeId)}`,
    {
      method: "GET",
      token,
    },
  );
}