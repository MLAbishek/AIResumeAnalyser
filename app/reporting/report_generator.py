from typing import Any

from app.reporting.schemas import (
    CandidateReport,
    ScreeningReport,
)


class ScreeningReportGenerator:
    """
    Converts final screening evaluations into
    human-readable screening reports.

    This component does not perform screening,
    ranking, eligibility, decision-making, or
    LLM inference.

    It only transforms already-computed evaluation
    results into a reporting representation.
    """

    def generate(
        self,
        evaluation: dict[str, Any],
    ) -> ScreeningReport:
        """
        Generate a screening report from the final
        ScreeningService output.
        """

        if not isinstance(evaluation, dict):
            raise TypeError(
                "evaluation must be a dictionary"
            )

        job_id = evaluation.get("job_id")

        if not isinstance(job_id, str) or not job_id.strip():
            raise ValueError(
                "evaluation must contain a valid job_id"
            )

        results = evaluation.get("results")

        if not isinstance(results, list):
            raise ValueError(
                "evaluation must contain a results list"
            )

        candidates = [
            self._build_candidate_report(result)
            for result in results
        ]

        shortlisted = sum(
            candidate.decision == "shortlist"
            for candidate in candidates
        )

        review = sum(
            candidate.decision == "review"
            for candidate in candidates
        )

        rejected = sum(
            candidate.decision == "reject"
            for candidate in candidates
        )

        eligible_candidates = sum(
            candidate.eligible
            for candidate in candidates
        )

        report_without_markdown = ScreeningReport(
            job_id=job_id,
            total_candidates=len(candidates),
            eligible_candidates=eligible_candidates,
            shortlisted_candidates=shortlisted,
            review_candidates=review,
            rejected_candidates=rejected,
            candidates=candidates,
            markdown="",
        )

        markdown = self._build_markdown(
            report_without_markdown
        )

        return report_without_markdown.model_copy(
            update={
                "markdown": markdown
            }
        )

    def _build_candidate_report(
        self,
        result: dict[str, Any],
    ) -> CandidateReport:
        if not isinstance(result, dict):
            raise TypeError(
                "Each screening result must be a dictionary"
            )

        resume_id = result.get("resume_id")

        if not isinstance(resume_id, str):
            raise ValueError(
                "Screening result must contain resume_id"
            )

        decision = str(
            result.get("decision", "review")
        ).strip().lower()

        if decision not in {
            "shortlist",
            "review",
            "reject",
        }:
            raise ValueError(
                f"Unsupported screening decision: {decision!r}"
            )

        eligibility = result.get(
            "eligibility",
            {},
        )

        if not isinstance(eligibility, dict):
            eligibility = {}

        explanation = result.get(
            "explanation",
            {},
        )

        if not isinstance(explanation, dict):
            explanation = {}

        gap_analysis = result.get(
            "gap_analysis",
            {},
        )

        if not isinstance(gap_analysis, dict):
            gap_analysis = {}

        evidence = result.get(
            "evidence",
            [],
        )

        if not isinstance(evidence, list):
            evidence = []

        ranking_score = result.get(
            "ranking_score_percent",
            0.0,
        )

        try:
            ranking_score = float(
                ranking_score or 0.0
            )
        except (TypeError, ValueError):
            ranking_score = 0.0

        ranking_score = max(
            0.0,
            min(100.0, ranking_score),
        )

        candidate_name = result.get(
            "candidate_name"
        )

        return CandidateReport(
            resume_id=resume_id,
            candidate_name=(
                str(candidate_name)
                if candidate_name is not None
                else None
            ),
            decision=decision,
            decision_reason=str(
                result.get(
                    "decision_reason",
                    "",
                )
            ),
            eligible=bool(
                result.get(
                    "eligible",
                    False,
                )
            ),
            ranking_score=ranking_score,
            summary=str(
                explanation.get(
                    "summary",
                    "",
                )
            ),
            strengths=self._as_string_list(
                explanation.get(
                    "strengths",
                    [],
                )
            ),
            gaps=self._as_string_list(
                explanation.get(
                    "gaps",
                    [],
                )
            ),
            matched_skills=self._as_string_list(
                gap_analysis.get(
                    "matched_skills",
                    [],
                )
            ),
            missing_skills=self._as_string_list(
                gap_analysis.get(
                    "missing_skills",
                    [],
                )
            ),
            evidence=evidence,
        )

    def _build_markdown(
        self,
        report: ScreeningReport,
    ) -> str:
        lines = [
            f"# Screening Report — {report.job_id}",
            "",
            "## Summary",
            "",
            f"- **Total candidates:** "
            f"{report.total_candidates}",
            f"- **Eligible candidates:** "
            f"{report.eligible_candidates}",
            f"- **Shortlisted:** "
            f"{report.shortlisted_candidates}",
            f"- **Requires review:** "
            f"{report.review_candidates}",
            f"- **Rejected:** "
            f"{report.rejected_candidates}",
            "",
            "## Candidate Results",
            "",
        ]

        if not report.candidates:
            lines.append(
                "No candidates were supplied for screening."
            )
            return "\n".join(lines)

        for index, candidate in enumerate(
            report.candidates,
            start=1,
        ):
            candidate_label = (
                candidate.candidate_name
                or candidate.resume_id
            )

            lines.extend(
                [
                    f"### {index}. {candidate_label}",
                    "",
                    f"- **Resume ID:** "
                    f"{candidate.resume_id}",
                    f"- **Decision:** "
                    f"{candidate.decision}",
                    f"- **Eligible:** "
                    f"{'Yes' if candidate.eligible else 'No'}",
                    f"- **Ranking score:** "
                    f"{candidate.ranking_score:.2f}/100",
                    f"- **Decision reason:** "
                    f"{candidate.decision_reason}",
                    "",
                    "**Summary**",
                    "",
                    candidate.summary or "No summary available.",
                    "",
                    "**Strengths**",
                    "",
                ]
            )

            if candidate.strengths:
                lines.extend(
                    f"- {strength}"
                    for strength in candidate.strengths
                )
            else:
                lines.append(
                    "- None identified."
                )

            lines.extend(
                [
                    "",
                    "**Gaps**",
                    "",
                ]
            )

            if candidate.gaps:
                lines.extend(
                    f"- {gap}"
                    for gap in candidate.gaps
                )
            else:
                lines.append(
                    "- None identified."
                )

            lines.extend(
                [
                    "",
                    "**Matched Skills**",
                    "",
                ]
            )

            if candidate.matched_skills:
                lines.append(
                    ", ".join(
                        candidate.matched_skills
                    )
                )
            else:
                lines.append("None.")

            lines.extend(
                [
                    "",
                    "**Missing Skills**",
                    "",
                ]
            )

            if candidate.missing_skills:
                lines.append(
                    ", ".join(
                        candidate.missing_skills
                    )
                )
            else:
                lines.append("None.")

            lines.extend(
                [
                    "",
                    "---",
                    "",
                ]
            )

        return "\n".join(lines).rstrip()

    @staticmethod
    def _as_string_list(
        value: Any,
    ) -> list[str]:
        if value is None:
            return []

        if isinstance(value, str):
            return [value]

        if not isinstance(
            value,
            (list, tuple, set),
        ):
            return [str(value)]

        return [
            str(item)
            for item in value
            if str(item).strip()
        ]