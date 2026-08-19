from __future__ import annotations

import json
from hashlib import sha1
from pathlib import Path
from typing import Sequence

import faiss
import numpy as np

from app.retrieval.embeddings import ChunkEmbedding
from app.retrieval.vector_retrieval import (
    VectorCandidateResult,
    VectorChunkResult,
)


def _stable_chunk_id(chunk_id: str) -> int:
    """
    Deterministic mapping from a chunk_id string (already a content
    hash - see ResumeChunker._append_chunk) to a positive int64 FAISS
    vector id. Using a stable, content-derived id (rather than a
    sequential position/counter) is what makes add()/remove_ids()
    safe under concurrent/repeated ingestion: re-adding the exact
    same chunk content always maps to the exact same id, so it is
    trivially detectable as "already indexed" instead of silently
    duplicated.
    """

    digest = sha1(chunk_id.encode("utf-8")).digest()
    # 8 bytes -> up to 63 bits, safely within a signed int64 and
    # always non-negative (FAISS ids must be non-negative).
    return int.from_bytes(digest[:8], "big") & 0x7FFFFFFFFFFFFFFF


class PersistentVectorIndex:
    """
    Persistent, incrementally-updatable FAISS-backed vector index.

    Stores:
        - FAISS vector index (IndexIDMap2 over IndexFlatIP, so
          individual vectors can be added/removed by a stable id
          without rebuilding the whole index)
        - chunk metadata, keyed by the same stable id
        - embedding dimension
        - model identifier

    The actual embedding model is intentionally not persisted.

    Supports:
        - build(): full (re)build from a batch of embeddings
        - add(): incremental insertion (new resumes / re-indexing)
        - remove_resume(): delete all of one resume's chunks
        - update_resume(): remove_resume() + add() in one step
        - save()/load(): survive a process restart
        - search_chunks()/search(): unchanged query contract
    """

    INDEX_FILENAME = "index.faiss"
    METADATA_FILENAME = "metadata.json"

    VERSION = 2

    def __init__(
        self,
        storage_path: str | Path,
        model_name: str = "BAAI/bge-m3",
        aggregation: str = "max",
    ) -> None:
        if not model_name.strip():
            raise ValueError(
                "model_name must not be empty"
            )

        if aggregation not in {
            "max",
            "sum",
            "mean",
        }:
            raise ValueError(
                "aggregation must be one of "
                "['max', 'mean', 'sum']"
            )

        self.storage_path = Path(storage_path)
        self.model_name = model_name
        self.aggregation = aggregation

        self._index: faiss.Index | None = None
        self._metadata: dict[int, dict] = {}
        self._dimension: int | None = None

    @property
    def is_built(self) -> bool:
        return self._index is not None

    @property
    def dimension(self) -> int | None:
        return self._dimension

    @property
    def size(self) -> int:
        if self._index is None:
            return 0

        return int(self._index.ntotal)

    def build(
        self,
        embeddings: Sequence[ChunkEmbedding],
    ) -> None:
        """
        Replace the entire index with the supplied embeddings.
        """
        self._index = None
        self._metadata = {}
        self._dimension = None

        if not embeddings:
            return

        self.add(embeddings)

    def add(
        self,
        embeddings: Sequence[ChunkEmbedding],
    ) -> int:
        """
        Incrementally add chunk embeddings to the index, creating it
        first if it does not exist yet.

        Chunks whose stable id is already present (i.e. identical
        chunk content already indexed) are skipped, not duplicated -
        this is the safety net for a duplicate upload/re-ingestion
        of unchanged content.

        Returns the number of vectors actually added.
        """
        if not embeddings:
            return 0

        new_embeddings = [
            embedding
            for embedding in embeddings
            if _stable_chunk_id(embedding.chunk_id)
            not in self._metadata
        ]

        if not new_embeddings:
            return 0

        vectors = np.asarray(
            [embedding.vector for embedding in new_embeddings],
            dtype=np.float32,
        )

        if vectors.ndim != 2:
            raise ValueError(
                "embeddings must form a 2-dimensional matrix"
            )

        if vectors.shape[1] == 0:
            raise ValueError(
                "embedding dimension must be greater than zero"
            )

        if not np.all(np.isfinite(vectors)):
            raise ValueError(
                "embeddings must contain only finite values"
            )

        norms = np.linalg.norm(vectors, axis=1, keepdims=True)

        if np.any(norms == 0):
            raise ValueError(
                "embeddings must not contain zero vectors"
            )

        vectors = np.ascontiguousarray(
            vectors / norms,
            dtype=np.float32,
        )

        dimension = vectors.shape[1]

        if self._index is None:
            base = faiss.IndexFlatIP(dimension)
            self._index = faiss.IndexIDMap2(base)
            self._dimension = dimension
        elif dimension != self._dimension:
            raise ValueError(
                "embedding dimension does not match the "
                f"existing index dimension ({self._dimension})"
            )

        ids = np.asarray(
            [
                _stable_chunk_id(embedding.chunk_id)
                for embedding in new_embeddings
            ],
            dtype=np.int64,
        )

        self._index.add_with_ids(vectors, ids)

        for embedding, vector_id in zip(new_embeddings, ids):
            self._metadata[int(vector_id)] = {
                "chunk_id": embedding.chunk_id,
                "resume_id": embedding.resume_id,
                "section": embedding.section,
            }

        return len(new_embeddings)

    def remove_resume(self, resume_id: str) -> int:
        """
        Remove every indexed chunk belonging to one resume.

        Used both for explicit deletion and as the first step of
        update_resume() (a resume being re-uploaded/edited gets its
        old chunk vectors fully replaced, since edited content
        produces different chunk_ids and would otherwise leave
        stale orphaned vectors behind).

        Returns the number of vectors removed.
        """
        if self._index is None:
            return 0

        ids_to_remove = [
            vector_id
            for vector_id, metadata in self._metadata.items()
            if metadata["resume_id"] == resume_id
        ]

        if not ids_to_remove:
            return 0

        self._index.remove_ids(
            np.asarray(ids_to_remove, dtype=np.int64)
        )

        for vector_id in ids_to_remove:
            del self._metadata[vector_id]

        return len(ids_to_remove)

    def update_resume(
        self,
        resume_id: str,
        embeddings: Sequence[ChunkEmbedding],
    ) -> None:
        """
        Replace one resume's indexed chunks with a fresh set -
        remove_resume() followed by add().
        """
        self.remove_resume(resume_id)
        self.add(embeddings)

    def save(self) -> None:
        """
        Persist the FAISS index and metadata atomically (write to a
        temp file, then rename) so a crash mid-save can never leave
        a corrupted index/metadata pair on disk.
        """
        if not self.is_built:
            raise ValueError(
                "cannot save an index that has not been built"
            )

        self.storage_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        index_path = self.storage_path / self.INDEX_FILENAME
        metadata_path = self.storage_path / self.METADATA_FILENAME

        tmp_index_path = self.storage_path / f"{self.INDEX_FILENAME}.tmp"
        faiss.write_index(self._index, str(tmp_index_path))
        tmp_index_path.replace(index_path)

        metadata = {
            "version": self.VERSION,
            "model_name": self.model_name,
            "dimension": self._dimension,
            "aggregation": self.aggregation,
            "vectors": {
                str(vector_id): entry
                for vector_id, entry in self._metadata.items()
            },
        }

        temporary_metadata_path = (
            self.storage_path
            / f"{self.METADATA_FILENAME}.tmp"
        )

        temporary_metadata_path.write_text(
            json.dumps(
                metadata,
                indent=2,
            ),
            encoding="utf-8",
        )

        temporary_metadata_path.replace(
            metadata_path
        )

    def load(self) -> None:
        """
        Load a previously persisted FAISS index.
        """
        index_path = (
            self.storage_path
            / self.INDEX_FILENAME
        )

        metadata_path = (
            self.storage_path
            / self.METADATA_FILENAME
        )

        if not index_path.exists():
            raise FileNotFoundError(
                f"Vector index not found: {index_path}"
            )

        if not metadata_path.exists():
            raise FileNotFoundError(
                f"Vector metadata not found: {metadata_path}"
            )

        metadata = json.loads(
            metadata_path.read_text(
                encoding="utf-8"
            )
        )

        if metadata.get("version") != self.VERSION:
            raise ValueError(
                "Unsupported vector index version"
            )

        if metadata.get("model_name") != self.model_name:
            raise ValueError(
                "Vector index was created with a "
                "different embedding model"
            )

        index = faiss.read_index(
            str(index_path)
        )

        dimension = metadata.get("dimension")

        vectors_metadata = metadata.get(
            "vectors",
            {},
        )

        if len(vectors_metadata) != index.ntotal:
            raise ValueError(
                "Vector metadata count does not match "
                "the FAISS index"
            )

        self._index = index
        self._dimension = int(dimension)
        self._metadata = {
            int(vector_id): entry
            for vector_id, entry in vectors_metadata.items()
        }

    def try_load(self) -> bool:
        """
        Load the persisted index if it exists; return whether a
        load happened. Convenience for service startup, where a
        first-ever run has no index on disk yet.
        """
        try:
            self.load()
            return True
        except FileNotFoundError:
            return False

    def search_chunks(
        self,
        query_vector: np.ndarray,
    ) -> list[VectorChunkResult]:
        """
        Search the persistent vector index at chunk level.
        """
        if not self.is_built:
            return []

        query = np.asarray(
            query_vector,
            dtype=np.float32,
        ).reshape(1, -1)

        if query.shape[1] != self._dimension:
            raise ValueError(
                "query vector dimension does not match "
                "the index dimension"
            )

        if not np.all(np.isfinite(query)):
            raise ValueError(
                "query vector contains non-finite values"
            )

        norm = np.linalg.norm(query)

        if norm == 0:
            raise ValueError(
                "query vector must not be a zero vector"
            )

        query = query / norm

        query = np.ascontiguousarray(
            query,
            dtype=np.float32,
        )

        scores, ids = self._index.search(
            query,
            self._index.ntotal,
        )

        results: list[VectorChunkResult] = []

        for score, vector_id in zip(
            scores[0],
            ids[0],
        ):
            if vector_id < 0:
                continue

            metadata = self._metadata[int(vector_id)]

            results.append(
                VectorChunkResult(
                    chunk_id=metadata["chunk_id"],
                    resume_id=metadata["resume_id"],
                    section=metadata["section"],
                    score=float(score),
                )
            )

        return results

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 10,
        min_score: float | None = None,
    ) -> list[VectorCandidateResult]:
        """
        Search vectors and aggregate results by resume.
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

        if top_k == 0 or not self.is_built:
            return []

        chunks = self.search_chunks(
            query_vector
        )

        if min_score is not None:
            chunks = [
                chunk
                for chunk in chunks
                if chunk.score >= min_score
            ]

        grouped: dict[
            str,
            list[VectorChunkResult],
        ] = {}

        for chunk in chunks:
            grouped.setdefault(
                chunk.resume_id,
                [],
            ).append(chunk)

        results: list[VectorCandidateResult] = []

        for resume_id, matched_chunks in grouped.items():
            scores = np.asarray(
                [
                    chunk.score
                    for chunk in matched_chunks
                ],
                dtype=np.float32,
            )

            if self.aggregation == "max":
                score = float(np.max(scores))
            elif self.aggregation == "sum":
                score = float(np.sum(scores))
            else:
                score = float(np.mean(scores))

            matched_chunks.sort(
                key=lambda result: (
                    -result.score,
                    result.chunk_id,
                )
            )

            results.append(
                VectorCandidateResult(
                    resume_id=resume_id,
                    score=score,
                    matched_chunks=tuple(
                        matched_chunks
                    ),
                )
            )

        results.sort(
            key=lambda result: (
                -result.score,
                result.resume_id,
            )
        )

        return results[:top_k]
