import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  closeJob,
  createJob,
  createJobFromFile,
  getJobs,
} from "../../api";
import { getApiErrorMessage } from "../../api/client";
import PageHeader from "../../components/PageHeader";
import SectionCard from "../../components/SectionCard";
import {
  EmptyState,
  ErrorState,
  LoadingState,
} from "../../components/UXStates";
import {
  IconBriefcase,
  IconPlus,
  IconUpload,
} from "../../components/icons";
import type { components } from "../../types/api";

type Job = components["schemas"]["JobResponse"];

type JdSource = "write" | "upload";

const JD_MAX_SIZE_BYTES = 10 * 1024 * 1024;
const JD_ALLOWED_EXTENSIONS = [".pdf", ".docx", ".txt"];

export default function RecruiterJobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [jdSource, setJdSource] = useState<JdSource>(
    "write",
  );

  const [title, setTitle] = useState("");
  const [location, setLocation] = useState("");
  const [jobType, setJobType] = useState("");
  const [experienceMonths, setExperienceMonths] = useState(0);
  const [skills, setSkills] = useState("");
  const [rawText, setRawText] = useState("");

  const [jdFile, setJdFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [creating, setCreating] = useState(false);
  const [formError, setFormError] = useState<
    string | null
  >(null);

  function loadJobs() {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setError("Authentication required.");
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    getJobs(token)
      .then(setJobs)
      .catch((err) => {
        console.error("Failed to load jobs:", err);
        setError(
          getApiErrorMessage(err, "Failed to load jobs."),
        );
      })
      .finally(() => setLoading(false));
  }

  useEffect(loadJobs, []);

  function resetForm() {
    setTitle("");
    setLocation("");
    setJobType("");
    setExperienceMonths(0);
    setSkills("");
    setRawText("");
    setJdFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  function handleFileChange(
    event: React.ChangeEvent<HTMLInputElement>,
  ) {
    const file = event.target.files?.[0] ?? null;
    setFormError(null);

    if (!file) {
      setJdFile(null);
      return;
    }

    const extension = file.name
      .slice(file.name.lastIndexOf("."))
      .toLowerCase();

    if (!JD_ALLOWED_EXTENSIONS.includes(extension)) {
      setFormError(
        "Unsupported file type. Please upload PDF, DOCX, or TXT.",
      );
      setJdFile(null);
      event.target.value = "";
      return;
    }

    if (file.size > JD_MAX_SIZE_BYTES) {
      setFormError(
        "File is too large. Maximum size is 10 MB.",
      );
      setJdFile(null);
      event.target.value = "";
      return;
    }

    setJdFile(file);
  }

  async function handleCreateJob(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const token = localStorage.getItem("access_token");
    if (!token) {
      setFormError("Authentication required.");
      return;
    }

    if (jdSource === "write") {
      if (!rawText.trim()) {
        setFormError("Raw job description is required.");
        return;
      }

      setCreating(true);
      setFormError(null);

      const jobId = `recruiter-${Date.now()}`;
      const parsedSkills = skills
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);

      try {
        const created = await createJob(
          {
            job_id: jobId,
            title: title || undefined,
            location: location || undefined,
            job_type: jobType || undefined,
            raw_text: rawText,
            required_experience_months: experienceMonths,
            required_skills: parsedSkills,
            preferred_skills: [],
            required_technologies: [],
            preferred_technologies: [],
          },
          token,
        );

        setJobs((current) => [created, ...current]);
        resetForm();
      } catch (err) {
        console.error("Failed to create job:", err);
        setFormError(
          getApiErrorMessage(err, "Failed to create job."),
        );
      } finally {
        setCreating(false);
      }

      return;
    }

    // Upload JD
    if (!jdFile) {
      setFormError(
        "Please select a job description file.",
      );
      return;
    }

    setCreating(true);
    setFormError(null);

    try {
      const created = await createJobFromFile(
        title,
        jdFile,
        token,
      );

      setJobs((current) => [created, ...current]);
      resetForm();
    } catch (err) {
      console.error(
        "Failed to create job from file:",
        err,
      );
      setFormError(
        getApiErrorMessage(
          err,
          "Failed to create job from the uploaded file.",
        ),
      );
    } finally {
      setCreating(false);
    }
  }

  async function handleCloseJob(jobId: string) {
    const token = localStorage.getItem("access_token");
    if (!token) return;

    try {
      const updated = await closeJob(jobId, token);
      setJobs((current) =>
        current.map((job) =>
          job.job_id === jobId ? updated : job,
        ),
      );
    } catch (err) {
      console.error("Failed to close job:", err);
      setError(
        getApiErrorMessage(err, "Failed to close job."),
      );
    }
  }

  return (
    <main>
      <PageHeader
        eyebrow="Recruiter"
        title="Job Openings"
        subtitle="Create and manage positions for AI-assisted candidate screening."
      />

      <div className="workflow-layout">
        <div className="stack">
          <SectionCard title="Jobs">
            {loading && (
              <LoadingState message="Loading jobs..." />
            )}
            {error && (
              <ErrorState message={error} onRetry={loadJobs} />
            )}
            {!loading && !error && jobs.length === 0 && (
              <EmptyState
                title="No jobs yet"
                message="No job descriptions have been created yet."
              />
            )}

            {!loading && !error && jobs.length > 0 && (
              <ul className="stack" style={{ gap: "0.6rem" }}>
                {jobs.map((job) => (
                  <li
                    key={job.job_id}
                    className="card"
                    style={{ margin: 0 }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "flex-start",
                        gap: "0.75rem",
                        flexWrap: "wrap",
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          gap: "0.75rem",
                        }}
                      >
                        <span className="stat-card__icon">
                          <IconBriefcase
                            width={16}
                            height={16}
                          />
                        </span>
                        <div>
                          <Link
                            to={`/recruiter/jobs/${encodeURIComponent(
                              job.job_id,
                            )}`}
                          >
                            <strong>
                              {job.title ?? job.job_id}
                            </strong>
                          </Link>
                          <p className="muted text-sm mt-0">
                            {job.job_id}
                            {job.location
                              ? ` · ${job.location}`
                              : ""}
                          </p>
                          <span
                            className={`badge ${
                              job.status === "open"
                                ? "badge-success"
                                : "badge-neutral"
                            }`}
                          >
                            {job.status === "open"
                              ? "Open"
                              : "Closed"}
                          </span>
                        </div>
                      </div>

                      <div
                        style={{
                          display: "flex",
                          gap: "0.5rem",
                        }}
                      >
                        <Link
                          to={`/recruiter/jobs/${encodeURIComponent(
                            job.job_id,
                          )}`}
                          className="btn btn-secondary"
                        >
                          Manage Candidates
                        </Link>
                        {job.status === "open" && (
                          <button
                            type="button"
                            className="btn btn-ghost"
                            onClick={() =>
                              handleCloseJob(job.job_id)
                            }
                          >
                            Close
                          </button>
                        )}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </SectionCard>
        </div>

        <div className="workflow-layout__aside">
          <SectionCard
            title="Create Job"
            subtitle="Add a new position to screen candidates against."
          >
            <form onSubmit={handleCreateJob}>
              <div className="field">
                <label htmlFor="recruiter-job-title">
                  Job Title
                </label>
                <input
                  id="recruiter-job-title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </div>

              <div className="field">
                <span
                  className="field-hint"
                  style={{
                    fontSize: "0.78rem",
                    fontWeight: 650,
                    color: "var(--color-text-muted)",
                  }}
                >
                  Job Description Source
                </span>
                <div
                  role="radiogroup"
                  aria-label="Job Description Source"
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: "0.5rem",
                  }}
                >
                  <button
                    type="button"
                    role="radio"
                    aria-checked={jdSource === "write"}
                    className={`btn ${
                      jdSource === "write"
                        ? "btn-primary"
                        : "btn-secondary"
                    }`}
                    onClick={() => {
                      setJdSource("write");
                      setFormError(null);
                    }}
                  >
                    Write JD
                  </button>
                  <button
                    type="button"
                    role="radio"
                    aria-checked={jdSource === "upload"}
                    className={`btn ${
                      jdSource === "upload"
                        ? "btn-primary"
                        : "btn-secondary"
                    }`}
                    onClick={() => {
                      setJdSource("upload");
                      setFormError(null);
                    }}
                  >
                    <IconUpload width={16} height={16} />
                    Upload JD
                  </button>
                </div>
              </div>

              {jdSource === "write" ? (
                <>
                  <div className="form-grid">
                    <div className="field">
                      <label htmlFor="recruiter-job-location">
                        Location
                      </label>
                      <input
                        id="recruiter-job-location"
                        value={location}
                        onChange={(e) =>
                          setLocation(e.target.value)
                        }
                      />
                    </div>
                    <div className="field">
                      <label htmlFor="recruiter-job-type">
                        Job Type
                      </label>
                      <input
                        id="recruiter-job-type"
                        value={jobType}
                        onChange={(e) =>
                          setJobType(e.target.value)
                        }
                      />
                    </div>
                  </div>

                  <div className="field">
                    <label htmlFor="recruiter-job-skills">
                      Required Skills
                    </label>
                    <input
                      id="recruiter-job-skills"
                      placeholder="React, TypeScript"
                      value={skills}
                      onChange={(e) =>
                        setSkills(e.target.value)
                      }
                    />
                  </div>

                  <div className="field">
                    <label htmlFor="recruiter-job-experience">
                      Required Experience (months)
                    </label>
                    <input
                      id="recruiter-job-experience"
                      type="number"
                      min="0"
                      value={experienceMonths}
                      onChange={(e) =>
                        setExperienceMonths(
                          Number(e.target.value),
                        )
                      }
                    />
                  </div>

                  <div className="field">
                    <label htmlFor="recruiter-job-raw-text">
                      Job Description
                    </label>
                    <textarea
                      id="recruiter-job-raw-text"
                      value={rawText}
                      onChange={(e) =>
                        setRawText(e.target.value)
                      }
                      rows={6}
                      required
                    />
                  </div>
                </>
              ) : (
                <div className="field">
                  <label htmlFor="recruiter-job-file">
                    Job Description File
                  </label>
                  <input
                    id="recruiter-job-file"
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.docx,.txt"
                    onChange={handleFileChange}
                    disabled={creating}
                  />
                  <p className="field-hint">
                    Accepted: PDF, DOCX, TXT. Maximum size:
                    10 MB.
                  </p>
                  {jdFile && (
                    <p className="muted text-sm">
                      Selected: {jdFile.name}
                    </p>
                  )}
                </div>
              )}

              {formError && (
                <p role="alert" className="validation-message">
                  {formError}
                </p>
              )}

              <button
                type="submit"
                className="btn btn-primary btn-block"
                disabled={creating}
              >
                {creating ? (
                  <span
                    className="spinner-inline"
                    aria-hidden="true"
                  />
                ) : (
                  <IconPlus width={16} height={16} />
                )}
                {creating
                  ? jdSource === "upload"
                    ? "Uploading and processing JD..."
                    : "Creating..."
                  : "Create Job"}
              </button>
            </form>
          </SectionCard>
        </div>
      </div>
    </main>
  );
}
