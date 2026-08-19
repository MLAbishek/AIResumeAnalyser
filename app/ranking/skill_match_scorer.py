from app.core.schemas import CanonicalJob, CanonicalResume
from app.normalization.normalizer_utils import (
    split_requirement_group,
)


def _normalize(value: str) -> str:
    return " ".join(value.lower().strip().split())


def _matches(required: str, candidate: str) -> bool:
    """
    Compare two skill names after normalization.
    """

    required = _normalize(required)
    candidate = _normalize(candidate)

    if required == candidate:
        return True

    return required in candidate or candidate in required


def score_skills(
    job: CanonicalJob,
    resume: CanonicalResume,
) -> float:
    """
    Calculate required and preferred skill coverage.

    Required skills = 70%
    Preferred skills = 30%

    Returns a normalized score between 0 and 1.
    """

    candidate_skills = [
        skill
        for skill in resume.skills
        if skill and skill.strip()
    ]

    required_skills = [
        skill
        for skill in job.required_skills
        if skill and skill.strip()
    ]

    preferred_skills = [
        skill
        for skill in job.preferred_skills
        if skill and skill.strip()
    ]

    def coverage(requirements: list[str]) -> float:
        if not requirements:
            return 1.0

        # A requirement entry may encode alternatives
        # ("java|python|c++|c#") - it counts as covered if the
        # candidate matches ANY ONE of them, consistent with
        # eligibility's check_skills() and gap analysis.
        matched = sum(
            any(
                _matches(alternative, candidate)
                for alternative in split_requirement_group(
                    requirement
                )
                for candidate in candidate_skills
            )
            for requirement in requirements
        )

        return matched / len(requirements)

    required_score = coverage(required_skills)
    preferred_score = coverage(preferred_skills)

    if required_skills and preferred_skills:
        score = (
            0.7 * required_score
            + 0.3 * preferred_score
        )
    elif required_skills:
        score = required_score
    else:
        score = preferred_score

    return round(score, 4)