from datetime import date

import numpy as np

from app.core.schemas import (
    CanonicalExperience,
    CanonicalResume,
)
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.deduplication import CandidateDeduplicator
from app.retrieval.embeddings import EmbeddingGenerator
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.resume_chunker import ResumeChunker
from app.retrieval.vector_retrieval import VectorRetriever


def make_resume(
    resume_id: str,
    skills: list[str],
    job_title: str,
    technologies: list[str],
) -> CanonicalResume:
    return CanonicalResume(
        resume_id=resume_id,
        skills=skills,
        job_titles=[job_title],
        technologies=technologies,
        experiences=[
            CanonicalExperience(
                job_title=job_title,
                company="Test Company",
                start_date=date(2022, 1, 1),
                end_date=date(2024, 1, 1),
                duration_months=24,
            )
        ],
    )


def test_end_to_end_retrieval_with_bge_m3_and_faiss():
    resumes = [
        make_resume(
            resume_id="candidate-a",
            skills=[
                "Python",
                "Machine Learning",
                "TensorFlow",
            ],
            job_title="ML Engineer",
            technologies=[
                "Python",
                "TensorFlow",
            ],
        ),
        make_resume(
            resume_id="candidate-b",
            skills=[
                "Java",
                "Spring",
                "Backend",
            ],
            job_title="Software Engineer",
            technologies=[
                "Java",
                "Spring",
            ],
        ),
        make_resume(
            resume_id="candidate-c",
            skills=[
                "Python",
                "Data Analysis",
            ],
            job_title="Data Analyst",
            technologies=[
                "Python",
                "Pandas",
            ],
        ),
    ]

    jd = (
        "Python machine learning engineer "
        "with TensorFlow experience"
    )

    # ---------------------------------------------------------
    # 1. Chunk resumes
    # ---------------------------------------------------------
    chunks = ResumeChunker().chunk_many(resumes)

    assert chunks

    # ---------------------------------------------------------
    # 2. Generate BGE-M3 embeddings
    # ---------------------------------------------------------
    generator = EmbeddingGenerator()

    embeddings = generator.embed_chunks(chunks)

    assert len(embeddings) == len(chunks)

    dimension = generator.embedding_dimension()

    assert dimension == 1024

    # ---------------------------------------------------------
    # 3. Generate JD embedding
    # ---------------------------------------------------------
    query_vector = generator.embed_query(jd)

    assert query_vector.shape == (1024,)
    assert np.isclose(
        np.linalg.norm(query_vector),
        1.0,
        atol=1e-5,
    )

    # ---------------------------------------------------------
    # 4. Dense / FAISS retrieval
    # ---------------------------------------------------------
    vector_retriever = VectorRetriever()

    dense_results = vector_retriever.retrieve(
        query_vector=query_vector,
        embeddings=embeddings,
        top_k=3,
    )

    assert dense_results
    assert dense_results[0].resume_id == "candidate-a"

    # ---------------------------------------------------------
    # 5. BM25 retrieval
    # ---------------------------------------------------------
    bm25_results = BM25Retriever().retrieve(
        query=jd,
        chunks=chunks,
        top_k=3,
    )

    assert bm25_results
    assert bm25_results[0].resume_id == "candidate-a"

    # ---------------------------------------------------------
    # 6. Hybrid fusion
    # ---------------------------------------------------------
    hybrid_results = HybridRetriever(
        bm25_weight=0.5,
    ).fuse(
        bm25_results=bm25_results,
        dense_results=dense_results,
        top_k=3,
    )

    assert hybrid_results
    assert hybrid_results[0].resume_id == "candidate-a"

    # ---------------------------------------------------------
    # 7. Candidate deduplication
    # ---------------------------------------------------------
    unique_candidates = CandidateDeduplicator().deduplicate(
        hybrid_results,
        top_k=3,
    )

    assert unique_candidates
    assert unique_candidates[0].resume_id == "candidate-a"

    # Every candidate must occur exactly once.
    resume_ids = [
        candidate.resume_id
        for candidate in unique_candidates
    ]

    assert len(resume_ids) == len(set(resume_ids))

    # Candidate A must contain both retrieval signals.
    candidate_a = unique_candidates[0]

    assert "bm25" in candidate_a.sources
    assert "dense" in candidate_a.sources
    assert candidate_a.bm25_score > 0.0
    assert candidate_a.dense_score > 0.0