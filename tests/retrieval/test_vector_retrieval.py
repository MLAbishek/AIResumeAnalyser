import numpy as np
import pytest

from app.retrieval.embeddings import ChunkEmbedding
from app.retrieval.vector_retrieval import (
    VectorRetriever,
    retrieve_vectors,
)


def make_embedding(
    chunk_id: str,
    resume_id: str,
    vector: list[float],
    section: str = "skills",
) -> ChunkEmbedding:
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
        make_embedding(
            "a-1",
            "candidate-a",
            [1.0, 0.0, 0.0],
        ),
        make_embedding(
            "a-2",
            "candidate-a",
            [0.9, 0.1, 0.0],
            section="experience",
        ),
        make_embedding(
            "b-1",
            "candidate-b",
            [0.0, 1.0, 0.0],
        ),
        make_embedding(
            "c-1",
            "candidate-c",
            [0.0, 0.0, 1.0],
        ),
    ]


def test_identical_vectors_have_similarity_one():
    vector = np.array(
        [1.0, 2.0, 3.0],
        dtype=np.float32,
    )

    score = VectorRetriever.cosine_similarity(
        vector,
        vector,
    )

    assert np.isclose(score, 1.0)


def test_orthogonal_vectors_have_similarity_zero():
    first = np.array(
        [1.0, 0.0],
        dtype=np.float32,
    )

    second = np.array(
        [0.0, 1.0],
        dtype=np.float32,
    )

    score = VectorRetriever.cosine_similarity(
        first,
        second,
    )

    assert np.isclose(score, 0.0)


def test_opposite_vectors_have_similarity_negative_one():
    first = np.array(
        [1.0, 0.0],
        dtype=np.float32,
    )

    second = np.array(
        [-1.0, 0.0],
        dtype=np.float32,
    )

    score = VectorRetriever.cosine_similarity(
        first,
        second,
    )

    assert np.isclose(score, -1.0)


def test_zero_vector_returns_zero():
    first = np.array(
        [0.0, 0.0],
        dtype=np.float32,
    )

    second = np.array(
        [1.0, 0.0],
        dtype=np.float32,
    )

    score = VectorRetriever.cosine_similarity(
        first,
        second,
    )

    assert score == 0.0


def test_dimension_mismatch_is_rejected():
    with pytest.raises(ValueError):
        VectorRetriever.cosine_similarity(
            np.array([1.0, 0.0]),
            np.array([1.0, 0.0, 0.0]),
        )


def test_empty_vector_is_rejected():
    with pytest.raises(ValueError):
        VectorRetriever.cosine_similarity(
            np.array([]),
            np.array([]),
        )


def test_build_index_creates_faiss_index():
    embeddings = make_embeddings()

    retriever = VectorRetriever()

    retriever.build_index(
        embeddings
    )

    assert retriever.is_built
    assert retriever.dimension == 3


def test_empty_embeddings_create_empty_index():
    retriever = VectorRetriever()

    retriever.build_index([])

    assert not retriever.is_built
    assert retriever.dimension is None


def test_score_chunks_ranks_similar_chunks_first():
    embeddings = make_embeddings()

    retriever = VectorRetriever()

    retriever.build_index(
        embeddings
    )

    query = np.array(
        [1.0, 0.0, 0.0],
        dtype=np.float32,
    )

    results = retriever.score_chunks(
        query,
    )

    assert results[0].chunk_id == "a-1"
    assert results[0].score > results[-1].score


def test_retrieve_returns_most_similar_candidate():
    embeddings = make_embeddings()

    retriever = VectorRetriever()

    retriever.build_index(
        embeddings
    )

    query = np.array(
        [1.0, 0.0, 0.0],
        dtype=np.float32,
    )

    results = retriever.retrieve(
        query,
        top_k=3,
    )

    assert results[0].resume_id == "candidate-a"


def test_retrieve_can_build_index_for_compatibility():
    embeddings = make_embeddings()

    query = np.array(
        [1.0, 0.0, 0.0],
        dtype=np.float32,
    )

    results = VectorRetriever().retrieve(
        query,
        embeddings,
        top_k=3,
    )

    assert results
    assert results[0].resume_id == "candidate-a"


def test_top_k_limits_results():
    embeddings = make_embeddings()

    retriever = VectorRetriever()

    retriever.build_index(
        embeddings
    )

    query = np.array(
        [1.0, 0.0, 0.0],
        dtype=np.float32,
    )

    results = retriever.retrieve(
        query,
        top_k=1,
    )

    assert len(results) == 1


