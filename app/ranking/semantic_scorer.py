import logging
import math
import re

from app.core.config import settings
from app.core.schemas import CanonicalJob, CanonicalResume

logger = logging.getLogger(__name__)

# Lazily constructed, process-wide singleton so the BGE-M3 model is
# loaded at most once per process, not once per screening request.
_semantic_service = None


def _get_semantic_service():
    global _semantic_service

    if _semantic_service is None:
        from app.services.semantic_matching_service import (
            SemanticMatchingService,
        )

        _semantic_service = SemanticMatchingService()

    return _semantic_service


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


def _lexical_overlap_score(
    job: CanonicalJob,
    resume: CanonicalResume,
) -> float:
    """
    Deterministic lexical (Jaccard token-overlap) fallback. Used ONLY
    when genuine embedding-based semantic scoring is disabled or
    fails - never presented as an embedding score (see
    score_semantic()'s explicit mode logging).
    """

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


def score_semantic(
    job: CanonicalJob,
    resume: CanonicalResume,
) -> float:
    """
    Semantic similarity between a JD and a candidate resume, in
    [0, 1].

    Genuinely computed from BGE-M3 embeddings + FAISS vector
    similarity when semantic search is enabled and the embedding
    path succeeds (see app/services/semantic_matching_service.py).
    Falls back to a clearly-logged deterministic lexical (token
    overlap) score - never silently - if semantic search is
    disabled, or if embedding generation/vector retrieval fails for
    any reason. Ranking must keep working either way.
    """

    if not settings.enable_semantic_search:
        logger.debug(
            "Semantic scoring using lexical fallback: "
            "disabled by configuration."
        )
        return _lexical_overlap_score(job, resume)

    try:
        result = _get_semantic_service().score(job, resume)

        if result.mode == "embedding":
            return result.score

        logger.warning(
            "Semantic scoring fell back to lexical overlap. "
            "reason=%s",
            result.reason,
        )
        return _lexical_overlap_score(job, resume)

    except Exception as exc:
        logger.warning(
            "Semantic embedding scoring failed; using lexical "
            "fallback. error_type=%s",
            type(exc).__name__,
        )
        return _lexical_overlap_score(job, resume)
