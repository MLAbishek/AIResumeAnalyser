import pytest

from app.retrieval.deduplication import (
    CandidateDeduplicator,
    deduplicate_candidates,
)
from app.retrieval.hybrid import HybridCandidateResult


def hybrid(
    resume_id: str,
    score: float,
    bm25_score: float = 0.0,
    dense_score: float = 0.0,
    bm25_chunks=(),
    dense_chunks=(),
) -> HybridCandidateResult:
    return HybridCandidateResult(
        resume_id=resume_id,
        score=score,
        bm25_score=bm25_score,
        dense_score=dense_score,
        normalized_bm25_score=0.0,
        normalized_dense_score=0.0,
        bm25_chunks=tuple(bm25_chunks),
        dense_chunks=tuple(dense_chunks),
    )


def test_unique_candidates_are_preserved():
    results = [
        hybrid("candidate-a", 0.9),
        hybrid("candidate-b", 0.8),
        hybrid("candidate-c", 0.7),
    ]

    unique = CandidateDeduplicator().deduplicate(
        results
    )

    assert [
        candidate.resume_id
        for candidate in unique
    ] == [
        "candidate-a",
        "candidate-b",
        "candidate-c",
    ]


def test_duplicate_resume_ids_are_merged():
    results = [
        hybrid("candidate-a", 0.9),
        hybrid("candidate-a", 0.8),
        hybrid("candidate-b", 0.7),
    ]

    unique = CandidateDeduplicator().deduplicate(
        results
    )

    assert len(unique) == 2

    ids = [
        candidate.resume_id
        for candidate in unique
    ]

    assert ids == [
        "candidate-a",
        "candidate-b",
    ]


def test_strongest_score_is_retained():
    results = [
        hybrid("candidate-a", 0.7),
        hybrid("candidate-a", 0.95),
        hybrid("candidate-a", 0.8),
    ]

    unique = CandidateDeduplicator().deduplicate(
        results
    )

    assert len(unique) == 1
    assert unique[0].score == 0.95


def test_bm25_and_dense_scores_are_preserved():
    results = [
        hybrid(
            "candidate-a",
            0.9,
            bm25_score=12.0,
            dense_score=0.8,
        )
    ]

    unique = CandidateDeduplicator().deduplicate(
        results
    )

    candidate = unique[0]

    assert candidate.bm25_score == 12.0
    assert candidate.dense_score == 0.8
    assert candidate.hybrid_score == 0.9


def test_retrieval_sources_are_preserved():
    results = [
        hybrid(
            "candidate-a",
            0.9,
            bm25_score=10.0,
        ),
        hybrid(
            "candidate-a",
            0.8,
            dense_score=0.8,
        ),
    ]

    unique = CandidateDeduplicator().deduplicate(
        results
    )

    assert unique[0].sources == (
        "bm25",
        "dense",
    )


def test_bm25_only_candidate_has_bm25_source():
    results = [
        hybrid(
            "candidate-a",
            0.9,
            bm25_score=10.0,
        )
    ]

    unique = CandidateDeduplicator().deduplicate(
        results
    )

    assert unique[0].sources == ("bm25",)


def test_dense_only_candidate_has_dense_source():
    results = [
        hybrid(
            "candidate-a",
            0.9,
            dense_score=0.9,
        )
    ]

    unique = CandidateDeduplicator().deduplicate(
        results
    )

    assert unique[0].sources == ("dense",)


def test_both_paths_are_merged_into_one_candidate():
    results = [
        hybrid(
            "candidate-a",
            0.9,
            bm25_score=10.0,
        ),
        hybrid(
            "candidate-a",
            0.95,
            dense_score=0.95,
        ),
    ]

    unique = CandidateDeduplicator().deduplicate(
        results
    )

    assert len(unique) == 1
    assert unique[0].resume_id == "candidate-a"
    assert unique[0].score == 0.95


def test_evidence_chunks_are_merged():
    results = [
        hybrid(
            "candidate-a",
            0.9,
            bm25_score=10.0,
            bm25_chunks=("bm25-chunk",),
        ),
        hybrid(
            "candidate-a",
            0.8,
            dense_score=0.8,
            dense_chunks=("dense-chunk",),
        ),
    ]

    unique = CandidateDeduplicator().deduplicate(
        results
    )

    assert unique[0].bm25_chunks == (
        "bm25-chunk",
    )

    assert unique[0].dense_chunks == (
        "dense-chunk",
    )


def test_results_are_sorted_by_score():
    results = [
        hybrid("candidate-a", 0.5),
        hybrid("candidate-b", 0.9),
        hybrid("candidate-c", 0.7),
    ]

    unique = CandidateDeduplicator().deduplicate(
        results
    )

    assert [
        candidate.resume_id
        for candidate in unique
    ] == [
        "candidate-b",
        "candidate-c",
        "candidate-a",
    ]


def test_ties_are_deterministic():
    results = [
        hybrid("candidate-b", 0.8),
        hybrid("candidate-a", 0.8),
    ]

    unique = CandidateDeduplicator().deduplicate(
        results
    )

    assert [
        candidate.resume_id
        for candidate in unique
    ] == [
        "candidate-a",
        "candidate-b",
    ]


def test_empty_results_return_empty():
    assert (
        CandidateDeduplicator().deduplicate([])
        == []
    )


def test_top_k_limits_unique_candidates():
    results = [
        hybrid("candidate-a", 0.9),
        hybrid("candidate-b", 0.8),
        hybrid("candidate-c", 0.7),
    ]

    unique = CandidateDeduplicator().deduplicate(
        results,
        top_k=2,
    )

    assert len(unique) == 2


def test_top_k_zero_returns_empty():
    results = [
        hybrid("candidate-a", 0.9),
    ]

    assert (
        CandidateDeduplicator().deduplicate(
            results,
            top_k=0,
        )
        == []
    )


def test_negative_top_k_is_rejected():
    with pytest.raises(ValueError):
        CandidateDeduplicator().deduplicate(
            [],
            top_k=-1,
        )


def test_deduplicate_many_merges_result_sets():
    first = [
        hybrid("candidate-a", 0.9),
        hybrid("candidate-b", 0.8),
    ]

    second = [
        hybrid("candidate-a", 0.95),
        hybrid("candidate-c", 0.7),
    ]

    unique = CandidateDeduplicator().deduplicate_many(
        [first, second]
    )

    assert len(unique) == 3

    assert [
        candidate.resume_id
        for candidate in unique
    ] == [
        "candidate-a",
        "candidate-b",
        "candidate-c",
    ]

    assert unique[0].score == 0.95


def test_convenience_function_matches_class():
    results = [
        hybrid("candidate-a", 0.9),
        hybrid("candidate-b", 0.8),
    ]

    direct = CandidateDeduplicator().deduplicate(
        results
    )

    convenience = deduplicate_candidates(
        results
    )

    assert direct == convenience