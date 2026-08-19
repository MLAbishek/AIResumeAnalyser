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
import SkillChip from "../../components/SkillChip";
import ResumeViewer from "../../components/ResumeViewer";
import { IconGraduationCap } from "../../components/icons";
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

  const resume = application.resume;

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
        subtitle={
          application.candidate_email
            ? `${application.candidate_email} · Resume ID: ${application.resume_id}`
            : `Resume ID: ${application.resume_id}`
        }
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

      <SectionCard
        title="Candidate Profile"
        subtitle="Parsed from the candidate's uploaded resume."
      >
        {resume ? (
          <div className="stack" style={{ gap: "1rem" }}>
            <div className="form-grid">
              <div>
                <p className="stat-card__label">Name</p>
                <p className="mt-0">
                  {resume.name ?? (
                    <span className="muted">
                      Not extracted
                    </span>
                  )}
                </p>
              </div>
              <div>
                <p className="stat-card__label">Email</p>
                <p className="mt-0">
                  {resume.email ?? (
                    <span className="muted">
                      Not extracted
                    </span>
                  )}
                </p>
              </div>
            </div>

            <div>
              <p
                className="stat-card__label"
                style={{ marginBottom: "0.4rem" }}
              >
                Summary
              </p>
              {resume.summary ? (
                <p style={{ margin: 0 }}>{resume.summary}</p>
              ) : (
                <p className="muted text-sm">
                  No summary was extracted from the resume.
                </p>
              )}
            </div>

            <div>
              <p
                className="stat-card__label"
                style={{ marginBottom: "0.4rem" }}
              >
                Skills
              </p>
              {resume.skills.length > 0 ? (
                <div className="chip-row">
                  {resume.skills.map((skill, index) => (
                    <SkillChip key={`${skill}-${index}`}>
                      {skill}
                    </SkillChip>
                  ))}
                </div>
              ) : (
                <p className="muted text-sm">
                  No skills were extracted from the resume.
                </p>
              )}
            </div>

            <div className="grid-2">
              <div>
                <p
                  className="stat-card__label"
                  style={{ marginBottom: "0.4rem" }}
                >
                  Experience
                </p>
                {resume.experiences.length > 0 ? (
                  <ul
                    className="stack"
                    style={{ gap: "0.5rem" }}
                  >
                    {resume.experiences.map((exp, index) => (
                      <li key={index}>
                        <strong>{exp.job_title}</strong>
                        <p className="muted text-sm mt-0">
                          {exp.company} ·{" "}
                          {exp.start_date} – {exp.end_date}
                        </p>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted text-sm">
                    {resume.total_experience_months > 0
                      ? `${resume.total_experience_months} months of experience (not broken down by role).`
                      : "No structured work experience was extracted."}
                  </p>
                )}
              </div>

              <div>
                <p
                  className="stat-card__label"
                  style={{ marginBottom: "0.4rem" }}
                >
                  Education
                </p>
                {resume.education.length > 0 ? (
                  <ul
                    className="stack"
                    style={{ gap: "0.5rem" }}
                  >
                    {resume.education.map((edu, index) => (
                      <li
                        key={index}
                        style={{
                          display: "flex",
                          gap: "0.5rem",
                        }}
                      >
                        <IconGraduationCap
                          width={15}
                          height={15}
                          style={{
                            marginTop: "0.2rem",
                            flexShrink: 0,
                            color: "var(--color-text-subtle)",
                          }}
                        />
                        <div>
                          <strong>{edu.degree}</strong>
                          <p className="muted text-sm mt-0">
                            {edu.institution}
                          </p>
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted text-sm">
                    No structured education was extracted.
                  </p>
                )}
              </div>
            </div>

            <div>
              <p
                className="stat-card__label"
                style={{ marginBottom: "0.4rem" }}
              >
                Projects
              </p>
              {resume.projects.length > 0 ? (
                <ul
                  className="stack"
                  style={{ gap: "0.75rem" }}
                >
                  {resume.projects.map((project, index) => (
                    <li key={index}>
                      <strong>{project.name}</strong>
                      {project.description && (
                        <p
                          className="muted text-sm"
                          style={{
                            marginTop: "0.15rem",
                            marginBottom:
                              project.technologies.length > 0
                                ? "0.4rem"
                                : 0,
                            whiteSpace: "pre-wrap",
                          }}
                        >
                          {project.description}
                        </p>
                      )}
                      {project.technologies.length > 0 && (
                        <div className="chip-row">
                          {project.technologies.map(
                            (tech, techIndex) => (
                              <SkillChip
                                key={techIndex}
                                tone="success"
                              >
                                {tech}
                              </SkillChip>
                            ),
                          )}
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="muted text-sm">
                  No projects were extracted from the resume.
                </p>
              )}
            </div>

            <div>
              <p
                className="stat-card__label"
                style={{ marginBottom: "0.4rem" }}
              >
                Certifications
              </p>
              {resume.certifications.length > 0 ? (
                <div className="chip-row">
                  {resume.certifications.map((cert, index) => (
                    <SkillChip key={index}>{cert}</SkillChip>
                  ))}
                </div>
              ) : (
                <p className="muted text-sm">
                  No certifications were extracted from the
                  resume.
                </p>
              )}
            </div>
          </div>
        ) : (
          <p className="muted">
            No resume profile is available for this
            application.
          </p>
        )}
      </SectionCard>

      <SectionCard title="Resume">
        <ResumeViewer
          jobId={jobId ?? ""}
          applicationId={application.application_id}
          resumeId={application.resume_id}
        />
      </SectionCard>

      {application.screening ? (
        <FeedbackPanel screening={application.screening} />
      ) : (
        <EmptyState
          title="No AI evaluation available"
          message="This application does not have a persisted screening result."
        />
      )}

      <SectionCard title="Application">
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
    </main>
  );
}
