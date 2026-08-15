import pytest

from app.retrieval.bm25 import BM25CandidateResult
from app.retrieval.hybrid import (
    HybridRetriever,
    fuse_retrieval_results,
)
from app.retrieval.vector_retrieval import VectorCandidateResult


def bm25(
    resume_id: str,
    score: float,
) -> BM25CandidateResult:
    return BM25CandidateResult(
        resume_id=resume_id,
        score=score,
        matched_chunks=(),
    )


def dense(
    resume_id: str,
    score: float,
) -> VectorCandidateResult:
    return VectorCandidateResult(
        resume_id=resume_id,
        score=score,
        matched_chunks=(),
    )


def test_fusion_combines_candidates_from_both_paths():
    results = HybridRetriever().fuse(
        [
            bm25("candidate-a", 10.0),
            bm25("candidate-b", 5.0),
        ],
        [
            dense("candidate-a", 0.9),
            dense("candidate-c", 0.8),
        ],
    )

    ids = {
        result.resume_id
        for result in results
    }

    assert ids == {
        "candidate-a",
        "candidate-b",
        "candidate-c",
    }


def test_candidate_present_in_both_paths_gets_both_scores():
    results = HybridRetriever().fuse(
        [bm25("candidate-a", 10.0)],
        [dense("candidate-a", 0.9)],
    )

    assert len(results) == 1

    result = results[0]

    assert result.resume_id == "candidate-a"
    assert result.bm25_score == 10.0
    assert result.dense_score == 0.9


def test_bm25_scores_are_normalized():
    results = HybridRetriever().fuse(
        [
            bm25("candidate-a", 10.0),
            bm25("candidate-b", 5.0),
        ],
        [],
    )

    by_id = {
        result.resume_id: result
        for result in results
    }

    assert by_id["candidate-a"].normalized_bm25_score == 1.0
    assert by_id["candidate-b"].normalized_bm25_score == 0.0


def test_dense_scores_are_normalized():
    results = HybridRetriever().fuse(
        [],
        [
            dense("candidate-a", 0.9),
            dense("candidate-b", 0.3),
        ],
    )

    by_id = {
        result.resume_id: result
        for result in results
    }

    assert by_id["candidate-a"].normalized_dense_score == 1.0
    assert by_id["candidate-b"].normalized_dense_score == 0.0


def test_equal_positive_scores_receive_one():
    results = HybridRetriever().fuse(
        [
            bm25("candidate-a", 5.0),
            bm25("candidate-b", 5.0),
        ],
        [],
    )

    assert all(
        result.normalized_bm25_score == 1.0
        for result in results
    )


def test_equal_zero_scores_receive_zero():
    results = HybridRetriever().fuse(
        [
            bm25("candidate-a", 0.0),
            bm25("candidate-b", 0.0),
        ],
        [],
    )

    assert all(
        result.normalized_bm25_score == 0.0
        for result in results
    )


def test_bm25_weight_controls_fusion():
    results = HybridRetriever(
        bm25_weight=1.0,
    ).fuse(
        [
            bm25("candidate-a", 10.0),
            bm25("candidate-b", 5.0),
        ],
        [
            dense("candidate-a", 0.1),
            dense("candidate-b", 0.9),
        ],
    )

    assert results[0].resume_id == "candidate-a"


def test_dense_weight_controls_fusion():
    results = HybridRetriever(
        bm25_weight=0.0,
    ).fuse(
        [
            bm25("candidate-a", 10.0),
            bm25("candidate-b", 5.0),
        ],
        [
            dense("candidate-a", 0.1),
            dense("candidate-b", 0.9),
        ],
    )

    assert results[0].resume_id == "candidate-b"


def test_default_weight_is_equal():
    retriever = HybridRetriever()

    assert retriever.bm25_weight == 0.5
    assert retriever.dense_weight == 0.5


def test_invalid_bm25_weight_is_rejected():
    with pytest.raises(ValueError):
        HybridRetriever(
            bm25_weight=-0.1,
        )

    with pytest.raises(ValueError):
        HybridRetriever(
            bm25_weight=1.1,
        )


def test_invalid_dense_weight_is_rejected():
    with pytest.raises(ValueError):
        HybridRetriever(
            bm25_weight=0.5,
            dense_weight=1.1,
        )


def test_weights_must_sum_to_one():
    with pytest.raises(ValueError):
        HybridRetriever(
            bm25_weight=0.7,
            dense_weight=0.7,
        )


def test_empty_inputs_return_empty():
    assert HybridRetriever().fuse(
        [],
        [],
    ) == []


def test_top_k_limits_results():
    results = HybridRetriever().fuse(
        [
            bm25("candidate-a", 10.0),
            bm25("candidate-b", 8.0),
            bm25("candidate-c", 5.0),
        ],
        [],
        top_k=2,
    )

    assert len(results) == 2


def test_top_k_zero_returns_empty():
    assert HybridRetriever().fuse(
        [bm25("candidate-a", 10.0)],
        [],
        top_k=0,
    ) == []


def test_negative_top_k_is_rejected():
    with pytest.raises(ValueError):
        HybridRetriever().fuse(
            [],
            [],
            top_k=-1,
        )


def test_results_are_deterministic():
    bm25_results = [
        bm25("candidate-a", 10.0),
        bm25("candidate-b", 5.0),
    ]

    dense_results = [
        dense("candidate-a", 0.9),
        dense("candidate-b", 0.8),
    ]

    retriever = HybridRetriever()

    first = retriever.fuse(
        bm25_results,
        dense_results,
    )

    second = retriever.fuse(
        bm25_results,
        dense_results,
    )

    assert first == second


def test_convenience_function_matches_retriever():
    bm25_results = [
        bm25("candidate-a", 10.0),
        bm25("candidate-b", 5.0),
    ]

    dense_results = [
        dense("candidate-a", 0.9),
        dense("candidate-b", 0.8),
    ]

    direct = HybridRetriever().fuse(
        bm25_results,
        dense_results,
    )

    convenience = fuse_retrieval_results(
        bm25_results,
        dense_results,
    )

    assert direct == convenience


def test_hybrid_score_is_weighted_sum():
    result = HybridRetriever(
        bm25_weight=0.7,
    ).fuse(
        [
            bm25("candidate-a", 10.0),
            bm25("candidate-b", 5.0),
        ],
        [
            dense("candidate-a", 0.9),
            dense("candidate-b", 0.3),
        ],
    )[0]

    expected = (
        0.7 * result.normalized_bm25_score
        + 0.3 * result.normalized_dense_score
    )

    assert result.score == pytest.approx(
        expected
    )