import pytest

from app.decision.final_decision import (
    FinalDecision,
    FinalDecisionEngine,
)


def test_eligible_high_score_is_shortlisted():
    engine = FinalDecisionEngine()

    result = engine.decide(
        eligibility={"eligible": True},
        ranking={"score": 90},
        llm_evaluation={"score": 90},
    )

    assert isinstance(result, FinalDecision)
    assert result.decision == "shortlist"
    assert result.eligibility is True
    assert result.final_score == 90.0


def test_eligible_medium_score_requires_review():
    engine = FinalDecisionEngine()

    result = engine.decide(
        eligibility={"eligible": True},
        ranking={"score": 60},
        llm_evaluation={"score": 60},
    )

    assert result.decision == "review"
    assert result.final_score == 60.0


def test_eligible_low_score_is_rejected():
    engine = FinalDecisionEngine()

    result = engine.decide(
        eligibility={"eligible": True},
        ranking={"score": 30},
        llm_evaluation={"score": 30},
    )

    assert result.decision == "reject"
    assert result.final_score == 30.0


def test_ineligible_candidate_is_rejected_even_with_high_score():
    engine = FinalDecisionEngine()

    result = engine.decide(
        eligibility={"eligible": False},
        ranking={"score": 100},
        llm_evaluation={"score": 100},
    )

    assert result.decision == "reject"
    assert result.eligibility is False
    assert result.final_score == 100.0


def test_weighted_score_is_calculated_correctly():
    engine = FinalDecisionEngine(
        ranking_weight=0.7,
        llm_weight=0.3,
    )

    result = engine.decide(
        eligibility={"eligible": True},
        ranking={"score": 80},
        llm_evaluation={"score": 60},
    )

    assert result.final_score == 74.0
    assert result.decision == "review"


def test_custom_thresholds():
    engine = FinalDecisionEngine(
        shortlist_threshold=80,
        review_threshold=60,
    )

    result = engine.decide(
        eligibility={"eligible": True},
        ranking={"score": 80},
        llm_evaluation={"score": 80},
    )

    assert result.decision == "shortlist"


def test_exact_review_threshold():
    engine = FinalDecisionEngine(
        shortlist_threshold=80,
        review_threshold=60,
    )

    result = engine.decide(
        eligibility={"eligible": True},
        ranking={"score": 60},
        llm_evaluation={"score": 60},
    )

    assert result.decision == "review"


def test_exact_shortlist_threshold():
    engine = FinalDecisionEngine(
        shortlist_threshold=80,
        review_threshold=60,
    )

    result = engine.decide(
        eligibility={"eligible": True},
        ranking={"score": 80},
        llm_evaluation={"score": 80},
    )

    assert result.decision == "shortlist"


def test_alternative_eligibility_field_is_supported():
    engine = FinalDecisionEngine()

    result = engine.decide(
        eligibility={"is_eligible": True},
        ranking={"score": 90},
        llm_evaluation={"score": 90},
    )

    assert result.decision == "shortlist"


def test_missing_eligibility_field_raises_error():
    engine = FinalDecisionEngine()

    with pytest.raises(KeyError):
        engine.decide(
            eligibility={},
            ranking={"score": 90},
            llm_evaluation={"score": 90},
        )


def test_missing_ranking_score_raises_error():
    engine = FinalDecisionEngine()

    with pytest.raises(KeyError):
        engine.decide(
            eligibility={"eligible": True},
            ranking={},
            llm_evaluation={"score": 90},
        )


def test_invalid_score_raises_error():
    engine = FinalDecisionEngine()

    with pytest.raises(ValueError):
        engine.decide(
            eligibility={"eligible": True},
            ranking={"score": 120},
            llm_evaluation={"score": 90},
        )


def test_negative_score_raises_error():
    engine = FinalDecisionEngine()

    with pytest.raises(ValueError):
        engine.decide(
            eligibility={"eligible": True},
            ranking={"score": -10},
            llm_evaluation={"score": 90},
        )


def test_weights_are_normalized():
    engine = FinalDecisionEngine(
        ranking_weight=7,
        llm_weight=3,
    )

    result = engine.decide(
        eligibility={"eligible": True},
        ranking={"score": 80},
        llm_evaluation={"score": 60},
    )

    assert result.final_score == 74.0


def test_zero_weights_are_rejected():
    with pytest.raises(ValueError):
        FinalDecisionEngine(
            ranking_weight=0,
            llm_weight=0,
        )


def test_negative_weight_is_rejected():
    with pytest.raises(ValueError):
        FinalDecisionEngine(
            ranking_weight=-1,
            llm_weight=1,
        )


def test_invalid_threshold_configuration_is_rejected():
    with pytest.raises(ValueError):
        FinalDecisionEngine(
            shortlist_threshold=50,
            review_threshold=75,
        )


def test_result_can_be_converted_to_dict():
    engine = FinalDecisionEngine()

    result = engine.decide(
        eligibility={"eligible": True},
        ranking={"score": 90},
        llm_evaluation={"score": 80},
    )

    data = result.to_dict()

    assert data["decision"] == "shortlist"
    assert data["eligibility"] is True
    assert data["final_score"] == 87.0