def test_top_k_zero_returns_empty():
    embeddings = make_embeddings()

    retriever = VectorRetriever()

    retriever.build_index(
        embeddings
    )

    query = np.array(
        [1.0, 0.0, 0.0],
        dtype=np.float32,
    )

    assert (
        retriever.retrieve(
            query,
            top_k=0,
        )
        == []
    )


def test_empty_index_returns_empty():
    query = np.array(
        [1.0, 0.0, 0.0],
        dtype=np.float32,
    )

    assert (
        VectorRetriever().retrieve(
            query,
            top_k=10,
        )
        == []
    )


def test_candidate_max_aggregation():
    embeddings = make_embeddings()

    retriever = VectorRetriever(
        aggregation="max"
    )

    retriever.build_index(
        embeddings
    )

    query = np.array(
        [1.0, 0.0, 0.0],
        dtype=np.float32,
    )

    results = retriever.retrieve(
        query,
        top_k=3,
    )

    candidate_a = next(
        result
        for result in results
        if result.resume_id == "candidate-a"
    )

    assert np.isclose(
        candidate_a.score,
        1.0,
    )


def test_candidate_sum_aggregation():
    embeddings = make_embeddings()

    retriever = VectorRetriever(
        aggregation="sum"
    )

    retriever.build_index(
        embeddings
    )

    query = np.array(
        [1.0, 0.0, 0.0],
        dtype=np.float32,
    )

    results = retriever.retrieve(
        query,
        top_k=3,
    )

    candidate_a = next(
        result
        for result in results
        if result.resume_id == "candidate-a"
    )

    assert candidate_a.score > 1.0


def test_candidate_mean_aggregation():
    embeddings = make_embeddings()

    retriever = VectorRetriever(
        aggregation="mean"
    )

    retriever.build_index(
        embeddings
    )

    query = np.array(
        [1.0, 0.0, 0.0],
        dtype=np.float32,
    )

    results = retriever.retrieve(
        query,
        top_k=3,
    )

    candidate_a = next(
        result
        for result in results
        if result.resume_id == "candidate-a"
    )

    assert 0.0 < candidate_a.score <= 1.0


def test_invalid_aggregation_is_rejected():
    with pytest.raises(ValueError):
        VectorRetriever(
            aggregation="invalid"
        )


def test_invalid_top_k_is_rejected():
    embeddings = make_embeddings()

    retriever = VectorRetriever()

    retriever.build_index(
        embeddings
    )

    with pytest.raises(ValueError):
        retriever.retrieve(
            np.array([1.0, 0.0, 0.0]),
            top_k=-1,
        )


def test_invalid_min_score_is_rejected():
    embeddings = make_embeddings()

    retriever = VectorRetriever()

    retriever.build_index(
        embeddings
    )

    with pytest.raises(ValueError):
        retriever.retrieve(
            np.array([1.0, 0.0, 0.0]),
            min_score=2.0,
        )


def test_min_score_filters_chunks():
    embeddings = make_embeddings()

    retriever = VectorRetriever()

    retriever.build_index(
        embeddings
    )

    query = np.array(
        [1.0, 0.0, 0.0],
        dtype=np.float32,
    )

    results = retriever.retrieve(
        query,
        top_k=10,
        min_score=0.8,
    )

    assert results

    for candidate in results:
        assert candidate.score >= 0.8


def test_matched_chunks_belong_to_candidate():
    embeddings = make_embeddings()

    retriever = VectorRetriever()

    retriever.build_index(
        embeddings
    )

    query = np.array(
        [1.0, 0.0, 0.0],
        dtype=np.float32,
    )

    results = retriever.retrieve(
        query,
        top_k=10,
    )

    for candidate in results:
        assert all(
            chunk.resume_id == candidate.resume_id
            for chunk in candidate.matched_chunks
        )


def test_results_are_deterministic():
    embeddings = make_embeddings()

    query = np.array(
        [1.0, 0.0, 0.0],
        dtype=np.float32,
    )

    retriever = VectorRetriever()

    retriever.build_index(
        embeddings
    )

    first = retriever.retrieve(
        query,
        top_k=10,
    )

    second = retriever.retrieve(
        query,
        top_k=10,
    )

    assert first == second


def test_convenience_function_matches_retriever():
    embeddings = make_embeddings()

    query = np.array(
        [1.0, 0.0, 0.0],
        dtype=np.float32,
    )

    direct = VectorRetriever().retrieve(
        query,
        embeddings,
        top_k=2,
    )

    convenience = retrieve_vectors(
        query,
        embeddings,
        top_k=2,
    )

    assert direct == convenience