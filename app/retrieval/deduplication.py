"""
Candidate deduplication for retrieval results.

Uses resume_id as the canonical candidate identity and merges evidence
from multiple retrieval paths without creating duplicate candidates.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from app.retrieval.hybrid import HybridCandidateResult


@dataclass(frozen=True)
class UniqueCandidate:
    """
    One unique candidate after retrieval-result deduplication.

    Attributes:
        resume_id: Canonical candidate identity.
        score: Candidate retrieval score.
        sources: Retrieval paths that produced this candidate.
        bm25_score: Original BM25 score when available.
        dense_score: Original dense score when available.
        hybrid_score: Hybrid score when available.
        bm25_chunks: BM25 retrieval evidence.
        dense_chunks: Dense retrieval evidence.
    """

    resume_id: str
    score: float
    sources: tuple[str, ...]

    bm25_score: float
    dense_score: float
    hybrid_score: float

    bm25_chunks: tuple
    dense_chunks: tuple


class CandidateDeduplicator:
    """
    Deduplicate retrieval candidates by resume_id.

    The deduplicator accepts HybridCandidateResult objects and guarantees
    that each resume_id occurs at most once in the output.
    """

    def deduplicate(
        self,
        results: Sequence[HybridCandidateResult],
        top_k: int | None = None,
    ) -> list[UniqueCandidate]:
        """
        Deduplicate candidates while preserving retrieval evidence.

        If multiple records have the same resume_id, their strongest score
        is retained and evidence from all records is merged.

        Args:
            results: Retrieval results from the hybrid layer.
            top_k: Optional maximum number of unique candidates.

        Returns:
            Unique candidates sorted by descending score.
        """
        if top_k is not None and top_k < 0:
            raise ValueError("top_k must be >= 0")

        if top_k == 0:
            return []

        grouped: dict[str, list[HybridCandidateResult]] = {}

        for result in results:
            grouped.setdefault(
                result.resume_id,
                [],
            ).append(result)

        unique_candidates: list[UniqueCandidate] = []

        for resume_id, candidate_results in grouped.items():
            unique_candidates.append(
                self._merge_candidate(
                    resume_id,
                    candidate_results,
                )
            )

        unique_candidates.sort(
            key=lambda candidate: (
                -candidate.score,
                candidate.resume_id,
            )
        )

        if top_k is not None:
            return unique_candidates[:top_k]

        return unique_candidates

    def deduplicate_many(
        self,
        result_sets: Iterable[
            Sequence[HybridCandidateResult]
        ],
        top_k: int | None = None,
    ) -> list[UniqueCandidate]:
        """
        Deduplicate candidates across multiple retrieval result sets.

        This is useful when results come from separate retrieval batches
        or separate retrieval stages.
        """
        combined: list[HybridCandidateResult] = []

        for result_set in result_sets:
            combined.extend(result_set)

        return self.deduplicate(
            combined,
            top_k=top_k,
        )

    @staticmethod
    def _merge_candidate(
        resume_id: str,
        results: Sequence[HybridCandidateResult],
    ) -> UniqueCandidate:
        """
        Merge all retrieval records belonging to one candidate.
        """
        strongest = max(
            results,
            key=lambda result: (
                result.score,
                result.resume_id,
            ),
        )

        sources: set[str] = set()

        bm25_chunks = []
        dense_chunks = []

        bm25_score = 0.0
        dense_score = 0.0
        hybrid_score = 0.0

        for result in results:
            if (
                result.bm25_score != 0.0
                or result.bm25_chunks
            ):
                sources.add("bm25")

            if (
                result.dense_score != 0.0
                or result.dense_chunks
            ):
                sources.add("dense")

            bm25_score = max(
                bm25_score,
                result.bm25_score,
            )

            dense_score = max(
                dense_score,
                result.dense_score,
            )

            hybrid_score = max(
                hybrid_score,
                result.score,
            )

            bm25_chunks.extend(
                result.bm25_chunks
            )

            dense_chunks.extend(
                result.dense_chunks
            )

        return UniqueCandidate(
            resume_id=resume_id,
            score=strongest.score,
            sources=tuple(sorted(sources)),
            bm25_score=bm25_score,
            dense_score=dense_score,
            hybrid_score=hybrid_score,
            bm25_chunks=tuple(
                bm25_chunks
            ),
            dense_chunks=tuple(
                dense_chunks
            ),
        )


def deduplicate_candidates(
    results: Sequence[HybridCandidateResult],
    top_k: int | None = None,
) -> list[UniqueCandidate]:
    """
    Convenience function for candidate deduplication.
    """
    return CandidateDeduplicator().deduplicate(
        results,
        top_k=top_k,
    )