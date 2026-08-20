from app.core.schemas import (
    CanonicalEducation,
    CanonicalExperience,
    CanonicalJob,
    CanonicalResume,
)
from app.database.models.job import Job
from app.database.models.resume import Resume
from app.normalization.canonical_jd_builder import CanonicalJobBuilder


def job_to_canonical(job: Job) -> CanonicalJob:
    """
    Job.required_skills/preferred_skills store the raw JD bullet
    text (kept raw deliberately, for human-readable display - see
    app/api/routes/jobs.py's upload endpoint). Ranking/eligibility
    need the canonicalized, soft/hard-reclassified atomic skill
    concepts instead, exactly like ScreeningService._build_canonical_job
    already produces for the one-shot screening flow - so this goes
    through the same CanonicalJobBuilder rather than passing the raw
    JD sentences through as if they were already atomic skills.
    """

    parsed_jd = {
        "job_id": job.job_id,
        "title": job.title,
        "description": job.description,
        "required_skills": job.required_skills or [],
        "preferred_skills": job.preferred_skills or [],
        "required_technologies": job.required_technologies or [],
        "preferred_technologies": (
            job.preferred_technologies or []
        ),
        "responsibilities": job.responsibilities or [],
        "experience": {
            "minimum_months": job.required_experience_months or 0,
            "maximum_months": None,
        },
        "education": [
            requirement
            for requirement in (job.education_requirements or [])
            if isinstance(requirement, dict)
        ],
    }

    return CanonicalJobBuilder().build(parsed_jd)


def resume_to_canonical(
    resume: Resume,
) -> CanonicalResume:

    experiences = [
        CanonicalExperience(
            job_title=experience.job_title,
            company=experience.company,
            start_date=experience.start_date,
            end_date=experience.end_date,
            duration_months=experience.duration_months,
        )
        for experience in resume.experiences
    ]

    education = [
        CanonicalEducation(
            degree=entry.degree,
            institution=entry.institution,
            field_of_study=entry.field_of_study,
            start_date=entry.start_date,
            end_date=entry.end_date,
        )
        for entry in resume.education
    ]

    return CanonicalResume(
        resume_id=resume.resume_id,
        name=resume.name,
        email=resume.email,
        phone=resume.phone,
        summary=resume.summary,
        skills=resume.skills or [],
        job_titles=resume.job_titles or [],
        organizations=resume.organizations or [],
        technologies=resume.technologies or [],
        experiences=experiences,
        education=education,
        total_experience_months=(
            resume.total_experience_months or 0
        ),
    )