from app.decision.threshold_policy import (
    DecisionPolicy,
    ThresholdPolicyEngine,
)


def test_high_score_shortlists_candidate():
    engine = ThresholdPolicyEngine()

    result = engine.evaluate(
        candidate_score=85,
        eligible=True,
    )

    assert result["decision"] == "shortlist"
    assert result["threshold_met"] is True


def test_medium_score_requires_review():
    engine = ThresholdPolicyEngine()

    result = engine.evaluate(
        candidate_score=60,
        eligible=True,
    )

    assert result["decision"] == "review"
    assert result["threshold_met"] is True


def test_low_score_rejects_candidate():
    engine = ThresholdPolicyEngine()

    result = engine.evaluate(
        candidate_score=40,
        eligible=True,
    )

    assert result["decision"] == "reject"
    assert result["threshold_met"] is False


def test_ineligible_candidate_is_rejected():
    engine = ThresholdPolicyEngine()

    result = engine.evaluate(
        candidate_score=95,
        eligible=False,
    )

    assert result["decision"] == "reject"
    assert result["threshold_met"] is False


def test_exact_shortlist_threshold():
    engine = ThresholdPolicyEngine()

    result = engine.evaluate(
        candidate_score=75,
        eligible=True,
    )

    assert result["decision"] == "shortlist"


def test_exact_review_threshold():
    engine = ThresholdPolicyEngine()

    result = engine.evaluate(
        candidate_score=50,
        eligible=True,
    )

    assert result["decision"] == "review"


def test_custom_policy():
    policy = DecisionPolicy(
        shortlist_threshold=80,
        review_threshold=60,
    )

    engine = ThresholdPolicyEngine(policy)

    assert engine.evaluate(80, True)["decision"] == "shortlist"
    assert engine.evaluate(60, True)["decision"] == "review"
    assert engine.evaluate(59, True)["decision"] == "reject"


def test_get_policy():
    policy = DecisionPolicy(
        shortlist_threshold=80,
        review_threshold=60,
    )

    engine = ThresholdPolicyEngine(policy)

    result = engine.get_policy()

    assert result == {
        "shortlist_threshold": 80,
        "review_threshold": 60,
    }