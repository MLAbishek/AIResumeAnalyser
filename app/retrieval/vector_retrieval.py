"""
Dense vector retrieval for semantic resume matching.

Retrieves semantically similar resume chunks using cosine similarity
and aggregates chunk-level similarities into candidate-level results.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from app.retrieval.embeddings import ChunkEmbedding


@dataclass(frozen=True)
class VectorChunkResult:
    """
    Similarity result for one resume chunk.
    """

    chunk_id: str
    resume_id: str
    section: str
    score: float


@dataclass(frozen=True)
class VectorCandidateResult:
    """
    Aggregated semantic retrieval result for one candidate.
    """

    resume_id: str
    score: float
    matched_chunks: tuple[VectorChunkResult, ...]


class VectorRetriever:
    """
    Retrieve semantically similar resume chunks/candidates.

    Candidate scores are calculated from the strongest matching chunks
    by default. This prevents a candidate with many mediocre chunks from
    automatically outranking a candidate with one highly relevant chunk.
    """

    def __init__(
        self,
        aggregation: str = "max",
    ) -> None:
        allowed = {
            "max",
            "sum",
            "mean",
        }

        if aggregation not in allowed:
            raise ValueError(
                f"aggregation must be one of {sorted(allowed)}"
            )

        self.aggregation = aggregation

    @staticmethod
    def cosine_similarity(
        query_vector: np.ndarray,
        document_vector: np.ndarray,
    ) -> float:
        """
        Calculate cosine similarity between two vectors.
        """
        query = np.asarray(
            query_vector,
            dtype=np.float32,
        ).reshape(-1)

        document = np.asarray(
            document_vector,
            dtype=np.float32,
        ).reshape(-1)

        if query.size == 0 or document.size == 0:
            raise ValueError(
                "vectors must not be empty"
            )

        if query.shape != document.shape:
            raise ValueError(
                "query and document vectors must have "
                "the same dimension"
            )

        if not np.all(np.isfinite(query)):
            raise ValueError(
                "query vector contains non-finite values"
            )

        if not np.all(np.isfinite(document)):
            raise ValueError(
                "document vector contains non-finite values"
            )

        query_norm = np.linalg.norm(query)
        document_norm = np.linalg.norm(document)

        if query_norm == 0 or document_norm == 0:
            return 0.0

        similarity = float(
            np.dot(query, document)
            / (query_norm * document_norm)
        )

        return similarity

    def score_chunks(
        self,
        query_vector: np.ndarray,
        embeddings: Sequence[ChunkEmbedding],
    ) -> list[VectorChunkResult]:
        """
        Calculate cosine similarity between the query and every chunk.

        Results are sorted by descending similarity with deterministic
        chunk-ID tie breaking.
        """
        if not embeddings:
            return []

        results: list[VectorChunkResult] = []

        for embedding in embeddings:
            score = self.cosine_similarity(
                query_vector,
                embedding.vector,
            )

            results.append(
                VectorChunkResult(
                    chunk_id=embedding.chunk_id,
                    resume_id=embedding.resume_id,
                    section=embedding.section,
                    score=score,
                )
            )

        results.sort(
            key=lambda result: (
                -result.score,
                result.chunk_id,
            )
        )

        return results

    def retrieve(
        self,
        query_vector: np.ndarray,
        embeddings: Sequence[ChunkEmbedding],
        top_k: int = 10,
        min_score: float | None = None,
    ) -> list[VectorCandidateResult]:
        """
        Retrieve top semantically similar candidates.

        Args:
            query_vector: Dense embedding for the JD/query.
            embeddings: Dense embeddings for resume chunks.
            top_k: Maximum number of candidates.
            min_score: Optional minimum cosine similarity.

        Returns:
            Candidate-level semantic retrieval results.
        """
        if top_k < 0:
            raise ValueError(
                "top_k must be >= 0"
            )

        if min_score is not None and not (
            -1.0 <= min_score <= 1.0
        ):
            raise ValueError(
                "min_score must be between -1 and 1"
            )

        if top_k == 0 or not embeddings:
            return []

        chunk_results = self.score_chunks(
            query_vector=query_vector,
            embeddings=embeddings,
        )

        if min_score is not None:
            chunk_results = [
                result
                for result in chunk_results
                if result.score >= min_score
            ]

        grouped: dict[
            str,
            list[VectorChunkResult],
        ] = {}

        for result in chunk_results:
            grouped.setdefault(
                result.resume_id,
                [],
            ).append(result)

        candidates: list[VectorCandidateResult] = []

        for resume_id, matched_chunks in grouped.items():
            score = self._aggregate(
                matched_chunks
            )

            matched_chunks.sort(
                key=lambda result: (
                    -result.score,
                    result.chunk_id,
                )
            )

            candidates.append(
                VectorCandidateResult(
                    resume_id=resume_id,
                    score=score,
                    matched_chunks=tuple(
                        matched_chunks
                    ),
                )
            )

        candidates.sort(
            key=lambda result: (
                -result.score,
                result.resume_id,
            )
        )

        return candidates[:top_k]

    def _aggregate(
        self,
        results: Sequence[VectorChunkResult],
    ) -> float:
        if not results:
            return 0.0

        scores = np.asarray(
            [result.score for result in results],
            dtype=np.float32,
        )

        if self.aggregation == "max":
            return float(np.max(scores))

        if self.aggregation == "sum":
            return float(np.sum(scores))

        return float(np.mean(scores))


def retrieve_vectors(
    query_vector: np.ndarray,
    embeddings: Sequence[ChunkEmbedding],
    top_k: int = 10,
    aggregation: str = "max",
    min_score: float | None = None,
) -> list[VectorCandidateResult]:
    """
    Convenience function for vector retrieval.
    """
    retriever = VectorRetriever(
        aggregation=aggregation,
    )

    return retriever.retrieve(
        query_vector=query_vector,
        embeddings=embeddings,
        top_k=top_k,
        min_score=min_score,
    )