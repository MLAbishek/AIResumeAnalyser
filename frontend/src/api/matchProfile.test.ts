import {
  describe,
  expect,
  it,
} from "vitest";

import { apiRequest } from "./client";
import { createJob } from "./jobs";
import { createResume } from "./resumes";
import { screenCandidates } from "./screening";
import {
  getCandidateMatchProfile,
} from "./matchProfile";

import {
    getScreenings,
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
          email:
            "frontend-test@example.com",
          password:
            "FrontendTest123!",
        }),
      },
    );

  return response.access_token;
}

describe("Candidate Match Profile API", () => {
  it(
    "retrieves detailed candidate match profile",
    async () => {
      const token =
        await getTestToken();

      const suffix = Date.now();

      const jobId =
        `frontend-profile-job-${suffix}`;

      const resumeId =
        `frontend-profile-resume-${suffix}`;

      const job = await createJob(
        {
          job_id: jobId,
          raw_text:
            "Frontend Engineer with React and TypeScript experience.",
          title:
            "Frontend Engineer",
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

      const resume =
        await createResume(
          {
            resume_id: resumeId,
            name:
              "Match Profile Test Candidate",
            email:
              "match-profile@example.com",
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
                company:
                  "Test Company",
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

      const profile =
        await getCandidateMatchProfile(
          jobId,
          resumeId,
          token,
        );

      expect(
        profile.job_id,
      ).toBe(jobId);

      expect(
        profile.resume_id,
      ).toBe(resumeId);

      const screenings =
        await getScreenings(
          jobId,
          token,
        );

      expect(
        screenings.total_candidates,
      ).toBe(1);

      expect(
        profile.screening_id,
      ).toBe(
        screenings.results[0]
          .screening_id,
      );

      expect(
        profile.candidate_name,
      ).toBe(
        "Match Profile Test Candidate",
      );

      expect(
        typeof profile.eligible,
      ).toBe("boolean");

      expect(
        profile.decision,
      ).toBeDefined();

      expect(
        profile.gap_analysis,
      ).toBeDefined();

      expect(
        profile.explanation,
      ).toBeDefined();

      expect(
        Array.isArray(
          profile.evidence,
        ),
      ).toBe(true);
    },
  );
});