import { describe, expect, it } from "vitest";
import { apiRequest } from "./client";
import { createJob, getJob, getJobs } from "./jobs";
import type { components } from "../types/api";

type TokenResponse = components["schemas"]["TokenResponse"];

async function getTestToken(): Promise<string> {
  const response = await apiRequest<TokenResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({
      email: "frontend-test@example.com",
      password: "FrontendTest123!",
    }),
  });

  return response.access_token;
}

describe("Job API", () => {
  it("creates, retrieves, and lists jobs", async () => {
    const token = await getTestToken();
    const jobId = `frontend-test-${Date.now()}`;

const created = await createJob(
  {
    job_id: jobId,
    raw_text:
      "Frontend Engineer with React and TypeScript experience.",
    title: "Frontend Engineer",
    description: "Build React applications.",
    location: "Remote",
    job_type: "Full-time",
    required_skills: ["React", "TypeScript"],
    preferred_skills: [],
    required_technologies: ["React", "TypeScript"],
    preferred_technologies: [],
    required_experience_months: 24,
  },
  token,
);

    expect(created.job_id).toBe(jobId);

    const retrieved = await getJob(jobId, token);

    expect(retrieved.job_id).toBe(jobId);

    const jobs = await getJobs(token);

    expect(jobs.some((job) => job.job_id === jobId)).toBe(true);
  });
});