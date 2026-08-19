"""
Targeted test proving semantic_score (from the embedding dispatch
path) actually flows into the existing ranking formula -
calculate_candidate_score() / extract_features() were not touched by
the semantic-matching integration, so this proves the wiring holds
end-to-end without needing to load the real BGE-M3 model.
"""

from unittest.mock import MagicMock

from app.core.config import settings
from app.core.schemas import CanonicalJob, CanonicalResume
from app.ranking import semantic_scorer
from app.ranking.scoring_engine import calculate_candidate_score
from app.services.semantic_matching_service import (
    SemanticScoreResult,
)


def _job() -> CanonicalJob:
    return CanonicalJob(
        job_id="job-1",
        title="Python Developer",
        required_skills=["python"],
    )


def _resume() -> CanonicalResume:
    return CanonicalResume(
        resume_id="resume-1",
        skills=["python"],
    )


def test_final_score_changes_with_the_embedding_semantic_score(
    monkeypatch,
):
    monkeypatch.setattr(settings, "enable_semantic_search", True)

    mock_service = MagicMock()
    monkeypatch.setattr(
        semantic_scorer,
        "_get_semantic_service",
        lambda: mock_service,
    )

    mock_service.score.return_value = SemanticScoreResult(
        score=0.1, mode="embedding"
    )
    low_semantic_result = calculate_candidate_score(
        _job(), _resume()
    )

    mock_service.score.return_value = SemanticScoreResult(
        score=0.9, mode="embedding"
    )
    high_semantic_result = calculate_candidate_score(
        _job(), _resume()
    )

    assert (
        low_semantic_result.features.semantic_score == 0.1
    )
    assert (
        high_semantic_result.features.semantic_score == 0.9
    )
    assert high_semantic_result.score > low_semantic_result.score


def test_semantic_score_is_present_in_the_feature_vector(
    monkeypatch,
):
    monkeypatch.setattr(settings, "enable_semantic_search", True)

    mock_service = MagicMock()
    mock_service.score.return_value = SemanticScoreResult(
        score=0.5, mode="embedding"
    )
    monkeypatch.setattr(
        semantic_scorer,
        "_get_semantic_service",
        lambda: mock_service,
    )

    result = calculate_candidate_score(_job(), _resume())

    assert result.features.semantic_score == 0.5


def test_ranking_weights_are_unchanged(monkeypatch):
    # The integration must not silently reweight the ranking formula
    # just because semantic_score is now "real".
    from app.ranking.scoring_engine import DEFAULT_WEIGHTS

    assert DEFAULT_WEIGHTS == {
        "skill": 0.35,
        "experience": 0.20,
        "seniority": 0.15,
        "education": 0.10,
        "semantic": 0.20,
    }
