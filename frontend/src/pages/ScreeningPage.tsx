import { useEffect, useState } from "react";
import type { components } from "../types/api";
import { ApiError } from "../api/client";
import { getJobs } from "../api/jobs";
import { getResumes } from "../api/resumes";
import { screenCandidates } from "../api/screening";

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
        <h1>Screening Setup</h1>
        <p>
          Loading jobs and resumes...
        </p>
      </main>
    );
  }

  return (
    <main>
      <h1>Screening Setup</h1>

      {error && (
        <section>
          <p role="alert">
            {error}
          </p>

          {screeningStatus === "error" && (
            <button
              type="button"
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
        </section>
      )}

      {screeningStatus === "processing" && (
        <section
          aria-live="polite"
        >
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
        </section>
      )}

      {screeningStatus === "success" &&
        result && (
          <section
            aria-live="polite"
          >
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
          </section>
        )}

      <section>
        <h2>
          1. Select Job Description
        </h2>

        {jobs.length === 0 ? (
          <p>
            No jobs available. Create a
            job before starting
            screening.
          </p>
        ) : (
          <div>
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
      </section>

      <section>
        <h2>
          2. Select Candidate Resumes
        </h2>

        {resumes.length === 0 ? (
          <p>
            No resumes available.
            Upload resumes before
            starting screening.
          </p>
        ) : (
          <>
            <div>
              <button
                type="button"
                onClick={
                  selectAllResumes
                }
                disabled={screening}
              >
                Select All
              </button>

              <button
                type="button"
                onClick={
                  clearResumeSelection
                }
                disabled={screening}
              >
                Clear Selection
              </button>
            </div>

            <p>
              Selected:{" "}
              {selectedResumeIds.length}{" "}
              / {resumes.length}
            </p>

            <ul>
              {resumes.map(
                (resume) => (
                  <li
                    key={
                      resume.resume_id
                    }
                  >
                    <label>
                      <input
                        type="checkbox"
                        checked={selectedResumeIds.includes(
                          resume.resume_id,
                        )}
                        disabled={screening}
                        onChange={() =>
                          toggleResume(
                            resume.resume_id,
                          )
                        }
                      />

                      {" "}

                      <strong>
                        {resume.name ??
                          resume.resume_id}
                      </strong>

                      {resume.email && (
                        <span>
                          {" "}—{" "}
                          {resume.email}
                        </span>
                      )}
                    </label>
                  </li>
                ),
              )}
            </ul>
          </>
        )}
      </section>

      <section>
        <h2>
          3. Start Screening
        </h2>

        <button
          type="button"
          onClick={handleScreening}
          disabled={
            screening ||
            !selectedJobId ||
            selectedResumeIds.length ===
              0
          }
        >
          {screening
            ? "Screening..."
            : "Start Screening"}
        </button>
      </section>

      {result && (
        <section>
          <h2>
            Screening Results
          </h2>

          <p>
            <strong>
              Job:
            </strong>{" "}
            {result.job_id}
          </p>

          <p>
            <strong>
              Total Candidates:
            </strong>{" "}
            {result.total_candidates}
          </p>

          <p>
            <strong>
              Eligible Candidates:
            </strong>{" "}
            {result.eligible_candidates}
          </p>

          <h3>
            Candidate Results
          </h3>

          {result.results.length ===
          0 ? (
            <p>
              No screening results.
            </p>
          ) : (
            <ul>
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
                      : "Unknown";

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
                    <li
                      key={resumeId}
                    >
                      <strong>
                        {resumeId}
                      </strong>

                      {" — "}

                      <span>
                        {eligible
                          ? "Eligible"
                          : "Not Eligible"}
                      </span>

                      {" — Decision: "}

                      <span>
                        {decision}
                      </span>

                      {score !==
                        null && (
                        <span>
                          {" — Score: "}
                          {score.toFixed(
                            2,
                          )}
                          %
                        </span>
                      )}
                    </li>
                  );
                },
              )}
            </ul>
          )}
        </section>
      )}
    </main>
  );
}