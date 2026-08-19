"""
Genuine embedding-based semantic matching for ranking.

Wires together the existing (previously unused by the live path)
retrieval stack for CANDIDATE-SPECIFIC scoring (job_id + resume_id):

    CanonicalJob/CanonicalResume
      -> JDChunker / ResumeChunker      (section-aware text chunks)
      -> EmbeddingCacheService          (get-or-compute, avoids
                                          re-running the model)
      -> EmbeddingGenerator (BGE-M3)    (dense vectors)
      -> direct cosine similarity       (real similarity, no index)
      -> aggregation                    (JD-requirement coverage)
      -> semantic_score in [0, 1]

This is "option A" for candidate-specific scoring (retrieve the
candidate's own cached vectors and compute cosine similarity
directly against JD vectors) rather than "option B" (query the
shared persistent FAISS corpus index and filter by resume_id):
simpler and cheaper for a single, already-known (job, resume) pair,
since no index needs to be built, searched, or discarded per call.
Candidate isolation is structural, not just a filter - only this
candidate's own cached embeddings are ever read.

For BULK retrieval (job -> most relevant resumes across the whole
corpus), see bulk_semantic_retrieval_service.py, which uses the
persistent, incrementally-updatable FAISS index
(app/infrastructure/vector/vector_index.py) instead - the right tool
when searching across many resumes rather than scoring one specific
pair.

Concurrency: EmbeddingGenerator's SentenceTransformer.encode() is
stateless per call once the model is loaded. No FAISS index is
built or mutated in this file at all, so no locking is needed here
(see resume_index_service.py for the locking around the shared
persistent index's writes). The EmbeddingCacheService's save() uses
write-then-atomic-rename, so a concurrent reader never observes a
partially written cache file.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from app.core.config import settings
from app.core.schemas import CanonicalJob, CanonicalResume
from app.retrieval.embeddings import EmbeddingGenerator
from app.retrieval.jd_chunker import JDChunker
from app.retrieval.resume_chunker import ResumeChunker
from app.retrieval.vector_retrieval import VectorRetriever
from app.services import embedding_registry
from app.services.embedding_cache_service import (
    EmbeddingCacheService,
)

logger = logging.getLogger(__name__)


@dataclass
class SemanticScoreResult:
    """
    The semantic score plus enough diagnostics to prove (or
    disprove) that the real embedding path produced it - see
    observability requirements: model, dimension, chunk counts, and
    the top similarity values that fed the aggregate.
    """

    score: float
    mode: str  # "embedding" or "fallback"
    model_name: str | None = None
    embedding_dimension: int | None = None
    jd_chunk_count: int = 0
    resume_chunk_count: int = 0
    top_similarities: list[float] = field(default_factory=list)
    reason: str | None = None


class SemanticMatchingService:
    """
    Computes a genuine embedding-based semantic score for one
    (job, resume) pair, reusing a single embedding model instance
    and a persistent chunk-embedding cache across calls.
    """

    def __init__(
        self,
        embedder: EmbeddingGenerator | None = None,
        cache: EmbeddingCacheService | None = None,
        jd_chunker: JDChunker | None = None,
        resume_chunker: ResumeChunker | None = None,
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
        self.jd_chunker = jd_chunker or JDChunker()
        self.resume_chunker = resume_chunker or ResumeChunker()

    def score(
        self,
        job: CanonicalJob,
        resume: CanonicalResume,
    ) -> SemanticScoreResult:
        jd_chunks = self.jd_chunker.chunk(job)
        resume_chunks = self.resume_chunker.chunk(resume)

        if not jd_chunks or not resume_chunks:
            logger.debug(
                "Semantic scoring skipped: no chunks to compare. "
                "jd_chunks=%d resume_chunks=%d",
                len(jd_chunks),
                len(resume_chunks),
            )
            return SemanticScoreResult(
                score=0.0,
                mode="embedding",
                jd_chunk_count=len(jd_chunks),
                resume_chunk_count=len(resume_chunks),
                reason="no chunkable content",
            )

        jd_embeddings = self.cache.get_or_compute_job_embeddings(
            job.job_id,
            jd_chunks,
        )
        resume_embeddings = (
            self.cache.get_or_compute_resume_embeddings(
                resume.resume_id,
                resume_chunks,
            )
        )

        # Direct cosine similarity against ONLY this candidate's own
        # cached chunk vectors - no shared/global index is touched,
        # so candidate isolation is structural rather than a filter
        # applied after the fact.
        #
        # Best resume-chunk match PER JD chunk, then averaged across
        # JD chunks ("requirement coverage"). A resume that matches
        # one JD chunk very strongly but has nothing relevant for
        # the rest will still pull the average down - this avoids
        # the score-inflation failure mode of taking a single global
        # max similarity across every possible pair.
        top_similarities: list[float] = []

        for jd_embedding in jd_embeddings:
            best_similarity = max(
                VectorRetriever.cosine_similarity(
                    jd_embedding.vector,
                    resume_embedding.vector,
                )
                for resume_embedding in resume_embeddings
            )

            top_similarities.append(best_similarity)

        if not top_similarities:
            return SemanticScoreResult(
                score=0.0,
                mode="embedding",
                model_name=self.embedder.model_name,
                jd_chunk_count=len(jd_chunks),
                resume_chunk_count=len(resume_chunks),
                reason="no vector matches returned",
            )

        mean_similarity = float(np.mean(top_similarities))

        # Cosine similarity is in [-1, 1]. Rescale to [0, 1] - the
        # same transform already used by ranking/semantic_scorer.py's
        # score_vector_similarity().
        normalized_score = round(
            max(0.0, min(1.0, (mean_similarity + 1.0) / 2.0)),
            4,
        )

        logger.info(
            "Semantic score computed via embeddings. "
            "model=%s dim=%s jd_chunks=%d resume_chunks=%d "
            "mean_similarity=%.4f score=%.4f",
            self.embedder.model_name,
            resume_embeddings[0].vector.shape[0],
            len(jd_chunks),
            len(resume_chunks),
            mean_similarity,
            normalized_score,
        )

        return SemanticScoreResult(
            score=normalized_score,
            mode="embedding",
            model_name=self.embedder.model_name,
            embedding_dimension=int(
                resume_embeddings[0].vector.shape[0]
            ),
            jd_chunk_count=len(jd_chunks),
            resume_chunk_count=len(resume_chunks),
            top_similarities=[
                round(value, 4) for value in top_similarities
            ],
        )
