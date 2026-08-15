"""
Hybrid retrieval fusion.

Combines lexical BM25 retrieval and dense vector retrieval into a single
candidate ranking using independently normalized scores.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from app.retrieval.bm25 import BM25CandidateResult
from app.retrieval.vector_retrieval import VectorCandidateResult


@dataclass(frozen=True)
class HybridCandidateResult:
    """
    Unified candidate result produced by hybrid retrieval.

    Attributes:
        resume_id: Canonical candidate/resume identifier.
        score: Final fused retrieval score.
        bm25_score: Original BM25 score.
        dense_score: Original dense/vector score.
        normalized_bm25_score: Min-max normalized BM25 score.
        normalized_dense_score: Min-max normalized dense score.
        bm25_chunks: BM25 evidence chunks.
        dense_chunks: Dense retrieval evidence chunks.
    """

    resume_id: str
    score: float

    bm25_score: float
    dense_score: float

    normalized_bm25_score: float
    normalized_dense_score: float

    bm25_chunks: tuple
    dense_chunks: tuple


class HybridRetriever:
    """
    Fuse BM25 and dense candidate rankings.

    Args:
        bm25_weight: Weight assigned to the normalized BM25 score.
        dense_weight: Weight assigned to the normalized dense score.
        score_normalization: Normalization strategy.
    """

    def __init__(
        self,
        bm25_weight: float = 0.5,
        dense_weight: float | None = None,
    ) -> None:
        if not 0.0 <= bm25_weight <= 1.0:
            raise ValueError(
                "bm25_weight must be between 0 and 1"
            )

        if dense_weight is None:
            dense_weight = 1.0 - bm25_weight

        if not 0.0 <= dense_weight <= 1.0:
            raise ValueError(
                "dense_weight must be between 0 and 1"
            )

        if abs(
            (bm25_weight + dense_weight) - 1.0
        ) > 1e-9:
            raise ValueError(
                "bm25_weight and dense_weight must sum to 1"
            )

        self.bm25_weight = bm25_weight
        self.dense_weight = dense_weight

    def fuse(
        self,
        bm25_results: Sequence[BM25CandidateResult],
        dense_results: Sequence[VectorCandidateResult],
        top_k: int | None = None,
    ) -> list[HybridCandidateResult]:
        """
        Fuse BM25 and dense candidate results.

        Candidates appearing in only one retrieval path are retained.
        Candidates appearing in both paths receive evidence from both.

        Args:
            bm25_results: Candidate-level BM25 results.
            dense_results: Candidate-level dense results.
            top_k: Optional maximum number of candidates.

        Returns:
            Unified candidates sorted by descending hybrid score.
        """
        if top_k is not None and top_k < 0:
            raise ValueError("top_k must be >= 0")

        if top_k == 0:
            return []

        bm25_by_id = {
            result.resume_id: result
            for result in bm25_results
        }

        dense_by_id = {
            result.resume_id: result
            for result in dense_results
        }

        candidate_ids = (
            set(bm25_by_id)
            | set(dense_by_id)
        )

        if not candidate_ids:
            return []

        bm25_scores = {
            resume_id: result.score
            for resume_id, result in bm25_by_id.items()
        }

        dense_scores = {
            resume_id: result.score
            for resume_id, result in dense_by_id.items()
        }

        normalized_bm25 = self._normalize_scores(
            bm25_scores
        )

        normalized_dense = self._normalize_scores(
            dense_scores
        )

        results: list[HybridCandidateResult] = []

        for resume_id in candidate_ids:
            bm25_score = bm25_scores.get(
                resume_id,
                0.0,
            )

            dense_score = dense_scores.get(
                resume_id,
                0.0,
            )

            normalized_bm25_score = normalized_bm25.get(
                resume_id,
                0.0,
            )

            normalized_dense_score = normalized_dense.get(
                resume_id,
                0.0,
            )

            hybrid_score = (
                self.bm25_weight
                * normalized_bm25_score
                + self.dense_weight
                * normalized_dense_score
            )

            bm25_chunks = (
                bm25_by_id[resume_id].matched_chunks
                if resume_id in bm25_by_id
                else ()
            )

            dense_chunks = (
                dense_by_id[resume_id].matched_chunks
                if resume_id in dense_by_id
                else ()
            )

            results.append(
                HybridCandidateResult(
                    resume_id=resume_id,
                    score=hybrid_score,
                    bm25_score=bm25_score,
                    dense_score=dense_score,
                    normalized_bm25_score=(
                        normalized_bm25_score
                    ),
                    normalized_dense_score=(
                        normalized_dense_score
                    ),
                    bm25_chunks=tuple(bm25_chunks),
                    dense_chunks=tuple(dense_chunks),
                )
            )

        results.sort(
            key=lambda result: (
                -result.score,
                result.resume_id,
            )
        )

        if top_k is not None:
            return results[:top_k]

        return results

    @staticmethod
    def _normalize_scores(
        scores: dict[str, float],
    ) -> dict[str, float]:
        """
        Min-max normalize scores to [0, 1].

        Missing candidates are represented outside this method as zero.

        If all scores are equal, every candidate receives 1.0 when the
        common score is positive, otherwise 0.0.
        """
        if not scores:
            return {}

        values = list(scores.values())

        minimum = min(values)
        maximum = max(values)

        if maximum == minimum:
            normalized_value = (
                1.0 if maximum > 0.0 else 0.0
            )

            return {
                candidate_id: normalized_value
                for candidate_id in scores
            }

        return {
            candidate_id: (
                (score - minimum)
                / (maximum - minimum)
            )
            for candidate_id, score in scores.items()
        }


def fuse_retrieval_results(
    bm25_results: Sequence[BM25CandidateResult],
    dense_results: Sequence[VectorCandidateResult],
    bm25_weight: float = 0.5,
    top_k: int | None = None,
) -> list[HybridCandidateResult]:
    """
    Convenience function for hybrid retrieval fusion.
    """
    retriever = HybridRetriever(
        bm25_weight=bm25_weight,
    )

    return retriever.fuse(
        bm25_results=bm25_results,
        dense_results=dense_results,
        top_k=top_k,
    )