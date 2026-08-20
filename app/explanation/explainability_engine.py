from typing import Any


class ExplainabilityEngine:
    """
    Generates deterministic, evidence-backed explanations
    for candidate scores and final decisions.

    The engine does not generate unsupported claims.
    Every explanation reason must be derived from the
    supplied evaluation data.
    """

    def explain(
        self,
        decision: str,
        matching_features: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Generate a structured explanation.

        Parameters
        ----------
        decision:
            Final candidate decision such as:
            shortlist, review, or reject.

        matching_features:
            Structured evidence from eligibility,
            ranking, evaluation, and gap analysis.

        Returns
        -------
        dict
            Structured explanation containing:
            - decision
            - summary
            - reasons
            - strengths
            - gaps
        """

        if not isinstance(matching_features, dict):
            raise TypeError(
                "matching_features must be a dictionary"
            )

        normalized_decision = self._normalize_decision(
            decision
        )

        strengths = self._extract_strengths(
            matching_features
        )

        gaps = self._extract_gaps(
            matching_features
        )

        reasons = self._build_reasons(
            matching_features,
            strengths,
            gaps,
        )

        summary = self._build_summary(
            normalized_decision,
            strengths,
            gaps,
        )

        return {
            "decision": normalized_decision,
            "summary": summary,
            "reasons": reasons,
            "strengths": strengths,
            "gaps": gaps,
        }

    def _normalize_decision(
        self,
        decision: str,
    ) -> str:
        if not isinstance(decision, str):
            raise TypeError(
                "decision must be a string"
            )

        normalized = decision.strip().lower()

        allowed = {
            "shortlist",
            "review",
            "reject",
        }

        if normalized not in allowed:
            raise ValueError(
                f"Unsupported decision: {decision!r}. "
                f"Expected one of {sorted(allowed)}."
            )

        return normalized

    def _extract_strengths(
        self,
        features: dict[str, Any],
    ) -> list[str]:
        strengths: list[str] = []

        matched_skills = self._as_list(
            features.get("matched_skills", [])
        )

        if matched_skills:
            strengths.append(
                "Matched required skills: "
                + ", ".join(
                    str(skill)
                    for skill in matched_skills
                )
                + "."
            )

        if features.get("experience_match") is True:
            strengths.append(
                "Required experience is satisfied."
            )

        if features.get("education_match") is True:
            strengths.append(
                "Education requirements are satisfied."
            )

        if features.get("certification_match") is True:
            strengths.append(
                "Required certification requirements are satisfied."
            )

        ranking_score = self._get_score(
            features,
            "ranking_score",
        )

        if ranking_score is not None:
            strengths.append(
                f"Ranking score: {ranking_score:.2f}."
            )

        llm_score = self._get_score(
            features,
            "llm_score",
        )

        if llm_score is not None:
            strengths.append(
                f"LLM evaluation score: {llm_score:.2f}."
            )

        return strengths

    def _extract_gaps(
        self,
        features: dict[str, Any],
    ) -> list[str]:
        gaps: list[str] = []

        # Prefer the severity-classified lists when available (see
        # GapAnalysisEngine) so a missing preferred/nice-to-have
        # skill is never worded as if it were a required-skill
        # failure. Falls back to the flat "missing_skills" list for
        # any caller that hasn't classified severity.
        if (
            "critical_missing_skills" in features
            or "nice_to_have_missing_skills" in features
        ):
            critical_missing = self._as_list(
                features.get("critical_missing_skills", [])
            )

            nice_to_have_missing = self._as_list(
                features.get("nice_to_have_missing_skills", [])
            )

            if critical_missing:
                gaps.append(
                    "Missing required skills: "
                    + ", ".join(
                        str(skill)
                        for skill in critical_missing
                    )
                    + "."
                )

            if nice_to_have_missing:
                gaps.append(
                    "Missing preferred (nice-to-have) skills: "
                    + ", ".join(
                        str(skill)
                        for skill in nice_to_have_missing
                    )
                    + "."
                )
        else:
            missing_skills = self._as_list(
                features.get("missing_skills", [])
            )

            if missing_skills:
                gaps.append(
                    "Missing required skills: "
                    + ", ".join(
                        str(skill)
                        for skill in missing_skills
                    )
                    + "."
                )

        experience_gap = features.get(
            "experience_gap"
        )

        if isinstance(experience_gap, dict):
            gap_years = experience_gap.get(
                "gap_years"
            )

            if gap_years is not None:
                try:
                    gap_years = float(gap_years)
                except (TypeError, ValueError):
                    gap_years = None

                if gap_years is not None and gap_years > 0:
                    gaps.append(
                        f"Experience gap: "
                        f"{gap_years:g} years."
                    )

        if features.get("experience_match") is False:
            if not any(
                "experience gap" in gap.lower()
                for gap in gaps
            ):
                gaps.append(
                    "Required experience is not satisfied."
                )

        if features.get("education_match") is False:
            gaps.append(
                "Education requirements are not satisfied."
            )

        if features.get("certification_match") is False:
            gaps.append(
                "Certification requirements are not satisfied."
            )

        return gaps

    def _build_reasons(
        self,
        features: dict[str, Any],
        strengths: list[str],
        gaps: list[str],
    ) -> list[str]:
        reasons: list[str] = []

        reasons.extend(strengths)
        reasons.extend(gaps)

        explicit_reasons = self._as_list(
            features.get("reasons", [])
        )

        for reason in explicit_reasons:
            reason = str(reason).strip()

            if reason and reason not in reasons:
                reasons.append(reason)

        return reasons

    def _build_summary(
        self,
        decision: str,
        strengths: list[str],
        gaps: list[str],
    ) -> str:

        if decision == "shortlist":
            prefix = "Candidate is shortlisted."
        elif decision == "review":
            prefix = "Candidate requires further review."
        else:
            prefix = "Candidate is rejected."

        if strengths and gaps:
            return (
                f"{prefix} "
                f"The evaluation identified "
                f"{len(strengths)} supporting factor(s) "
                f"and {len(gaps)} gap(s)."
            )

        if strengths:
            return (
                f"{prefix} "
                f"The evaluation identified "
                f"{len(strengths)} supporting factor(s)."
            )

        if gaps:
            return (
                f"{prefix} "
                f"The evaluation identified "
                f"{len(gaps)} gap(s)."
            )

        return prefix

    @staticmethod
    def _as_list(value: Any) -> list[Any]:
        if value is None:
            return []

        if isinstance(value, list):
            return value

        if isinstance(value, tuple):
            return list(value)

        return [value]

    @staticmethod
    def _get_score(
        features: dict[str, Any],
        field: str,
    ) -> float | None:

        value = features.get(field)

        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None