from datetime import date

import pytest

from app.core.schemas import (
    CanonicalExperience,
    CanonicalResume,
)
from app.retrieval.bm25 import (
    BM25Retriever,
    retrieve_candidates,
)
from app.retrieval.resume_chunker import ResumeChunker


def make_resume(
    resume_id: str,
    skills: list[str],
    job_title: str,
    company: str = "Company",
) -> CanonicalResume:
    return CanonicalResume(
        resume_id=resume_id,
        skills=skills,
        job_titles=[job_title],
        experiences=[
            CanonicalExperience(
                job_title=job_title,
                company=company,
                start_date=date(2022, 1, 1),
                end_date=date(2024, 1, 1),
                duration_months=24,
            )
        ],
    )


def make_chunks():
    resumes = [
        make_resume(
            "candidate-a",
            ["Python", "Machine Learning", "TensorFlow"],
            "ML Engineer",
        ),
        make_resume(
            "candidate-b",
            ["Java", "Spring", "Backend"],
            "Software Engineer",
        ),
        make_resume(
            "candidate-c",
            ["Python", "Data Analysis"],
            "Data Analyst",
        ),
    ]

    return ResumeChunker().chunk_many(resumes)


def test_tokenize_lowercases_text():
    retriever = BM25Retriever()

    assert retriever.tokenize(
        "Python, TensorFlow!"
    ) == [
        "python",
        "tensorflow",
    ]


def test_tokenize_empty_text():
    retriever = BM25Retriever()

    assert retriever.tokenize("") == []


def test_exact_relevant_candidate_ranks_first():
    chunks = make_chunks()

    results = BM25Retriever().retrieve(
        "Python Machine Learning TensorFlow",
        chunks,
        top_k=3,
    )

    assert results
    assert results[0].resume_id == "candidate-a"


def test_irrelevant_candidate_is_not_returned():
    chunks = make_chunks()

    results = BM25Retriever().retrieve(
        "Python Machine Learning",
        chunks,
        top_k=3,
    )

    ids = [result.resume_id for result in results]

    assert "candidate-b" not in ids


def test_candidate_scores_are_positive_for_matches():
    chunks = make_chunks()

    results = BM25Retriever().retrieve(
        "Python",
        chunks,
        top_k=3,
    )

    assert results
    assert all(result.score > 0 for result in results)


def test_top_k_limits_candidate_results():
    chunks = make_chunks()

    results = BM25Retriever().retrieve(
        "Python",
        chunks,
        top_k=1,
    )

    assert len(results) == 1


def test_top_k_zero_returns_empty():
    chunks = make_chunks()

    results = BM25Retriever().retrieve(
        "Python",
        chunks,
        top_k=0,
    )

    assert results == []


def test_empty_corpus_returns_empty():
    results = BM25Retriever().retrieve(
        "Python",
        [],
        top_k=10,
    )

    assert results == []


def test_empty_query_returns_zero_scores():
    chunks = make_chunks()

    results = BM25Retriever().score_documents(
        "",
        chunks,
    )

    assert len(results) == len(chunks)
    assert all(result.score == 0.0 for result in results)


def test_multiple_chunks_are_aggregated_by_candidate():
    resume = CanonicalResume(
        resume_id="candidate-a",
        skills=["Python"],
        technologies=["TensorFlow"],
        experiences=[
            CanonicalExperience(
                job_title="ML Engineer",
                company="ABC",
                start_date=date(2022, 1, 1),
                end_date=date(2024, 1, 1),
                duration_months=24,
            )
        ],
    )

    chunks = ResumeChunker().chunk(resume)

    results = BM25Retriever().retrieve(
        "Python TensorFlow",
        chunks,
        top_k=10,
    )

    assert len(results) == 1
    assert results[0].resume_id == "candidate-a"
    assert len(results[0].matched_chunks) >= 2


def test_matched_chunks_belong_to_candidate():
    chunks = make_chunks()

    results = BM25Retriever().retrieve(
        "Python",
        chunks,
        top_k=3,
    )

    for candidate in results:
        assert all(
            chunk.resume_id == candidate.resume_id
            for chunk in candidate.matched_chunks
        )


def test_scores_are_deterministic():
    chunks = make_chunks()

    retriever = BM25Retriever()

    first = retriever.retrieve(
        "Python Machine Learning",
        chunks,
        top_k=10,
    )

    second = retriever.retrieve(
        "Python Machine Learning",
        chunks,
        top_k=10,
    )

    assert first == second


def test_invalid_k1_is_rejected():
    with pytest.raises(ValueError):
        BM25Retriever(k1=-1)


def test_invalid_b_is_rejected():
    with pytest.raises(ValueError):
        BM25Retriever(b=1.5)


def test_convenience_function_matches_retriever():
    chunks = make_chunks()

    direct = BM25Retriever().retrieve(
        "Python",
        chunks,
        top_k=2,
    )

    convenience = retrieve_candidates(
        "Python",
        chunks,
        top_k=2,
    )

    assert direct == convenience