import { useEffect, useState } from "react";
import { createJob, getJobs } from "../api/jobs";
import { getApiErrorMessage } from "../api/client";
import type { components } from "../types/api";
import PageHeader from "../components/PageHeader";
import SectionCard from "../components/SectionCard";
import {
  EmptyState,
  ErrorState,
  LoadingState,
} from "../components/UXStates";
import { IconBriefcase, IconPlus } from "../components/icons";

type Job = components["schemas"]["JobResponse"];

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [location, setLocation] = useState("");
  const [jobType, setJobType] = useState("");
  const [experienceMonths, setExperienceMonths] = useState(0);
  const [rawText, setRawText] = useState("");
  const [creating, setCreating] = useState(false);
  const [formError, setFormError] = useState<string | null>(
    null,
  );

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
      .then((data) => {
        setJobs(data);
      })
      .catch((err) => {
        console.error("Failed to load jobs:", err);
        setError(
          getApiErrorMessage(err, "Failed to load jobs."),
        );
      })
      .finally(() => {
        setLoading(false);
      });
  }

  useEffect(() => {
    loadJobs();
  }, []);

  async function handleCreateJob(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const token = localStorage.getItem("access_token");

    if (!token) {
      setFormError("Authentication required.");
      return;
    }

    if (!rawText.trim()) {
      setFormError("Raw job description is required.");
      return;
    }

    setCreating(true);
    setFormError(null);

    const jobId = `frontend-${Date.now()}`;

    try {
      const created = await createJob(
        {
          job_id: jobId,
          title: title || undefined,
          description: description || undefined,
          location: location || undefined,
          job_type: jobType || undefined,
          raw_text: rawText,
          required_experience_months: experienceMonths,
          required_skills: [],
          preferred_skills: [],
          required_technologies: [],
          preferred_technologies: [],
        },
        token,
      );

      setJobs((currentJobs) => [created, ...currentJobs]);

      setTitle("");
      setDescription("");
      setLocation("");
      setJobType("");
      setExperienceMonths(0);
      setRawText("");
    } catch (err) {
      console.error("Failed to create job:", err);
      setFormError(
        getApiErrorMessage(err, "Failed to create job."),
      );
    } finally {
      setCreating(false);
    }
  }

  return (
    <main>
      <PageHeader
        eyebrow="Jobs"
        title="Job Management"
        subtitle="Create and manage positions for candidate screening."
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
                  <li key={job.job_id} className="card" style={{ margin: 0 }}>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "0.75rem",
                      }}
                    >
                      <span className="stat-card__icon">
                        <IconBriefcase width={16} height={16} />
                      </span>
                      <div>
                        <strong>
                          {job.title ?? job.job_id}
                        </strong>
                        <p className="muted text-sm mt-0">
                          {job.job_id}
                          {job.location
                            ? ` · ${job.location}`
                            : ""}
                          {job.job_type
                            ? ` · ${job.job_type}`
                            : ""}
                        </p>
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
                <label htmlFor="job-title">Job Title</label>
                <input
                  id="job-title"
                  name="title"
                  value={title}
                  onChange={(event) =>
                    setTitle(event.target.value)
                  }
                />
              </div>

              <div className="field">
                <label htmlFor="job-description">
                  Description
                </label>
                <textarea
                  id="job-description"
                  name="description"
                  value={description}
                  onChange={(event) =>
                    setDescription(event.target.value)
                  }
                />
              </div>

              <div className="form-grid">
                <div className="field">
                  <label htmlFor="job-location">
                    Location
                  </label>
                  <input
                    id="job-location"
                    name="location"
                    value={location}
                    onChange={(event) =>
                      setLocation(event.target.value)
                    }
                  />
                </div>

                <div className="field">
                  <label htmlFor="job-type">Job Type</label>
                  <input
                    id="job-type"
                    name="job_type"
                    value={jobType}
                    onChange={(event) =>
                      setJobType(event.target.value)
                    }
                  />
                </div>
              </div>

              <div className="field">
                <label htmlFor="job-experience">
                  Required Experience (months)
                </label>
                <input
                  id="job-experience"
                  name="required_experience_months"
                  type="number"
                  min="0"
                  value={experienceMonths}
                  onChange={(event) =>
                    setExperienceMonths(
                      Number(event.target.value),
                    )
                  }
                />
              </div>

              <div className="field">
                <label htmlFor="job-raw-text">
                  Raw Job Description
                </label>
                <textarea
                  id="job-raw-text"
                  name="raw_text"
                  value={rawText}
                  onChange={(event) =>
                    setRawText(event.target.value)
                  }
                  rows={6}
                  required
                />
                <p className="field-hint">
                  Used by the AI screening pipeline to match
                  candidates against this role.
                </p>
              </div>

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
                {creating ? "Creating..." : "Create Job"}
              </button>
            </form>
          </SectionCard>
        </div>
      </div>
    </main>
  );
}
