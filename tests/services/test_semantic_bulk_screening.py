"""
Targeted tests for the bulk-screening-via-semantic-retrieval
orchestration: job_id -> (mocked) FAISS retrieval -> unique
resume_ids -> real DB lookup -> real deterministic
BulkScreeningService. The retrieval step is mocked (controlled
resume_id list) so these don't need real embeddings; everything
downstream of retrieval is real.
"""

from unittest.mock import MagicMock

import pytest

from app.database.crud.jobs import create_job
from app.database.crud.resumes import create_resume
from app.services.bulk_semantic_retrieval_service import (
    BulkCandidateSemanticResult,
)
from app.services.semantic_bulk_screening import (
    screen_job_via_semantic_retrieval,
)


@pytest.fixture
def job_and_resumes(db):
    job = create_job(
        db,
        job_id="semantic-bulk-job-1",
        title="Python Developer",
        raw_text="Python developer role.",
        required_skills=["Python"],
    )

    matching = create_resume(
        db,
        resume_id="semantic-bulk-resume-match",
        name="Matching Candidate",
        skills=["Python"],
        raw_text="Python developer.",
    )

    non_matching = create_resume(
        db,
        resume_id="semantic-bulk-resume-nonmatch",
        name="Non-Matching Candidate",
        skills=["Cobol"],
        raw_text="Cobol developer.",
    )

    db.commit()

    return job, matching, non_matching


def _mock_retrieval(resume_ids):
    service = MagicMock()
    service.retrieve.return_value = [
        BulkCandidateSemanticResult(
            resume_id=resume_id,
            score=0.9 - i * 0.1,
            matched_jd_chunk_count=1,
            total_jd_chunk_count=1,
        )
        for i, resume_id in enumerate(resume_ids)
    ]
    return service


class TestOrchestration:
    def test_retrieved_resumes_are_screened_deterministically(
        self, db, job_and_resumes
    ):
        job, matching, non_matching = job_and_resumes

        retrieval = _mock_retrieval(
            ["semantic-bulk-resume-match"]
        )

        result = screen_job_via_semantic_retrieval(
            db,
            job_id="semantic-bulk-job-1",
            top_k=10,
            retrieval_service=retrieval,
        )

        assert result["total_candidates"] == 1
        assert result["results"][0]["resume_id"] == (
            "semantic-bulk-resume-match"
        )
        assert result["results"][0]["eligible"] is True

    def test_semantic_retrieval_metadata_is_attached(
        self, db, job_and_resumes
    ):
        job, matching, non_matching = job_and_resumes

        retrieval = _mock_retrieval(
            [
                "semantic-bulk-resume-match",
                "semantic-bulk-resume-nonmatch",
            ]
        )

        result = screen_job_via_semantic_retrieval(
            db,
            job_id="semantic-bulk-job-1",
            top_k=10,
            retrieval_service=retrieval,
        )

        assert result["semantic_retrieval"][
            "candidates_considered"
        ] == 2
        assert set(
            result["semantic_retrieval"]["resume_ids"]
        ) == {
            "semantic-bulk-resume-match",
            "semantic-bulk-resume-nonmatch",
        }

    def test_duplicate_resume_ids_from_retrieval_are_deduplicated(
        self, db, job_and_resumes
    ):
        job, matching, non_matching = job_and_resumes

        retrieval = MagicMock()
        retrieval.retrieve.return_value = [
            BulkCandidateSemanticResult(
                resume_id="semantic-bulk-resume-match",
                score=0.9,
                matched_jd_chunk_count=1,
                total_jd_chunk_count=2,
            ),
            BulkCandidateSemanticResult(
                resume_id="semantic-bulk-resume-match",
                score=0.85,
                matched_jd_chunk_count=1,
                total_jd_chunk_count=2,
            ),
        ]

        result = screen_job_via_semantic_retrieval(
            db,
            job_id="semantic-bulk-job-1",
            top_k=10,
            retrieval_service=retrieval,
        )

        assert result["total_candidates"] == 1

    def test_unknown_job_id_raises(self, db):
        retrieval = _mock_retrieval([])

        with pytest.raises(ValueError):
            screen_job_via_semantic_retrieval(
                db,
                job_id="does-not-exist",
                retrieval_service=retrieval,
            )

    def test_empty_retrieval_result_screens_nothing(
        self, db, job_and_resumes
    ):
        job, matching, non_matching = job_and_resumes

        retrieval = _mock_retrieval([])

        result = screen_job_via_semantic_retrieval(
            db,
            job_id="semantic-bulk-job-1",
            retrieval_service=retrieval,
        )

        assert result["total_candidates"] == 0
        assert result["results"] == []
