"""
Targeted tests for BulkSemanticRetrievalService - JD-vs-whole-corpus
retrieval via the persistent FAISS index. A fixed-vector fake
embedder gives precise control over similarity for aggregation and
anti-domination tests.
"""

import numpy as np

from app.core.schemas import CanonicalJob
from app.infrastructure.vector.vector_index import (
    PersistentVectorIndex,
)
from app.retrieval.embeddings import ChunkEmbedding, JDChunkEmbedding
from app.retrieval.jd_chunker import JDChunker
from app.retrieval.resume_chunker import ResumeChunker
from app.services.bulk_semantic_retrieval_service import (
    BulkSemanticRetrievalService,
)
from app.services.embedding_cache_service import (
    EmbeddingCacheService,
)


class FixedVectorEmbedder:
    model_name = "fixed-vector-test-embedder"

    def __init__(self, vectors: dict[str, list[float]]):
        self.vectors = vectors

    def _vector(self, text: str) -> np.ndarray:
        raw = np.asarray(self.vectors[text], dtype=np.float32)
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
        title=None,
        description="job-description-text",
    )
    defaults.update(overrides)
    return CanonicalJob(**defaults)


def _service(tmp_path, embedder):
    cache = EmbeddingCacheService(tmp_path / "cache", embedder)
    index = PersistentVectorIndex(tmp_path / "index")
    return (
        BulkSemanticRetrievalService(
            embedder=embedder,
            cache=cache,
            index=index,
            jd_chunker=JDChunker(),
        ),
        cache,
        index,
    )


def _index_resume(index, cache, resume_id, section_texts):
    chunks = []
    for i, (section, text) in enumerate(section_texts.items()):
        from app.retrieval.resume_chunker import ResumeChunk

        chunks.append(
            ResumeChunk(
                chunk_id=f"{resume_id}-{section}",
                resume_id=resume_id,
                section=section,
                text=text,
                position=i,
                metadata={},
            )
        )
    embeddings = cache.get_or_compute_resume_embeddings(
        resume_id, chunks
    )
    index.add(embeddings)


class TestEmptyIndex:
    def test_empty_index_returns_no_candidates(self, tmp_path):
        embedder = FixedVectorEmbedder(
            {"job-description-text": [1.0, 0.0]}
        )
        service, cache, index = _service(tmp_path, embedder)

        results = service.retrieve(_job())

        assert results == []


class TestTopKAndOrdering:
    def test_more_relevant_resume_ranks_first(self, tmp_path):
        job_text = "job-description-text"
        embedder = FixedVectorEmbedder(
            {
                job_text: [1.0, 0.0],
                "strong-match": [0.99, 0.05],
                "weak-match": [0.2, 0.98],
            }
        )
        service, cache, index = _service(tmp_path, embedder)

        _index_resume(
            index, cache, "resume-strong", {"skills": "strong-match"}
        )
        _index_resume(
            index, cache, "resume-weak", {"skills": "weak-match"}
        )

        results = service.retrieve(_job(description=job_text), top_k=10)

        assert results[0].resume_id == "resume-strong"
        assert results[0].score > results[1].score

    def test_top_k_limits_result_count(self, tmp_path):
        job_text = "job-description-text"
        vectors = {job_text: [1.0, 0.0]}
        for i in range(5):
            vectors[f"resume-text-{i}"] = [1.0 - i * 0.1, 0.1 * i]

        embedder = FixedVectorEmbedder(vectors)
        service, cache, index = _service(tmp_path, embedder)

        for i in range(5):
            _index_resume(
                index,
                cache,
                f"resume-{i}",
                {"skills": f"resume-text-{i}"},
            )

        results = service.retrieve(_job(description=job_text), top_k=2)

        assert len(results) == 2


class TestNoChunkCountDomination:
    def test_resume_with_many_chunks_does_not_win_on_count_alone(
        self, tmp_path
    ):
        # resume-many has 5 chunks, all only weakly related to the
        # JD. resume-one has a single chunk that matches the JD very
        # well. The many-chunk resume must not out-rank the strong
        # single-chunk resume just by having more chunks - each JD
        # chunk only contributes ONE (its best) match per resume.
        job_text = "job-description-text"
        vectors = {
            job_text: [1.0, 0.0],
            "one-strong-match": [0.99, 0.05],
        }
        for i in range(5):
            vectors[f"weak-chunk-{i}"] = [0.3, 0.95]

        embedder = FixedVectorEmbedder(vectors)
        service, cache, index = _service(tmp_path, embedder)

        _index_resume(
            index,
            cache,
            "resume-one",
            {"skills": "one-strong-match"},
        )
        _index_resume(
            index,
            cache,
            "resume-many",
            {f"section-{i}": f"weak-chunk-{i}" for i in range(5)},
        )

        results = service.retrieve(_job(description=job_text))
        by_id = {result.resume_id: result for result in results}

        assert by_id["resume-one"].score > by_id["resume-many"].score


class TestGroupingAndUniqueness:
    def test_results_contain_unique_resume_ids(self, tmp_path):
        job_text = "job-description-text"
        embedder = FixedVectorEmbedder(
            {
                job_text: [1.0, 0.0],
                "chunk-a": [0.9, 0.1],
                "chunk-b": [0.8, 0.2],
            }
        )
        service, cache, index = _service(tmp_path, embedder)

        _index_resume(
            index,
            cache,
            "resume-1",
            {"skills": "chunk-a", "experience": "chunk-b"},
        )

        results = service.retrieve(_job(description=job_text))

        resume_ids = [result.resume_id for result in results]
        assert len(resume_ids) == len(set(resume_ids))

    def test_matched_chunk_count_reflects_jd_chunk_coverage(
        self, tmp_path
    ):
        job_text = "job-description-text"
        embedder = FixedVectorEmbedder(
            {
                job_text: [1.0, 0.0],
                "chunk-a": [0.9, 0.1],
            }
        )
        service, cache, index = _service(tmp_path, embedder)

        _index_resume(
            index, cache, "resume-1", {"skills": "chunk-a"}
        )

        results = service.retrieve(_job(description=job_text))

        assert results[0].total_jd_chunk_count == 1
        assert results[0].matched_jd_chunk_count == 1
