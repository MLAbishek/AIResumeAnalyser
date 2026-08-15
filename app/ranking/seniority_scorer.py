import re

from app.core.schemas import CanonicalJob, CanonicalResume


SENIORITY_LEVELS = {
    "intern": 0,
    "trainee": 0,
    "junior": 1,
    "associate": 2,
    "mid": 2,
    "intermediate": 2,
    "senior": 3,
    "lead": 4,
    "principal": 5,
    "staff": 5,
    "manager": 5,
    "director": 6,
    "head": 7,
    "vp": 8,
    "vice president": 8,
    "chief": 9,
}


def _normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def _extract_level(title: str) -> int | None:
    normalized = _normalize(title)

    for keyword, level in sorted(
        SENIORITY_LEVELS.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        if re.search(
            rf"\b{re.escape(keyword)}\b",
            normalized,
        ):
            return level

    return None


def _role_similarity(
    job_title: str,
    candidate_title: str,
) -> float:
    job_words = set(_normalize(job_title).split())
    candidate_words = set(_normalize(candidate_title).split())

    if not job_words or not candidate_words:
        return 0.0

    return len(job_words & candidate_words) / len(job_words)


def score_seniority(
    job: CanonicalJob,
    resume: CanonicalResume,
) -> float:

    if not job.title:
        return 1.0

    candidate_titles = [
        title
        for title in resume.job_titles
        if title and title.strip()
    ]

    candidate_titles.extend(
        experience.job_title
        for experience in resume.experiences
        if experience.job_title
    )

    if not candidate_titles:
        return 0.0

    role_score = max(
        _role_similarity(job.title, title)
        for title in candidate_titles
    )

    job_level = _extract_level(job.title)

    candidate_levels = [
        level
        for title in candidate_titles
        if (level := _extract_level(title)) is not None
    ]

    if job_level is None or not candidate_levels:
        seniority_score = 0.5
    else:
        closest = min(
            candidate_levels,
            key=lambda level: abs(level - job_level),
        )

        difference = abs(closest - job_level)

        if difference == 0:
            seniority_score = 1.0
        elif difference == 1:
            seniority_score = 0.75
        elif difference == 2:
            seniority_score = 0.5
        else:
            seniority_score = 0.25

    return round(
        0.5 * role_score + 0.5 * seniority_score,
        4,
    )