from types import SimpleNamespace
from typing import Any

from app.core.schemas import (
    CanonicalJob,
    CanonicalResume,
    JobDescription,
    Resume,
)
from app.decision.evidence_citation import EvidenceCitationEngine
from app.decision.gap_analysis import GapAnalysisEngine
from app.decision.threshold_policy import ThresholdPolicyEngine
from app.explanation.explainability_engine import ExplainabilityEngine
from app.filtering.eligibility import check_eligibility
from app.filtering.schemas import EligibilityCriteria
from app.normalization.canonical_jd_builder import CanonicalJobBuilder
from app.normalization.canonical_resume_builder import (
    CanonicalResumeBuilder,
)
from app.ranking.scoring_engine import (
    CandidateScore,
    calculate_candidate_score,
    rank_candidates,
)


class ScreeningService:
    """
    Application-level orchestration for resume screening.

    This service connects the existing deterministic modules
    without introducing an LLM dependency.

    Current flow:

        input
          ↓
        canonicalization
          ↓
        eligibility
          ↓
        ranking
          ↓
        threshold decision
          ↓
        gap analysis
          ↓
        explanation
          ↓
        evidence
    """

    def __init__(
        self,
        jd_builder: CanonicalJobBuilder | None = None,
        resume_builder: CanonicalResumeBuilder | None = None,
        threshold_policy: ThresholdPolicyEngine | None = None,
        gap_engine: GapAnalysisEngine | None = None,
        explanation_engine: ExplainabilityEngine | None = None,
        evidence_engine: EvidenceCitationEngine | None = None,
    ):
        self.jd_builder = jd_builder or CanonicalJobBuilder()
        self.resume_builder = (
            resume_builder or CanonicalResumeBuilder()
        )

        self.threshold_policy = (
            threshold_policy or ThresholdPolicyEngine()
        )

        self.gap_engine = (
            gap_engine or GapAnalysisEngine()
        )

        self.explanation_engine = (
            explanation_engine or ExplainabilityEngine()
        )

        self.evidence_engine = (
            evidence_engine or EvidenceCitationEngine()
        )

    def screen(
        self,
        job_description: JobDescription,
        resumes: list[Resume],
    ) -> dict[str, Any]:
        """
        Screen all supplied resumes against one job description.
        """

        if not isinstance(job_description, JobDescription):
            raise TypeError(
                "job_description must be a JobDescription"
            )

        if not isinstance(resumes, list):
            raise TypeError(
                "resumes must be a list"
            )

        if any(
            not isinstance(resume, Resume)
            for resume in resumes
        ):
            raise TypeError(
                "Every resume must be a Resume instance"
            )

        canonical_job = self._build_canonical_job(
            job_description
        )

        canonical_resumes = [
            self._build_canonical_resume(resume)
            for resume in resumes
        ]

        eligibility_results = {
            resume.resume_id: self._evaluate_eligibility(
                job_description,
                canonical_job,
                resume,
                canonical_resume,
            )
            for resume, canonical_resume in zip(
                resumes,
                canonical_resumes,
            )
        }

        eligible_resumes = [
            canonical_resume
            for canonical_resume in canonical_resumes
            if eligibility_results[
                canonical_resume.resume_id
            ]["eligible"]
        ]

        ranked_scores = rank_candidates(
            canonical_job,
            eligible_resumes,
        )

        ranked_by_id = {
            result.resume_id: result
            for result in ranked_scores
        }

        results = []

        for resume in resumes:
            eligibility = eligibility_results[
                resume.resume_id
            ]

            ranking = ranked_by_id.get(
                resume.resume_id
            )

            result = self._build_candidate_result(
                job_description=job_description,
                resume=resume,
                canonical_job=canonical_job,
                eligibility=eligibility,
                ranking=ranking,
            )

            results.append(result)

        results.sort(
            key=lambda result: (
                -(result["ranking_score"] or 0.0),
                result["resume_id"],
            )
        )

        return {
            "job_id": job_description.job_id,
            "total_candidates": len(resumes),
            "eligible_candidates": len(
                eligible_resumes
            ),
            "results": results,
        }

    def _build_canonical_job(
        self,
        job_description: JobDescription,
    ) -> CanonicalJob:
        """
        Adapt the existing JobDescription schema to the
        canonical JD builder.
        """

        required_experience_months = 0

        if (
            job_description.required_experience_years
            is not None
        ):
            required_experience_months = int(
                job_description.required_experience_years
                * 12
            )

        parsed_jd = {
            "job_id": job_description.job_id,
            "title": job_description.title,
            "description": job_description.summary,
            "required_skills": (
                job_description.required_skills
            ),
            "preferred_skills": (
                job_description.preferred_skills
            ),
            "required_technologies": [],
            "preferred_technologies": [],
            "experience": {
                "minimum_months": (
                    required_experience_months
                ),
            },
            "education": [
                {
                    "degree": education,
                    "required": True,
                }
                for education
                in job_description.education
            ],
        }

        return self.jd_builder.build(
            parsed_jd
        )

    def _build_canonical_resume(
        self,
        resume: Resume,
    ) -> CanonicalResume:
        """
        Adapt the existing Resume schema to the
        canonical resume builder.
        """

        experiences = [
            {
                "job_title": (
                    experience.role
                    or ""
                ),
                "company": (
                    experience.company
                    or ""
                ),
                "start_date": (
                    experience.start_date
                    or ""
                ),
                "end_date": (
                    experience.end_date
                    or ""
                ),
            }
            for experience in resume.experience
        ]

        education = [
            {
                "degree": education.degree or "",
                "institution": (
                    education.institution
                    or ""
                ),
                "field_of_study": (
                    education.field
                ),
                "start_date": (
                    education.start_date
                ),
                "end_date": (
                    education.end_date
                ),
            }
            for education in resume.education
        ]

        parsed_resume = {
            "resume_id": resume.resume_id,
            "name": resume.name,
            "summary": resume.summary,
            "skills": resume.skills,
            "job_titles": resume.job_titles,
            "organizations": [
                experience.company
                for experience in resume.experience
                if experience.company
            ],
            "technologies": [],
            "experiences": experiences,
            "education": education,
        }

        return self.resume_builder.build(
            parsed_resume
        )

    def _evaluate_eligibility(
        self,
        job_description: JobDescription,
        canonical_job: CanonicalJob,
        resume: Resume,
        canonical_resume: CanonicalResume,
    ) -> dict[str, Any]:
        """
        Adapt the project's Resume representation to
        the candidate representation expected by eligibility.
        """

        education_text = "; ".join(
            filter(
                None,
                [
                    education.degree
                    for education
                    in resume.education
                ],
            )
        )

        candidate = SimpleNamespace(
            skills=resume.skills,
            experience_months=(
                canonical_resume.total_experience_months
            ),
            education=education_text,
            certifications=resume.certifications,
            location=None,
            authorization=True,
        )

        criteria = EligibilityCriteria(
            required_skills=(
                canonical_job.required_skills
            ),
            required_technologies=(
                canonical_job.required_technologies
            ),
            minimum_experience_months=(
                canonical_job.experience.minimum_months
            ),
            required_education=(
                canonical_job.education
            ),
            required_certifications=(
                job_description.certifications
            ),
            location=job_description.location,
            work_authorization_required=False,
        )

        result = check_eligibility(
            candidate,
            criteria,
        )

        return {
            "eligible": result.eligible,
            "result": result.model_dump(),
        }

    def _build_candidate_result(
        self,
        *,
        job_description: JobDescription,
        resume: Resume,
        canonical_job: CanonicalJob,
        eligibility: dict[str, Any],
        ranking: CandidateScore | None,
    ) -> dict[str, Any]:
        """
        Build the complete candidate-level screening result.
        """

        ranking_score = None

        if ranking is not None:
            ranking_score = ranking.score

        ranking_score_100 = (
            ranking_score * 100
            if ranking_score is not None
            else 0.0
        )

        threshold = self.threshold_policy.evaluate(
            candidate_score=ranking_score_100,
            eligible=eligibility["eligible"],
        )

        resume_dict = resume.model_dump()

        jd_dict = job_description.model_dump()

        gap_analysis = self.gap_engine.analyze(
            jd=jd_dict,
            resume=resume_dict,
        )

        matching_features = {
            **gap_analysis,
            "experience_match": (
                eligibility["result"]
                ["experience_match"]
                ["eligible"]
            ),
            "education_match": (
                eligibility["result"]
                ["education_certification"]
                ["eligible"]
            ),
            "certification_match": (
                eligibility["result"]
                ["education_certification"]
                ["eligible"]
            ),
            "ranking_score": ranking_score_100,
            "reasons": (
                eligibility["result"]["reasons"]
                + [threshold["reason"]],
            ),
        }

        explanation = self.explanation_engine.explain(
            decision=threshold["decision"],
            matching_features=matching_features,
        )

        evidence = self.evidence_engine.build_references(
            parsed_resume=resume_dict,
            parsed_jd=jd_dict,
            evaluation={
                "ranking_score": ranking_score_100,
                "final_score": ranking_score_100,
            },
        )

        return {
            "resume_id": resume.resume_id,
            "eligible": eligibility["eligible"],
            "ranking_score": ranking_score,
            "ranking_score_percent": round(
                ranking_score_100,
                2,
            ),
            "decision": threshold["decision"],
            "decision_reason": threshold["reason"],
            "eligibility": eligibility["result"],
            "gap_analysis": gap_analysis,
            "explanation": explanation,
            "evidence": evidence,
            "ranking": (
                ranking.model_dump()
                if ranking is not None
                else None
            ),
        }