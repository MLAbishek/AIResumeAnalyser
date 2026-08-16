from app.api.repository import InMemoryRepository
from app.api.schemas.profile import CandidateProfileResponse
from app.decision.evidence_citation import EvidenceCitationEngine
from app.decision.gap_analysis import GapAnalysisEngine
from app.explanation.explainability_engine import ExplainabilityEngine
from app.ranking.scoring_engine import calculate_candidate_score


class CandidateProfileService:
    """
    Module 47.

    Produces detailed, deterministic matching information
    for one candidate against one JD.
    """

    def __init__(
        self,
        repository: InMemoryRepository,
    ):
        self.repository = repository

        self.gap_engine = GapAnalysisEngine()
        self.evidence_engine = EvidenceCitationEngine()
        self.explanation_engine = ExplainabilityEngine()

    def get_profile(
        self,
        candidate_id: str,
        jd_id: str,
    ) -> CandidateProfileResponse:

        job = self.repository.get_job(jd_id)

        candidate = self.repository.get_resume(
            candidate_id
        )

        score = calculate_candidate_score(
            job,
            candidate,
        )

        parsed_jd = self._job_to_gap_dict(job)
        parsed_resume = self._resume_to_gap_dict(candidate)

        gap_analysis = self.gap_engine.analyze(
            parsed_jd,
            parsed_resume,
        )

        evaluation = {
            "ranking_score": round(
                score.score * 100,
                2,
            )
        }

        evidence = self.evidence_engine.build_references(
            parsed_resume=parsed_resume,
            parsed_jd=parsed_jd,
            evaluation=evaluation,
        )

        explanation_features = {
            "matched_skills": gap_analysis["matched_skills"],
            "missing_skills": gap_analysis["missing_skills"],
            "experience_gap": gap_analysis["experience_gap"],
            "ranking_score": round(
                score.score * 100,
                2,
            ),
        }

        decision = self._derive_decision(
            score.score
        )

        explanation = self.explanation_engine.explain(
            decision=decision,
            matching_features=explanation_features,
        )

        return CandidateProfileResponse(
            candidate_id=candidate_id,
            jd_id=jd_id,
            ranking_score=score.score,
            feature_scores={
                "skill_score": score.features.skill_score,
                "experience_score": score.features.experience_score,
                "seniority_score": score.features.seniority_score,
                "education_score": score.features.education_score,
                "semantic_score": score.features.semantic_score,
            },
            matched_skills=gap_analysis["matched_skills"],
            missing_skills=gap_analysis["missing_skills"],
            experience_gap=gap_analysis["experience_gap"],
            education_gap=gap_analysis["education_gap"],
            certification_gap=gap_analysis["certification_gap"],
            evidence=evidence,
            decision=decision,
            explanation=explanation,
        )

    @staticmethod
    def _job_to_gap_dict(job):
        return {
            "required_skills": job.required_skills,
            "minimum_experience_years": (
                job.experience.minimum_months / 12
            ),
            "required_education": [
                requirement.degree
                for requirement in job.education
                if requirement.degree
            ],
            "required_certifications": [],
        }

    @staticmethod
    def _resume_to_gap_dict(resume):
        return {
            "skills": resume.skills,
            "experience_years": (
                resume.total_experience_months / 12
            ),
            "education": [
                education.degree
                for education in resume.education
                if education.degree
            ],
            "certifications": [],
        }

    @staticmethod
    def _derive_decision(
        score: float,
    ) -> str:
        """
        Temporary deterministic decision mapping.

        Ranking scores are 0–1.
        Decision thresholds are represented on the same
        conceptual 0–100 scale used elsewhere.
        """

        score_100 = score * 100

        if score_100 >= 75:
            return "shortlist"

        if score_100 >= 50:
            return "review"

        return "reject"