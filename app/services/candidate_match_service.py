from datetime import date

from sqlalchemy.orm import Session, selectinload

from app.api.schemas.screenings import ScreeningResultResponse
from app.core.schemas import (
    Education as CoreEducation,
    Experience as CoreExperience,
    JobDescription,
    Resume as CoreResume,
)
from app.database.crud.screening_results import (
    get_screening_result,
)
from app.database.models.job import Job
from app.database.models.profile import MatchProfile
from app.database.models.resume import Resume
from app.database.models.screening import ScreeningResult
from app.services.screening_persistence_service import (
    ScreeningPersistenceService,
)
from app.services.screening_service import ScreeningService


def _job_to_screening_schema(job: Job) -> JobDescription:
    return JobDescription(
        job_id=job.job_id,
        title=job.title,
        summary=job.description,
        required_skills=job.required_skills or [],
        preferred_skills=job.preferred_skills or [],
        required_experience_years=(
            job.required_experience_months / 12
            if job.required_experience_months
            else None
        ),
        education=[
            requirement.get("description", "")
            for requirement in (job.education_requirements or [])
            if requirement.get("description")
        ],
        certifications=job.required_certifications or [],
        responsibilities=job.responsibilities or [],
        location=job.location,
        job_type=job.job_type,
        raw_text=job.raw_text,
    )


def _months_before(reference: date, months: int) -> date:
    month_index = (
        reference.year * 12
        + (reference.month - 1)
        - months
    )

    year, month = divmod(month_index, 12)

    return date(year, month + 1, min(reference.day, 28))


def _experience_items(resume: Resume) -> list[CoreExperience]:
    if resume.experiences:
        # Real per-role history exists (e.g. resumes created via
        # the recruiter JSON endpoint) - use it directly.
        return [
            CoreExperience(
                role=experience.job_title,
                company=experience.company,
                start_date=(
                    experience.start_date.isoformat()
                    if experience.start_date
                    else None
                ),
                end_date=(
                    experience.end_date.isoformat()
                    if experience.end_date
                    else None
                ),
            )
            for experience in resume.experiences
        ]

    if not resume.total_experience_months:
        return []

    # Candidate-uploaded resumes are parsed from free text and
    # don't yield reliable per-role start/end dates, but the total
    # months of experience IS a real value already computed by the
    # deterministic parser. Encode it as a single aggregate entry
    # spanning that duration so eligibility/ranking see the actual
    # parsed experience instead of zero - this does not fabricate a
    # score, it only reshapes an already-computed real number into
    # the pipeline's expected input.
    today = date.today()

    return [
        CoreExperience(
            role=(
                resume.job_titles[0]
                if resume.job_titles
                else "Professional Experience"
            ),
            company="Prior Experience",
            start_date=_months_before(
                today,
                resume.total_experience_months,
            ).isoformat(),
            end_date=today.isoformat(),
        )
    ]


def _resume_to_screening_schema(resume: Resume) -> CoreResume:
    return CoreResume(
        resume_id=resume.resume_id,
        name=resume.name,
        summary=resume.summary,
        skills=resume.skills or [],
        experience=_experience_items(resume),
        education=[
            CoreEducation(
                institution=education.institution,
                degree=education.degree,
                field=education.field_of_study,
                start_date=(
                    education.start_date.isoformat()
                    if education.start_date
                    else None
                ),
                end_date=(
                    education.end_date.isoformat()
                    if education.end_date
                    else None
                ),
            )
            for education in resume.education
        ],
        certifications=[],
        projects=[],
        job_titles=resume.job_titles or [],
        total_experience_years=(
            resume.total_experience_months / 12
            if resume.total_experience_months
            else None
        ),
        raw_text=resume.raw_text or "",
    )


def screening_to_response(
    screening: ScreeningResult,
) -> ScreeningResultResponse:
    """
    Convert a persisted ScreeningResult into the same response
    shape already used by GET /api/screenings/{job_id}/{resume_id} -
    the candidate and recruiter surfaces both present the identical
    AI evaluation, never a re-derived or simplified one.
    """

    ranking = None

    if screening.ranking is not None:
        ranking = {
            "rank": screening.ranking.rank,
            "score": screening.ranking.score,
            "skill_score": screening.ranking.skill_score,
            "experience_score": (
                screening.ranking.experience_score
            ),
            "seniority_score": (
                screening.ranking.seniority_score
            ),
            "education_score": (
                screening.ranking.education_score
            ),
            "semantic_score": (
                screening.ranking.semantic_score
            ),
        }

    profile = screening.profile

    evidence = []

    if profile is not None:
        evidence = [
            {
                "id": reference.id,
                "claim": reference.claim,
                "source": reference.source,
                "section": reference.section,
                "evidence": reference.evidence,
            }
            for reference in profile.evidence
        ]

    return ScreeningResultResponse(
        screening_id=screening.id,
        job_id=screening.job.job_id,
        resume_id=screening.resume.resume_id,
        candidate_name=screening.resume.name,
        eligible=screening.eligible,
        decision=screening.decision,
        final_score=screening.final_score,
        decision_reason=screening.decision_reason,
        ranking=ranking,
        gap_analysis=(
            profile.gap_analysis
            if profile is not None
            else None
        ),
        explanation=(
            profile.explanation
            if profile is not None
            else None
        ),
        evidence=evidence,
    )


class CandidateMatchService:
    """
    Orchestrates the existing screening pipeline for the
    candidate-facing "match preview" and "apply" flows.

    This does NOT reimplement scoring/eligibility/decision logic -
    it adapts a persisted (Job, Resume) pair into the same
    ScreeningService/ScreeningPersistenceService already used by the
    recruiter-facing /api/screen endpoint, and reuses the persisted
    result as the single source of truth for screening_id.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_preview(
        self,
        *,
        job: Job,
        resume: Resume,
        candidate_user_id: int,
    ) -> ScreeningResult:
        """
        Return the persisted ScreeningResult for (job, resume),
        computing it via the real pipeline once and reusing it on
        every subsequent call (preview or apply) for the same pair.

        This intentionally never recomputes an existing screening:
        doing so would both re-run the AI pipeline needlessly (see
        performance guidance) and risk the preview and apply steps
        ending up with two different persisted screening_id values
        for what the candidate experienced as one evaluation. A
        candidate who wants a fresh score after editing their resume
        uploads it again, which naturally gets its own resume_id and
        therefore its own screening.
        """

        existing_screening = get_screening_result(
            self.db,
            job_id=job.id,
            resume_id=resume.id,
        )

        if existing_screening is not None:
            return self.reload_screening(existing_screening.id)

        job_description = _job_to_screening_schema(job)
        core_resume = _resume_to_screening_schema(resume)

        service = ScreeningService()

        result = service.screen(
            job_description=job_description,
            resumes=[core_resume],
        )

        persistence = ScreeningPersistenceService(self.db)

        screening_ids = persistence.persist(
            job_id=result["job_id"],
            results=result["results"],
        )

        return self.reload_screening(screening_ids[0])

    def reload_screening(
        self,
        screening_id: int,
    ) -> ScreeningResult:
        return (
            self.db.query(ScreeningResult)
            .options(
                selectinload(ScreeningResult.job),
                selectinload(ScreeningResult.resume),
                selectinload(ScreeningResult.ranking),
                selectinload(
                    ScreeningResult.profile
                ).selectinload(MatchProfile.evidence),
            )
            .filter(ScreeningResult.id == screening_id)
            .one()
        )
