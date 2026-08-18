import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listMyApplications } from "../../api";
import { getApiErrorMessage } from "../../api/client";
import PageHeader from "../../components/PageHeader";
import SectionCard from "../../components/SectionCard";
import { DecisionBadge } from "../../components/StatusBadge";
import {
  EmptyState,
  ErrorState,
  LoadingState,
} from "../../components/UXStates";
import type { ApplicationResponse } from "../../api/candidateJobs";

export default function CandidateApplicationsPage() {
  const [applications, setApplications] = useState<
    ApplicationResponse[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function load() {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setError("Authentication required.");
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    listMyApplications(token)
      .then(setApplications)
      .catch((err) => {
        console.error(
          "Failed to load applications:",
          err,
        );
        setError(
          getApiErrorMessage(
            err,
            "Failed to load your applications.",
          ),
        );
      })
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  return (
    <main>
      <PageHeader
        eyebrow="Candidate"
        title="My Applications"
        subtitle="Track the status and feedback for every job you've applied to."
      />

      {loading && (
        <LoadingState message="Loading your applications..." />
      )}
      {error && (
        <ErrorState message={error} onRetry={load} />
      )}

      {!loading && !error && applications.length === 0 && (
        <EmptyState
          title="No applications yet"
          message="You haven't applied to any jobs yet."
          action={
            <Link to="/candidate/jobs" className="btn btn-primary">
              Browse Jobs
            </Link>
          }
        />
      )}

      {!loading && !error && applications.length > 0 && (
        <SectionCard title="Applications">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Job</th>
                  <th>Status</th>
                  <th>Match Score</th>
                  <th>Applied</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {applications.map((app) => (
                  <tr key={app.application_id}>
                    <td>
                      {app.job_title ?? app.job_id}
                    </td>
                    <td>
                      <DecisionBadge
                        decision={app.status}
                      />
                    </td>
                    <td>
                      {app.screening?.final_score !== null &&
                      app.screening?.final_score !== undefined
                        ? `${app.screening.final_score.toFixed(1)}%`
                        : "—"}
                    </td>
                    <td className="muted text-sm">
                      {new Date(
                        app.applied_at,
                      ).toLocaleDateString()}
                    </td>
                    <td>
                      <Link
                        to={`/candidate/applications/${app.application_id}`}
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </SectionCard>
      )}
    </main>
  );
}
