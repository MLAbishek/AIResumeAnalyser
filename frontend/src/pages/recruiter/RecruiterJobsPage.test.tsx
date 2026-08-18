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
import { MemoryRouter } from "react-router-dom";

import RecruiterJobsPage from "./RecruiterJobsPage";
import { ApiError } from "../../api/client";

const mockGetJobs = vi.fn();
const mockCreateJob = vi.fn();
const mockCreateJobFromFile = vi.fn();
const mockCloseJob = vi.fn();

vi.mock("../../api", () => ({
  getJobs: (...args: unknown[]) => mockGetJobs(...args),
  createJob: (...args: unknown[]) => mockCreateJob(...args),
  createJobFromFile: (...args: unknown[]) =>
    mockCreateJobFromFile(...args),
  closeJob: (...args: unknown[]) => mockCloseJob(...args),
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <RecruiterJobsPage />
    </MemoryRouter>,
  );
}

function makeFile(
  name: string,
  sizeBytes = 1024,
): File {
  const file = new File(["dummy content"], name, {
    type: "text/plain",
  });

  Object.defineProperty(file, "size", {
    value: sizeBytes,
  });

  return file;
}

async function selectUploadMode() {
  fireEvent.click(
    screen.getByRole("radio", { name: /Upload JD/i }),
  );
}

beforeEach(() => {
  localStorage.setItem("access_token", "test-token");
  mockGetJobs.mockResolvedValue([]);
});

afterEach(() => {
  cleanup();
  localStorage.clear();
  vi.clearAllMocks();
});

describe("RecruiterJobsPage - job description source", () => {
  it("defaults to Write JD mode with the textarea visible", async () => {
    renderPage();

    await waitFor(() => {
      expect(mockGetJobs).toHaveBeenCalled();
    });

    expect(
      screen.getByLabelText("Job Description"),
    ).toBeTruthy();
    expect(
      screen.queryByLabelText("Job Description File"),
    ).toBeNull();
  });

  it("shows the file input when Upload JD is selected", async () => {
    renderPage();
    await waitFor(() =>
      expect(mockGetJobs).toHaveBeenCalled(),
    );

    await selectUploadMode();

    expect(
      screen.getByLabelText("Job Description File"),
    ).toBeTruthy();
    expect(
      screen.queryByLabelText("Job Description"),
    ).toBeNull();
  });

  it("accepts a PDF file and displays its name", async () => {
    renderPage();
    await waitFor(() =>
      expect(mockGetJobs).toHaveBeenCalled(),
    );
    await selectUploadMode();

    const input = screen.getByLabelText(
      "Job Description File",
    ) as HTMLInputElement;

    fireEvent.change(input, {
      target: { files: [makeFile("role.pdf")] },
    });

    expect(
      screen.getByText("Selected: role.pdf"),
    ).toBeTruthy();
  });

  it("accepts a DOCX file and displays its name", async () => {
    renderPage();
    await waitFor(() =>
      expect(mockGetJobs).toHaveBeenCalled(),
    );
    await selectUploadMode();

    const input = screen.getByLabelText(
      "Job Description File",
    ) as HTMLInputElement;

    fireEvent.change(input, {
      target: { files: [makeFile("role.docx")] },
    });

    expect(
      screen.getByText("Selected: role.docx"),
    ).toBeTruthy();
  });

  it("accepts a TXT file and displays its name", async () => {
    renderPage();
    await waitFor(() =>
      expect(mockGetJobs).toHaveBeenCalled(),
    );
    await selectUploadMode();

    const input = screen.getByLabelText(
      "Job Description File",
    ) as HTMLInputElement;

    fireEvent.change(input, {
      target: { files: [makeFile("role.txt")] },
    });

    expect(
      screen.getByText("Selected: role.txt"),
    ).toBeTruthy();
  });

  it("rejects an unsupported file extension client-side", async () => {
    renderPage();
    await waitFor(() =>
      expect(mockGetJobs).toHaveBeenCalled(),
    );
    await selectUploadMode();

    const input = screen.getByLabelText(
      "Job Description File",
    ) as HTMLInputElement;

    fireEvent.change(input, {
      target: { files: [makeFile("role.exe")] },
    });

    expect(
      screen.getByText(
        "Unsupported file type. Please upload PDF, DOCX, or TXT.",
      ),
    ).toBeTruthy();
    expect(
      screen.queryByText("Selected: role.exe"),
    ).toBeNull();
  });

  it("rejects an oversized file client-side", async () => {
    renderPage();
    await waitFor(() =>
      expect(mockGetJobs).toHaveBeenCalled(),
    );
    await selectUploadMode();

    const input = screen.getByLabelText(
      "Job Description File",
    ) as HTMLInputElement;

    fireEvent.change(input, {
      target: {
        files: [
          makeFile("huge.pdf", 10 * 1024 * 1024 + 1),
        ],
      },
    });

    expect(
      screen.getByText(
        "File is too large. Maximum size is 10 MB.",
      ),
    ).toBeTruthy();
  });

  it("requires a file to be selected before submitting", async () => {
    renderPage();
    await waitFor(() =>
      expect(mockGetJobs).toHaveBeenCalled(),
    );
    await selectUploadMode();

    fireEvent.click(
      screen.getByRole("button", { name: /Create Job/i }),
    );

    expect(
      await screen.findByText(
        "Please select a job description file.",
      ),
    ).toBeTruthy();
    expect(mockCreateJobFromFile).not.toHaveBeenCalled();
  });

  it("enters a loading state and calls createJobFromFile on submit", async () => {
    let resolveUpload: (value: unknown) => void = () => {};

    mockCreateJobFromFile.mockReturnValue(
      new Promise((resolve) => {
        resolveUpload = resolve;
      }),
    );

    renderPage();
    await waitFor(() =>
      expect(mockGetJobs).toHaveBeenCalled(),
    );
    await selectUploadMode();

    fireEvent.change(
      screen.getByLabelText("Job Title"),
      { target: { value: "Backend Engineer" } },
    );

    const input = screen.getByLabelText(
      "Job Description File",
    ) as HTMLInputElement;

    fireEvent.change(input, {
      target: { files: [makeFile("role.pdf")] },
    });

    fireEvent.click(
      screen.getByRole("button", { name: /Create Job/i }),
    );

    expect(
      await screen.findByText(
        "Uploading and processing JD...",
      ),
    ).toBeTruthy();

    expect(mockCreateJobFromFile).toHaveBeenCalledWith(
      "Backend Engineer",
      expect.objectContaining({ name: "role.pdf" }),
      "test-token",
    );

    resolveUpload({
      job_id: "recruiter-upload-1",
      title: "Backend Engineer",
      raw_text: "Extracted text",
      required_skills: [],
      preferred_skills: [],
      required_technologies: [],
      preferred_technologies: [],
      education_requirements: [],
      required_certifications: [],
      required_experience_months: 0,
      status: "open",
    });

    await waitFor(() => {
      expect(
        screen.queryByText(
          "Uploading and processing JD...",
        ),
      ).toBeNull();
    });
  });

  it("refreshes the job list after a successful upload", async () => {
    mockCreateJobFromFile.mockResolvedValue({
      job_id: "recruiter-upload-2",
      title: "Data Engineer",
      raw_text: "Extracted text",
      required_skills: [],
      preferred_skills: [],
      required_technologies: [],
      preferred_technologies: [],
      education_requirements: [],
      required_certifications: [],
      required_experience_months: 0,
      status: "open",
    });

    renderPage();
    await waitFor(() =>
      expect(mockGetJobs).toHaveBeenCalled(),
    );
    await selectUploadMode();

    fireEvent.change(
      screen.getByLabelText("Job Description File"),
      { target: { files: [makeFile("role.pdf")] } },
    );

    fireEvent.click(
      screen.getByRole("button", { name: /Create Job/i }),
    );

    expect(
      await screen.findByText("Data Engineer"),
    ).toBeTruthy();
  });

  it("displays a backend error safely", async () => {
    mockCreateJobFromFile.mockRejectedValue(
      new ApiError(415, {
        detail:
          "Unsupported job description file type. Allowed formats: PDF, DOCX, TXT.",
      }),
    );

    renderPage();
    await waitFor(() =>
      expect(mockGetJobs).toHaveBeenCalled(),
    );
    await selectUploadMode();

    fireEvent.change(
      screen.getByLabelText("Job Description File"),
      { target: { files: [makeFile("role.pdf")] } },
    );

    fireEvent.click(
      screen.getByRole("button", { name: /Create Job/i }),
    );

    expect(
      await screen.findByText(
        "Unsupported job description file type. Allowed formats: PDF, DOCX, TXT.",
      ),
    ).toBeTruthy();
  });

  it("Write JD mode still submits via createJob unchanged", async () => {
    mockCreateJob.mockResolvedValue({
      job_id: "recruiter-write-1",
      title: "QA Engineer",
      raw_text: "Manually written JD",
      required_skills: [],
      preferred_skills: [],
      required_technologies: [],
      preferred_technologies: [],
      education_requirements: [],
      required_certifications: [],
      required_experience_months: 0,
      status: "open",
    });

    renderPage();
    await waitFor(() =>
      expect(mockGetJobs).toHaveBeenCalled(),
    );

    fireEvent.change(
      screen.getByLabelText("Job Description"),
      { target: { value: "Manually written JD" } },
    );

    fireEvent.click(
      screen.getByRole("button", { name: /Create Job/i }),
    );

    expect(
      await screen.findByText("QA Engineer"),
    ).toBeTruthy();
    expect(mockCreateJobFromFile).not.toHaveBeenCalled();
  });
});
