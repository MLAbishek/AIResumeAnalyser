"""
Targeted tests for EmbeddingCacheService: duplicate-embedding
prevention (Part 11 of the semantic-matching task) - the same
resume/JD must not be re-embedded on every screening request.

Uses a fake embedder that counts calls, so these tests prove caching
behavior without loading the real BGE-M3 model.
"""

import numpy as np
import pytest

from app.retrieval.jd_chunker import JDChunk
from app.retrieval.resume_chunker import ResumeChunk
from app.services.embedding_cache_service import (
    EmbeddingCacheService,
)


class CountingEmbedder:
    """Deterministic fake embedder that counts real embed calls."""

    def __init__(self, dimension: int = 4):
        self.dimension = dimension
        self.embed_chunks_calls = 0
        self.embed_jd_chunks_calls = 0

    def _vector(self, text: str) -> np.ndarray:
        value = float(len(text))
        vector = np.array(
            [value, value + 1, value + 2, value + 3],
            dtype=np.float32,
        )
        return vector / np.linalg.norm(vector)

    def embed_chunks(self, chunks):
        self.embed_chunks_calls += 1

        from app.retrieval.embeddings import ChunkEmbedding

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
        self.embed_jd_chunks_calls += 1

        from app.retrieval.embeddings import JDChunkEmbedding

        return [
            JDChunkEmbedding(
                chunk_id=chunk.chunk_id,
                job_id=chunk.job_id,
                section=chunk.section,
                vector=self._vector(chunk.text),
            )
            for chunk in chunks
        ]


def _resume_chunks(resume_id="r1", text="Python and SQL"):
    return [
        ResumeChunk(
            chunk_id=f"{resume_id}-skills",
            resume_id=resume_id,
            section="skills",
            text=text,
            position=0,
            metadata={},
        )
    ]


def _jd_chunks(job_id="j1", text="Python developer role"):
    return [
        JDChunk(
            chunk_id=f"{job_id}-desc",
            job_id=job_id,
            section="description",
            text=text,
            position=0,
        )
    ]


class TestResumeEmbeddingCache:
    def test_first_call_computes_embeddings(self, tmp_path):
        embedder = CountingEmbedder()
        cache = EmbeddingCacheService(tmp_path, embedder)

        result = cache.get_or_compute_resume_embeddings(
            "r1", _resume_chunks()
        )

        assert len(result) == 1
        assert embedder.embed_chunks_calls == 1

    def test_second_call_in_same_process_uses_memory_cache(
        self, tmp_path
    ):
        embedder = CountingEmbedder()
        cache = EmbeddingCacheService(tmp_path, embedder)

        cache.get_or_compute_resume_embeddings(
            "r1", _resume_chunks()
        )
        cache.get_or_compute_resume_embeddings(
            "r1", _resume_chunks()
        )

        assert embedder.embed_chunks_calls == 1

    def test_call_after_cache_object_recreated_uses_disk_cache(
        self, tmp_path
    ):
        embedder = CountingEmbedder()
        cache_1 = EmbeddingCacheService(tmp_path, embedder)
        cache_1.get_or_compute_resume_embeddings(
            "r1", _resume_chunks()
        )

        # A brand new cache instance (e.g. a fresh process) must
        # still find the persisted embeddings on disk.
        cache_2 = EmbeddingCacheService(tmp_path, embedder)
        result = cache_2.get_or_compute_resume_embeddings(
            "r1", _resume_chunks()
        )

        assert len(result) == 1
        assert embedder.embed_chunks_calls == 1

    def test_changed_content_triggers_re_embedding(self, tmp_path):
        embedder = CountingEmbedder()
        cache = EmbeddingCacheService(tmp_path, embedder)

        cache.get_or_compute_resume_embeddings(
            "r1", _resume_chunks(text="Python and SQL")
        )
        cache.get_or_compute_resume_embeddings(
            "r1", _resume_chunks(text="Completely different content")
        )

        assert embedder.embed_chunks_calls == 2

    def test_different_resumes_are_cached_independently(
        self, tmp_path
    ):
        embedder = CountingEmbedder()
        cache = EmbeddingCacheService(tmp_path, embedder)

        cache.get_or_compute_resume_embeddings(
            "r1", _resume_chunks(resume_id="r1")
        )
        cache.get_or_compute_resume_embeddings(
            "r2", _resume_chunks(resume_id="r2")
        )

        assert embedder.embed_chunks_calls == 2

    def test_cached_vectors_match_original(self, tmp_path):
        embedder = CountingEmbedder()
        cache = EmbeddingCacheService(tmp_path, embedder)

        original = cache.get_or_compute_resume_embeddings(
            "r1", _resume_chunks()
        )

        cache_2 = EmbeddingCacheService(tmp_path, embedder)
        reloaded = cache_2.get_or_compute_resume_embeddings(
            "r1", _resume_chunks()
        )

        np.testing.assert_allclose(
            original[0].vector, reloaded[0].vector
        )


class TestJobEmbeddingCache:
    def test_first_call_computes_embeddings(self, tmp_path):
        embedder = CountingEmbedder()
        cache = EmbeddingCacheService(tmp_path, embedder)

        result = cache.get_or_compute_job_embeddings(
            "j1", _jd_chunks()
        )

        assert len(result) == 1
        assert embedder.embed_jd_chunks_calls == 1

    def test_repeated_calls_do_not_re_embed(self, tmp_path):
        # Mirrors screening the same job against many candidates -
        # the JD must only be embedded once.
        embedder = CountingEmbedder()
        cache = EmbeddingCacheService(tmp_path, embedder)

        for _ in range(5):
            cache.get_or_compute_job_embeddings("j1", _jd_chunks())

        assert embedder.embed_jd_chunks_calls == 1


class TestEmptyInput:
    def test_empty_resume_chunks_returns_empty_without_embedding(
        self, tmp_path
    ):
        embedder = CountingEmbedder()
        cache = EmbeddingCacheService(tmp_path, embedder)

        result = cache.get_or_compute_resume_embeddings("r1", [])

        assert result == []
        assert embedder.embed_chunks_calls == 0
