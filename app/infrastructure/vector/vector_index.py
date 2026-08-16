from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

import faiss
import numpy as np

from app.retrieval.embeddings import ChunkEmbedding
from app.retrieval.vector_retrieval import (
    VectorCandidateResult,
    VectorChunkResult,
)


class PersistentVectorIndex:
    """
    Persistent FAISS-backed vector index.

    Stores:
        - FAISS vector index
        - chunk metadata
        - embedding dimension
        - model identifier

    The actual embedding model is intentionally not persisted.
    """

    INDEX_FILENAME = "index.faiss"
    METADATA_FILENAME = "metadata.json"

    VERSION = 1

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
        self._metadata: list[dict] = []
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
        Build the FAISS index from chunk embeddings.
        """
        if not embeddings:
            self._index = None
            self._metadata = []
            self._dimension = None
            return

        vectors = np.asarray(
            [embedding.vector for embedding in embeddings],
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

        norms = np.linalg.norm(
            vectors,
            axis=1,
            keepdims=True,
        )

        if np.any(norms == 0):
            raise ValueError(
                "embeddings must not contain zero vectors"
            )

        vectors = vectors / norms
        vectors = np.ascontiguousarray(
            vectors,
            dtype=np.float32,
        )

        dimension = vectors.shape[1]

        index = faiss.IndexFlatIP(dimension)
        index.add(vectors)

        self._index = index
        self._dimension = dimension

        self._metadata = [
            {
                "chunk_id": embedding.chunk_id,
                "resume_id": embedding.resume_id,
                "section": embedding.section,
            }
            for embedding in embeddings
        ]

    def save(self) -> None:
        """
        Persist the FAISS index and metadata.
        """
        if not self.is_built:
            raise ValueError(
                "cannot save an index that has not been built"
            )

        self.storage_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        index_path = (
            self.storage_path
            / self.INDEX_FILENAME
        )

        metadata_path = (
            self.storage_path
            / self.METADATA_FILENAME
        )

        faiss.write_index(
            self._index,
            str(index_path),
        )

        metadata = {
            "version": self.VERSION,
            "model_name": self.model_name,
            "dimension": self._dimension,
            "aggregation": self.aggregation,
            "vectors": self._metadata,
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

        if dimension != index.d:
            raise ValueError(
                "Vector index dimension does not match metadata"
            )

        vectors_metadata = metadata.get(
            "vectors",
            [],
        )

        if len(vectors_metadata) != index.ntotal:
            raise ValueError(
                "Vector metadata count does not match "
                "the FAISS index"
            )

        self._index = index
        self._dimension = int(dimension)
        self._metadata = vectors_metadata

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

        scores, indices = self._index.search(
            query,
            self._index.ntotal,
        )

        results: list[VectorChunkResult] = []

        for score, index_position in zip(
            scores[0],
            indices[0],
        ):
            if index_position < 0:
                continue

            metadata = self._metadata[index_position]

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