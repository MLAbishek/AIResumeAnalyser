import { useEffect, useState } from "react";
import { createJob, getJobs } from "../api/jobs";
import type { components } from "../types/api";

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

  useEffect(() => {
    const token = localStorage.getItem("access_token");

    if (!token) {
      setError("Authentication required.");
      setLoading(false);
      return;
    }

    getJobs(token)
      .then((data) => {
        setJobs(data);
      })
      .catch((err) => {
        console.error("Failed to load jobs:", err);
        setError("Failed to load jobs.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  async function handleCreateJob(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const token = localStorage.getItem("access_token");

    if (!token) {
      setError("Authentication required.");
      return;
    }

    if (!rawText.trim()) {
      setError("Raw job description is required.");
      return;
    }

    setCreating(true);
    setError(null);

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
      setError("Failed to create job.");
    } finally {
      setCreating(false);
    }
  }

  return (
    <main>
      <h1>Job Management</h1>

      <section>
        <h2>Create Job</h2>

        <form onSubmit={handleCreateJob}>
          <div>
            <label htmlFor="job-title">Job Title</label>
            <input
              id="job-title"
              name="title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
            />
          </div>

          <div>
            <label htmlFor="job-description">Description</label>
            <textarea
              id="job-description"
              name="description"
              value={description}
              onChange={(event) =>
                setDescription(event.target.value)
              }
            />
          </div>

          <div>
            <label htmlFor="job-location">Location</label>
            <input
              id="job-location"
              name="location"
              value={location}
              onChange={(event) =>
                setLocation(event.target.value)
              }
            />
          </div>

          <div>
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

          <div>
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
                setExperienceMonths(Number(event.target.value))
              }
            />
          </div>

          <div>
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
              required
            />
          </div>

          <button type="submit" disabled={creating}>
            {creating ? "Creating..." : "Create Job"}
          </button>
        </form>
      </section>

      <section>
        <h2>Jobs</h2>

        {loading && <p>Loading jobs...</p>}

        {error && <p>{error}</p>}

        {!loading && !error && jobs.length === 0 && (
          <p>No jobs available.</p>
        )}

        {!loading && !error && jobs.length > 0 && (
          <ul>
            {jobs.map((job) => (
              <li key={job.job_id}>
                <strong>{job.title ?? job.job_id}</strong>

                {job.location && (
                  <span> — {job.location}</span>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}