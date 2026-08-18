import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  getJobApplication,
  updateApplicationStatus,
} from "../../api";
import { getApiErrorMessage } from "../../api/client";
import PageHeader from "../../components/PageHeader";
import SectionCard from "../../components/SectionCard";
import FeedbackPanel from "../../components/FeedbackPanel";
import {
  EmptyState,
  ErrorState,
  LoadingState,
} from "../../components/UXStates";
import type { ApplicationResponse } from "../../api/applications";

export default function RecruiterCandidateDetailPage() {
  const { jobId, applicationId } = useParams<{
    jobId: string;
    applicationId: string;
  }>();

  const [application, setApplication] =
    useState<ApplicationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updating, setUpdating] = useState(false);

  function load() {
    const token = localStorage.getItem("access_token");
    if (!token || !jobId || !applicationId) {
      setError("Authentication required.");
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    getJobApplication(jobId, Number(applicationId), token)
      .then(setApplication)
      .catch((err) => {
        console.error(
          "Failed to load candidate:",
          err,
        );
        setError(
          getApiErrorMessage(
            err,
            "Failed to load candidate profile.",
          ),
        );
      })
      .finally(() => setLoading(false));
  }

  useEffect(load, [jobId, applicationId]);

  async function handleStatusChange(
    status: "shortlisted" | "rejected",
  ) {
    const token = localStorage.getItem("access_token");
    if (!token || !application) return;

    setUpdating(true);

    try {
      const updated = await updateApplicationStatus(
        application.application_id,
        status,
        token,
      );
      setApplication(updated);
    } catch (err) {
      console.error(
        "Failed to update application status:",
        err,
      );
      setError(
        getApiErrorMessage(
          err,
          "Failed to update application status.",
        ),
      );
    } finally {
      setUpdating(false);
    }
  }

  if (loading) {
    return (
      <main>
        <PageHeader
          eyebrow="Recruiter"
          title="Candidate Profile"
        />
        <LoadingState message="Loading candidate profile..." />
      </main>
    );
  }

  if (error || !application) {
    return (
      <main>
        <PageHeader
          eyebrow="Recruiter"
          title="Candidate Profile"
        />
        <ErrorState
          message={error ?? "Application not found."}
          onRetry={load}
        />
        <Link
          to={`/recruiter/jobs/${encodeURIComponent(
            jobId ?? "",
          )}`}
        >
          Back to Candidates
        </Link>
      </main>
    );
  }

  return (
    <main>
      <Link
        to={`/recruiter/jobs/${encodeURIComponent(
          jobId ?? "",
        )}`}
        className="btn btn-ghost"
        style={{ marginBottom: "1rem" }}
      >
        ← Back to Candidates
      </Link>

      <PageHeader
        eyebrow={application.job_title ?? application.job_id}
        title={
          application.candidate_name ?? "Unknown Candidate"
        }
        subtitle={`Resume ID: ${application.resume_id}`}
        actions={
          <>
            <button
              type="button"
              className="btn btn-secondary"
              disabled={
                updating ||
                application.status === "shortlisted"
              }
              onClick={() =>
                handleStatusChange("shortlisted")
              }
            >
              Shortlist
            </button>
            <button
              type="button"
              className="btn btn-danger"
              disabled={
                updating || application.status === "rejected"
              }
              onClick={() => handleStatusChange("rejected")}
            >
              Reject
            </button>
          </>
        }
      />

      <SectionCard title="Application Information">
        <div className="grid-3">
          <div>
            <p className="stat-card__label">Status</p>
            <p className="mt-0">
              <span className="badge badge-primary">
                {application.status}
              </span>
            </p>
          </div>
          <div>
            <p className="stat-card__label">Applied</p>
            <p className="mt-0">
              {new Date(
                application.applied_at,
              ).toLocaleString()}
            </p>
          </div>
          <div>
            <p className="stat-card__label">Last Updated</p>
            <p className="mt-0">
              {new Date(
                application.updated_at,
              ).toLocaleString()}
            </p>
          </div>
        </div>
      </SectionCard>

      {application.screening ? (
        <FeedbackPanel screening={application.screening} />
      ) : (
        <EmptyState
          title="No AI evaluation available"
          message="This application does not have a persisted screening result."
        />
      )}
    </main>
  );
}
