import { describe, expect, it } from "vitest";
import { apiRequest } from "./client";
import { createJob } from "./jobs";
import { createResume } from "./resumes";
import { screenCandidates } from "./screening";
import {
  getScreenings,
  rankJobCandidates,
} from "./ranking";
import type { components } from "../types/api";

type TokenResponse =
  components["schemas"]["TokenResponse"];

async function getTestToken(): Promise<string> {
  const response =
    await apiRequest<TokenResponse>(
      "/api/auth/login",
      {
        method: "POST",
        body: JSON.stringify({
          email: "frontend-test@example.com",
          password: "FrontendTest123!",
        }),
      },
    );

  return response.access_token;
}

describe("Ranking API", () => {
  it("ranks screened candidates and retrieves candidate metadata", async () => {
    const token = await getTestToken();

    const suffix = Date.now();

    const jobId =
      `frontend-ranking-job-${suffix}`;

    const resumeId =
      `frontend-ranking-resume-${suffix}`;

    const job = await createJob(
      {
        job_id: jobId,
        raw_text:
          "Frontend Engineer with React and TypeScript experience.",
        title: "Frontend Engineer",
        description:
          "Build React applications.",
        location: null,
        job_type: "Full-time",
        required_skills: [
          "React",
          "TypeScript",
        ],
        preferred_skills: [],
        required_technologies: [
          "React",
          "TypeScript",
        ],
        preferred_technologies: [],
        required_experience_months: 12,
      },
      token,
    );

    const resume = await createResume(
      {
        resume_id: resumeId,
        name: "Ranking Test Candidate",
        email: "screening-test@example.com",
        summary:
          "Frontend engineer experienced with React and TypeScript.",
        skills: [
          "React",
          "TypeScript",
        ],
        job_titles: [
          "Frontend Engineer",
        ],
        organizations: [
          "Test Company",
        ],
        technologies: [
          "React",
          "TypeScript",
        ],
        total_experience_months: 24,
        raw_text:
          "Frontend Engineer with React and TypeScript experience.",
        experiences: [
          {
            job_title: "Frontend Engineer",
            company: "Test Company",
            start_date: "2022-01-01",
            end_date: "2024-01-01",
            duration_months: 24,
          },
        ],
        education: [],
      },
      token,
    );

    const screening =
      await screenCandidates(
        job,
        [resume],
        token,
      );

    expect(screening.job_id).toBe(jobId);
    expect(
      screening.total_candidates,
    ).toBe(1);

    const ranking =
      await rankJobCandidates(
        jobId,
        token,
      );

    expect(ranking.job_id).toBe(jobId);
    expect(
      ranking.count,
    ).toBeGreaterThan(0);
    expect(
      ranking.results.length,
    ).toBeGreaterThan(0);

    const rankedCandidate =
      ranking.results[0];

    expect(rankedCandidate).toBeDefined();

    expect(
      rankedCandidate.rank,
    ).toBeGreaterThanOrEqual(1);

    expect(
      typeof rankedCandidate.score,
    ).toBe("number");

    const screenings =
      await getScreenings(
        jobId,
        token,
      );

    expect(
      screenings.job_id,
    ).toBe(jobId);

    expect(
      screenings.total_candidates,
    ).toBe(1);

    expect(
      screenings.results[0].resume_id,
    ).toBe(resumeId);

    expect(
      screenings.results[0].candidate_name,
    ).toBe("Ranking Test Candidate");

    expect(
      screenings.results[0].eligible,
    ).toBe(true);
  });
});
