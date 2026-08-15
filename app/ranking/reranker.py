from collections.abc import Callable

from app.core.schemas import CanonicalJob, CanonicalResume
from app.ranking.scoring_engine import (
    calculate_candidate_score,
)


Reranker = Callable[
    [
        CanonicalJob,
        list[CanonicalResume],
    ],
    list[CanonicalResume],
]


def rerank_candidates(
    job: CanonicalJob,
    candidates: list[CanonicalResume],
    top_n: int | None = None,
    reranker: Reranker | None = None,
) -> list[CanonicalResume]:
    """
    Rerank the top-N candidates.

    If a stronger external reranker is supplied, it is used.
    Otherwise, the deterministic scoring engine is used as fallback.
    """

    if not candidates:
        return []

    if top_n is None:
        selected = list(candidates)
    else:
        selected = candidates[:max(0, top_n)]

    if not selected:
        return []

    # Optional stronger model / cross-encoder / LLM.
    if reranker is not None:
        reranked = reranker(
            job,
            selected,
        )

        if len(reranked) != len(selected):
            raise ValueError(
                "Reranker must return exactly the same "
                "number of candidates."
            )

        original_ids = {
            candidate.resume_id
            for candidate in selected
        }

        returned_ids = {
            candidate.resume_id
            for candidate in reranked
        }

        if original_ids != returned_ids:
            raise ValueError(
                "Reranker must return the same candidates."
            )

        return reranked

    # Deterministic fallback.
    scored = [
        (
            calculate_candidate_score(
                job,
                candidate,
            ),
            candidate,
        )
        for candidate in selected
    ]

    scored.sort(
        key=lambda item: (
            -item[0].score,
            item[1].resume_id,
        )
    )

    return [
        candidate
        for _, candidate in scored
    ]