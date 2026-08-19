import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
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

import RecruiterCandidateDetailPage from "./RecruiterCandidateDetailPage";

const mockGetJobApplication = vi.fn();
const mockUpdateApplicationStatus = vi.fn();
const mockGetApplicationResumeBlob = vi.fn();

vi.mock("../../api", () => ({
  getJobApplication: (...args: unknown[]) =>
    mockGetJobApplication(...args),
  updateApplicationStatus: (...args: unknown[]) =>
    mockUpdateApplicationStatus(...args),
  getApplicationResumeBlob: (...args: unknown[]) =>
    mockGetApplicationResumeBlob(...args),
}));

const APPLICATION = {
  application_id: 42,
  job_id: "job-1",
  job_title: "Backend Engineer",
  resume_id: "resume_abc",
  candidate_name: "Jamie Doe",
  candidate_email: "jamie@example.com",
  status: "applied",
  applied_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  resume: {
    resume_id: "resume_abc",
    name: "Jamie Doe",
    email: "jamie@example.com",
    phone: null,
    summary: "Backend engineer with 3 years of experience.",
    skills: ["Python", "SQL"],
    job_titles: ["Backend Engineer"],
    organizations: [],
    technologies: [],
    certifications: ["AWS Certified Cloud Practitioner"],
    total_experience_months: 36,
    raw_text: "Jamie Doe resume text",
    experiences: [
      {
        id: 1,
        job_title: "Backend Engineer",
        company: "Acme",
        start_date: "2022-01-01",
        end_date: "2024-01-01",
        duration_months: 24,
      },
    ],
    education: [
      {
        id: 1,
        degree: "BSc Computer Science",
        institution: "State University",
        field_of_study: null,
        start_date: "2018-01-01",
        end_date: "2022-01-01",
      },
    ],
    projects: [
      {
        id: 1,
        name: "Resume Screening System",
        description: "An AI-assisted resume screening platform.",
        technologies: ["Python", "FastAPI"],
      },
    ],
  },
  screening: {
    screening_id: 7,
    job_id: "job-1",
    resume_id: "resume_abc",
    candidate_name: "Jamie Doe",
    eligible: true,
    decision: "shortlist",
    final_score: 85.4,
    decision_reason: "Strong match.",
    ranking: {
      rank: 1,
      score: 0.854,
      skill_score: 0.9,
      experience_score: 0.8,
      seniority_score: 0.7,
      education_score: 1.0,
      semantic_score: 0.75,
    },
    gap_analysis: {
      has_gap: false,
      matched_skills: ["Python", "SQL"],
      missing_skills: [],
    },
    explanation: {
      summary: "Great fit for the role.",
      strengths: ["Strong Python skills"],
    },
    evidence: [
      {
        id: 1,
        claim: "Candidate received a ranking score.",
        source: "ranking",
        section: "ranking",
        evidence: "85.4",
      },
    ],
  },
};

function renderPage() {
  return render(
    <MemoryRouter
      initialEntries={[
        "/recruiter/jobs/job-1/candidates/42",
      ]}
    >
      <Routes>
        <Route
          path="/recruiter/jobs/:jobId/candidates/:applicationId"
          element={<RecruiterCandidateDetailPage />}
        />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  localStorage.setItem("access_token", "test-token");
  mockGetJobApplication.mockResolvedValue(APPLICATION);

  if (!URL.createObjectURL) {
    URL.createObjectURL = vi.fn();
  }
  if (!URL.revokeObjectURL) {
    URL.revokeObjectURL = vi.fn();
  }
  vi.spyOn(URL, "createObjectURL").mockReturnValue(
    "blob:mock-url",
  );
  vi.spyOn(URL, "revokeObjectURL").mockImplementation(
    () => {},
  );
});

afterEach(() => {
  cleanup();
  localStorage.clear();
  vi.clearAllMocks();
});

