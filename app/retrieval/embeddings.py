"""
Dense semantic embedding generation for resume retrieval.

Uses Sentence Transformers to convert job-description text and
resume chunks into fixed-size dense vectors.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np

from app.retrieval.jd_chunker import JDChunk
from app.retrieval.resume_chunker import ResumeChunk


DEFAULT_MODEL_NAME = "BAAI/bge-m3"
DEFAULT_EMBEDDING_DIMENSION = 1024


@dataclass(frozen=True)
class ChunkEmbedding:
    """
    Embedding associated with one resume chunk.
    """

    chunk_id: str
    resume_id: str
    section: str
    vector: np.ndarray


@dataclass(frozen=True)
class JDChunkEmbedding:
    """
    Embedding associated with one job-description chunk. Mirrors
    ChunkEmbedding for the JD side (job_id instead of resume_id).
    """

    chunk_id: str
    job_id: str
    section: str
    vector: np.ndarray


class EmbeddingGenerator:
    """
    Generate dense semantic embeddings.

    The SentenceTransformer model is loaded lazily so importing this
    module does not immediately download a model.

    A model can also be injected for testing.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        model: Any | None = None,
        batch_size: int = 32,
        normalize_embeddings: bool = True,
    ) -> None:
        if not model_name.strip():
            raise ValueError("model_name must not be empty")

        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero")

        self.model_name = model_name
        self._model = model
        self.batch_size = batch_size
        self.normalize_embeddings = normalize_embeddings

    @property
    def model(self) -> Any:
        """
        Lazily load the configured Sentence Transformer model.
        """
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RuntimeError(
                    "sentence-transformers is required for embedding "
                    "generation. Install it with "
                    "`python -m pip install sentence-transformers`."
                ) from exc

            self._model = SentenceTransformer(self.model_name)

        return self._model

    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate one dense embedding for a text string.
        """
        if not isinstance(text, str):
            raise TypeError("text must be a string")

        if not text.strip():
            raise ValueError("text must not be empty")

        embeddings = self._encode([text])

        return embeddings[0]

    def embed_texts(
        self,
        texts: Sequence[str],
    ) -> np.ndarray:
        """
        Generate embeddings for multiple texts.

        Returns:
            Float32 NumPy array with shape:
            (number_of_texts, embedding_dimension)
        """
        if not texts:
            return np.empty((0, 0), dtype=np.float32)

        if any(
            not isinstance(text, str)
            for text in texts
        ):
            raise TypeError("all texts must be strings")

        if any(
            not text.strip()
            for text in texts
        ):
            raise ValueError("texts must not contain empty strings")

        return self._encode(texts)

    def embed_query(self, query: str) -> np.ndarray:
        """
        Generate an embedding specifically for a retrieval query.

        If the underlying model supports encode_query(), use it.
        Otherwise fall back to encode().
        """
        if not isinstance(query, str):
            raise TypeError("query must be a string")

        if not query.strip():
            raise ValueError("query must not be empty")

        model = self.model

        if hasattr(model, "encode_query"):
            embeddings = model.encode_query(
                [query],
                batch_size=self.batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=self.normalize_embeddings,
            )

            return self._validate_embeddings(
                np.asarray(embeddings)
            )[0]

        return self.embed_text(query)

    def embed_chunks(
        self,
        chunks: Sequence[ResumeChunk],
    ) -> list[ChunkEmbedding]:
        """
        Generate embeddings for resume chunks while preserving provenance.
        """
        if not chunks:
            return []

        vectors = self.embed_texts(
            [chunk.text for chunk in chunks]
        )

        return [
            ChunkEmbedding(
                chunk_id=chunk.chunk_id,
                resume_id=chunk.resume_id,
                section=chunk.section,
                vector=vector,
            )
            for chunk, vector in zip(chunks, vectors)
        ]

    def embed_jd_chunks(
        self,
        chunks: Sequence[JDChunk],
    ) -> list[JDChunkEmbedding]:
        """
        Generate embeddings for JD chunks while preserving provenance.
        Mirrors embed_chunks() for the JD side.
        """
        if not chunks:
            return []

        vectors = self.embed_texts(
            [chunk.text for chunk in chunks]
        )

        return [
            JDChunkEmbedding(
                chunk_id=chunk.chunk_id,
                job_id=chunk.job_id,
                section=chunk.section,
                vector=vector,
            )
            for chunk, vector in zip(chunks, vectors)
        ]

    def embedding_dimension(self) -> int:
        """
        Return the dimensionality of the configured embedding model.
        """
        model = self.model

        if hasattr(model, "get_embedding_dimension"):
            dimension = model.get_embedding_dimension()

            if dimension is not None:
                return int(dimension)

        if hasattr(model, "get_sentence_embedding_dimension"):
            dimension = model.get_sentence_embedding_dimension()

            if dimension is not None:
                return int(dimension)

        # Fall back to a one-text encoding for custom model implementations.
        vector = self.embed_text("dimension probe")
        return int(vector.shape[0])

    def _encode(
        self,
        texts: Sequence[str],
    ) -> np.ndarray:
        model = self.model

        embeddings = model.encode(
            list(texts),
            batch_size=self.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=self.normalize_embeddings,
        )

        return self._validate_embeddings(
            np.asarray(embeddings)
        )

    @staticmethod
    def _validate_embeddings(
        embeddings: np.ndarray,
    ) -> np.ndarray:
        """
        Validate and standardize an embedding matrix.
        """
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)

        if embeddings.ndim != 2:
            raise ValueError(
                "embeddings must be a 2-dimensional array"
            )

        if embeddings.shape[1] == 0:
            raise ValueError(
                "embedding dimension must be greater than zero"
            )

        if not np.issubdtype(
            embeddings.dtype,
            np.number,
        ):
            raise TypeError(
                "embeddings must contain numeric values"
            )

        embeddings = embeddings.astype(
            np.float32,
            copy=False,
        )

        if not np.all(np.isfinite(embeddings)):
            raise ValueError(
                "embeddings must contain only finite values"
            )

        return embeddings