"""
Targeted tests for the semantic_scorer.score_semantic() dispatcher:
it must use the genuine embedding path when enabled and working, and
fall back to the deterministic lexical (Jaccard) score - explicitly,
never silently - when disabled or when embedding scoring fails for
any reason.

The real SemanticMatchingService is mocked here (via the module's
_get_semantic_service() lazy singleton hook), so these tests never
load the real BGE-M3 model.
"""

from unittest.mock import MagicMock

from app.core.config import settings
from app.core.schemas import CanonicalJob, CanonicalResume
from app.ranking import semantic_scorer
from app.ranking.semantic_scorer import (
    _lexical_overlap_score,
    score_semantic,
)
from app.services.semantic_matching_service import (
    SemanticScoreResult,
)


def _job() -> CanonicalJob:
    return CanonicalJob(
        job_id="job-1",
        title="Python Developer",
        description="Build backend services.",
        required_skills=["python"],
    )


def _resume() -> CanonicalResume:
    return CanonicalResume(
        resume_id="resume-1",
        summary="Python backend engineer.",
        skills=["python"],
    )


def test_disabled_uses_lexical_fallback_not_embedding_service(
    monkeypatch,
):
    monkeypatch.setattr(
        settings, "enable_semantic_search", False
    )

    mock_get_service = MagicMock()
    monkeypatch.setattr(
        semantic_scorer, "_get_semantic_service", mock_get_service
    )

    score = score_semantic(_job(), _resume())

    mock_get_service.assert_not_called()
    assert score == _lexical_overlap_score(_job(), _resume())


def test_enabled_and_successful_uses_embedding_score(monkeypatch):
    monkeypatch.setattr(settings, "enable_semantic_search", True)

    mock_service = MagicMock()
    mock_service.score.return_value = SemanticScoreResult(
        score=0.8342,
        mode="embedding",
        model_name="BAAI/bge-m3",
    )
    monkeypatch.setattr(
        semantic_scorer,
        "_get_semantic_service",
        lambda: mock_service,
    )

    score = score_semantic(_job(), _resume())

    assert score == 0.8342
    mock_service.score.assert_called_once()


def test_service_reporting_fallback_mode_uses_lexical_score(
    monkeypatch,
):
    monkeypatch.setattr(settings, "enable_semantic_search", True)

    mock_service = MagicMock()
    mock_service.score.return_value = SemanticScoreResult(
        score=0.0,
        mode="fallback",
        reason="no chunkable content",
    )
    monkeypatch.setattr(
        semantic_scorer,
        "_get_semantic_service",
        lambda: mock_service,
    )

    score = score_semantic(_job(), _resume())

    assert score == _lexical_overlap_score(_job(), _resume())


def test_service_raising_falls_back_without_crashing(monkeypatch):
    monkeypatch.setattr(settings, "enable_semantic_search", True)

    mock_service = MagicMock()
    mock_service.score.side_effect = RuntimeError(
        "embedding model failed to load"
    )
    monkeypatch.setattr(
        semantic_scorer,
        "_get_semantic_service",
        lambda: mock_service,
    )

    score = score_semantic(_job(), _resume())

    assert score == _lexical_overlap_score(_job(), _resume())


def test_lexical_fallback_score_is_still_normalized(monkeypatch):
    monkeypatch.setattr(
        settings, "enable_semantic_search", False
    )

    score = score_semantic(_job(), _resume())

    assert 0.0 <= score <= 1.0
