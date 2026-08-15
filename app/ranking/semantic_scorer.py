import math
import re

from app.core.schemas import CanonicalJob, CanonicalResume


def _tokens(text: str) -> set[str]:
    return {
        token.lower()
        for token in re.findall(
            r"\b[a-zA-Z0-9+#.]+\b",
            text,
        )
        if len(token) > 1
    }


def _cosine_similarity(
    vector_a: list[float],
    vector_b: list[float],
) -> float:

    if not vector_a or not vector_b:
        return 0.0

    if len(vector_a) != len(vector_b):
        raise ValueError(
            "Semantic vectors must have the same dimensionality."
        )

    dot = sum(
        a * b
        for a, b in zip(vector_a, vector_b)
    )

    norm_a = math.sqrt(
        sum(a * a for a in vector_a)
    )

    norm_b = math.sqrt(
        sum(b * b for b in vector_b)
    )

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


def score_vector_similarity(
    job_vector: list[float],
    candidate_vector: list[float],
) -> float:

    similarity = _cosine_similarity(
        job_vector,
        candidate_vector,
    )

    return round(
        max(
            0.0,
            min(
                1.0,
                (similarity + 1.0) / 2.0,
            ),
        ),
        4,
    )


def score_semantic(
    job: CanonicalJob,
    resume: CanonicalResume,
) -> float:

    job_text = " ".join(
        filter(
            None,
            [
                job.title,
                job.description,
                *job.required_skills,
                *job.preferred_skills,
                *job.required_technologies,
                *job.preferred_technologies,
            ],
        )
    )

    candidate_text = " ".join(
        filter(
            None,
            [
                resume.summary,
                *resume.skills,
                *resume.job_titles,
                *resume.organizations,
                *resume.technologies,
                *[
                    experience.job_title
                    for experience in resume.experiences
                ],
            ],
        )
    )

    job_tokens = _tokens(job_text)
    candidate_tokens = _tokens(candidate_text)

    if not job_tokens or not candidate_tokens:
        return 0.0

    union = job_tokens | candidate_tokens

    if not union:
        return 0.0

    intersection = job_tokens & candidate_tokens

    return round(
        len(intersection) / len(union),
        4,
    )