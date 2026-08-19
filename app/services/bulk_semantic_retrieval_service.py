"""
Bulk semantic retrieval: given a job, find the most semantically
relevant resumes across the WHOLE indexed corpus using the
persistent FAISS resume index (app/infrastructure/vector/vector_index.py),
rather than scoring one already-known candidate.

    CanonicalJob
      -> JDChunker
      -> EmbeddingCacheService (get-or-compute JD chunk vectors)
      -> PersistentVectorIndex.search_chunks() per JD chunk
      -> best-matching-chunk-per-resume, deduplicated
      -> averaged across JD chunks ("requirement coverage")
      -> top-K unique resume_ids, ranked

This is a RETRIEVAL signal only - it selects which candidates are
worth running through the deterministic pipeline, and reports a
semantic score for informational/ranking purposes. It never decides
eligibility, and the resumes it returns still go through the full
existing ScreeningService/BulkScreeningService unchanged (see
semantic_bulk_screening.py for that orchestration).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from app.core.config import settings
from app.core.schemas import CanonicalJob
from app.infrastructure.vector.vector_index import (
    PersistentVectorIndex,
)
from app.retrieval.embeddings import EmbeddingGenerator
from app.retrieval.jd_chunker import JDChunker
from app.services import embedding_registry
from app.services.embedding_cache_service import (
    EmbeddingCacheService,
)

logger = logging.getLogger(__name__)


@dataclass
class BulkCandidateSemanticResult:
    resume_id: str
    score: float
    matched_jd_chunk_count: int
    total_jd_chunk_count: int
    top_similarities: list[float] = field(default_factory=list)


class BulkSemanticRetrievalService:
    """
    Retrieves the most semantically relevant resumes for a job from
    the persistent resume vector index.
    """

    def __init__(
        self,
        embedder: EmbeddingGenerator | None = None,
        cache: EmbeddingCacheService | None = None,
        index: PersistentVectorIndex | None = None,
        jd_chunker: JDChunker | None = None,
    ) -> None:
        self.embedder = embedder or (
            embedding_registry.get_shared_embedding_generator()
        )
        self.cache = cache or EmbeddingCacheService(
            storage_dir=(
                Path(settings.data_dir) / "storage" / "embeddings"
            ),
            embedder=self.embedder,
        )
        self.index = index or PersistentVectorIndex(
            storage_path=(
                Path(settings.data_dir)
                / "storage"
                / "vector_index"
                / "resumes"
            ),
            model_name=self.embedder.model_name,
        )
        self.jd_chunker = jd_chunker or JDChunker()

        if not self.index.is_built:
            self.index.try_load()

    def retrieve(
        self,
        job: CanonicalJob,
        top_k: int = 20,
    ) -> list[BulkCandidateSemanticResult]:
        """
        Return up to top_k unique resume_ids most semantically
        relevant to `job`, ranked descending by score.

        Formula (documented, deliberately not "max over every
        pair"): for each JD chunk, find every resume's single BEST
        matching chunk (deduplicated per resume so a resume with
        many chunks cannot dominate just by having more chunks to
        compare). Average each resume's per-JD-chunk best match
        across ALL JD chunks (dividing by the total JD chunk count,
        not just how many chunks it matched) - this is "requirement
        coverage": a resume that only shows up strongly for one of
        five JD requirements scores lower than one that is
        consistently relevant across all five. The mean cosine
        similarity (in [-1, 1]) is rescaled to [0, 1] via (x+1)/2,
        matching score_vector_similarity()/SemanticMatchingService.
        """

        if not self.index.is_built:
            logger.info(
                "Bulk semantic retrieval skipped: resume index is "
                "empty/not built."
            )
            return []

        jd_chunks = self.jd_chunker.chunk(job)

        if not jd_chunks:
            return []

        jd_embeddings = self.cache.get_or_compute_job_embeddings(
            job.job_id, jd_chunks
        )

        # resume_id -> {jd_chunk_index: best_similarity}
        per_resume_per_jd_chunk: dict[str, dict[int, float]] = {}

        for jd_chunk_index, jd_embedding in enumerate(jd_embeddings):
            chunk_results = self.index.search_chunks(
                jd_embedding.vector
            )

            seen_resume_ids: set[str] = set()

            # search_chunks() returns results sorted by descending
            # score, so the FIRST time we see a resume_id here is
            # its best-matching chunk for this JD chunk.
            for result in chunk_results:
                if result.resume_id in seen_resume_ids:
                    continue

                seen_resume_ids.add(result.resume_id)
                per_resume_per_jd_chunk.setdefault(
                    result.resume_id, {}
                )[jd_chunk_index] = result.score

        total_jd_chunks = len(jd_embeddings)
        results: list[BulkCandidateSemanticResult] = []

        for resume_id, chunk_scores in per_resume_per_jd_chunk.items():
            mean_similarity = (
                sum(chunk_scores.values()) / total_jd_chunks
            )

            normalized_score = round(
                max(0.0, min(1.0, (mean_similarity + 1.0) / 2.0)),
                4,
            )

            results.append(
                BulkCandidateSemanticResult(
                    resume_id=resume_id,
                    score=normalized_score,
                    matched_jd_chunk_count=len(chunk_scores),
                    total_jd_chunk_count=total_jd_chunks,
                    top_similarities=[
                        round(chunk_scores[i], 4)
                        for i in sorted(chunk_scores)
                    ],
                )
            )

        results.sort(key=lambda r: (-r.score, r.resume_id))

        logger.info(
            "Bulk semantic retrieval completed. job_id=%s "
            "jd_chunks=%d candidates_found=%d top_k=%d",
            job.job_id,
            total_jd_chunks,
            len(results),
            top_k,
        )

        return results[:top_k]
