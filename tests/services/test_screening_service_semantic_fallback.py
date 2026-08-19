"""
Targeted test proving the live ScreeningService.screen() path keeps
working end-to-end even when the embedding/vector semantic path
fails completely (model load failure, FAISS error, etc.) -
eligibility and the rest of ranking must remain unaffected; only the
semantic component degrades to the deterministic lexical fallback.
"""

from unittest.mock import MagicMock

from app.core.config import settings
from app.core.schemas import (
    Experience,
    JobDescription,
    Resume,
)
from app.ranking import semantic_scorer
from app.services.llm_service import LLMExplanationService
from app.services.screening_service import ScreeningService


def _job() -> JobDescription:
    return JobDescription(
        job_id="JD-SEMANTIC-FALLBACK-001",
        title="Python Developer",
        required_skills=["Python"],
        required_experience_years=1,
        raw_text="Python developer.",
    )


def _resume() -> Resume:
    return Resume(
        resume_id="RES-SEMANTIC-FALLBACK-001",
        skills=["Python"],
        experience=[
            Experience(
                company="Acme",
                role="Python Developer",
                start_date="01/2023",
                end_date="01/2024",
            ),
        ],
        raw_text="Python developer.",
    )


def test_screening_completes_when_embedding_model_fails_to_load(
    monkeypatch,
):
    monkeypatch.setattr(settings, "enable_semantic_search", True)

    broken_service = MagicMock()
    broken_service.score.side_effect = RuntimeError(
        "sentence-transformers model failed to load"
    )
    monkeypatch.setattr(
        semantic_scorer,
        "_get_semantic_service",
        lambda: broken_service,
    )

    service = ScreeningService(
        llm_service=LLMExplanationService(enabled=False)
    )

    result = service.screen(
        job_description=_job(), resumes=[_resume()]
    )
    candidate = result["results"][0]

    assert candidate["eligible"] is True
    assert candidate["decision"] in {
        "shortlist",
        "review",
        "reject",
    }
    assert candidate["ranking"] is not None
    assert (
        0.0
        <= candidate["ranking"]["features"]["semantic_score"]
        <= 1.0
    )


def test_screening_completes_when_vector_retrieval_raises(
    monkeypatch,
):
    monkeypatch.setattr(settings, "enable_semantic_search", True)

    broken_service = MagicMock()
    broken_service.score.side_effect = ValueError(
        "FAISS index dimension mismatch"
    )
    monkeypatch.setattr(
        semantic_scorer,
        "_get_semantic_service",
        lambda: broken_service,
    )

    service = ScreeningService(
        llm_service=LLMExplanationService(enabled=False)
    )

    result = service.screen(
        job_description=_job(), resumes=[_resume()]
    )
    candidate = result["results"][0]

    assert candidate["eligible"] is True
    assert candidate["ranking"]["features"]["skill_score"] == 1.0
