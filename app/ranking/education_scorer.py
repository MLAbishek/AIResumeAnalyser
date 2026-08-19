from app.core.schemas import CanonicalJob, CanonicalResume
from app.normalization.education_normalizer import (
    EducationNormalizer,
)

_education_normalizer = EducationNormalizer()


def score_education(
    job: CanonicalJob,
    resume: CanonicalResume,
) -> float:

    requirements = [
        requirement
        for requirement in job.education
        if requirement.degree
        or requirement.field_of_study
    ]

    if not requirements:
        return 1.0

    if not resume.education:
        if any(
            requirement.required
            for requirement in requirements
        ):
            return 0.0

        return 0.5

    matched = 0

    for requirement in requirements:
        for education in resume.education:
            if _education_normalizer.requirement_satisfied(
                requirement_degree=requirement.degree,
                requirement_field=requirement.field_of_study,
                candidate_degree=education.degree,
                candidate_field=education.field_of_study,
            ):
                matched += 1
                break

    return round(
        matched / len(requirements),
        4,
    )