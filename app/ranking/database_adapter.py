from app.core.schemas import (
    CanonicalEducation,
    CanonicalExperience,
    CanonicalJob,
    CanonicalJobEducationRequirement,
    CanonicalJobExperienceRequirement,
    CanonicalResume,
)
from app.database.models.job import Job
from app.database.models.resume import Resume


def job_to_canonical(job: Job) -> CanonicalJob:
    education_requirements = []

    for requirement in job.education_requirements or []:
        if isinstance(requirement, dict):
            education_requirements.append(
                CanonicalJobEducationRequirement(
                    degree=requirement.get("degree"),
                    field_of_study=requirement.get(
                        "field_of_study"
                    ),
                    required=requirement.get(
                        "required",
                        False,
                    ),
                )
            )

    return CanonicalJob(
        job_id=job.job_id,
        title=job.title,
        description=job.description,
        required_skills=job.required_skills or [],
        preferred_skills=job.preferred_skills or [],
        required_technologies=(
            job.required_technologies or []
        ),
        preferred_technologies=(
            job.preferred_technologies or []
        ),
        organizations=[],
        experience=CanonicalJobExperienceRequirement(
            minimum_months=job.required_experience_months or 0,
            maximum_months=None,
        ),
        education=education_requirements,
    )


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