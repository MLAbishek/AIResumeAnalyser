import { describe, expect, it } from "vitest";
import { apiRequest } from "./client";
import {
  createResume,
  getResume,
  getResumes,
} from "./resumes";
import type { components } from "../types/api";

type TokenResponse = components["schemas"]["TokenResponse"];

async function getTestToken(): Promise<string> {
  const response = await apiRequest<TokenResponse>(
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

describe("Resume API", () => {
  it("creates, retrieves, and lists resumes", async () => {
    const token = await getTestToken();

    const resumeId = `frontend-test-${Date.now()}`;

    const created = await createResume(
      {
        resume_id: resumeId,
        name: "Frontend Test Candidate",
        email: "candidate@example.com",
        phone: "+91-9000000000",
        summary:
          "Frontend engineer with React and TypeScript experience.",
        skills: ["React", "TypeScript"],
        job_titles: ["Frontend Engineer"],
        organizations: ["Test Company"],
        technologies: ["React", "TypeScript"],
        total_experience_months: 24,
        raw_text:
          "Frontend Engineer with React and TypeScript experience.",
        experiences: [],
        education: [],
      },
      token,
    );

    expect(created.resume_id).toBe(resumeId);
    expect(created.name).toBe("Frontend Test Candidate");

    const retrieved = await getResume(
      resumeId,
      token,
    );

    expect(retrieved.resume_id).toBe(resumeId);
    expect(retrieved.email).toBe(
      "candidate@example.com",
    );

    const resumes = await getResumes(token);

    expect(
      resumes.some(
        (resume) => resume.resume_id === resumeId,
      ),
    ).toBe(true);
  });
});