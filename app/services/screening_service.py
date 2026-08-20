import concurrent.futures
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

        # Rank every candidate, not just the eligibility-gate
        # survivors - eligibility (hard requirements) and ranking
        # (relative strength) are different concerns. An ineligible
        # candidate can still have a real, evidence-backed score;
        # forcing their ranking to a hardcoded 0.0 (the old
        # eligible_resumes-only behavior) silently contradicted their
        # own matched_skills/experience/education evidence and made
        # the reported score meaningless for anyone who failed even
        # one hard gate.
        ranked_scores = rank_candidates(
            canonical_job,
            canonical_resumes,
        )

        ranked_by_id = {
            result.resume_id: result
            for result in ranked_scores
        }

        results = []
        llm_contexts: list[dict[str, Any] | None] = []

        for resume in resumes:
            eligibility = eligibility_results[
                resume.resume_id
            ]

            ranking = ranked_by_id.get(
                resume.resume_id
            )

            result, llm_context = self._build_candidate_result(
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
            llm_contexts.append(llm_context)

        # Every candidate already has a complete, correct result with
        # a deterministic narrative fallback at this point - fetching
        # LLM narratives is a best-effort enhancement layered on top,
        # run concurrently and time-boxed so N selected candidates
        # never turns into N sequential 15-45s network calls.
        self._attach_narratives(results, llm_contexts)

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
            # candidate.location above is always None - neither
            # Resume nor CanonicalResume has a location field
            # anywhere in this codebase, so there is no signal to
            # compare a job's location against. Passing the job's
            # location through here would make check_location()
            # reject every candidate for any job with a location
            # set (unavailable candidate location + a real
            # requirement = ineligible), which is a guaranteed
            # false rejection, not a real location mismatch.
            location=None,
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
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        """
        Build the complete candidate-level screening result, plus the
        LLM narrative context for that candidate (None if LLM
        explanations are disabled/unconfigured).
        """

        ranking_score = None

        if ranking is not None:
            ranking_score = ranking.score

        # Rounded once, here, and reused by every downstream consumer
        # (threshold decision, explanation, evidence, LLM context,
        # the final result dict) - this is the one canonical
        # percentage value. Rounding separately at each consumption
        # site (as before) let unrounded float noise (e.g.
        # 73.42999999999999) leak into evidence citations while the
        # API-facing field showed the rounded 73.43, a spurious
        # mismatch between two presentations of the same score.
        ranking_score_100 = round(
            ranking_score * 100
            if ranking_score is not None
            else 0.0,
            2,
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
        # strength here, not as neither matched nor missing. They are
        # kept as two SEPARATE lists (not merged) so GapAnalysisEngine
        # can classify a missing entry's severity - missing a
        # required skill is a critical gap, missing a preferred one
        # is nice-to-have, and conflating them would make every
        # missing optional technology look as serious as a genuine
        # requirement failure.
        matching_jd = {
            "required_skills": canonical_job.required_skills,
            "preferred_skills": canonical_job.preferred_skills,
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
            # NOTE: no trailing comma here - a stray trailing comma
            # previously wrapped this concatenated list in a 1-tuple,
            # which ExplainabilityEngine then stringified whole
            # (producing a single garbled "['reason one', 'reason
            # two', ...]" entry in the narrative's reasons instead of
            # the individual reason strings).
            "reasons": (
                eligibility["result"]["reasons"]
                + [threshold["reason"]]
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

        # A deterministic narrative is always present up front - the
        # LLM narrative (if any) is layered on afterwards by
        # _attach_narratives, so this result is already complete and
        # valid on its own.
        explanation = {
            **explanation,
            "narrative": explanation["summary"],
            "narrative_source": "deterministic",
        }

        # Building the context is pure/local (no network call) -
        # whether to actually call out to the LLM is entirely
        # llm_service's own decision (it no-ops instantly if
        # disabled/unconfigured), so ScreeningService always builds
        # it and always offers it to _attach_narratives.
        llm_context = self._build_llm_context(
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
        }, llm_context

    def _build_llm_context(
        self,
        *,
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
        Build the grounded context an LLM narrative for this
        candidate would be generated from. Pure/local - makes no
        network call, so building it for every candidate up front is
        cheap regardless of how many candidates are being screened.
        """

        return {
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

    def _attach_narratives(
        self,
        results: list[dict[str, Any]],
        llm_contexts: list[dict[str, Any] | None],
    ) -> None:
        """
        Fetch LLM narratives for every candidate concurrently and
        attach them in place, replacing each result's deterministic
        narrative fallback where the LLM produced one in time.

        Runs all candidates' requests in parallel instead of
        sequentially, and never waits for stragglers past a fixed
        cap - a slow/hanging call for one candidate can never stall
        the whole screening request, and every candidate already has
        a complete, valid result (with the deterministic narrative)
        regardless of what happens here.
        """

        runnable = [
            (index, context)
            for index, context in enumerate(llm_contexts)
            if context is not None
        ]

        if not runnable:
            return

        max_workers = min(len(runnable), 5)
        executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers
        )

        try:
            future_to_index = {
                executor.submit(
                    self.llm_service.generate_explanation,
                    context,
                ): index
                for index, context in runnable
            }

            # getattr with a fallback: llm_service is a caller-
            # injectable dependency (e.g. a test mock), not
            # guaranteed to expose timeout_seconds.
            wait_timeout = (
                getattr(
                    self.llm_service,
                    "timeout_seconds",
                    15.0,
                )
                + 10
            )

            done, _ = concurrent.futures.wait(
                future_to_index,
                timeout=wait_timeout,
            )

            for future in done:
                index = future_to_index[future]

                try:
                    narrative = future.result()
                except Exception:
                    logger.warning(
                        "LLM explanation raised unexpectedly; "
                        "keeping the deterministic narrative.",
                        exc_info=False,
                    )
                    narrative = None

                if narrative:
                    results[index]["explanation"] = {
                        **results[index]["explanation"],
                        "narrative": narrative,
                        "narrative_source": "llm",
                    }
        finally:
            # wait=False: any request still in flight past the cap
            # above is abandoned from the caller's perspective (its
            # result is simply never used) rather than blocking this
            # request further.
            executor.shutdown(wait=False)