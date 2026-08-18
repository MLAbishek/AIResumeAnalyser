import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getApiErrorMessage } from "../api/client";
import {
  EmptyState,
  ErrorState,
  LoadingState,
} from "../components/UXStates";
import type { components } from "../types/api";
import { getCandidateMatchProfile } from "../api/matchProfile";
import PageHeader from "../components/PageHeader";
import SectionCard from "../components/SectionCard";
import ScoreBar from "../components/ScoreBar";
import SkillChip from "../components/SkillChip";
import { EligibilityBadge, DecisionBadge } from "../components/StatusBadge";
import { IconCheck } from "../components/icons";

type CandidateMatchProfile =
  components["schemas"]["ScreeningResultResponse"];

type JsonObject = Record<string, unknown>;

function isObject(
  value: unknown,
): value is JsonObject {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

function formatValue(
  value: unknown,
): string {
  if (value === null || value === undefined) {
    return "—";
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  if (typeof value === "number") {
    return value.toFixed(2);
  }

  if (typeof value === "string") {
    return value;
  }

  return JSON.stringify(value);
}

function formatList(
  value: unknown,
): string {
  if (!Array.isArray(value)) {
    return "—";
  }

  if (value.length === 0) {
    return "None";
  }

  return value
    .map((item) => String(item))
    .join(", ");
}

function formatPercent(
  value: unknown,
): number | null {
  if (typeof value !== "number") {
    return null;
  }

  return value * 100;
}

function getArray(
  object: JsonObject | null | undefined,
  key: string,
): unknown[] {
  const value = object?.[key];

  return Array.isArray(value)
    ? value
    : [];
}


function getNumber(
  object: JsonObject | null | undefined,
  key: string,
): number | null {
  const value = object?.[key];

  return typeof value === "number"
    ? value
    : null;
}


export default function CandidateMatchProfilePage() {
  const {
    jobId,
    resumeId,
  } = useParams<{
    jobId: string;
    resumeId: string;
  }>();

  const [profile, setProfile] =
    useState<CandidateMatchProfile | null>(
      null,
    );

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  useEffect(() => {
    const token =
      localStorage.getItem(
        "access_token",
      );

    if (!token) {
      setError(
        "Authentication required.",
      );
      setLoading(false);
      return;
    }

    if (!jobId || !resumeId) {
      setError(
        "Job ID and resume ID are required.",
      );
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    getCandidateMatchProfile(
      jobId,
      resumeId,
      token,
    )
      .then((data) => {
        setProfile(data);
      })
      .catch((err) => {
        console.error(
          "Failed to load candidate match profile:",
          err,
        );

        setError(
          getApiErrorMessage(
            err,
            "Failed to load candidate match profile.",
          ),
        );
      })
      .finally(() => {
        setLoading(false);
      });
  }, [jobId, resumeId]);

  const backLink = (
    <Link
      to={
        jobId
          ? `/ranking?jobId=${encodeURIComponent(
              jobId,
            )}`
          : "/ranking"
      }
      className="btn btn-ghost"
      style={{ marginBottom: "1rem" }}
    >
      ← Back to Ranking
    </Link>
  );

  if (loading) {
    return (
      <main>
        <PageHeader
          eyebrow="Candidate Intelligence"
          title="Candidate Match Profile"
        />
        <LoadingState
          message="Loading candidate match profile..."
        />
      </main>
    );
  }

  if (error) {
    return (
      <main>
        <PageHeader
          eyebrow="Candidate Intelligence"
          title="Candidate Match Profile"
        />

        <ErrorState
          message={error}
          onRetry={() => {
            window.location.reload();
          }}
        />

        <Link
          to={
            jobId
              ? `/ranking?jobId=${encodeURIComponent(
                  jobId,
                )}`
              : "/ranking"
          }
        >
          Back to Ranking
        </Link>
      </main>
    );
  }

  if (!profile) {
    return (
      <main>
        <PageHeader
          eyebrow="Candidate Intelligence"
          title="Candidate Match Profile"
        />
        <EmptyState
          title="Candidate not found"
          message="No match profile exists for this candidate."
        />

        <Link to="/ranking">
          Back to Ranking
        </Link>
      </main>
    );
  }

  const ranking = isObject(
    profile.ranking,
  )
    ? profile.ranking
    : null;

  const gapAnalysis = isObject(
    profile.gap_analysis,
  )
    ? profile.gap_analysis
    : null;

  const explanation = isObject(
    profile.explanation,
  )
    ? profile.explanation
    : null;


  const finalScore =
    profile.final_score !== null
      ? profile.final_score
      : ranking
        ? getNumber(
            ranking,
            "score",
          )
        : null;

  const finalScorePercent =
    finalScore !== null
      ? finalScore <= 1
        ? finalScore * 100
        : finalScore
      : null;

  const matchedSkills = getArray(
    gapAnalysis,
    "matched_skills",
  );

  const missingSkills = getArray(
    gapAnalysis,
    "missing_skills",
  );

  const strengths = getArray(
    explanation,
    "strengths",
  );

  const explanationGaps = getArray(
    explanation,
    "gaps",
  );

  const noGaps =
    gapAnalysis?.has_gap === false ||
    (gapAnalysis === null &&
      missingSkills.length === 0 &&
      explanationGaps.length === 0);

  return (
    <main>
      {backLink}

      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "space-between",
            alignItems: "flex-start",
            gap: "1rem",
          }}
        >
          <div>
            <p className="page-header__eyebrow">
              Candidate Match Profile
            </p>
            <h1 className="mt-0">
              {profile.candidate_name ??
                "Unknown Candidate"}
            </h1>
            <p className="muted text-sm">
              Resume ID: {profile.resume_id} · Job ID:{" "}
              {profile.job_id} · Screening ID:{" "}
              {profile.screening_id}
            </p>

            <div
              style={{
                display: "flex",
                gap: "0.5rem",
                flexWrap: "wrap",
                marginTop: "0.5rem",
              }}
            >
              <EligibilityBadge eligible={profile.eligible} />
              <DecisionBadge decision={profile.decision} />
            </div>
          </div>

          {finalScorePercent !== null && (
            <div style={{ textAlign: "right", minWidth: "140px" }}>
              <p className="stat-card__label" style={{ margin: 0 }}>
                Overall Match Score
              </p>
              <p
                className="stat-card__value"
                style={{ fontSize: "2rem" }}
              >
                {finalScorePercent.toFixed(1)}%
              </p>
            </div>
          )}
        </div>
      </div>

      <div className="stack">
        <SectionCard title="Match Overview">
          <div className="grid-3">
            <div>
              <p className="stat-card__label">Eligibility</p>
              <p className="mt-0">
                {profile.eligible
                  ? "Eligible"
                  : "Not Eligible"}
              </p>
            </div>
            <div>
              <p className="stat-card__label">Decision</p>
              <p className="mt-0">
                {profile.decision ?? "—"}
              </p>
            </div>
            <div>
              <p className="stat-card__label">
                Final Score
              </p>
              <p className="mt-0">
                {finalScore !== null
                  ? finalScore.toFixed(2)
                  : "—"}
              </p>
            </div>
          </div>

          <p className="stat-card__label">Decision Reason</p>
          <p className="mt-0">
            {profile.decision_reason ?? "—"}
          </p>
        </SectionCard>

        {ranking && (
          <SectionCard
            title="Match Breakdown"
            subtitle="The candidate's ranking is calculated from multiple matching signals."
          >
            <div className="stack" style={{ gap: "0.9rem" }}>
              {(
                [
                  ["Skills", "skill_score"],
                  ["Experience", "experience_score"],
                  ["Seniority", "seniority_score"],
                  ["Education", "education_score"],
                  ["Semantic Match", "semantic_score"],
                ] as const
              ).map(([label, key]) => {
                const percent = formatPercent(ranking[key]);

                return (
                  <div key={key}>
                    <p
                      className="stat-card__label"
                      style={{ marginBottom: "0.3rem" }}
                    >
                      {label}
                    </p>
                    <ScoreBar value={percent ?? 0} />
                  </div>
                );
              })}
            </div>

            <hr className="divider" />

            <p style={{ margin: 0 }}>
              <strong>Overall Ranking Score:</strong>{" "}
              {formatPercent(ranking.score)?.toFixed(1) ?? "—"}%
            </p>
          </SectionCard>
        )}

        <SectionCard title="Strengths">
          {strengths.length > 0 ? (
            <div className="chip-row">
              {strengths.map((strength, index) => (
                <SkillChip key={index} tone="success">
                  {String(strength)}
                </SkillChip>
              ))}
            </div>
          ) : (
            <p className="muted">
              No specific strengths recorded.
            </p>
          )}

          {matchedSkills.length > 0 && (
            <>
              <p className="stat-card__label" style={{ marginTop: "1rem" }}>
                Matched Skills
              </p>
              <div className="chip-row">
                {matchedSkills.map((skill, index) => (
                  <SkillChip key={index} tone="success">
                    {String(skill)}
                  </SkillChip>
                ))}
              </div>
            </>
          )}
        </SectionCard>

        <SectionCard title="Gaps">
          {noGaps ? (
            <p className="muted">
              Excellent alignment — no requirement gaps
              identified.
            </p>
          ) : (
            <div className="stack" style={{ gap: "1rem" }}>
              {missingSkills.length > 0 && (
                <div>
                  <p className="stat-card__label">
                    Missing Skills
                  </p>
                  <div className="chip-row">
                    {missingSkills.map((skill, index) => (
                      <SkillChip key={index} tone="danger">
                        {String(skill)}
                      </SkillChip>
                    ))}
                  </div>
                </div>
              )}

              {gapAnalysis &&
                isObject(gapAnalysis.experience_gap) && (
                  <div className="state-panel state-panel--error" style={{ textAlign: "left", alignItems: "flex-start" }}>
                    <h3 className="mt-0">Experience Gap</h3>
                    <p style={{ margin: 0 }}>
                      Required:{" "}
                      {formatValue(
                        gapAnalysis.experience_gap
                          .required_years,
                      )}{" "}
                      years · Candidate:{" "}
                      {formatValue(
                        gapAnalysis.experience_gap
                          .candidate_years,
                      )}{" "}
                      years · Gap:{" "}
                      {formatValue(
                        gapAnalysis.experience_gap
                          .gap_years,
                      )}{" "}
                      years
                    </p>
                  </div>
                )}

              {gapAnalysis &&
                isObject(gapAnalysis.education_gap) && (
                  <div className="state-panel state-panel--error" style={{ textAlign: "left", alignItems: "flex-start" }}>
                    <h3 className="mt-0">Education Gap</h3>
                    <p style={{ margin: 0 }}>
                      Required:{" "}
                      {formatList(
                        gapAnalysis.education_gap.required,
                      )}{" "}
                      · Candidate:{" "}
                      {formatList(
                        gapAnalysis.education_gap.candidate,
                      )}{" "}
                      · Missing:{" "}
                      {formatList(
                        gapAnalysis.education_gap.missing,
                      )}
                    </p>
                  </div>
                )}

              {gapAnalysis &&
                isObject(gapAnalysis.certification_gap) && (
                  <div className="state-panel state-panel--error" style={{ textAlign: "left", alignItems: "flex-start" }}>
                    <h3 className="mt-0">
                      Certification Gap
                    </h3>
                    <p style={{ margin: 0 }}>
                      Required:{" "}
                      {formatList(
                        gapAnalysis.certification_gap
                          .required,
                      )}{" "}
                      · Candidate:{" "}
                      {formatList(
                        gapAnalysis.certification_gap
                          .candidate,
                      )}{" "}
                      · Missing:{" "}
                      {formatList(
                        gapAnalysis.certification_gap
                          .missing,
                      )}
                    </p>
                  </div>
                )}

              {explanationGaps.length > 0 && (
                <div>
                  <p className="stat-card__label">
                    Identified Gaps
                  </p>
                  <ul className="stack" style={{ gap: "0.3rem" }}>
                    {explanationGaps.map((gap, index) => (
                      <li key={index}>{String(gap)}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </SectionCard>

        {explanation && (
          <SectionCard title="Why This Decision Was Made">
            <p>
              <strong>Decision:</strong>{" "}
              {formatValue(explanation.decision)}
            </p>

            <p>
              <strong>Summary:</strong>{" "}
              {formatValue(explanation.summary)}
            </p>

            <p className="stat-card__label">
              Supporting Reasons
            </p>
            {getArray(explanation, "reasons").length > 0 ? (
              <ul className="stack" style={{ gap: "0.3rem" }}>
                {getArray(explanation, "reasons").map(
                  (reason, index) => (
                    <li key={index}>{String(reason)}</li>
                  ),
                )}
              </ul>
            ) : (
              <p className="muted">No reasons recorded.</p>
            )}
          </SectionCard>
        )}

        <SectionCard title="Evidence & Citations">
          {profile.evidence && profile.evidence.length > 0 ? (
            <>
              <p className="muted text-sm">
                These evidence references show which
                candidate information supports the
                evaluation.
              </p>

              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Claim</th>
                      <th>Source</th>
                      <th>Section</th>
                      <th>Evidence</th>
                    </tr>
                  </thead>

                  <tbody>
                    {profile.evidence.map(
                      (reference, index) => (
                        <tr
                          key={
                            typeof reference.id ===
                            "number"
                              ? reference.id
                              : index
                          }
                        >
                          <td>
                            {formatValue(reference.claim)}
                          </td>
                          <td>
                            {formatValue(reference.source)}
                          </td>
                          <td>
                            {formatValue(
                              reference.section,
                            )}
                          </td>
                          <td>
                            {formatValue(
                              reference.evidence,
                            )}
                          </td>
                        </tr>
                      ),
                    )}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <p className="muted">
              No evidence references were recorded for this
              candidate.
            </p>
          )}
        </SectionCard>

        <SectionCard title="Screening Status">
          <p>
            <IconCheck
              width={14}
              height={14}
              style={{
                marginRight: "0.35rem",
                color: profile.eligible
                  ? "var(--color-success)"
                  : "var(--color-text-subtle)",
              }}
            />
            {profile.eligible
              ? "Passed eligibility filtering"
              : "Did not pass eligibility filtering"}
          </p>
          <p className="mt-0">
            <strong>Decision:</strong>{" "}
            {profile.decision ?? "Not available"}
          </p>
        </SectionCard>
      </div>
    </main>
  );
}
