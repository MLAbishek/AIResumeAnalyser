import logging
from types import SimpleNamespace
from typing import Any

from app.core.schemas import (
    CanonicalJob,
    CanonicalResume,
    JobDescription,
    Resume,
)
from app.normalization.education_normalizer import (
    EducationNormalizer,
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
from app.services.llm_service import LLMExplanationService

logger = logging.getLogger(__name__)


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
        llm_service: LLMExplanationService | None = None,
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

        self.llm_service = (
            llm_service or LLMExplanationService()
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

        canonical_resume_by_id = {
            canonical_resume.resume_id: canonical_resume
            for canonical_resume in canonical_resumes
        }

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
                canonical_resume=canonical_resume_by_id[
                    resume.resume_id
                ],
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

        maximum_experience_months = None

        if job_description.max_experience_years is not None:
            maximum_experience_months = round(
                job_description.max_experience_years * 12
            )

            # A stated upper bound must never be below the minimum
            # (e.g. rounding "0-1 year" must not accidentally
            # produce max < min) - CanonicalJobBuilder rejects that
            # combination outright, so clamp defensively instead of
            # letting a malformed JD value crash canonicalization.
            if maximum_experience_months < required_experience_months:
                maximum_experience_months = (
                    required_experience_months
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
            "responsibilities": (
                job_description.responsibilities
            ),
            "experience": {
                "minimum_months": (
                    required_experience_months
                ),
                "maximum_months": maximum_experience_months,
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
                    " ".join(
                        filter(
                            None,
                            [
                                education.degree,
                                education.field,
                            ],
                        )
                    )
                    for education
                    in resume.education
                ],
            )
        )

        candidate = SimpleNamespace(
            skills=canonical_resume.skills,
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
        canonical_resume: CanonicalResume,
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

        # Gap analysis and evidence must reason about the SAME
        # canonical, normalized skills that eligibility and ranking
        # already use - not the raw JobDescription/Resume dumps.
        # Those raw dumps also use different key names than
        # GapAnalysisEngine/EvidenceCitationEngine expect
        # (required_experience_years vs minimum_experience_years,
        # education as structured objects vs a flat string list),
        # which silently made the experience/education/certification
        # portions of both engines always see empty input regardless
        # of the real JD/resume content. Building one shared,
        # correctly-keyed, canonically-normalized view fixes both
        # problems at once and keeps every downstream consumer
        # (gap analysis, evidence, and therefore explanation/LLM
        # context) consistent with what eligibility/ranking already
        # decided.
        # Gap analysis/evidence are informational, not gating, so
        # they reflect BOTH required and preferred skills - a
        # soft-signal JD line ("Familiarity with TypeScript") is
        # reclassified out of the hard eligibility gate but a
        # candidate who has it should still show it as a genuine
        # strength here, not as neither matched nor missing.
        gap_analysis_skills = list(
            dict.fromkeys(
                [
                    *canonical_job.required_skills,
                    *canonical_job.preferred_skills,
                ]
            )
        )

        matching_jd = {
            "required_skills": gap_analysis_skills,
            "minimum_experience_years": (
                canonical_job.experience.minimum_months / 12
                if canonical_job.experience.minimum_months
                else 0
            ),
            "required_education": [
                " ".join(
                    part
                    for part in (
                        requirement.degree,
                        requirement.field_of_study,
                    )
                    if part
                )
                for requirement in canonical_job.education
                if requirement.degree
                or requirement.field_of_study
            ],
            "required_certifications": (
                job_description.certifications
            ),
        }

        matching_resume = {
            "skills": canonical_resume.skills,
            "experience_years": (
                canonical_resume.total_experience_months / 12
                if canonical_resume.total_experience_months
                else 0
            ),
            "education": [
                " ".join(
                    part
                    for part in (
                        education.degree,
                        education.field_of_study,
                    )
                    if part
                )
                for education in canonical_resume.education
                if education.degree
                or education.field_of_study
            ],
            "certifications": resume.certifications,
        }

        gap_analysis = self.gap_engine.analyze(
            jd=matching_jd,
            resume=matching_resume,
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
            parsed_resume=matching_resume,
            parsed_jd=matching_jd,
            evaluation={
                "ranking_score": ranking_score_100,
                "final_score": ranking_score_100,
            },
        )

        explanation = self._add_llm_narrative(
            explanation=explanation,
            job_description=job_description,
            resume=resume,
            eligibility=eligibility,
            ranking=ranking,
            ranking_score_100=ranking_score_100,
            decision=threshold["decision"],
            decision_reason=threshold["reason"],
            gap_analysis=gap_analysis,
            evidence=evidence,
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

    def _add_llm_narrative(
        self,
        *,
        explanation: dict[str, Any],
        job_description: JobDescription,
        resume: Resume,
        eligibility: dict[str, Any],
        ranking: CandidateScore | None,
        ranking_score_100: float,
        decision: str,
        decision_reason: str,
        gap_analysis: dict[str, Any],
        evidence: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Attach an LLM-generated natural-language narrative to the
        existing deterministic explanation dict, additively.

        The deterministic keys (decision/summary/reasons/strengths/
        gaps) produced by ExplainabilityEngine are never modified -
        this only adds a "narrative" field grounded in the already-
        computed evaluation, decision, gap analysis, and evidence.
        If the LLM is disabled, unconfigured, or fails for any
        reason, the deterministic summary is used as the narrative
        instead so the screening result and API response are always
        complete.
        """

        context = {
            "job": {
                "title": job_description.title,
                "required_skills": (
                    job_description.required_skills
                ),
                "preferred_skills": (
                    job_description.preferred_skills
                ),
                "responsibilities": (
                    job_description.responsibilities[:5]
                ),
            },
            "candidate": {
                "skills": resume.skills,
                "experience": [
                    {
                        "role": item.role,
                        "company": item.company,
                    }
                    for item in resume.experience
                ],
                "education": [
                    {
                        "degree": item.degree,
                        "institution": item.institution,
                    }
                    for item in resume.education
                ],
            },
            "evaluation": {
                "eligible": eligibility["eligible"],
                "final_score_percent": round(
                    ranking_score_100, 2
                ),
                "decision": decision,
                "decision_reason": decision_reason,
                "ranking_components": (
                    ranking.model_dump()["features"]
                    if ranking is not None
                    else {}
                ),
            },
            "gaps": {
                "missing_skills": gap_analysis[
                    "missing_skills"
                ],
                "experience_gap": gap_analysis[
                    "experience_gap"
                ],
                "education_gap": gap_analysis[
                    "education_gap"
                ],
                "certification_gap": gap_analysis[
                    "certification_gap"
                ],
            },
            "evidence": [
                {
                    "claim": item.get("claim"),
                    "evidence": item.get("evidence"),
                }
                for item in evidence
            ],
        }

        # LLMExplanationService itself never raises, but screening
        # must remain functional even if a differently-implemented
        # llm_service (e.g. injected via dependency override) does -
        # explanation generation is an enhancement layer and must
        # never be able to fail the screening pipeline.
        try:
            narrative = self.llm_service.generate_explanation(
                context
            )
        except Exception:
            logger.warning(
                "LLM explanation raised unexpectedly; "
                "falling back to the deterministic summary.",
                exc_info=False,
            )
            narrative = None

        if narrative:
            return {
                **explanation,
                "narrative": narrative,
                "narrative_source": "llm",
            }

        return {
            **explanation,
            "narrative": explanation["summary"],
            "narrative_source": "deterministic",
        }