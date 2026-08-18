import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { closeJob, getJob, listJobApplications } from "../../api";
import { getApiErrorMessage } from "../../api/client";
import PageHeader from "../../components/PageHeader";
import SectionCard from "../../components/SectionCard";
import ScoreBar from "../../components/ScoreBar";
import { DecisionBadge, EligibilityBadge } from "../../components/StatusBadge";
import {
  EmptyState,
  ErrorState,
  LoadingState,
} from "../../components/UXStates";
import type { components } from "../../types/api";
import type { RecruiterApplicationListResponse } from "../../api/applications";

type Job = components["schemas"]["JobResponse"];

export default function RecruiterJobDetailPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();

  const [job, setJob] = useState<Job | null>(null);
  const [applications, setApplications] =
    useState<RecruiterApplicationListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function load() {
    const token = localStorage.getItem("access_token");
    if (!token || !jobId) {
      setError("Authentication required.");
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    Promise.all([
      getJob(jobId, token),
      listJobApplications(jobId, token),
    ])
      .then(([jobData, applicationsData]) => {
        setJob(jobData);
        setApplications(applicationsData);
      })
      .catch((err) => {
        console.error(
          "Failed to load job candidates:",
          err,
        );
        setError(
          getApiErrorMessage(
            err,
            "Failed to load this job.",
          ),
        );
      })
      .finally(() => setLoading(false));
  }

  useEffect(load, [jobId]);

  async function handleClose() {
    const token = localStorage.getItem("access_token");
    if (!token || !jobId) return;

    try {
      const updated = await closeJob(jobId, token);
      setJob(updated);
    } catch (err) {
      console.error("Failed to close job:", err);
      setError(
        getApiErrorMessage(err, "Failed to close job."),
      );
    }
  }

  if (loading) {
    return (
      <main>
        <PageHeader eyebrow="Recruiter" title="Job" />
        <LoadingState message="Loading candidates..." />
      </main>
    );
  }

  if (error || !job) {
    return (
      <main>
        <PageHeader eyebrow="Recruiter" title="Job" />
        <ErrorState
          message={error ?? "Job not found."}
          onRetry={load}
        />
        <Link to="/recruiter/jobs">Back to Jobs</Link>
      </main>
    );
  }

  return (
    <main>
      <Link
        to="/recruiter/jobs"
        className="btn btn-ghost"
        style={{ marginBottom: "1rem" }}
      >
        ← Back to Jobs
      </Link>

      <PageHeader
        eyebrow="Recruiter"
        title={job.title ?? job.job_id}
        subtitle={job.job_id}
        actions={
          <>
            <span
              className={`badge ${
                job.status === "open"
                  ? "badge-success"
                  : "badge-neutral"
              }`}
            >
              {job.status === "open" ? "Open" : "Closed"}
            </span>
            {job.status === "open" && (
              <button
                type="button"
                className="btn btn-secondary"
                onClick={handleClose}
              >
                Close Applications
              </button>
            )}
          </>
        }
      />

      <SectionCard
        title="Applications"
        subtitle={`${
          applications?.total_applications ?? 0
        } candidate(s) ranked by AI match score.`}
      >
        {!applications || applications.results.length === 0 ? (
          <EmptyState
            title="No applications yet"
            message="No candidates have applied to this job yet."
          />
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Candidate</th>
                  <th>Match Score</th>
                  <th>Eligibility</th>
                  <th>Decision</th>
                  <th>Status</th>
                  <th>Applied</th>
                </tr>
              </thead>
              <tbody>
                {applications.results.map((row, index) => (
                  <tr
                    key={row.application_id}
                    style={{ cursor: "pointer" }}
                    onClick={() =>
                      navigate(
                        `/recruiter/jobs/${encodeURIComponent(
                          jobId ?? "",
                        )}/candidates/${row.application_id}`,
                      )
                    }
                  >
                    <td>
                      <span
                        className={`rank-badge${
                          index < 3 ? " rank-badge--top" : ""
                        }`}
                      >
                        {row.rank ?? index + 1}
                      </span>
                    </td>
                    <td>
                      <Link
                        to={`/recruiter/jobs/${encodeURIComponent(
                          jobId ?? "",
                        )}/candidates/${row.application_id}`}
                      >
                        {row.candidate_name ??
                          "Unknown Candidate"}
                      </Link>
                      <p className="muted text-sm mt-0">
                        {row.resume_id}
                      </p>
                    </td>
                    <td>
                      {row.score !== null ? (
                        <ScoreBar value={row.score * 100} />
                      ) : (
                        "—"
                      )}
                    </td>
                    <td>
                      {row.eligible !== null && (
                        <EligibilityBadge
                          eligible={row.eligible}
                        />
                      )}
                    </td>
                    <td>
                      <DecisionBadge
                        decision={row.decision}
                      />
                    </td>
                    <td>
                      <span className="badge badge-primary">
                        {row.status}
                      </span>
                    </td>
                    <td className="muted text-sm">
                      {new Date(
                        row.applied_at,
                      ).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>
    </main>
  );
}
