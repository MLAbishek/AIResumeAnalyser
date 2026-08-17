import { describe, expect, it } from "vitest";
import { apiRequest } from "./client";
import {
  createJob,
} from "./jobs";
import {
  createResume,
} from "./resumes";
import {
  screenCandidates,
} from "./screening";
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

describe("Screening API", () => {
  it("screens selected resumes against a job", async () => {
    const token = await getTestToken();

    const jobId =
      `frontend-screening-job-${Date.now()}`;

    const resumeId =
      `frontend-screening-resume-${Date.now()}`;

    const job = await createJob(
      {
        job_id: jobId,
        raw_text:
          "Frontend Engineer with React and TypeScript experience.",
        title: "Frontend Engineer",
        description:
          "Build React applications.",
        location: "Remote",
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
        name: "Screening Test Candidate",
        email:
          "screening-test@example.com",
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
            job_title:
              "Frontend Engineer",
            company: "Test Company",
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

    let result;

    try {
      result = await screenCandidates(
        job,
        [resume],
        token,
      );
    } catch (error) {
      if (error instanceof Error) {
        console.error("SCREENING ERROR:", error);
      }

      if (
        typeof error === "object" &&
        error !== null &&
        "data" in error
      ) {
        console.error(
          "SCREENING RESPONSE:",
          (error as { data: unknown }).data,
        );
      }

      throw error;
    }

    expect(result.job_id).toBe(jobId);
    expect(
      result.total_candidates,
    ).toBe(1);

    expect(
      result.results.length,
    ).toBe(1);

    expect(
      result.results[0].resume_id,
    ).toBe(resumeId);
  });
});
