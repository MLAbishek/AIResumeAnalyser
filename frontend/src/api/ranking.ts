import { apiRequest } from "./client";
export type RankingResult = {
  screening_id: number;
  resume_id: string;
  candidate_name: string | null;
  rank: number;
  score: number;
  skill_score: number;
  experience_score: number;
  seniority_score: number;
  education_score: number;
  semantic_score: number;
};

export type RankingResponse = {
  job_id: string;
  count: number;
  results: RankingResult[];
};

export type ScreeningResult = {
  screening_id: number;
  job_id: string;
  resume_id: string;
  candidate_name: string | null;
  eligible: boolean;
  decision: string | null;
  final_score: number | null;
  decision_reason: string | null;
  ranking: {
    rank: number | null;
    score: number;
    skill_score: number;
    experience_score: number;
    seniority_score: number;
    education_score: number;
    semantic_score: number;
  } | null;
  gap_analysis: Record<string, unknown> | null;
  explanation: Record<string, unknown> | null;
  evidence: Array<Record<string, unknown>>;
};

export type ScreeningListResponse = {
  job_id: string;
  total_candidates: number;
  results: ScreeningResult[];
};

export async function rankJobCandidates(
  jobId: string,
  token: string,
): Promise<RankingResponse> {
  return apiRequest<RankingResponse>(
    `/api/ranking/${encodeURIComponent(jobId)}`,
    {
      method: "POST",
      token,
    },
  );
}

export async function getScreenings(
  jobId: string,
  token: string,
): Promise<ScreeningListResponse> {
  return apiRequest<ScreeningListResponse>(
    `/api/screenings/${encodeURIComponent(jobId)}`,
    {
      method: "GET",
      token,
    },
  );
}
