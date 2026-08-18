import { useEffect, useState } from "react";
import type { components } from "../types/api";
import { ApiError } from "../api/client";
import { getJobs } from "../api/jobs";
import { getResumes } from "../api/resumes";
import { screenCandidates } from "../api/screening";
import PageHeader from "../components/PageHeader";
import SectionCard from "../components/SectionCard";
import { EligibilityBadge, DecisionBadge } from "../components/StatusBadge";
import ScoreBar from "../components/ScoreBar";
import { LoadingState } from "../components/UXStates";
import {
  IconCheck,
  IconWand,
} from "../components/icons";

type Job = components["schemas"]["JobResponse"];
type Resume = components["schemas"]["ResumeResponse"];
type ScreeningResponse =
  components["schemas"]["ScreeningResponse"];

type ScreeningStatus =
  | "idle"
  | "processing"
  | "success"
  | "error";

function getScreeningErrorMessage(
  error: unknown,
): string {
  if (error instanceof ApiError) {
    if (
      typeof error.data === "object" &&
      error.data !== null &&
      "detail" in error.data
    ) {
      const detail = (
        error.data as {
          detail?: unknown;
        }
      ).detail;

      if (typeof detail === "string") {
        return detail;
      }
    }

    return `Screening failed with status ${error.status}.`;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Screening failed. Please try again.";
}

export default function ScreeningPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [resumes, setResumes] = useState<Resume[]>([]);

  const [selectedJobId, setSelectedJobId] =
    useState("");

  const [selectedResumeIds, setSelectedResumeIds] =
    useState<string[]>([]);

  const [loading, setLoading] = useState(true);

  const [screeningStatus, setScreeningStatus] =
    useState<ScreeningStatus>("idle");

  const [error, setError] =
    useState<string | null>(null);

  const [result, setResult] =
    useState<ScreeningResponse | null>(null);

  const screening =
    screeningStatus === "processing";

  useEffect(() => {
    const token =
      localStorage.getItem("access_token");

    if (!token) {
      setError("Authentication required.");
      setLoading(false);
      return;
    }

    Promise.all([
      getJobs(token),
      getResumes(token),
    ])
      .then(([jobsData, resumesData]) => {
        setJobs(jobsData);
        setResumes(resumesData);
      })
      .catch((err) => {
        console.error(
          "Failed to load screening data:",
          err,
        );

        setError(
          "Failed to load jobs and resumes.",
        );
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  function toggleResume(
    resumeId: string,
  ) {
    if (screening) {
      return;
    }

    setSelectedResumeIds((current) => {
      if (current.includes(resumeId)) {
        return current.filter(
          (id) => id !== resumeId,
        );
      }

      return [...current, resumeId];
    });
  }

  function selectAllResumes() {
    if (screening) {
      return;
    }

    setSelectedResumeIds(
      resumes.map(
        (resume) => resume.resume_id,
      ),
    );
  }

  function clearResumeSelection() {
    if (screening) {
      return;
    }

    setSelectedResumeIds([]);
  }

  async function handleScreening() {
    const token =
      localStorage.getItem("access_token");

    if (!token) {
      setError("Authentication required.");
      setScreeningStatus("error");
      return;
    }

    if (!selectedJobId) {
      setError("Please select a job.");
      setScreeningStatus("error");
      return;
    }

    if (selectedResumeIds.length === 0) {
      setError(
        "Please select at least one resume.",
      );
      setScreeningStatus("error");
      return;
    }

    const selectedJob = jobs.find(
      (job) =>
        job.job_id === selectedJobId,
    );

    if (!selectedJob) {
      setError(
        "Selected job was not found.",
      );
      setScreeningStatus("error");
      return;
    }

    const selectedResumes =
      resumes.filter((resume) =>
        selectedResumeIds.includes(
          resume.resume_id,
        ),
      );

    setScreeningStatus("processing");
    setError(null);
    setResult(null);

    try {
      const response =
        await screenCandidates(
          selectedJob,
          selectedResumes,
          token,
        );

      setResult(response);
      setScreeningStatus("success");
    } catch (err) {
      console.error(
        "Screening failed:",
        err,
      );

      setError(
        getScreeningErrorMessage(err),
      );

      setScreeningStatus("error");
    }
  }

  if (loading) {
    return (
      <main>
        <PageHeader
          eyebrow="Screening"
          title="Screening Setup"
          subtitle="Run AI-assisted eligibility screening for candidates against a job."
        />
        <LoadingState message="Loading jobs and resumes..." />
      </main>
    );
  }

  const selectedJob = jobs.find(
    (job) => job.job_id === selectedJobId,
  );

  const stepIndex = !selectedJobId
    ? 1
    : selectedResumeIds.length === 0
      ? 2
      : screeningStatus === "success"
        ? 4
        : 3;

  const shortlistedCount =
    result?.results.filter(
      (candidate) =>
        typeof candidate.decision === "string" &&
        candidate.decision.toLowerCase() === "shortlist",
    ).length ?? 0;

  return (
    <main>
      <PageHeader
        eyebrow="Screening"
        title="Screening Setup"
        subtitle="Run AI-assisted eligibility screening for candidates against a job."
      />

      <ol className="steps">
        {[
          "Select Job",
          "Select Candidates",
          "Run Screening",
          "Review Results",
        ].map((label, index) => {
          const num = index + 1;
          const stateClass =
            num === stepIndex
              ? " step--active"
              : num < stepIndex
                ? " step--done"
                : "";

          return (
            <li key={label} className={`step${stateClass}`}>
              <span className="step__num">
                {num < stepIndex ? (
                  <IconCheck width={11} height={11} strokeWidth={3} />
                ) : (
                  num
                )}
              </span>
              {label}
            </li>
          );
        })}
      </ol>

      {error && (
        <div
          role="alert"
          className="state-panel state-panel--error"
          style={{ marginBottom: "1.5rem" }}
        >
          <h2>Screening could not run</h2>
          <p>{error}</p>

          {screeningStatus === "error" && (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleScreening}
              disabled={
                screening ||
                !selectedJobId ||
                selectedResumeIds.length ===
                  0
              }
            >
              Retry Screening
            </button>
          )}
        </div>
      )}

      {screeningStatus === "processing" && (
        <div
          aria-live="polite"
          className="state-panel"
          style={{ marginBottom: "1.5rem" }}
        >
          <span className="spinner" aria-hidden="true" />
          <h2>
            Screening in Progress
          </h2>

          <p>
            Screening{" "}
            {selectedResumeIds.length}{" "}
            candidate
            {selectedResumeIds.length === 1
              ? ""
              : "s"}{" "}
            against the selected job...
          </p>

          <p>
            The screening pipeline is
            running eligibility, ranking,
            decision analysis and
            explanation.
          </p>
        </div>
      )}

      {screeningStatus === "success" &&
        result && (
          <div
            aria-live="polite"
            className="state-panel"
            style={{
              marginBottom: "1.5rem",
              borderStyle: "solid",
              borderColor: "var(--color-success-border)",
              background: "var(--color-success-soft)",
            }}
          >
            <IconCheck
              width={26}
              height={26}
              style={{ color: "var(--color-success)" }}
            />
            <h2>
              Screening Completed
            </h2>

            <p>
              Screening completed
              successfully for{" "}
              {result.total_candidates}{" "}
              candidate
              {result.total_candidates ===
              1
                ? ""
                : "s"}.
            </p>
          </div>
        )}

      <div className="workflow-layout">
        <div className="stack">
          <SectionCard title="1. Select Job Description">
            {jobs.length === 0 ? (
              <p className="muted">
                No jobs available. Create a
                job before starting
                screening.
              </p>
            ) : (
              <div className="field">
                <label htmlFor="screening-job">
                  Job Description
                </label>

                <select
                  id="screening-job"
                  value={selectedJobId}
                  disabled={screening}
                  onChange={(event) => {
                    setSelectedJobId(
                      event.target.value,
                    );

                    setResult(null);
                    setError(null);

                    if (
                      event.target.value
                    ) {
                      setScreeningStatus(
                        "idle",
                      );
                    }
                  }}
                >
                  <option value="">
                    Select a job
                  </option>

                  {jobs.map((job) => (
                    <option
                      key={job.job_id}
                      value={job.job_id}
                    >
                      {job.title ??
                        job.job_id}

                      {job.location
                        ? ` — ${job.location}`
                        : ""}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </SectionCard>

          <SectionCard title="2. Select Candidate Resumes">
            {resumes.length === 0 ? (
              <p className="muted">
                No resumes available.
                Upload resumes before
                starting screening.
              </p>
            ) : (
              <>
                <div
                  className="card__actions"
                  style={{ marginBottom: "0.85rem" }}
                >
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={
                      selectAllResumes
                    }
                    disabled={screening}
                  >
                    Select All
                  </button>

                  <button
                    type="button"
                    className="btn btn-ghost"
                    onClick={
                      clearResumeSelection
                    }
                    disabled={screening}
                  >
                    Clear Selection
                  </button>
                </div>

                <p className="muted text-sm">
                  Selected:{" "}
                  {selectedResumeIds.length}{" "}
                  / {resumes.length}
                </p>

                <ul className="stack" style={{ gap: "0.5rem" }}>
                  {resumes.map(
                    (resume) => {
                      const checked =
                        selectedResumeIds.includes(
                          resume.resume_id,
                        );

                      return (
                        <li
                          key={
                            resume.resume_id
                          }
                          className="card"
                          style={{
                            margin: 0,
                            borderColor: checked
                              ? "var(--color-primary)"
                              : undefined,
                            background: checked
                              ? "var(--color-primary-soft)"
                              : undefined,
                          }}
                        >
                          <label className="checkbox-row">
                            <input
                              type="checkbox"
                              checked={checked}
                              disabled={screening}
                              onChange={() =>
                                toggleResume(
                                  resume.resume_id,
                                )
                              }
                            />

                            <span style={{ flex: 1 }}>
                              <strong>
                                {resume.name ??
                                  resume.resume_id}
                              </strong>

                              <p className="muted text-sm mt-0">
                                {resume.resume_id}
                                {resume.email && (
                                  <> — {resume.email}</>
                                )}
                                {" · "}
                                {resume.total_experience_months} months
                              </p>

                              {resume.skills.length > 0 && (
                                <span className="muted text-sm">
                                  {resume.skills.slice(0, 5).join(", ")}
                                </span>
                              )}
                            </span>
                          </label>
                        </li>
                      );
                    },
                  )}
                </ul>
              </>
            )}
          </SectionCard>
        </div>

        <div className="workflow-layout__aside">
          <SectionCard title="3. Start Screening">
            <div className="stack" style={{ gap: "0.5rem" }}>
              <p className="muted text-sm mt-0">
                Job:{" "}
                <strong>
                  {selectedJob
                    ? selectedJob.title ?? selectedJob.job_id
                    : "None selected"}
                </strong>
              </p>
              <p className="muted text-sm mt-0">
                Candidates selected:{" "}
                <strong>{selectedResumeIds.length}</strong>
              </p>
            </div>

            <button
              type="button"
              className="btn btn-primary btn-block"
              onClick={handleScreening}
              disabled={
                screening ||
                !selectedJobId ||
                selectedResumeIds.length ===
                  0
              }
            >
              {screening ? (
                <span
                  className="spinner-inline"
                  aria-hidden="true"
                />
              ) : (
                <IconWand width={16} height={16} />
              )}
              {screening
                ? "Screening..."
                : "Start Screening"}
            </button>
          </SectionCard>
        </div>
      </div>

      {result && (
        <SectionCard title="Screening Results">
          <div className="grid-4" style={{ marginBottom: "1.25rem" }}>
            <div className="stat-card">
              <div className="stat-card__body">
                <p className="stat-card__label">Screened</p>
                <p className="stat-card__value">
                  {result.total_candidates}
                </p>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-card__body">
                <p className="stat-card__label">Eligible</p>
                <p className="stat-card__value">
                  {result.eligible_candidates}
                </p>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-card__body">
                <p className="stat-card__label">Not Eligible</p>
                <p className="stat-card__value">
                  {result.total_candidates -
                    result.eligible_candidates}
                </p>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-card__body">
                <p className="stat-card__label">Shortlisted</p>
                <p className="stat-card__value">
                  {shortlistedCount}
                </p>
              </div>
            </div>
          </div>

          <h3>
            Candidate Results
          </h3>

          {result.results.length ===
          0 ? (
            <p className="muted">
              No screening results.
            </p>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Candidate</th>
                    <th>Eligibility</th>
                    <th>Decision</th>
                    <th>Match Score</th>
                  </tr>
                </thead>
                <tbody>
                  {result.results.map(
                    (
                      candidate,
                      index,
                    ) => {
                      const resumeId =
                        typeof candidate.resume_id ===
                        "string"
                          ? candidate.resume_id
                          : `candidate-${index}`;

                      const decision =
                        typeof candidate.decision ===
                        "string"
                          ? candidate.decision
                          : null;

                      const eligible =
                        typeof candidate.eligible ===
                        "boolean"
                          ? candidate.eligible
                          : false;

                      const score =
                        typeof candidate.ranking_score_percent ===
                        "number"
                          ? candidate.ranking_score_percent
                          : null;

                      return (
                        <tr key={resumeId}>
                          <td>{resumeId}</td>
                          <td>
                            <EligibilityBadge eligible={eligible} />
                          </td>
                          <td>
                            <DecisionBadge decision={decision} />
                          </td>
                          <td>
                            {score !== null ? (
                              <ScoreBar value={score} />
                            ) : (
                              "—"
                            )}
                          </td>
                        </tr>
                      );
                    },
                  )}
                </tbody>
              </table>
            </div>
          )}
        </SectionCard>
      )}
    </main>
  );
}
