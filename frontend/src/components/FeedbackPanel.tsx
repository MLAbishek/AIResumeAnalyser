import SectionCard from "./SectionCard";
import ScoreBar from "./ScoreBar";
import SkillChip from "./SkillChip";
import RadialScore from "./RadialScore";
import { EligibilityBadge, DecisionBadge } from "./StatusBadge";
import type { components } from "../types/api";

type ScreeningResultResponse =
  components["schemas"]["ScreeningResultResponse"];

type JsonObject = Record<string, unknown>;

function isObject(value: unknown): value is JsonObject {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

function getArray(
  object: JsonObject | null | undefined,
  key: string,
): unknown[] {
  const value = object?.[key];
  return Array.isArray(value) ? value : [];
}

function formatPercent(value: unknown): number | null {
  return typeof value === "number" ? value * 100 : null;
}

/**
 * Renders the full AI evaluation for one screening: overall score,
 * per-factor breakdown, strengths, gaps and evidence & citations.
 * Shared by the candidate match preview, a candidate's own
 * application detail, and the recruiter's candidate detail page -
 * all three present the exact same persisted evaluation, just with
 * different surrounding chrome/actions.
 */
export default function FeedbackPanel({
  screening,
}: {
  screening: ScreeningResultResponse;
}) {
  const ranking = isObject(screening.ranking)
    ? screening.ranking
    : null;

  const gapAnalysis = isObject(screening.gap_analysis)
    ? screening.gap_analysis
    : null;

  const explanation = isObject(screening.explanation)
    ? screening.explanation
    : null;

  const matchedSkills = getArray(
    gapAnalysis,
    "matched_skills",
  );
  const missingSkills = getArray(
    gapAnalysis,
    "missing_skills",
  );
  const strengths = getArray(explanation, "strengths");

  const noGaps =
    gapAnalysis?.has_gap === false ||
    (gapAnalysis === null && missingSkills.length === 0);

  const finalScorePercent =
    screening.final_score !== null
      ? screening.final_score <= 1
        ? screening.final_score * 100
        : screening.final_score
      : null;

  return (
    <div className="stack">
      <div className="card">
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
              AI Match Assessment
            </p>
            <div
              style={{
                display: "flex",
                gap: "0.5rem",
                flexWrap: "wrap",
                marginTop: "0.35rem",
              }}
            >
              <EligibilityBadge
                eligible={screening.eligible}
              />
              <DecisionBadge
                decision={screening.decision}
              />
            </div>
          </div>

          {finalScorePercent !== null && (
            <div style={{ textAlign: "center" }}>
              <p
                className="stat-card__label"
                style={{ margin: "0 0 0.35rem" }}
              >
                Overall Match Score
              </p>
              <RadialScore value={finalScorePercent} />
            </div>
          )}
        </div>

        {screening.decision_reason && (
          <p className="muted text-sm" style={{ marginTop: "0.75rem" }}>
            {screening.decision_reason}
          </p>
        )}
      </div>

      {ranking && (
        <SectionCard
          title="Match Breakdown"
          subtitle="Calculated from multiple matching signals by the AI screening pipeline."
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
        </SectionCard>
      )}

      <SectionCard title="Strengths">
        {strengths.length > 0 || matchedSkills.length > 0 ? (
          <div className="chip-row">
            {strengths.map((strength, index) => (
              <SkillChip key={`s-${index}`} tone="success">
                {String(strength)}
              </SkillChip>
            ))}
            {matchedSkills.map((skill, index) => (
              <SkillChip key={`m-${index}`} tone="success">
                {String(skill)}
              </SkillChip>
            ))}
          </div>
        ) : (
          <p className="muted">
            No specific strengths recorded.
          </p>
        )}
      </SectionCard>

      <SectionCard title="Gaps">
        {noGaps ? (
          <p className="muted">
            Excellent alignment — no requirement gaps
            identified.
          </p>
        ) : missingSkills.length > 0 ? (
          <div className="chip-row">
            {missingSkills.map((skill, index) => (
              <SkillChip key={index} tone="danger">
                {String(skill)}
              </SkillChip>
            ))}
          </div>
        ) : (
          <p className="muted">
            No significant gaps were identified.
          </p>
        )}
      </SectionCard>

      {explanation && (
        <SectionCard title="AI Match Feedback">
          <p style={{ margin: 0 }}>
            {String(
              explanation.summary ?? "No summary available.",
            )}
          </p>
        </SectionCard>
      )}

      <SectionCard title="Evidence & Citations">
        {screening.evidence && screening.evidence.length > 0 ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Claim</th>
                  <th>Source</th>
                  <th>Evidence</th>
                </tr>
              </thead>
              <tbody>
                {screening.evidence.map((reference, index) => (
                  <tr key={index}>
                    <td>{String(reference.claim ?? "—")}</td>
                    <td>{String(reference.source ?? "—")}</td>
                    <td>{String(reference.evidence ?? "—")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="muted">
            No evidence references were recorded for this
            candidate.
          </p>
        )}
      </SectionCard>
    </div>
  );
}
