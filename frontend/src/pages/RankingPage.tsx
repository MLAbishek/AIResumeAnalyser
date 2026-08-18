import {
  useEffect,
  useMemo,
  useState,
} from "react";
import { Link, useSearchParams } from "react-router-dom";
import type { components } from "../types/api";
import { getApiErrorMessage } from "../api/client";
import { getJobs } from "../api/jobs";
import {
  getScreenings,
  rankJobCandidates,
  type RankingResult,
} from "../api/ranking";
import {
  EmptyState,
  ErrorState,
  LoadingState,
  ValidationMessage,
} from "../components/UXStates";
import PageHeader from "../components/PageHeader";
import SectionCard from "../components/SectionCard";
import StatCard from "../components/StatCard";
import ScoreBar from "../components/ScoreBar";
import { EligibilityBadge, DecisionBadge } from "../components/StatusBadge";
import {
  IconBarChart,
  IconCheck,
  IconTarget,
} from "../components/icons";

type Job = components["schemas"]["JobResponse"];
type Screening =
  components["schemas"]["ScreeningResultResponse"];

type CandidateRow = RankingResult & {
  candidate_name: string | null;
  resume_id: string;
  eligible: boolean;
  decision: string | null;
  decision_reason: string | null;
};

function formatPercent(fraction: number): string {
  return `${(fraction * 100).toFixed(0)}%`;
}

