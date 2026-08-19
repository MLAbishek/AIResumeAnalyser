"""
Targeted tests for ResumeIndexService - the resume ingestion path
into the persistent FAISS corpus index. A fake embedder is used
throughout so these never load the real BGE-M3 model.
"""

import numpy as np
import pytest

from app.core.schemas import CanonicalResume
from app.infrastructure.vector.vector_index import (
    PersistentVectorIndex,
)
from app.retrieval.embeddings import ChunkEmbedding
from app.retrieval.resume_chunker import ResumeChunker
from app.services.embedding_cache_service import (
    EmbeddingCacheService,
)
from app.services.resume_index_service import ResumeIndexService


class CountingEmbedder:
    model_name = "fake-test-embedder"

    def __init__(self, dimension: int = 4):
        self.dimension = dimension
        self.embed_chunks_calls = 0

    def _vector(self, text: str) -> np.ndarray:
        value = float(len(text))
        vector = np.array(
            [value, value + 1, value + 2, value + 3],
            dtype=np.float32,
        )
        return vector / np.linalg.norm(vector)

    def embed_chunks(self, chunks):
        self.embed_chunks_calls += 1

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
        raise AssertionError(
            "ResumeIndexService should never embed JD chunks."
        )


def _resume(resume_id="resume-1", skills=None) -> CanonicalResume:
    return CanonicalResume(
        resume_id=resume_id,
        summary="Backend engineer.",
        skills=skills or ["python", "sql"],
    )


def _service(tmp_path, embedder=None):
    embedder = embedder or CountingEmbedder()
    cache = EmbeddingCacheService(tmp_path / "cache", embedder)
    index = PersistentVectorIndex(tmp_path / "index")
    return ResumeIndexService(
        embedder=embedder,
        cache=cache,
        index=index,
        chunker=ResumeChunker(),
    ), embedder, index


class TestIndexResume:
    def test_indexing_a_resume_adds_it_to_the_persistent_index(
        self, tmp_path
    ):
        service, embedder, index = _service(tmp_path)

        added = service.index_resume(_resume())

        assert added > 0
        assert index.is_built
        assert index.size == added

    def test_index_is_persisted_to_disk(self, tmp_path):
        service, embedder, index = _service(tmp_path)
        service.index_resume(_resume())

        reloaded = PersistentVectorIndex(tmp_path / "index")
        reloaded.load()

        assert reloaded.size == index.size

    def test_reindexing_unchanged_resume_does_not_re_embed(
        self, tmp_path
    ):
        service, embedder, index = _service(tmp_path)

        service.index_resume(_resume())
        calls_after_first = embedder.embed_chunks_calls

        service.index_resume(_resume())

        assert embedder.embed_chunks_calls == calls_after_first

    def test_reindexing_changed_resume_replaces_old_chunks(
        self, tmp_path
    ):
        service, embedder, index = _service(tmp_path)

        service.index_resume(
            _resume(skills=["python", "sql"])
        )

        service.index_resume(
            _resume(skills=["python", "sql", "docker", "aws"])
        )

        # Only the current content's chunks remain for this resume
        # (chunk_id is content-derived, so the old skills chunk's id
        # differs from the new one and must not still be present).
        resume_chunk_ids = {
            metadata["chunk_id"]
            for metadata in index._metadata.values()
            if metadata["resume_id"] == "resume-1"
        }
        current_chunk_ids = {
            chunk.chunk_id
            for chunk in ResumeChunker().chunk(
                _resume(
                    skills=["python", "sql", "docker", "aws"]
                )
            )
        }
        assert resume_chunk_ids == current_chunk_ids

    def test_resume_with_no_chunkable_content_is_not_indexed(
        self, tmp_path
    ):
        service, embedder, index = _service(tmp_path)

        added = service.index_resume(
            CanonicalResume(resume_id="empty-resume")
        )

        assert added == 0
        assert not index.is_built


class TestRemoveResume:
    def test_remove_deletes_the_resume_from_the_index(
        self, tmp_path
    ):
        service, embedder, index = _service(tmp_path)
        service.index_resume(_resume(resume_id="resume-1"))
        service.index_resume(_resume(resume_id="resume-2"))

        removed = service.remove_resume("resume-1")

        assert removed > 0
        assert all(
            metadata["resume_id"] != "resume-1"
            for metadata in index._metadata.values()
        )
        assert any(
            metadata["resume_id"] == "resume-2"
            for metadata in index._metadata.values()
        )


class TestIndexFromParsedResume:
    def test_index_parsed_resume_builds_canonical_and_indexes(
        self, tmp_path
    ):
        from app.core.schemas import (
            Experience,
            Resume as CoreResume,
        )

        service, embedder, index = _service(tmp_path)

        parsed = CoreResume(
            resume_id="raw-resume-1",
            name="Jamie Doe",
            skills=["python", "fastapi"],
            experience=[
                Experience(
                    role="Backend Engineer",
                    company="Acme",
                    start_date="01/2022",
                    end_date="01/2024",
                )
            ],
            raw_text="Jamie Doe resume text.",
        )

        added = service.index_parsed_resume(
            "raw-resume-1", parsed
        )

        assert added > 0
        assert any(
            metadata["resume_id"] == "raw-resume-1"
            for metadata in index._metadata.values()
        )

    def test_incomplete_experience_entries_are_skipped_safely(
        self, tmp_path
    ):
        from app.core.schemas import (
            Experience,
            Resume as CoreResume,
        )

        service, embedder, index = _service(tmp_path)

        parsed = CoreResume(
            resume_id="raw-resume-2",
            skills=["python"],
            experience=[
                Experience(role=None, company=None),
            ],
            raw_text="text",
        )

        # Must not raise even though the experience entry is
        # incomplete (missing role/company/start_date).
        added = service.index_parsed_resume(
            "raw-resume-2", parsed
        )

        assert added > 0
