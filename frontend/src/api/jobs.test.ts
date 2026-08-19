import { describe, expect, it } from "vitest";
import { apiRequest, ApiError } from "./client";
import { createJob, getJob, getJobs } from "./jobs";
import type { components } from "../types/api";

type TokenResponse = components["schemas"]["TokenResponse"];

// Hits the real backend/database directly (no mocking), so it must
// not depend on a pre-existing account seeded outside this file -
// register on demand and tolerate a 409 if a previous run already
// created it.
async function getTestToken(): Promise<string> {
  const email = "frontend-test@example.com";
  const password = "FrontendTest123!";

  try {
    await apiRequest("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, role: "recruiter" }),
    });
  } catch (err) {
    if (!(err instanceof ApiError) || err.status !== 409) {
      throw err;
    }
  }

  const response = await apiRequest<TokenResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
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