export default function RankingPage() {
  const [searchParams] = useSearchParams();

  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJobId, setSelectedJobId] = useState("");

  const [rows, setRows] = useState<CandidateRow[]>([]);

  const [loadingJobs, setLoadingJobs] = useState(true);
  const [ranking, setRanking] = useState(false);

  const [error, setError] = useState<string | null>(null);

  async function loadJobs() {
    const token = localStorage.getItem("access_token");

    if (!token) {
      setError("Authentication required.");
      setLoadingJobs(false);
      return;
    }

    setLoadingJobs(true);
    setError(null);

    try {
      const data = await getJobs(token);
      setJobs(data);
    } catch (err) {
      console.error("Failed to load jobs:", err);
      setError(
        getApiErrorMessage(
          err,
          "Failed to load jobs.",
        ),
      );
    } finally {
      setLoadingJobs(false);
    }
  }

  useEffect(() => {
    void loadJobs();
  }, []);

  useEffect(() => {
    const jobIdFromQuery = searchParams.get("jobId");

    if (
      jobIdFromQuery &&
      jobs.some(
        (job) => job.job_id === jobIdFromQuery,
      )
    ) {
      setSelectedJobId(jobIdFromQuery);
      void handleLoadRanking(jobIdFromQuery);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobs]);

  async function handleLoadRanking(
    jobIdOverride?: string,
  ) {
    const token = localStorage.getItem("access_token");

    const targetJobId =
      jobIdOverride ?? selectedJobId;

    if (!token) {
      setError("Authentication required.");
      return;
    }

    if (!targetJobId) {
      setError("Please select a job.");
      return;
    }

    setRanking(true);
    setError(null);
    setRows([]);

    try {
      const [rankingResponse, screeningResponse] =
        await Promise.all([
          rankJobCandidates(
            targetJobId,
            token,
          ),
          getScreenings(
            targetJobId,
            token,
          ),
        ]);

      const screeningsById = new Map<
        number,
        Screening
      >();

      screeningResponse.results.forEach(
        (screening) => {
          screeningsById.set(
            screening.screening_id,
            screening,
          );
        },
      );

      const mergedRows: CandidateRow[] =
        rankingResponse.results.map(
          (rankingResult) => {
            const screening =
              screeningsById.get(
                rankingResult.screening_id,
              );

            return {
              ...rankingResult,
              candidate_name:
                screening?.candidate_name ?? null,
              resume_id:
                screening?.resume_id ??
                `screening-${rankingResult.screening_id}`,
              eligible:
                screening?.eligible ?? false,
              decision:
                screening?.decision ?? null,
              decision_reason:
                screening?.decision_reason ?? null,
            };
          },
        );

      mergedRows.sort(
        (a, b) => a.rank - b.rank,
      );

      setRows(mergedRows);
    } catch (err) {
      console.error(
        "Failed to load ranking:",
        err,
      );

      setError(
        getApiErrorMessage(
          err,
          "Failed to load ranking. Make sure screening has been completed for this job.",
        ),
      );
    } finally {
      setRanking(false);
    }
  }

  const eligibleCount = useMemo(
    () =>
      rows.filter(
        (row) => row.eligible,
      ).length,
    [rows],
  );

  const averageScore = useMemo(() => {
    if (rows.length === 0) {
      return 0;
    }

    return (
      rows.reduce(
        (total, row) => total + row.score,
        0,
      ) / rows.length
    );
  }, [rows]);

  const selectedJob = jobs.find(
    (job) => job.job_id === selectedJobId,
  );

  if (loadingJobs) {
    return (
      <main>
        <PageHeader
          eyebrow="Ranking"
          title="Candidate Ranking"
        />
        <LoadingState message="Loading jobs..." />
      </main>
    );
  }

  return (
    <main>
      <PageHeader
        eyebrow="Ranking"
        title="Candidate Ranking"
        subtitle="AI-ranked candidates based on job requirements and semantic matching."
      />

      {error && (
        <ErrorState
          message={error}
          onRetry={
            error === "Please select a job."
              ? undefined
              : () => {
                  if (selectedJobId) {
                    void handleLoadRanking();
                  } else {
                    void loadJobs();
                  }
                }
          }
        />
      )}

      <SectionCard title="Select Job">
        {jobs.length === 0 ? (
          <EmptyState
            title="No jobs available"
            message="Create a job before viewing candidate rankings."
          />
        ) : (
          <>
            <div className="field">
              <label htmlFor="ranking-job">
                Job Description
              </label>

              <select
                id="ranking-job"
                value={selectedJobId}
                onChange={(event) => {
                  setSelectedJobId(
                    event.target.value,
                  );
                  setRows([]);
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

            {!selectedJobId && (
              <ValidationMessage message="Select a job to load rankings." />
            )}

            <button
              type="button"
              className="btn btn-primary"
              onClick={() => handleLoadRanking()}
              disabled={
                ranking || !selectedJobId
              }
            >
              {ranking ? (
                <span
                  className="spinner-inline"
                  aria-hidden="true"
                />
              ) : (
                <IconBarChart width={16} height={16} />
              )}
              {ranking
                ? "Loading Ranking..."
                : "Load Ranking"}
            </button>
          </>
        )}
      </SectionCard>

      {rows.length > 0 && (
        <>
          <div className="grid-3" style={{ marginBottom: "1.5rem" }}>
            <StatCard
              icon={<IconTarget width={18} height={18} />}
              label="Candidates"
              value={rows.length}
              hint={
                selectedJob
                  ? selectedJob.title ?? selectedJob.job_id
                  : undefined
              }
            />
            <StatCard
              icon={<IconCheck width={18} height={18} />}
              label="Eligible"
              value={eligibleCount}
            />
            <StatCard
              icon={<IconBarChart width={18} height={18} />}
              label="Average Score"
              value={formatPercent(averageScore)}
            />
          </div>

          <SectionCard title="Ranked Candidates">
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Candidate</th>
                    <th>Overall Score</th>
                    <th>Eligibility</th>
                    <th>Decision</th>
                    <th>Skills</th>
                    <th>Experience</th>
                    <th>Seniority</th>
                    <th>Education</th>
                    <th>Semantic</th>
                  </tr>
                </thead>

                <tbody>
                  {rows.map((candidate) => (
                    <tr
                      key={
                        candidate.screening_id
                      }
                    >
                      <td>
                        <span
                          className={`rank-badge${
                            candidate.rank <= 3
                              ? " rank-badge--top"
                              : ""
                          }`}
                        >
                          {candidate.rank}
                        </span>
                      </td>

                      <td>
                        <Link
                          to={`/ranking/${encodeURIComponent(
                            selectedJobId,
                          )}/${encodeURIComponent(
                            candidate.resume_id,
                          )}`}
                        >
                          {candidate.candidate_name ??
                            "Unknown Candidate"}
                        </Link>
                        <p className="muted text-sm mt-0">
                          {candidate.resume_id}
                        </p>
                      </td>

                      <td>
                        <ScoreBar
                          value={candidate.score * 100}
                        />
                      </td>

                      <td>
                        <EligibilityBadge
                          eligible={candidate.eligible}
                        />
                      </td>

                      <td>
                        <DecisionBadge
                          decision={candidate.decision}
                        />
                      </td>

                      <td>
                        {formatPercent(
                          candidate.skill_score,
                        )}
                      </td>

                      <td>
                        {formatPercent(
                          candidate.experience_score,
                        )}
                      </td>

                      <td>
                        {formatPercent(
                          candidate.seniority_score,
                        )}
                      </td>

                      <td>
                        {formatPercent(
                          candidate.education_score,
                        )}
                      </td>

                      <td>
                        {formatPercent(
                          candidate.semantic_score,
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </SectionCard>
        </>
      )}

      {!ranking &&
        selectedJobId &&
        rows.length === 0 &&
        !error && (
          <EmptyState
            title="No ranking results"
            message="No eligible candidates are available for this job."
          />
        )}
    </main>
  );
}
