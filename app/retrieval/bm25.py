"""
BM25 lexical retrieval for resume matching.

This module implements the Okapi BM25 ranking function without requiring
an external BM25 dependency. Resume chunks are scored individually and
then aggregated to candidate/resume-level results.
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Iterable, Sequence

from app.retrieval.resume_chunker import ResumeChunk


@dataclass(frozen=True)
class BM25ChunkResult:
    """
    BM25 score for one resume chunk.
    """

    chunk_id: str
    resume_id: str
    section: str
    text: str
    score: float


@dataclass(frozen=True)
class BM25CandidateResult:
    """
    Aggregated BM25 result for one candidate/resume.
    """

    resume_id: str
    score: float
    matched_chunks: tuple[BM25ChunkResult, ...]


class BM25Retriever:
    """
    Deterministic Okapi BM25 lexical retriever.

    Args:
        k1: Term-frequency saturation parameter.
        b: Document-length normalization parameter.
    """

    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        if k1 < 0:
            raise ValueError("k1 must be >= 0")

        if not 0 <= b <= 1:
            raise ValueError("b must be between 0 and 1")

        self.k1 = k1
        self.b = b

    @staticmethod
    def tokenize(text: str) -> list[str]:
        """
        Normalize text and split it into lowercase lexical tokens.

        Alphanumeric terms are retained. Punctuation is treated as a
        separator.
        """
        if not text:
            return []

        return re.findall(
            r"[a-z0-9]+",
            text.lower(),
        )

    def score_documents(
        self,
        query: str,
        chunks: Sequence[ResumeChunk],
    ) -> list[BM25ChunkResult]:
        """
        Score all chunks against a query.

        Returns results in descending score order.
        Ties are resolved deterministically using chunk_id.
        """
        if not chunks:
            return []

        query_tokens = self.tokenize(query)

        if not query_tokens:
            return [
                BM25ChunkResult(
                    chunk_id=chunk.chunk_id,
                    resume_id=chunk.resume_id,
                    section=chunk.section,
                    text=chunk.text,
                    score=0.0,
                )
                for chunk in chunks
            ]

        tokenized_documents = [
            self.tokenize(chunk.text)
            for chunk in chunks
        ]

        document_frequency = self._document_frequencies(
            tokenized_documents
        )

        average_document_length = (
            sum(len(tokens) for tokens in tokenized_documents)
            / len(tokenized_documents)
        )

        query_terms = set(query_tokens)

        results: list[BM25ChunkResult] = []

        total_documents = len(chunks)

        for chunk, document_tokens in zip(
            chunks,
            tokenized_documents,
        ):
            score = self._score_document(
                query_terms=query_terms,
                document_tokens=document_tokens,
                document_frequency=document_frequency,
                total_documents=total_documents,
                average_document_length=average_document_length,
            )

            results.append(
                BM25ChunkResult(
                    chunk_id=chunk.chunk_id,
                    resume_id=chunk.resume_id,
                    section=chunk.section,
                    text=chunk.text,
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
        query: str,
        chunks: Sequence[ResumeChunk],
        top_k: int = 10,
    ) -> list[BM25CandidateResult]:
        """
        Retrieve top candidates for a query.

        Multiple matching chunks belonging to the same resume are
        aggregated by summing their positive BM25 scores.

        Args:
            query: Job-description/query text.
            chunks: Resume chunks.
            top_k: Maximum number of candidates to return.

        Returns:
            Candidate-level BM25 results ordered by descending score.
        """
        if top_k < 0:
            raise ValueError("top_k must be >= 0")

        if top_k == 0 or not chunks:
            return []

        chunk_results = self.score_documents(
            query=query,
            chunks=chunks,
        )

        grouped: dict[str, list[BM25ChunkResult]] = defaultdict(list)

        for result in chunk_results:
            if result.score > 0:
                grouped[result.resume_id].append(result)

        candidates: list[BM25CandidateResult] = []

        for resume_id, matched_chunks in grouped.items():
            candidate_score = sum(
                result.score
                for result in matched_chunks
            )

            matched_chunks.sort(
                key=lambda result: (
                    -result.score,
                    result.chunk_id,
                )
            )

            candidates.append(
                BM25CandidateResult(
                    resume_id=resume_id,
                    score=candidate_score,
                    matched_chunks=tuple(matched_chunks),
                )
            )

        candidates.sort(
            key=lambda result: (
                -result.score,
                result.resume_id,
            )
        )

        return candidates[:top_k]

    def _score_document(
        self,
        query_terms: set[str],
        document_tokens: Sequence[str],
        document_frequency: dict[str, int],
        total_documents: int,
        average_document_length: float,
    ) -> float:
        document_length = len(document_tokens)

        if document_length == 0:
            return 0.0

        term_frequency = Counter(document_tokens)

        score = 0.0

        for term in query_terms:
            frequency = term_frequency.get(term, 0)

            if frequency == 0:
                continue

            df = document_frequency.get(term, 0)

            idf = math.log(
                1
                + (
                    total_documents - df + 0.5
                )
                / (
                    df + 0.5
                )
            )

            denominator = (
                frequency
                + self.k1
                * (
                    1
                    - self.b
                    + self.b
                    * (
                        document_length
                        / average_document_length
                    )
                )
            )

            term_score = (
                idf
                * frequency
                * (self.k1 + 1)
                / denominator
            )

            score += term_score

        return score

    @staticmethod
    def _document_frequencies(
        tokenized_documents: Sequence[Sequence[str]],
    ) -> dict[str, int]:
        frequencies: Counter[str] = Counter()

        for document in tokenized_documents:
            frequencies.update(set(document))

        return dict(frequencies)


def retrieve_candidates(
    query: str,
    chunks: Iterable[ResumeChunk],
    top_k: int = 10,
    k1: float = 1.5,
    b: float = 0.75,
) -> list[BM25CandidateResult]:
    """
    Convenience function for candidate-level BM25 retrieval.
    """
    retriever = BM25Retriever(
        k1=k1,
        b=b,
    )

    return retriever.retrieve(
        query=query,
        chunks=list(chunks),
        top_k=top_k,
    )