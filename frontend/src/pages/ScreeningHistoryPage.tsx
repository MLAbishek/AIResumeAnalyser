import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { components } from "../types/api";
import { getJobs } from "../api/jobs";
import { getScreenings } from "../api/ranking";

type Job = components["schemas"]["JobResponse"];
type Screening =
  components["schemas"]["ScreeningResultResponse"];

function formatScore(
  score: number | null,
): string {
  if (score === null) {
    return "—";
  }

  return score.toFixed(2);
}

function formatDecision(
  decision: string | null,
): string {
  if (!decision) {
    return "—";
  }

  return decision;
}

export default function ScreeningHistoryPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJobId, setSelectedJobId] =
    useState("");

  const [results, setResults] = useState<
    Screening[]
  >([]);

  const [loadingJobs, setLoadingJobs] =
    useState(true);

  const [loadingHistory, setLoadingHistory] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const [loadedJobId, setLoadedJobId] =
    useState<string | null>(null);

  useEffect(() => {
    const token =
      localStorage.getItem("access_token");

    if (!token) {
      setError("Authentication required.");
      setLoadingJobs(false);
      return;
    }

    getJobs(token)
      .then((data) => {
        setJobs(data);
      })
      .catch((err) => {
        console.error(
          "Failed to load jobs:",
          err,
        );

        setError(
          "Failed to load jobs.",
        );
      })
      .finally(() => {
        setLoadingJobs(false);
      });
  }, []);

  async function handleLoadHistory() {
    const token =
      localStorage.getItem("access_token");

    if (!token) {
      setError("Authentication required.");
      return;
    }

    if (!selectedJobId) {
      setError("Please select a job.");
      return;
    }

    setLoadingHistory(true);
    setError(null);
    setResults([]);
    setLoadedJobId(null);

    try {
      const response =
        await getScreenings(
          selectedJobId,
          token,
        );

      setResults(response.results);
      setLoadedJobId(response.job_id);
    } catch (err) {
      console.error(
        "Failed to load screening history:",
        err,
      );

      setError(
        "Failed to load screening history.",
      );
    } finally {
      setLoadingHistory(false);
    }
  }

  const eligibleCount = useMemo(
    () =>
      results.filter(
        (result) => result.eligible,
      ).length,
    [results],
  );

  const shortlistedCount = useMemo(
    () =>
      results.filter(
        (result) =>
          result.decision?.toLowerCase() ===
          "shortlist",
      ).length,
    [results],
  );

  const rejectedCount = useMemo(
    () =>
      results.filter(
        (result) =>
          result.decision?.toLowerCase() ===
          "reject",
      ).length,
    [results],
  );

  const averageScore = useMemo(() => {
    const scoredResults = results.filter(
      (result) =>
        result.final_score !== null,
    );

    if (scoredResults.length === 0) {
      return null;
    }

    const total = scoredResults.reduce(
      (sum, result) =>
        sum + (result.final_score ?? 0),
      0,
    );

    return total / scoredResults.length;
  }, [results]);

  if (loadingJobs) {
    return (
      <main>
        <h1>Screening History & Reports</h1>
        <p>Loading jobs...</p>
      </main>
    );
  }

  return (
    <main>
      <header>
        <h1>Screening History & Reports</h1>

        <p>
          View previously persisted screening
          results for a selected job.
        </p>
      </header>

      {error && (
        <p role="alert">
          {error}
        </p>
      )}

      <section>
        <h2>Select Job</h2>

        {jobs.length === 0 ? (
          <p>
            No jobs available.
          </p>
        ) : (
          <>
            <label htmlFor="history-job">
              Job Description
            </label>

            <select
              id="history-job"
              value={selectedJobId}
              onChange={(event) => {
                setSelectedJobId(
                  event.target.value,
                );

                setResults([]);
                setLoadedJobId(null);
                setError(null);
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
                  {job.title ?? job.job_id}
                  {job.location
                    ? ` — ${job.location}`
                    : ""}
                </option>
              ))}
            </select>

            <button
              type="button"
              onClick={
                handleLoadHistory
              }
              disabled={
                loadingHistory ||
                !selectedJobId
              }
            >
              {loadingHistory
                ? "Loading History..."
                : "Load Screening History"}
            </button>
          </>
        )}
      </section>

      {loadedJobId && (
        <>
          <section>
            <h2>Screening Summary</h2>

            <p>
              <strong>Job:</strong>{" "}
              {loadedJobId}
            </p>

            <p>
              <strong>
                Total Candidates:
              </strong>{" "}
              {results.length}
            </p>

            <p>
              <strong>Eligible:</strong>{" "}
              {eligibleCount}
            </p>

            <p>
              <strong>Shortlisted:</strong>{" "}
              {shortlistedCount}
            </p>

            <p>
              <strong>Rejected:</strong>{" "}
              {rejectedCount}
            </p>

            <p>
              <strong>
                Average Score:
              </strong>{" "}
              {averageScore === null
                ? "—"
                : averageScore.toFixed(2)}
            </p>
          </section>

          <section>
            <h2>Previous Screening Results</h2>

            {results.length === 0 ? (
              <p>
                No screening results have been
                persisted for this job.
              </p>
            ) : (
              <div
                style={{
                  overflowX: "auto",
                }}
              >
                <table>
                  <thead>
                    <tr>
                      <th>Screening ID</th>
                      <th>Candidate</th>
                      <th>Resume ID</th>
                      <th>Eligibility</th>
                      <th>Decision</th>
                      <th>Final Score</th>
                      <th>Reason</th>
                      <th>Details</th>
                    </tr>
                  </thead>

                  <tbody>
                    {results.map(
                      (result) => (
                        <tr
                          key={
                            result.screening_id
                          }
                        >
                          <td>
                            {
                              result.screening_id
                            }
                          </td>

                          <td>
                            {result.candidate_name ??
                              "Unknown Candidate"}
                          </td>

                          <td>
                            {
                              result.resume_id
                            }
                          </td>

                          <td>
                            {result.eligible
                              ? "Eligible"
                              : "Not Eligible"}
                          </td>

                          <td>
                            {formatDecision(
                              result.decision,
                            )}
                          </td>

                          <td>
                            {formatScore(
                              result.final_score,
                            )}
                          </td>

                          <td>
                            {result.decision_reason ??
                              "—"}
                          </td>

                          <td>
                            <Link
                              to={`/ranking/${encodeURIComponent(
                                result.job_id,
                              )}/${encodeURIComponent(
                                result.resume_id,
                              )}`}
                            >
                              View Profile
                            </Link>
                          </td>
                        </tr>
                      ),
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}

      {!loadingHistory &&
        selectedJobId &&
        !loadedJobId &&
        !error && (
          <section>
            <p>
              Select the job and load its
              screening history.
            </p>
          </section>
        )}
    </main>
  );
}