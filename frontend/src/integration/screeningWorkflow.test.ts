import { describe, expect, it } from "vitest";
import { apiRequest, ApiError } from "../api/client";
import { createJob } from "../api/jobs";
import { createResume } from "../api/resumes";
import { screenCandidates } from "../api/screening";
import {
  getScreenings,
  rankJobCandidates,
} from "../api/ranking";
import { getCandidateMatchProfile } from "../api/matchProfile";
import type { components } from "../types/api";

type TokenResponse =
  components["schemas"]["TokenResponse"];

// This test hits the real backend/database directly (no mocking),
// so it must not depend on a pre-existing account seeded outside
// this file - a clean database (e.g. after a dev DB reset) must not
// break it. Register the fixture account on demand and tolerate a
// 409 if a previous run already created it.
async function getTestToken(): Promise<string> {
  const email = "frontend-test@example.com";
  const password = "FrontendTest123!";

  try {
    await apiRequest("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({
        email,
        password,
        role: "recruiter",
      }),
    });
  } catch (err) {
    if (!(err instanceof ApiError) || err.status !== 409) {
      throw err;
    }
  }

  const response =
    await apiRequest<TokenResponse>(
      "/api/auth/login",
      {
        method: "POST",
        body: JSON.stringify({
          email,
          password,
        }),
      },
    );

  return response.access_token;
}

describe("Frontend Integration Workflow", () => {
  it(
    "completes job → resume → screening → ranking → profile workflow",
    async () => {
      const token = await getTestToken();

      const suffix = Date.now();

      const jobId =
        `frontend-integration-job-${suffix}`;

      const resumeId =
        `frontend-integration-resume-${suffix}`;

      // ------------------------------------------------
      // F03/F04: Create job
      // ------------------------------------------------

      const job = await createJob(
        {
          job_id: jobId,
          raw_text:
            "Frontend Engineer with React and TypeScript experience.",
          title: "Frontend Engineer",
          description:
            "Build frontend applications using React and TypeScript.",
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

      expect(job.job_id).toBe(jobId);

      // ------------------------------------------------
      // F05: Create resume
      // ------------------------------------------------

      const resume = await createResume(
        {
          resume_id: resumeId,
          name: "Integration Test Candidate",
          email:
            "integration-test@example.com",
          summary:
            "Frontend engineer with React and TypeScript experience.",
          skills: [
            "React",
            "TypeScript",
          ],
          job_titles: [
            "Frontend Engineer",
          ],
          organizations: [
            "Integration Test Company",
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
              job_title:
                "Frontend Engineer",
              company:
                "Integration Test Company",
              start_date:
                "2022-01-01",
              end_date:
                "2024-01-01",
              duration_months: 24,
            },
          ],
          education: [],
        },
        token,
      );

      expect(resume.resume_id).toBe(
        resumeId,
      );

      // ------------------------------------------------
      // F07: Screening
      // ------------------------------------------------

      const screening =
        await screenCandidates(
          job,
          [resume],
          token,
        );

      expect(
        screening.job_id,
      ).toBe(jobId);

      expect(
        screening.total_candidates,
      ).toBe(1);

      expect(
        screening.results.length,
      ).toBeGreaterThan(0);

      const screeningResult =
        screening.results[0];

      expect(
        screeningResult.resume_id,
      ).toBe(resumeId);

      console.log(
        "INTEGRATION SCREENING RESULT:",
        JSON.stringify(
            screeningResult,
            null,
            2,
        ),
        );

      expect(
        screeningResult.eligible,
      ).toBe(true);

      // ------------------------------------------------
      // F11: Screening history
      // ------------------------------------------------

      const history =
        await getScreenings(
          jobId,
          token,
        );

      expect(history.job_id).toBe(
        jobId,
      );

      expect(
        history.total_candidates,
      ).toBe(1);

      const historyResult =
        history.results.find(
          (result) =>
            result.resume_id ===
            resumeId,
        );

        expect(historyResult).toBeDefined();

        expect(
        historyResult?.resume_id,
        ).toBe(resumeId);

        expect(
        historyResult?.eligible,
        ).toBe(true);

      // ------------------------------------------------
      // F08: Ranking
      // ------------------------------------------------

      const ranking =
        await rankJobCandidates(
          jobId,
          token,
        );
        console.log(
        "INTEGRATION RANKING RESULT:",
        JSON.stringify(ranking, null, 2),
        );
      expect(ranking.job_id).toBe(
        jobId,
      );

      expect(
        ranking.count,
      ).toBeGreaterThan(0);

      const rankedCandidate =
        ranking.results.find(
          (candidate) =>
            candidate.screening_id ===
            historyResult?.screening_id,
        );

      expect(
        rankedCandidate,
      ).toBeDefined();

      expect(
        rankedCandidate?.rank,
      ).toBeGreaterThanOrEqual(1);

      expect(
        typeof rankedCandidate?.score,
      ).toBe("number");

      // ------------------------------------------------
      // F09/F10: Candidate profile
      // ------------------------------------------------

      const profile =
        await getCandidateMatchProfile(
          jobId,
          resumeId,
          token,
        );

      expect(
        profile.screening_id,
      ).toBe(
        historyResult?.screening_id,
      );

      expect(
        profile.job_id,
      ).toBe(jobId);

      expect(
        profile.resume_id,
      ).toBe(resumeId);

      expect(
        profile.eligible,
      ).toBe(true);

      // ------------------------------------------------
      // F10: Explainability/evidence
      // ------------------------------------------------

      expect(
        profile.gap_analysis,
      ).not.toBeNull();

      expect(
        profile.explanation,
      ).not.toBeNull();

      expect(
        profile.evidence,
      ).toBeDefined();

      expect(
        Array.isArray(
          profile.evidence,
        ),
      ).toBe(true);
    },
    30000,
  );
});