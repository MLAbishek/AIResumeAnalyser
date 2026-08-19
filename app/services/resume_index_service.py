"""
Resume ingestion into the persistent, incrementally-updatable FAISS
resume corpus index (app/infrastructure/vector/vector_index.py).

This is the write path for bulk semantic retrieval: every resume
that should be discoverable via "find relevant candidates for this
job" (bulk_semantic_retrieval_service.py) must be indexed here once,
after which it survives process restarts and is never re-embedded
unless its content actually changes (EmbeddingCacheService already
handles that de-duplication).

Concurrency: FastAPI can run synchronous route handlers on multiple
worker threads, and a single process-wide PersistentVectorIndex
instance is shared across requests (module-level singleton, loaded
once). FAISS index mutation (add_with_ids/remove_ids) is not
thread-safe, so all writes (index_resume/remove_resume) are guarded
by one lock; reads (bulk retrieval's search_chunks) also take it
briefly to avoid reading mid-mutation state. Given the size of this
index (thousands of chunks, infrequent writes relative to reads),
one coarse lock is sufficient without overengineering a finer-
grained scheme.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path

from app.core.config import settings
from app.core.schemas import CanonicalResume, Resume
from app.infrastructure.vector.vector_index import (
    PersistentVectorIndex,
)
from app.normalization.canonical_resume_builder import (
    CanonicalResumeBuilder,
)
from app.retrieval.embeddings import EmbeddingGenerator
from app.retrieval.resume_chunker import ResumeChunker
from app.services import embedding_registry
from app.services.embedding_cache_service import (
    EmbeddingCacheService,
)

logger = logging.getLogger(__name__)


class ResumeIndexService:
    """
    Get-or-create wrapper around one persistent resume vector index,
    handling chunking, embedding (via the shared cache), and safe
    concurrent index mutation.
    """

    def __init__(
        self,
        embedder: EmbeddingGenerator | None = None,
        cache: EmbeddingCacheService | None = None,
        index: PersistentVectorIndex | None = None,
        chunker: ResumeChunker | None = None,
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
        self.chunker = chunker or ResumeChunker()
        self.resume_builder = CanonicalResumeBuilder()
        self.index = index or PersistentVectorIndex(
            storage_path=(
                Path(settings.data_dir)
                / "storage"
                / "vector_index"
                / "resumes"
            ),
            model_name=self.embedder.model_name,
        )
        self._lock = threading.Lock()

        with self._lock:
            self.index.try_load()

    def index_parsed_resume(
        self,
        resume_id: str,
        parsed: Resume,
    ) -> int:
        """
        Convenience entry point for the resume upload route: adapts
        the parser's Resume output into a CanonicalResume (the same
        shape ScreeningService builds internally) and indexes it.
        Skips experience/education entries missing a required field,
        mirroring the same tolerant handling already used when
        persisting them to the database.
        """

        canonical_resume = self.resume_builder.build(
            {
                "resume_id": resume_id,
                "name": parsed.name,
                "summary": parsed.summary,
                "skills": parsed.skills,
                "job_titles": parsed.job_titles,
                "organizations": [
                    experience.company
                    for experience in parsed.experience
                    if experience.company
                ],
                "technologies": [],
                "experiences": [
                    {
                        "job_title": experience.role,
                        "company": experience.company,
                        "start_date": experience.start_date,
                        "end_date": (
                            experience.end_date
                            or "present"
                        ),
                    }
                    for experience in parsed.experience
                    if experience.role
                    and experience.company
                    and experience.start_date
                ],
                "education": [
                    {
                        "degree": education.degree,
                        "institution": education.institution,
                        "field_of_study": education.field,
                    }
                    for education in parsed.education
                    if education.degree
                    and education.institution
                ],
            }
        )

        return self.index_resume(canonical_resume)

    def index_resume(self, resume: CanonicalResume) -> int:
        """
        (Re-)index one resume: chunk -> get-or-compute embeddings
        (cached, so unchanged content never re-embeds) -> replace
        any previously indexed chunks for this resume_id -> persist.

        Returns the number of chunk vectors now indexed for this
        resume.
        """
        chunks = self.chunker.chunk(resume)

        if not chunks:
            logger.debug(
                "Resume %s has no chunkable content; not indexed.",
                resume.resume_id,
            )
            return 0

        embeddings = self.cache.get_or_compute_resume_embeddings(
            resume.resume_id, chunks
        )

        with self._lock:
            self.index.update_resume(resume.resume_id, embeddings)
            self.index.save()

        logger.info(
            "Indexed resume into persistent vector index. "
            "resume_id=%s chunks=%d index_size=%d",
            resume.resume_id,
            len(embeddings),
            self.index.size,
        )

        return len(embeddings)

    def remove_resume(self, resume_id: str) -> int:
        """
        Remove a resume from the persistent index (e.g. resume
        deleted). Returns the number of chunk vectors removed.
        """
        with self._lock:
            removed = self.index.remove_resume(resume_id)

            if removed:
                self.index.save()

        return removed
