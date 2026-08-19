"""
File-based cache for resume/JD chunk embeddings.

Embedding generation (running the BGE-M3 model) is the expensive
part of semantic matching - re-running it for the same resume or job
description on every screening request would make the system
unusable at scale (thousands of resumes, repeated screenings against
multiple jobs). This cache makes embedding generation a one-time
cost per (entity, content) pair:

    resume/job unchanged  -> cached vectors reused, no model call
    resume/job edited     -> content hash changes, re-embedded once

Persisted as one .npz (vectors) + one .json (chunk metadata + a
content hash) file per resume/job under storage_dir, plus an
in-process in-memory layer so repeated lookups within the same
request/batch never touch disk twice. No database migration is
introduced: this mirrors the project's existing pattern of storing
generated artifacts under data/storage/ (see
app/storage/document_storage.py for resume PDFs) rather than adding
a vector column/table that nothing else in the schema needs.
"""

from __future__ import annotations

import json
from hashlib import sha1
from pathlib import Path
from typing import Sequence

import numpy as np

from app.retrieval.embeddings import (
    ChunkEmbedding,
    EmbeddingGenerator,
    JDChunkEmbedding,
)
from app.retrieval.jd_chunker import JDChunk
from app.retrieval.resume_chunker import ResumeChunk


def _content_hash(chunks: Sequence) -> str:
    """
    Stable hash of chunk text content, used to detect whether a
    resume/JD's content has changed since it was last embedded
    (e.g. a candidate re-uploading an edited resume with the same
    resume_id would still get fresh embeddings).
    """

    payload = "␟".join(
        f"{chunk.chunk_id}:{chunk.text}" for chunk in chunks
    )

    return sha1(payload.encode("utf-8")).hexdigest()


class EmbeddingCacheService:
    """
    Get-or-compute cache for resume and JD chunk embeddings.

    Safe for concurrent reads. Writes are atomic (write-then-rename)
    so a concurrent reader never observes a partially written cache
    file; this app does not run multiple worker processes writing
    the *same* resume/job concurrently, so no additional file
    locking is added (see semantic_matching_service.py's docstring
    for the fuller concurrency note).
    """

    def __init__(
        self,
        storage_dir: str | Path,
        embedder: EmbeddingGenerator,
    ) -> None:
        self.storage_dir = Path(storage_dir)
        self.embedder = embedder

        self._resume_memory_cache: dict[
            str, tuple[str, list[ChunkEmbedding]]
        ] = {}
        self._job_memory_cache: dict[
            str, tuple[str, list[JDChunkEmbedding]]
        ] = {}

    def get_or_compute_resume_embeddings(
        self,
        resume_id: str,
        chunks: Sequence[ResumeChunk],
    ) -> list[ChunkEmbedding]:
        if not chunks:
            return []

        content_hash = _content_hash(chunks)

        cached = self._resume_memory_cache.get(resume_id)

        if cached is not None and cached[0] == content_hash:
            return cached[1]

        path = self._path("resumes", resume_id)
        loaded = self._load(path, content_hash)

        if loaded is not None:
            embeddings = [
                ChunkEmbedding(
                    chunk_id=chunk.chunk_id,
                    resume_id=resume_id,
                    section=chunk.section,
                    vector=vector,
                )
                for chunk, vector in zip(chunks, loaded)
            ]

            self._resume_memory_cache[resume_id] = (
                content_hash,
                embeddings,
            )

            return embeddings

        embeddings = self.embedder.embed_chunks(list(chunks))

        self._save(
            path,
            content_hash,
            chunks,
            [embedding.vector for embedding in embeddings],
        )

        self._resume_memory_cache[resume_id] = (
            content_hash,
            embeddings,
        )

        return embeddings

    def get_or_compute_job_embeddings(
        self,
        job_id: str,
        chunks: Sequence[JDChunk],
    ) -> list[JDChunkEmbedding]:
        if not chunks:
            return []

        content_hash = _content_hash(chunks)

        cached = self._job_memory_cache.get(job_id)

        if cached is not None and cached[0] == content_hash:
            return cached[1]

        path = self._path("jobs", job_id)
        loaded = self._load(path, content_hash)

        if loaded is not None:
            embeddings = [
                JDChunkEmbedding(
                    chunk_id=chunk.chunk_id,
                    job_id=job_id,
                    section=chunk.section,
                    vector=vector,
                )
                for chunk, vector in zip(chunks, loaded)
            ]

            self._job_memory_cache[job_id] = (
                content_hash,
                embeddings,
            )

            return embeddings

        embeddings = self.embedder.embed_jd_chunks(list(chunks))

        self._save(
            path,
            content_hash,
            chunks,
            [embedding.vector for embedding in embeddings],
        )

        self._job_memory_cache[job_id] = (
            content_hash,
            embeddings,
        )

        return embeddings

    def _path(self, kind: str, entity_id: str) -> Path:
        # entity ids are already URL/filesystem-safe (job_id/
        # resume_id generated elsewhere in the app), but guard
        # against path traversal from an unexpected id anyway.
        safe_id = "".join(
            char if char.isalnum() or char in "-_." else "_"
            for char in entity_id
        )

        return self.storage_dir / kind / f"{safe_id}.npz"

    @staticmethod
    def _load(
        path: Path,
        expected_content_hash: str,
    ) -> np.ndarray | None:
        metadata_path = path.with_suffix(".json")

        if not path.exists() or not metadata_path.exists():
            return None

        try:
            metadata = json.loads(
                metadata_path.read_text(encoding="utf-8")
            )

            if metadata.get("content_hash") != expected_content_hash:
                return None

            with np.load(path) as data:
                return data["vectors"]
        except (
            OSError,
            ValueError,
            KeyError,
            json.JSONDecodeError,
        ):
            # A corrupted/partial cache entry is treated as a cache
            # miss - the caller re-embeds and overwrites it.
            return None

    @staticmethod
    def _save(
        path: Path,
        content_hash: str,
        chunks: Sequence,
        vectors: Sequence[np.ndarray],
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

        matrix = np.asarray(vectors, dtype=np.float32)

        # np.savez_compressed appends ".npz" to the filename if it
        # isn't already present, so the temp file must itself end in
        # ".npz" or the rename below would silently miss it.
        tmp_vectors_path = (
            path.parent / f"{path.stem}.tmp.npz"
        )
        np.savez_compressed(tmp_vectors_path, vectors=matrix)
        tmp_vectors_path.replace(path)

        metadata = {
            "content_hash": content_hash,
            "chunk_ids": [chunk.chunk_id for chunk in chunks],
            "sections": [chunk.section for chunk in chunks],
        }

        metadata_path = path.with_suffix(".json")
        tmp_metadata_path = path.with_suffix(".json.tmp")
        tmp_metadata_path.write_text(
            json.dumps(metadata, indent=2),
            encoding="utf-8",
        )
        tmp_metadata_path.replace(metadata_path)
