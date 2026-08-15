from app.core.schemas import CanonicalJob, CanonicalResume


def score_experience(
    job: CanonicalJob,
    resume: CanonicalResume,
) -> float:
    """
    Score candidate experience against the JD requirement.

    Returns:
        1.0 if the candidate meets or exceeds the minimum.
        A proportional score if the candidate has partial experience.
        1.0 when no minimum experience is required.
    """

    minimum = job.experience.minimum_months
    candidate_months = resume.total_experience_months

    if minimum <= 0:
        return 1.0

    if candidate_months <= 0:
        return 0.0

    return round(
        min(candidate_months / minimum, 1.0),
        4,
    )