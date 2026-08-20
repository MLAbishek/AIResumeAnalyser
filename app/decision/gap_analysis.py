from typing import Any

from app.normalization.education_normalizer import (
    EducationNormalizer,
)
from app.normalization.normalizer_utils import (
    split_requirement_group,
)

_education_normalizer = EducationNormalizer()


class GapAnalysisEngine:
    """
    Identifies gaps between job requirements and candidate data.

    The engine performs deterministic comparisons and does not
    infer or invent missing candidate information.
    """

    def analyze(
        self,
        jd: dict[str, Any],
        resume: dict[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(jd, dict):
            raise TypeError("jd must be a dictionary")

        if not isinstance(resume, dict):
            raise TypeError("resume must be a dictionary")

        candidate_skills = self._normalize_set(
            resume.get("skills", [])
        )

        # Required and preferred requirements carry different
        # severity: a candidate missing a REQUIRED skill has a
        # critical gap, while missing a PREFERRED ("nice to have")
        # skill is a minor gap that must never be portrayed with the
        # same weight. jd["preferred_skills"] is optional - callers
        # that only pass "required_skills" (including every existing
        # caller/test of this method) get identical behavior to
        # before, just with critical_missing_skills/
        # nice_to_have_missing_skills additionally exposed.
        matched_required, missing_required = self._calculate_skill_gap(
            jd.get("required_skills", []),
            candidate_skills,
        )

        matched_preferred, missing_preferred = self._calculate_skill_gap(
            jd.get("preferred_skills", []),
            candidate_skills,
        )

        matched_skills = sorted(
            set(matched_required) | set(matched_preferred)
        )

        missing_skills = sorted(
            set(missing_required) | set(missing_preferred)
        )

        experience_gap = self._calculate_experience_gap(
            jd,
            resume,
        )

        education_gap = self._calculate_education_gap(
            jd,
            resume,
        )

        certification_gap = self._calculate_certification_gap(
            jd,
            resume,
        )

        return {
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "skill_gap_count": len(missing_skills),
            # Severity breakdown of missing_skills: a missing
            # required skill is a critical gap; a missing preferred
            # skill is nice-to-have and must not be weighted the same
            # in any downstream narrative/UI.
            "critical_missing_skills": sorted(missing_required),
            "nice_to_have_missing_skills": sorted(missing_preferred),
            "experience_gap": experience_gap,
            "education_gap": education_gap,
            "certification_gap": certification_gap,
            # Only critical (required-skill) gaps and hard-requirement
            # gaps (experience/education/certification) mark this
            # evaluation as having a gap - a candidate missing only
            # optional/preferred skills is not "gapped" in any
            # meaningful sense.
            "has_gap": bool(
                missing_required
                or experience_gap["has_gap"]
                or education_gap["has_gap"]
                or certification_gap["has_gap"]
            ),
        }

    @staticmethod
    def _normalize_set(
        values: Any,
    ) -> set[str]:
        if values is None:
            return set()

        if isinstance(values, str):
            values = [values]

        if not isinstance(values, (list, tuple, set)):
            raise TypeError(
                "Skill values must be a list, tuple, set, or string"
            )

        return {
            " ".join(
                str(value).strip().lower().split()
            )
            for value in values
            if str(value).strip()
        }

    @staticmethod
    def _calculate_skill_gap(
        required_entries: Any,
        candidate_skills: set[str],
    ) -> tuple[list[str], list[str]]:
        """
        Same canonical requirement representation eligibility and
        ranking use: a required_skills entry may be a single
        mandatory skill or a pipe-joined alternatives group (see
        normalizer_utils.split_requirement_group()) - satisfied by
        ANY ONE alternative. A satisfied group is reported as
        matched using the specific alternative the candidate has,
        never the raw "|"-joined string; an unsatisfied group is
        reported as a human-readable "a or b or c" gap instead.
        """

        if required_entries is None:
            required_entries = []

        if isinstance(required_entries, str):
            required_entries = [required_entries]

        matched: set[str] = set()
        missing: set[str] = set()

        for entry in required_entries:
            normalized_entry = " ".join(
                str(entry).strip().lower().split()
            )

            if not normalized_entry:
                continue

            alternatives = split_requirement_group(
                normalized_entry
            )

            matched_alternative = next(
                (
                    alternative
                    for alternative in alternatives
                    if alternative in candidate_skills
                ),
                None,
            )

            if matched_alternative is not None:
                matched.add(matched_alternative)
            else:
                missing.add(
                    " or ".join(alternatives)
                    if len(alternatives) > 1
                    else alternatives[0]
                )

        return sorted(matched), sorted(missing)

    @staticmethod
    def _calculate_experience_gap(
        jd: dict[str, Any],
        resume: dict[str, Any],
    ) -> dict[str, Any]:

        required = float(
            jd.get("minimum_experience_years", 0) or 0
        )

        candidate = float(
            resume.get("experience_years", 0) or 0
        )

        gap = max(0.0, required - candidate)

        return {
            "required_years": required,
            "candidate_years": candidate,
            "gap_years": gap,
            "has_gap": gap > 0,
            "meets_requirement": gap == 0,
        }

    @classmethod
    def _calculate_education_gap(
        cls,
        jd: dict[str, Any],
        resume: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Uses the same EducationNormalizer as eligibility
        (check_education_certification) and ranking (score_education)
        so this gap can never disagree with what those already
        decided - e.g. a candidate degree phrased as "AI & ML" must
        be recognized here exactly like it is everywhere else, not
        flagged as a gap by a stricter literal-string comparison.
        """

        required = cls._normalize_set(
            jd.get("required_education", [])
        )

        candidate = cls._normalize_set(
            resume.get("education", [])
        )

        if not required:
            return {
                "required": [],
                "candidate": sorted(candidate),
                "missing": [],
                "has_gap": False,
                "meets_requirement": True,
            }

        matched: set[str] = set()
        missing: set[str] = set()

        for requirement in required:
            satisfied = any(
                _education_normalizer.requirement_satisfied(
                    requirement_degree=requirement,
                    requirement_field=None,
                    candidate_degree=candidate_entry,
                )
                for candidate_entry in candidate
            )

            if satisfied:
                matched.add(requirement)
            else:
                missing.add(requirement)

        return {
            "required": sorted(required),
            "candidate": sorted(candidate),
            "missing": sorted(missing),
            "has_gap": bool(missing),
            "meets_requirement": bool(matched),
        }

    @classmethod
    def _calculate_certification_gap(
        cls,
        jd: dict[str, Any],
        resume: dict[str, Any],
    ) -> dict[str, Any]:

        required = cls._normalize_set(
            jd.get("required_certifications", [])
        )

        candidate = cls._normalize_set(
            resume.get("certifications", [])
        )

        missing = required - candidate

        return {
            "required": sorted(required),
            "candidate": sorted(candidate),
            "missing": sorted(missing),
            "has_gap": bool(missing),
            "meets_requirement": not bool(missing),
        }