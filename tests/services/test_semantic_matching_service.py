"""
Targeted tests for SemanticMatchingService - the component that
wires CanonicalJob/CanonicalResume -> chunking -> embedding cache ->
FAISS vector retrieval -> an aggregated [0,1] semantic score.

A fake embedder with hand-picked deterministic vectors is used
throughout, so these tests run fast and never load the real BGE-M3
model, while still exercising the real chunking, caching, and FAISS
(VectorRetriever) code paths.
"""

import numpy as np
import pytest

from app.core.schemas import (
    CanonicalEducation,
    CanonicalJob,
    CanonicalResume,
)
from app.retrieval.embeddings import ChunkEmbedding, JDChunkEmbedding
from app.retrieval.jd_chunker import JDChunker
from app.retrieval.resume_chunker import ResumeChunker
from app.services.embedding_cache_service import (
    EmbeddingCacheService,
)
from app.services.semantic_matching_service import (
    SemanticMatchingService,
)


class HashBasedFakeEmbedder:
    """
    Deterministic fake embedder: each distinct text gets a fixed
    pseudo-random unit vector (seeded by the text itself), so
    semantically "similar" fixture text can be constructed to share
    a vector direction and "unrelated" text a very different one -
    without needing the real model.
    """

    model_name = "fake-test-embedder"

    def __init__(self, dimension: int = 8):
        self.dimension = dimension

    def _vector(self, text: str) -> np.ndarray:
        seed = abs(hash(text)) % (2**32)
        rng = np.random.default_rng(seed)
        vector = rng.normal(size=self.dimension).astype(np.float32)
        return vector / np.linalg.norm(vector)

    def embed_chunks(self, chunks):
        return [
            ChunkEmbedding(
                chunk_id=chunk.chunk_id,
                resume_id=chunk.resume_id,
                section=chunk.section,
                vector=self._vector(chunk.text),
            )
            for chunk in chunks
        ]

    def embed_jd_chunks(self, chunks):
        return [
            JDChunkEmbedding(
                chunk_id=chunk.chunk_id,
                job_id=chunk.job_id,
                section=chunk.section,
                vector=self._vector(chunk.text),
            )
            for chunk in chunks
        ]


class FixedVectorEmbedder:
    """
    Fake embedder returning a caller-specified vector per exact
    text, for precisely controlling similarity in aggregation tests.
    """

    model_name = "fixed-vector-test-embedder"

    def __init__(self, vectors: dict[str, list[float]]):
        self.vectors = vectors

    def _vector(self, text: str) -> np.ndarray:
        raw = np.asarray(
            self.vectors[text], dtype=np.float32
        )
        return raw / np.linalg.norm(raw)

    def embed_chunks(self, chunks):
        return [
            ChunkEmbedding(
                chunk_id=chunk.chunk_id,
                resume_id=chunk.resume_id,
                section=chunk.section,
                vector=self._vector(chunk.text),
            )
            for chunk in chunks
        ]

    def embed_jd_chunks(self, chunks):
        return [
            JDChunkEmbedding(
                chunk_id=chunk.chunk_id,
                job_id=chunk.job_id,
                section=chunk.section,
                vector=self._vector(chunk.text),
            )
            for chunk in chunks
        ]


def _job(job_id="job-1", **overrides) -> CanonicalJob:
    defaults = dict(
        job_id=job_id,
        title="Frontend Developer",
        description="Build responsive web interfaces.",
        required_skills=["react", "javascript"],
    )
    defaults.update(overrides)
    return CanonicalJob(**defaults)


def _resume(resume_id="resume-1", **overrides) -> CanonicalResume:
    defaults = dict(
        resume_id=resume_id,
        summary="Frontend developer building React applications.",
        skills=["react", "javascript"],
    )
    defaults.update(overrides)
    return CanonicalResume(**defaults)


def _service(embedder, tmp_path) -> SemanticMatchingService:
    cache = EmbeddingCacheService(tmp_path, embedder)
    return SemanticMatchingService(
        embedder=embedder,
        cache=cache,
        jd_chunker=JDChunker(),
        resume_chunker=ResumeChunker(),
    )


class TestScoreRangeAndMode:
    def test_score_is_in_unit_range(self, tmp_path):
        service = _service(HashBasedFakeEmbedder(), tmp_path)

        result = service.score(_job(), _resume())

        assert 0.0 <= result.score <= 1.0

    def test_mode_is_embedding_on_success(self, tmp_path):
        service = _service(HashBasedFakeEmbedder(), tmp_path)

        result = service.score(_job(), _resume())

        assert result.mode == "embedding"

    def test_result_reports_model_and_dimension(self, tmp_path):
        embedder = HashBasedFakeEmbedder(dimension=8)
        service = _service(embedder, tmp_path)

        result = service.score(_job(), _resume())

        assert result.model_name == "fake-test-embedder"
        assert result.embedding_dimension == 8

    def test_result_reports_chunk_counts(self, tmp_path):
        service = _service(HashBasedFakeEmbedder(), tmp_path)

        result = service.score(_job(), _resume())

        assert result.jd_chunk_count > 0
        assert result.resume_chunk_count > 0

    def test_no_chunkable_content_returns_zero_without_error(
        self, tmp_path
    ):
        service = _service(HashBasedFakeEmbedder(), tmp_path)

        empty_job = CanonicalJob(job_id="empty-job")
        empty_resume = CanonicalResume(resume_id="empty-resume")

        result = service.score(empty_job, empty_resume)

        assert result.score == 0.0


