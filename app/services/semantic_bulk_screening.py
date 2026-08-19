"""
Orchestrates a real bulk screening request through the persistent
FAISS resume corpus:

    job_id
      -> load Job from DB
      -> CanonicalJob (same adapter ScreeningService uses)
      -> BulkSemanticRetrievalService.retrieve()   (persistent FAISS)
      -> unique resume_ids, ranked by semantic relevance
      -> load those Resume rows from DB
      -> BulkScreeningService.screen()             (unchanged,
                                                      deterministic)

FAISS only narrows WHICH candidates get screened and contributes the
ranking's semantic_score signal (via score_semantic() inside
ScreeningService, independently, as it always has) - it never
decides eligibility or the final decision. Those remain entirely the
responsibility of the existing deterministic pipeline.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.database.crud.jobs import get_job_by_id
from app.database.crud.resumes import get_resume_by_id
from app.normalization.canonical_jd_builder import CanonicalJobBuilder
from app.services.bulk_semantic_retrieval_service import (
    BulkSemanticRetrievalService,
)
from app.services.bulk_screening_service import BulkScreeningService
from app.services.candidate_match_service import (
    _job_to_screening_schema,
    _resume_to_screening_schema,
)


def screen_job_via_semantic_retrieval(
    db: Session,
    *,
    job_id: str,
    top_k: int = 20,
    retrieval_service: BulkSemanticRetrievalService | None = None,
    bulk_screening_service: BulkScreeningService | None = None,
) -> dict[str, Any]:
    """
    Run a real bulk screening request: retrieve the top_k most
    semantically relevant resumes for job_id from the persistent
    FAISS index, then run the existing deterministic
    ScreeningService/BulkScreeningService pipeline on exactly that
    (deduplicated) candidate set.

    Raises ValueError if the job does not exist.
    """

    job = get_job_by_id(db, job_id)

    if job is None:
        raise ValueError(f"Job '{job_id}' not found.")

    job_description = _job_to_screening_schema(job)
    canonical_job = CanonicalJobBuilder().build(
        {
            "job_id": job_description.job_id,
            "title": job_description.title,
            "description": job_description.summary,
            "required_skills": job_description.required_skills,
            "preferred_skills": job_description.preferred_skills,
            "responsibilities": job_description.responsibilities,
            "experience": {
                "minimum_months": int(
                    (
                        job_description.required_experience_years
                        or 0
                    )
                    * 12
                ),
            },
            "education": [
                {"degree": item, "required": True}
                for item in job_description.education
            ],
        }
    )

    retrieval = retrieval_service or BulkSemanticRetrievalService()
    semantic_matches = retrieval.retrieve(canonical_job, top_k=top_k)

    # BulkCandidateSemanticResult.resume_id values are already
    # unique (one dict entry per resume_id in the retrieval
    # aggregation), but Part 8 explicitly calls for an unmistakable
    # dedup step at this boundary too.
    unique_resume_ids = list(
        dict.fromkeys(
            match.resume_id for match in semantic_matches
        )
    )

    resumes = []

    for resume_id in unique_resume_ids:
        resume = get_resume_by_id(db, resume_id)

        if resume is not None:
            resumes.append(_resume_to_screening_schema(resume))

    screening = bulk_screening_service or BulkScreeningService()

    result = screening.screen(
        job_description=job_description,
        resumes=resumes,
    )

    result["semantic_retrieval"] = {
        "candidates_considered": len(semantic_matches),
        "resume_ids": unique_resume_ids,
        "scores": {
            match.resume_id: match.score
            for match in semantic_matches
        },
    }

    return result
