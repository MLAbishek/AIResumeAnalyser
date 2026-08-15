from typing import Any


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

        required_skills = self._normalize_set(
            jd.get("required_skills", [])
        )

        candidate_skills = self._normalize_set(
            resume.get("skills", [])
        )

        matched_skills = sorted(
            required_skills & candidate_skills
        )

        missing_skills = sorted(
            required_skills - candidate_skills
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
            "experience_gap": experience_gap,
            "education_gap": education_gap,
            "certification_gap": certification_gap,
            "has_gap": bool(
                missing_skills
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

        matched = required & candidate
        missing = required - candidate

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