import numpy as np
import pytest

from app.infrastructure.vector import (
    PersistentVectorIndex,
)
from app.retrieval.embeddings import ChunkEmbedding


def embedding(
    chunk_id,
    resume_id,
    vector,
    section="skills",
):
    return ChunkEmbedding(
        chunk_id=chunk_id,
        resume_id=resume_id,
        section=section,
        vector=np.asarray(
            vector,
            dtype=np.float32,
        ),
    )


def make_embeddings():
    return [
        embedding(
            "a-1",
            "candidate-a",
            [1.0, 0.0, 0.0],
        ),
        embedding(
            "a-2",
            "candidate-a",
            [0.9, 0.1, 0.0],
            section="experience",
        ),
        embedding(
            "b-1",
            "candidate-b",
            [0.0, 1.0, 0.0],
        ),
    ]


def test_build_index(tmp_path):
    index = PersistentVectorIndex(tmp_path)

    index.build(make_embeddings())

    assert index.is_built
    assert index.dimension == 3
    assert index.size == 3


def test_empty_index(tmp_path):
    index = PersistentVectorIndex(tmp_path)

    index.build([])

    assert not index.is_built
    assert index.size == 0
    assert index.dimension is None


def test_search_returns_best_candidate(tmp_path):
    index = PersistentVectorIndex(tmp_path)

    index.build(make_embeddings())

    results = index.search(
        np.array(
            [1.0, 0.0, 0.0],
            dtype=np.float32,
        ),
        top_k=2,
    )

    assert results[0].resume_id == "candidate-a"


def test_search_preserves_chunk_metadata(tmp_path):
    index = PersistentVectorIndex(tmp_path)

    index.build(make_embeddings())

    results = index.search_chunks(
        np.array(
            [1.0, 0.0, 0.0],
            dtype=np.float32,
        )
    )

    assert results[0].chunk_id == "a-1"
    assert results[0].resume_id == "candidate-a"
    assert results[0].section == "skills"


def test_save_and_load(tmp_path):
    original = PersistentVectorIndex(
        tmp_path,
        model_name="BAAI/bge-m3",
    )

    original.build(make_embeddings())
    original.save()

    loaded = PersistentVectorIndex(
        tmp_path,
        model_name="BAAI/bge-m3",
    )

    loaded.load()

    assert loaded.is_built
    assert loaded.dimension == 3
    assert loaded.size == 3

    query = np.array(
        [1.0, 0.0, 0.0],
        dtype=np.float32,
    )

    assert (
        loaded.search(query)
        == original.search(query)
    )


def test_missing_index_is_rejected(tmp_path):
    index = PersistentVectorIndex(tmp_path)

    with pytest.raises(FileNotFoundError):
        index.load()


def test_save_before_build_is_rejected(tmp_path):
    index = PersistentVectorIndex(tmp_path)

    with pytest.raises(ValueError):
        index.save()


def test_model_mismatch_is_rejected(tmp_path):
    index = PersistentVectorIndex(
        tmp_path,
        model_name="BAAI/bge-m3",
    )

    index.build(make_embeddings())
    index.save()

    different = PersistentVectorIndex(
        tmp_path,
        model_name="different-model",
    )

    with pytest.raises(ValueError):
        different.load()


def test_query_dimension_mismatch_is_rejected(tmp_path):
    index = PersistentVectorIndex(tmp_path)

    index.build(make_embeddings())

    with pytest.raises(ValueError):
        index.search(
            np.array(
                [1.0, 0.0],
                dtype=np.float32,
            )
        )


def test_top_k_zero_returns_empty(tmp_path):
    index = PersistentVectorIndex(tmp_path)

    index.build(make_embeddings())

    assert (
        index.search(
            np.array(
                [1.0, 0.0, 0.0],
                dtype=np.float32,
            ),
            top_k=0,
        )
        == []
    )


def test_min_score_filters_results(tmp_path):
    index = PersistentVectorIndex(tmp_path)

    index.build(make_embeddings())

    results = index.search(
        np.array(
            [1.0, 0.0, 0.0],
            dtype=np.float32,
        ),
        min_score=0.8,
    )

    assert results

    assert all(
        result.score >= 0.8
        for result in results
    )