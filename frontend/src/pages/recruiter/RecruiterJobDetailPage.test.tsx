import {
  cleanup,
  render,
  screen,
} from "@testing-library/react";
import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import RecruiterJobDetailPage from "./RecruiterJobDetailPage";

const mockGetJob = vi.fn();
const mockListJobApplications = vi.fn();
const mockCloseJob = vi.fn();
const mockNavigate = vi.fn();

vi.mock("react-router-dom", async (importOriginal) => {
  const actual =
    await importOriginal<
      typeof import("react-router-dom")
    >();

  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock("../../api", () => ({
  getJob: (...args: unknown[]) => mockGetJob(...args),
  listJobApplications: (...args: unknown[]) =>
    mockListJobApplications(...args),
  closeJob: (...args: unknown[]) => mockCloseJob(...args),
}));

const JOB = {
  job_id: "job-1",
  title: "Backend Engineer",
  status: "open",
  raw_text: "Backend role",
  required_skills: [],
  preferred_skills: [],
  required_technologies: [],
  preferred_technologies: [],
  education_requirements: [],
  required_certifications: [],
  responsibilities: [],
  required_experience_months: 12,
};

const APPLICATIONS = {
  job_id: "job-1",
  total_applications: 1,
  results: [
    {
      application_id: 42,
      resume_id: "resume_abc",
      candidate_name: "Jamie Doe",
      candidate_email: "jamie@example.com",
      status: "applied",
      applied_at: "2026-01-01T00:00:00Z",
      rank: null,
      score: 0.85,
      eligible: true,
      decision: "shortlist",
      skills: ["Python", "SQL", "FastAPI", "Docker"],
    },
  ],
};

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/recruiter/jobs/job-1"]}>
      <Routes>
        <Route
          path="/recruiter/jobs/:jobId"
          element={<RecruiterJobDetailPage />}
        />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  localStorage.setItem("access_token", "test-token");
  mockGetJob.mockResolvedValue(JOB);
  mockListJobApplications.mockResolvedValue(APPLICATIONS);
});

afterEach(() => {
  cleanup();
  localStorage.clear();
  vi.clearAllMocks();
});

describe("RecruiterJobDetailPage - applicants", () => {
  it("displays the job's applicants with skills and score", async () => {
    renderPage();

    expect(
      await screen.findByText("Jamie Doe"),
    ).toBeTruthy();
    expect(
      screen.getByText("jamie@example.com"),
    ).toBeTruthy();
    expect(screen.getByText("Python")).toBeTruthy();
    expect(screen.getByText("SQL")).toBeTruthy();
    // Only the first 3 skills are shown, with a "+N" overflow.
    expect(screen.getByText("+1")).toBeTruthy();
  });

  it("shows an empty state when nobody has applied", async () => {
    mockListJobApplications.mockResolvedValue({
      job_id: "job-1",
      total_applications: 0,
      results: [],
    });

    renderPage();

    expect(
      await screen.findByText("No applications yet"),
    ).toBeTruthy();
  });

  it("provides a View Candidate action that links to the candidate detail route", async () => {
    renderPage();

    const link = await screen.findByRole("link", {
      name: "View Candidate",
    });

    expect(link.getAttribute("href")).toBe(
      "/recruiter/jobs/job-1/candidates/42",
    );
  });

  it("clicking the applicant row navigates to the candidate detail page", async () => {
    renderPage();

    const nameLink = await screen.findByRole("link", {
      name: "Jamie Doe",
    });

    expect(nameLink.getAttribute("href")).toBe(
      "/recruiter/jobs/job-1/candidates/42",
    );
  });
});

describe("RecruiterJobDetailPage - parsed job description", () => {
  it("renders the raw extracted JD text when structured fields are empty (the actual JD-upload case)", async () => {
    mockGetJob.mockResolvedValue({
      ...JOB,
      raw_text:
        "Java Developer Intern\n\nRequired: OOP fundamentals.",
    });

    renderPage();

    expect(
      await screen.findByText("Parsed Job Description"),
    ).toBeTruthy();
    expect(
      screen.getByText(/Java Developer Intern/),
    ).toBeTruthy();
    expect(
      screen.getByText(/Required: OOP fundamentals\./),
    ).toBeTruthy();

    // No structured requirement chips were fabricated for empty
    // backend arrays.
    expect(
      screen.queryByText("Required Skills"),
    ).toBeNull();
    expect(
      screen.queryByText("Education Requirements"),
    ).toBeNull();
  });

  it("renders structured JD fields when the backend has populated them", async () => {
    mockGetJob.mockResolvedValue({
      ...JOB,
      description: "Build backend services.",
      location: "Remote",
      job_type: "Full-time",
      required_skills: ["Kubernetes", "Terraform"],
      preferred_skills: ["GraphQL"],
      required_certifications: ["AWS Certified"],
      responsibilities: ["Design and develop backend services"],
    });

    renderPage();

    expect(
      await screen.findByText("Build backend services."),
    ).toBeTruthy();
    expect(screen.getByText("Remote")).toBeTruthy();
    expect(screen.getByText("Full-time")).toBeTruthy();
    expect(screen.getByText("Required Skills")).toBeTruthy();
    expect(screen.getByText("Kubernetes")).toBeTruthy();
    expect(screen.getByText("Preferred Skills")).toBeTruthy();
    expect(screen.getByText("GraphQL")).toBeTruthy();
    expect(
      screen.getByText("Required Certifications"),
    ).toBeTruthy();
    expect(screen.getByText("AWS Certified")).toBeTruthy();
    expect(screen.getByText("Responsibilities")).toBeTruthy();
    expect(
      screen.getByText("Design and develop backend services"),
    ).toBeTruthy();
  });

  it("shows an empty-text message when no JD text was extracted at all", async () => {
    mockGetJob.mockResolvedValue({
      ...JOB,
      raw_text: "",
    });

    renderPage();

    expect(
      await screen.findByText(
        "No job description text was extracted.",
      ),
    ).toBeTruthy();
  });
});
