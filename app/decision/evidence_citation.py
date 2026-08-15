from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class EvidenceReference:
    """
    A traceable piece of evidence supporting an evaluation claim.
    """

    claim: str
    source: str
    section: str
    evidence: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class EvidenceCitationEngine:
    """
    Builds evidence references for candidate evaluation results.

    The engine only cites information supplied in the resume/JD
    structures. It does not invent evidence.
    """

    def build_references(
        self,
        parsed_resume: dict[str, Any],
        parsed_jd: dict[str, Any],
        evaluation: dict[str, Any] | None = None,
    ) -> list[dict[str, str]]:

        if not isinstance(parsed_resume, dict):
            raise TypeError(
                "parsed_resume must be a dictionary"
            )

        if not isinstance(parsed_jd, dict):
            raise TypeError(
                "parsed_jd must be a dictionary"
            )

        if evaluation is not None and not isinstance(
            evaluation, dict
        ):
            raise TypeError(
                "evaluation must be a dictionary"
            )

        evaluation = evaluation or {}

        references: list[EvidenceReference] = []

        self._add_skill_evidence(
            references,
            parsed_resume,
            parsed_jd,
        )

        self._add_experience_evidence(
            references,
            parsed_resume,
            parsed_jd,
        )

        self._add_education_evidence(
            references,
            parsed_resume,
            parsed_jd,
        )

        self._add_certification_evidence(
            references,
            parsed_resume,
            parsed_jd,
        )

        self._add_evaluation_evidence(
            references,
            evaluation,
        )

        return [
            reference.to_dict()
            for reference in references
        ]

    def _add_skill_evidence(
        self,
        references: list[EvidenceReference],
        resume: dict[str, Any],
        jd: dict[str, Any],
    ) -> None:

        resume_skills = self._normalize_list(
            resume.get("skills", [])
        )

        required_skills = self._normalize_list(
            jd.get("required_skills", [])
        )

        resume_lookup = {
            self._normalize(skill): skill
            for skill in resume_skills
        }

        for required_skill in required_skills:
            normalized = self._normalize(
                required_skill
            )

            if normalized in resume_lookup:
                references.append(
                    EvidenceReference(
                        claim=(
                            f"Candidate has "
                            f"{required_skill}."
                        ),
                        source="resume",
                        section="skills",
                        evidence=(
                            resume_lookup[normalized]
                        ),
                    )
                )

    def _add_experience_evidence(
        self,
        references: list[EvidenceReference],
        resume: dict[str, Any],
        jd: dict[str, Any],
    ) -> None:

        candidate_years = resume.get(
            "experience_years"
        )

        required_years = jd.get(
            "minimum_experience_years"
        )

        if candidate_years is None:
            return

        if required_years is None:
            claim = (
                "Candidate experience was evaluated."
            )
        else:
            claim = (
                "Candidate experience was evaluated "
                "against the required experience."
            )

        references.append(
            EvidenceReference(
                claim=claim,
                source="resume",
                section="experience",
                evidence=(
                    f"{candidate_years} years"
                ),
            )
        )

    def _add_education_evidence(
        self,
        references: list[EvidenceReference],
        resume: dict[str, Any],
        jd: dict[str, Any],
    ) -> None:

        education = self._normalize_list(
            resume.get("education", [])
        )

        if not education:
            return

        required_education = self._normalize_list(
            jd.get("required_education", [])
        )

        if required_education:
            claim = (
                "Candidate education was evaluated "
                "against the job requirements."
            )
        else:
            claim = (
                "Candidate education was identified "
                "from the resume."
            )

        references.append(
            EvidenceReference(
                claim=claim,
                source="resume",
                section="education",
                evidence="; ".join(education),
            )
        )

    def _add_certification_evidence(
        self,
        references: list[EvidenceReference],
        resume: dict[str, Any],
        jd: dict[str, Any],
    ) -> None:

        certifications = self._normalize_list(
            resume.get("certifications", [])
        )

        if not certifications:
            return

        required = self._normalize_list(
            jd.get("required_certifications", [])
        )

        if required:
            claim = (
                "Candidate certifications were evaluated "
                "against the job requirements."
            )
        else:
            claim = (
                "Candidate certifications were identified "
                "from the resume."
            )

        references.append(
            EvidenceReference(
                claim=claim,
                source="resume",
                section="certifications",
                evidence="; ".join(certifications),
            )
        )

    def _add_evaluation_evidence(
        self,
        references: list[EvidenceReference],
        evaluation: dict[str, Any],
    ) -> None:

        ranking_score = evaluation.get(
            "ranking_score"
        )

        if ranking_score is not None:
            references.append(
                EvidenceReference(
                    claim="Candidate received a ranking score.",
                    source="ranking",
                    section="ranking",
                    evidence=str(ranking_score),
                )
            )

        llm_score = evaluation.get(
            "llm_score"
        )

        if llm_score is not None:
            references.append(
                EvidenceReference(
                    claim="Candidate received an LLM evaluation score.",
                    source="llm_evaluation",
                    section="evaluation",
                    evidence=str(llm_score),
                )
            )

        final_score = evaluation.get(
            "final_score"
        )

        if final_score is not None:
            references.append(
                EvidenceReference(
                    claim="Candidate received a final evaluation score.",
                    source="decision",
                    section="final_score",
                    evidence=str(final_score),
                )
            )

    @staticmethod
    def _normalize_list(
        value: Any,
    ) -> list[str]:

        if value is None:
            return []

        if isinstance(value, str):
            value = [value]

        if not isinstance(
            value,
            (list, tuple, set),
        ):
            raise TypeError(
                "Expected a list, tuple, set, or string"
            )

        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

    @staticmethod
    def _normalize(
        value: str,
    ) -> str:
        return " ".join(
            value.lower().strip().split()
        )