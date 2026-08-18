import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { components } from "../types/api";
import { getApiErrorMessage } from "../api/client";
import { getJobs } from "../api/jobs";
import { getScreenings } from "../api/ranking";
import {
  EmptyState,
  ErrorState,
  LoadingState,
} from "../components/UXStates";
import PageHeader from "../components/PageHeader";
import SectionCard from "../components/SectionCard";
import StatCard from "../components/StatCard";
import { EligibilityBadge, DecisionBadge } from "../components/StatusBadge";
import {
  IconBarChart,
  IconCheck,
  IconHistory,
} from "../components/icons";

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
          getApiErrorMessage(
            err,
            "Failed to load jobs.",
          ),
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
        getApiErrorMessage(
          err,
          "Failed to load screening history.",
        ),
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
        <PageHeader
          eyebrow="History"
          title="Screening History & Reports"
        />
        <LoadingState message="Loading jobs..." />
      </main>
    );
  }

  return (
    <main>
      <PageHeader
        eyebrow="History"
        title="Screening History & Reports"
        subtitle="Review previously persisted screening results for a selected job."
      />

      {error && (
        <ErrorState
          message={error}
          onRetry={
            selectedJobId
              ? handleLoadHistory
              : undefined
          }
        />
      )}

      <SectionCard title="Select Job">
        {jobs.length === 0 ? (
          <EmptyState
            title="No jobs available"
            message="Create a job before viewing screening history."
          />
        ) : (
          <>
            <div className="field">
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
            </div>

            <button
              type="button"
              className="btn btn-primary"
              onClick={
                handleLoadHistory
              }
              disabled={
                loadingHistory ||
                !selectedJobId
              }
            >
              {loadingHistory ? (
                <span
                  className="spinner-inline"
                  aria-hidden="true"
                />
              ) : (
                <IconHistory width={16} height={16} />
              )}
              {loadingHistory
                ? "Loading History..."
                : "Load Screening History"}
            </button>
          </>
        )}
      </SectionCard>

      {loadedJobId && (
        <>
          <div className="grid-4" style={{ marginBottom: "1.5rem" }}>
            <StatCard
              icon={<IconBarChart width={18} height={18} />}
              label="Total Candidates"
              value={results.length}
            />
            <StatCard
              icon={<IconCheck width={18} height={18} />}
              label="Eligible"
              value={eligibleCount}
            />
            <StatCard
              label="Shortlisted"
              value={shortlistedCount}
            />
            <StatCard
              label="Rejected"
              value={rejectedCount}
            />
          </div>

          <SectionCard
            title="Previous Screening Results"
            subtitle={
              averageScore !== null
                ? `Average score: ${averageScore.toFixed(2)}`
                : undefined
            }
          >
            {results.length === 0 ? (
              <EmptyState
                title="No screening results"
                message="No screening results have been persisted for this job."
              />
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Candidate</th>
                      <th>Resume ID</th>
                      <th>Eligibility</th>
                      <th>Decision</th>
                      <th>Score</th>
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
                            {result.candidate_name ??
                              "Unknown Candidate"}
                          </td>

                          <td>
                            {
                              result.resume_id
                            }
                          </td>

                          <td>
                            <EligibilityBadge
                              eligible={result.eligible}
                            />
                          </td>

                          <td>
                            <DecisionBadge
                              decision={result.decision}
                            />
                          </td>

                          <td>
                            {formatScore(
                              result.final_score,
                            )}
                          </td>

                          <td className="muted text-sm">
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
          </SectionCard>
        </>
      )}

      {!loadingHistory &&
        selectedJobId &&
        !loadedJobId &&
        !error && (
          <p className="muted">
            Select the job and load its
            screening history.
          </p>
        )}
    </main>
  );
}
