import numpy as np
import pytest

from app.retrieval.embeddings import (
    DEFAULT_MODEL_NAME,
    EmbeddingGenerator,
)
from app.retrieval.resume_chunker import ResumeChunk


class FakeEmbeddingModel:
    """
    Small deterministic fake model for unit testing.

    This avoids downloading/loading a transformer model during tests.
    """

    def __init__(self, dimension: int = 4):
        self.dimension = dimension

    def encode(
        self,
        texts,
        batch_size=32,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ):
        vectors = []

        for text in texts:
            value = float(len(text))

            vector = np.array(
                [
                    value,
                    value + 1,
                    value + 2,
                    value + 3,
                ],
                dtype=np.float32,
            )

            if normalize_embeddings:
                vector = vector / np.linalg.norm(vector)

            vectors.append(vector)

        return np.vstack(vectors)

    def encode_query(
        self,
        texts,
        batch_size=32,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ):
        return self.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress_bar,
            convert_to_numpy=convert_to_numpy,
            normalize_embeddings=normalize_embeddings,
        )

    def get_sentence_embedding_dimension(self):
        return self.dimension


def make_chunk(
    chunk_id="chunk-1",
    resume_id="resume-1",
):
    return ResumeChunk(
        chunk_id=chunk_id,
        resume_id=resume_id,
        section="skills",
        text="Python machine learning",
        position=0,
        metadata={},
    )


def test_default_model_name_is_defined():
    assert DEFAULT_MODEL_NAME == (
        "sentence-transformers/all-MiniLM-L6-v2"
    )


def test_embed_text_returns_one_vector():
    generator = EmbeddingGenerator(
        model=FakeEmbeddingModel()
    )

    vector = generator.embed_text(
        "Python machine learning"
    )

    assert isinstance(vector, np.ndarray)
    assert vector.shape == (4,)
    assert vector.dtype == np.float32


def test_embed_texts_returns_matrix():
    generator = EmbeddingGenerator(
        model=FakeEmbeddingModel()
    )

    vectors = generator.embed_texts(
        [
            "Python",
            "Machine Learning",
            "TensorFlow",
        ]
    )

    assert vectors.shape == (3, 4)
    assert vectors.dtype == np.float32


def test_embeddings_are_normalized_by_default():
    generator = EmbeddingGenerator(
        model=FakeEmbeddingModel()
    )

    vector = generator.embed_text("Python")

    assert np.isclose(
        np.linalg.norm(vector),
        1.0,
        atol=1e-6,
    )


def test_embed_query_returns_vector():
    generator = EmbeddingGenerator(
        model=FakeEmbeddingModel()
    )

    vector = generator.embed_query(
        "machine learning engineer"
    )

    assert vector.shape == (4,)


def test_embed_chunks_preserves_metadata():
    chunks = [
        make_chunk(
            chunk_id="chunk-1",
            resume_id="resume-1",
        ),
        make_chunk(
            chunk_id="chunk-2",
            resume_id="resume-2",
        ),
    ]

    generator = EmbeddingGenerator(
        model=FakeEmbeddingModel()
    )

    results = generator.embed_chunks(chunks)

    assert len(results) == 2

    assert results[0].chunk_id == "chunk-1"
    assert results[0].resume_id == "resume-1"
    assert results[0].section == "skills"

    assert results[1].chunk_id == "chunk-2"
    assert results[1].resume_id == "resume-2"


def test_empty_text_is_rejected():
    generator = EmbeddingGenerator(
        model=FakeEmbeddingModel()
    )

    with pytest.raises(ValueError):
        generator.embed_text("")


def test_empty_texts_return_empty_matrix():
    generator = EmbeddingGenerator(
        model=FakeEmbeddingModel()
    )

    result = generator.embed_texts([])

    assert result.shape == (0, 0)


def test_empty_chunk_list_returns_empty_result():
    generator = EmbeddingGenerator(
        model=FakeEmbeddingModel()
    )

    assert generator.embed_chunks([]) == []


def test_invalid_batch_size_is_rejected():
    with pytest.raises(ValueError):
        EmbeddingGenerator(
            model=FakeEmbeddingModel(),
            batch_size=0,
        )


def test_embedding_dimension():
    generator = EmbeddingGenerator(
        model=FakeEmbeddingModel()
    )

    assert generator.embedding_dimension() == 4


def test_model_is_loaded_lazily():
    generator = EmbeddingGenerator(
        model=FakeEmbeddingModel()
    )

    assert generator._model is not None


def test_non_string_text_is_rejected():
    generator = EmbeddingGenerator(
        model=FakeEmbeddingModel()
    )

    with pytest.raises(TypeError):
        generator.embed_text(None)


def test_non_finite_embeddings_are_rejected():
    class InvalidModel:
        def encode(self, *args, **kwargs):
            return np.array(
                [[np.nan, 1.0, 2.0, 3.0]],
                dtype=np.float32,
            )

    generator = EmbeddingGenerator(
        model=InvalidModel()
    )

    with pytest.raises(ValueError):
        generator.embed_text("Python")