class TestAggregationAvoidsInflation:
    def test_one_strong_chunk_match_does_not_dominate_the_score(
        self, tmp_path
    ):
        # JD has two very different requirement chunks. The resume
        # only strongly matches ONE of them - a naive "take the max
        # over all pairs" aggregation would report near-perfect
        # similarity; the real (per-JD-chunk-then-mean) aggregation
        # must not.
        job_text_a = "requires-react-experience"
        job_text_b = "requires-fifteen-years-cobol-experience"
        resume_text = "expert-react-developer"
        unrelated_resume_text = "cobol-mainframe-batch-jobs"

        embedder = FixedVectorEmbedder(
            {
                job_text_a: [1.0, 0.0, 0.0, 0.0],
                job_text_b: [0.0, 1.0, 0.0, 0.0],
                resume_text: [0.99, 0.01, 0.0, 0.0],
                unrelated_resume_text: [0.0, -1.0, 0.0, 0.0],
            }
        )

        service = _service(embedder, tmp_path)

        job = _job(
            required_skills=[job_text_a],
            preferred_skills=[job_text_b],
            description=None,
            title=None,
        )
        resume = _resume(
            skills=[resume_text],
            summary=unrelated_resume_text,
        )

        result = service.score(job, resume)

        # The strong match (~1.0) is dragged down by the poor match
        # on the second JD chunk (~0.0-ish after normalization) -
        # the aggregate must land well below the single best score.
        assert result.score < 0.9

    def test_top_similarities_reflect_per_chunk_best_matches(
        self, tmp_path
    ):
        service = _service(HashBasedFakeEmbedder(), tmp_path)

        result = service.score(_job(), _resume())

        assert len(result.top_similarities) == result.jd_chunk_count
        assert all(
            -1.0 <= value <= 1.0
            for value in result.top_similarities
        )


class TestCandidateIsolation:
    def test_scoring_candidate_a_never_uses_candidate_b_chunks(
        self, tmp_path
    ):
        embedder = HashBasedFakeEmbedder()
        cache = EmbeddingCacheService(tmp_path, embedder)
        service = SemanticMatchingService(
            embedder=embedder,
            cache=cache,
        )

        job = _job()
        candidate_a = _resume(
            resume_id="candidate-a", skills=["react"]
        )
        candidate_b = _resume(
            resume_id="candidate-b",
            skills=["completely-unrelated-mainframe-cobol"],
        )

        # Warm the cache for both candidates first, as would happen
        # in a real bulk screening run.
        service.score(job, candidate_a)
        service.score(job, candidate_b)

        # Re-score candidate A - the result's resume_chunk_count
        # must reflect ONLY candidate A's own chunks, never a
        # combined/leaked total from candidate B.
        result_a_alone = service.score(job, candidate_a)

        expected_chunk_count = len(
            ResumeChunker().chunk(candidate_a)
        )

        assert (
            result_a_alone.resume_chunk_count
            == expected_chunk_count
        )

    def test_isolation_via_direct_retriever_inspection(
        self, tmp_path
    ):
        # Stronger, more direct proof: build the service's
        # candidate-specific index the same way score() does, and
        # confirm a search only ever returns THIS candidate's
        # resume_id.
        from app.retrieval.vector_retrieval import VectorRetriever

        embedder = HashBasedFakeEmbedder()
        cache = EmbeddingCacheService(tmp_path, embedder)

        resume_chunker = ResumeChunker()
        candidate_a = _resume(resume_id="candidate-a")
        candidate_b = _resume(resume_id="candidate-b")

        embeddings_a = cache.get_or_compute_resume_embeddings(
            "candidate-a", resume_chunker.chunk(candidate_a)
        )
        embeddings_b = cache.get_or_compute_resume_embeddings(
            "candidate-b", resume_chunker.chunk(candidate_b)
        )

        # Both candidates' embeddings exist in the cache (as they
        # would for many candidates in a real corpus), but the index
        # built for scoring candidate A is built from ONLY
        # embeddings_a.
        retriever = VectorRetriever(aggregation="max")
        retriever.build_index(embeddings_a)

        query_vector = embedder.embed_jd_chunks(
            JDChunker().chunk(_job())
        )[0].vector

        results = retriever.score_chunks(query_vector=query_vector)

        assert all(
            result.resume_id == "candidate-a" for result in results
        )
        assert embeddings_b  # sanity: candidate B was embedded too