describe("RecruiterCandidateDetailPage", () => {
  it("renders candidate profile information from the real application response", async () => {
    renderPage();

    expect(
      await screen.findByRole("heading", {
        name: "Jamie Doe",
      }),
    ).toBeTruthy();

    expect(
      screen.getAllByText(/jamie@example\.com/).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText(
        "Backend engineer with 3 years of experience.",
      ),
    ).toBeTruthy();
    expect(screen.getAllByText("Python").length).toBeGreaterThan(
      0,
    );
    expect(screen.getByText(/Acme/)).toBeTruthy();
    expect(
      screen.getByText("BSc Computer Science"),
    ).toBeTruthy();
    expect(
      screen.getByText("Resume Screening System"),
    ).toBeTruthy();
    expect(
      screen.getByText("AWS Certified Cloud Practitioner"),
    ).toBeTruthy();
  });

  it("renders the AI screening/match information", async () => {
    renderPage();

    await screen.findByRole("heading", { name: "Jamie Doe" });

    expect(
      screen.getByText("85.4%"),
    ).toBeTruthy();
    expect(
      screen.getByText("Great fit for the role."),
    ).toBeTruthy();
  });

  it("loads and displays the actual uploaded resume on View Resume", async () => {
    const pdfBlob = new Blob([new Uint8Array([1, 2, 3])], {
      type: "application/pdf",
    });
    mockGetApplicationResumeBlob.mockResolvedValue(pdfBlob);

    renderPage();

    await screen.findByRole("heading", { name: "Jamie Doe" });

    fireEvent.click(
      screen.getByRole("button", { name: "View Resume" }),
    );

    await waitFor(() => {
      expect(
        mockGetApplicationResumeBlob,
      ).toHaveBeenCalledWith("job-1", 42, "test-token");
    });

    await waitFor(() => {
      expect(
        screen.getByTitle("Resume resume_abc"),
      ).toBeTruthy();
    });
  });

  it("shows a clean message when the resume file is unavailable", async () => {
    mockGetApplicationResumeBlob.mockRejectedValue({
      status: 404,
      data: { detail: "not available" },
    });

    renderPage();

    await screen.findByRole("heading", { name: "Jamie Doe" });

    fireEvent.click(
      screen.getByRole("button", { name: "View Resume" }),
    );

    expect(
      await screen.findByText(
        "The original resume file is not available for this application.",
      ),
    ).toBeTruthy();
  });

  it("shortlisting the candidate still works", async () => {
    mockUpdateApplicationStatus.mockResolvedValue({
      ...APPLICATION,
      status: "shortlisted",
    });

    renderPage();

    await screen.findByRole("heading", { name: "Jamie Doe" });

    fireEvent.click(
      screen.getByRole("button", { name: "Shortlist" }),
    );

    await waitFor(() => {
      expect(mockUpdateApplicationStatus).toHaveBeenCalledWith(
        42,
        "shortlisted",
        "test-token",
      );
    });

    expect(
      await screen.findByText("shortlisted"),
    ).toBeTruthy();
  });
});

describe("RecruiterCandidateDetailPage - parsed resume honesty", () => {
  it("shows honest empty states for genuinely empty parsed fields, matching resume_001.pdf's real extraction result", async () => {
    // Mirrors the real, verified API response for
    // resume_13728357634803e4: skills and raw_text populated,
    // summary/email/phone/experiences/education/certifications/
    // projects all empty/null.
    mockGetJobApplication.mockResolvedValue({
      ...APPLICATION,
      resume: {
        ...APPLICATION.resume,
        email: null,
        summary: null,
        total_experience_months: 0,
        experiences: [],
        education: [],
        certifications: [],
        projects: [],
      },
    });

    renderPage();

    await screen.findByRole("heading", { name: "Jamie Doe" });

    expect(
      screen.getByText(
        "No summary was extracted from the resume.",
      ),
    ).toBeTruthy();
    expect(
      screen.getByText(
        "No structured work experience was extracted.",
      ),
    ).toBeTruthy();
    expect(
      screen.getByText(
        "No structured education was extracted.",
      ),
    ).toBeTruthy();
    expect(
      screen.getAllByText("Not extracted").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText(
        "No projects were extracted from the resume.",
      ),
    ).toBeTruthy();
    expect(
      screen.getByText(
        "No certifications were extracted from the resume.",
      ),
    ).toBeTruthy();
  });

  it("shows an empty-skills message when no skills were extracted", async () => {
    mockGetJobApplication.mockResolvedValue({
      ...APPLICATION,
      resume: {
        ...APPLICATION.resume,
        skills: [],
      },
    });

    renderPage();

    await screen.findByRole("heading", { name: "Jamie Doe" });

    expect(
      screen.getByText(
        "No skills were extracted from the resume.",
      ),
    ).toBeTruthy();
  });

  it("shows a not-available message when no resume profile exists on the application", async () => {
    mockGetJobApplication.mockResolvedValue({
      ...APPLICATION,
      resume: null,
    });

    renderPage();

    await screen.findByRole("heading", { name: "Jamie Doe" });

    expect(
      screen.getByText(
        "No resume profile is available for this application.",
      ),
    ).toBeTruthy();
  });
});
