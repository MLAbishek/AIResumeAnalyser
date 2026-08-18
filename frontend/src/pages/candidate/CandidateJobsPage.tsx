import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listAvailableJobs } from "../../api";
import { getApiErrorMessage } from "../../api/client";
import PageHeader from "../../components/PageHeader";
import SkillChip from "../../components/SkillChip";
import {
  EmptyState,
  ErrorState,
  LoadingState,
} from "../../components/UXStates";
import type { CandidateJobSummary } from "../../api/candidateJobs";

export default function CandidateJobsPage() {
  const [jobs, setJobs] = useState<CandidateJobSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  function load() {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setError("Authentication required.");
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    listAvailableJobs(token)
      .then(setJobs)
      .catch((err) => {
        console.error(
          "Failed to load available jobs:",
          err,
        );
        setError(
          getApiErrorMessage(
            err,
            "Failed to load available jobs.",
          ),
        );
      })
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  const filteredJobs = jobs.filter((job) => {
    const haystack = `${job.title ?? ""} ${job.job_id} ${job.required_skills.join(
      " ",
    )}`.toLowerCase();
    return haystack.includes(search.toLowerCase());
  });

  return (
    <main>
      <PageHeader
        eyebrow="Candidate"
        title="Available Job Openings"
        subtitle="Explore open roles and see your AI match score before you apply."
      />

      <div className="field" style={{ maxWidth: "24rem" }}>
        <label htmlFor="job-search">Search jobs</label>
        <input
          id="job-search"
          placeholder="Search by title or skill..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {loading && (
        <LoadingState message="Loading available jobs..." />
      )}
      {error && (
        <ErrorState message={error} onRetry={load} />
      )}

      {!loading && !error && filteredJobs.length === 0 && (
        <EmptyState
          title="No jobs available"
          message="There are no open job openings right now. Check back soon."
        />
      )}

      {!loading && !error && filteredJobs.length > 0 && (
        <div className="grid-2">
          {filteredJobs.map((job) => (
            <div key={job.job_id} className="card">
              <h2 style={{ marginBottom: "0.35rem" }}>
                {job.title ?? job.job_id}
              </h2>
              <p className="muted text-sm">
                {job.location ?? "Location not specified"}
                {job.job_type ? ` · ${job.job_type}` : ""}
                {" · "}
                {job.required_experience_months}+ months
                experience
              </p>

              {job.required_skills.length > 0 && (
                <div className="chip-row" style={{ marginBottom: "1rem" }}>
                  {job.required_skills
                    .slice(0, 6)
                    .map((skill) => (
                      <SkillChip key={skill}>
                        {skill}
                      </SkillChip>
                    ))}
                </div>
              )}

              <Link
                to={`/candidate/jobs/${encodeURIComponent(
                  job.job_id,
                )}`}
                className="btn btn-primary"
              >
                View Job
              </Link>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
