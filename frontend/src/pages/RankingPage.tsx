import { useEffect, useMemo, useState } from "react";
import type { components } from "../types/api";
import { getJobs } from "../api/jobs";
import {
  getScreenings,
  rankJobCandidates,
  type RankingResult,
} from "../api/ranking";

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

export default function RankingPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJobId, setSelectedJobId] = useState("");

  const [rows, setRows] = useState<CandidateRow[]>([]);

  const [loadingJobs, setLoadingJobs] = useState(true);
  const [ranking, setRanking] = useState(false);

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("access_token");

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
        console.error("Failed to load jobs:", err);
        setError("Failed to load jobs.");
      })
      .finally(() => {
        setLoadingJobs(false);
      });
  }, []);

  async function handleLoadRanking() {
    const token = localStorage.getItem("access_token");

    if (!token) {
      setError("Authentication required.");
      return;
    }

    if (!selectedJobId) {
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
            selectedJobId,
            token,
          ),
          getScreenings(
            selectedJobId,
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
        "Failed to load ranking. Make sure screening has been completed for this job.",
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

  if (loadingJobs) {
    return (
      <main>
        <h1>Candidate Ranking</h1>
        <p>Loading jobs...</p>
      </main>
    );
  }

  return (
    <main>
      <h1>Candidate Ranking Dashboard</h1>

      {error && (
        <p role="alert">
          {error}
        </p>
      )}

      <section>
        <h2>Select Job</h2>

        {jobs.length === 0 ? (
          <p>
            No jobs available. Create a job
            before viewing rankings.
          </p>
        ) : (
          <>
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

            <button
              type="button"
              onClick={handleLoadRanking}
              disabled={
                ranking || !selectedJobId
              }
            >
              {ranking
                ? "Loading Ranking..."
                : "Load Ranking"}
            </button>
          </>
        )}
      </section>

      {rows.length > 0 && (
        <>
          <section>
            <h2>Ranking Summary</h2>

            <p>
              <strong>
                Candidates:
              </strong>{" "}
              {rows.length}
            </p>

            <p>
              <strong>
                Eligible:
              </strong>{" "}
              {eligibleCount}
            </p>

            <p>
              <strong>
                Average Score:
              </strong>{" "}
              {averageScore.toFixed(2)}
            </p>
          </section>

          <section>
            <h2>Ranked Candidates</h2>

            <div
              style={{
                overflowX: "auto",
              }}
            >
              <table>
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Candidate</th>
                    <th>Resume ID</th>
                    <th>Score</th>
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
                        {candidate.rank}
                      </td>

                      <td>
                        {candidate.candidate_name ??
                          "Unknown Candidate"}
                      </td>

                      <td>
                        {candidate.resume_id}
                      </td>

                      <td>
                        {candidate.score.toFixed(
                          2,
                        )}
                      </td>

                      <td>
                        {candidate.eligible
                          ? "Eligible"
                          : "Not Eligible"}
                      </td>

                      <td>
                        {candidate.decision ??
                          "—"}
                      </td>

                      <td>
                        {candidate.skill_score.toFixed(
                          2,
                        )}
                      </td>

                      <td>
                        {candidate.experience_score.toFixed(
                          2,
                        )}
                      </td>

                      <td>
                        {candidate.seniority_score.toFixed(
                          2,
                        )}
                      </td>

                      <td>
                        {candidate.education_score.toFixed(
                          2,
                        )}
                      </td>

                      <td>
                        {candidate.semantic_score.toFixed(
                          2,
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}

      {!ranking &&
        selectedJobId &&
        rows.length === 0 &&
        !error && (
          <section>
            <p>
              No ranking results available for
              this job.
            </p>
          </section>
        )}
    </main>
  );
}
