import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getMyApplication } from "../../api";
import { getApiErrorMessage } from "../../api/client";
import PageHeader from "../../components/PageHeader";
import SectionCard from "../../components/SectionCard";
import FeedbackPanel from "../../components/FeedbackPanel";
import { DecisionBadge } from "../../components/StatusBadge";
import {
  EmptyState,
  ErrorState,
  LoadingState,
} from "../../components/UXStates";
import type { ApplicationResponse } from "../../api/candidateJobs";

export default function CandidateApplicationDetailPage() {
  const { applicationId } = useParams<{
    applicationId: string;
  }>();

  const [application, setApplication] =
    useState<ApplicationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function load() {
    const token = localStorage.getItem("access_token");
    if (!token || !applicationId) {
      setError("Authentication required.");
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    getMyApplication(Number(applicationId), token)
      .then(setApplication)
      .catch((err) => {
        console.error(
          "Failed to load application:",
          err,
        );
        setError(
          getApiErrorMessage(
            err,
            "Failed to load this application.",
          ),
        );
      })
      .finally(() => setLoading(false));
  }

  useEffect(load, [applicationId]);

  if (loading) {
    return (
      <main>
        <PageHeader eyebrow="Candidate" title="Application" />
        <LoadingState message="Loading application..." />
      </main>
    );
  }

  if (error || !application) {
    return (
      <main>
        <PageHeader eyebrow="Candidate" title="Application" />
        <ErrorState
          message={error ?? "Application not found."}
          onRetry={load}
        />
        <Link to="/candidate/applications">
          Back to Applications
        </Link>
      </main>
    );
  }

  return (
    <main>
      <Link
        to="/candidate/applications"
        className="btn btn-ghost"
        style={{ marginBottom: "1rem" }}
      >
        ← Back to Applications
      </Link>

      <PageHeader
        eyebrow="Candidate"
        title={application.job_title ?? application.job_id}
        subtitle={`Applied ${new Date(
          application.applied_at,
        ).toLocaleDateString()}`}
        actions={
          <DecisionBadge decision={application.status} />
        }
      />

      {application.screening ? (
        <FeedbackPanel screening={application.screening} />
      ) : (
        <SectionCard title="AI Match Assessment">
          <EmptyState
            title="Evaluation not yet available"
            message="This application does not have a persisted screening result yet."
          />
        </SectionCard>
      )}
    </main>
  );
}
