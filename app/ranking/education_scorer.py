from app.core.schemas import CanonicalJob, CanonicalResume


def _normalize(value: str) -> str:
    return " ".join(value.lower().strip().split())


def _matches(candidate: str, requirement: str) -> bool:
    candidate = _normalize(candidate)
    requirement = _normalize(requirement)

    return (
        candidate == requirement
        or candidate in requirement
        or requirement in candidate
    )


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

            degree_match = (
                requirement.degree is None
                or _matches(
                    education.degree,
                    requirement.degree,
                )
            )

            field_match = (
                requirement.field_of_study is None
                or (
                    education.field_of_study
                    and _matches(
                        education.field_of_study,
                        requirement.field_of_study,
                    )
                )
            )

            if degree_match and field_match:
                matched += 1
                break

    return round(
        matched / len(requirements),
        4,
    )