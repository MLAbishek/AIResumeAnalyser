import pytest

from app.explanation.explainability_engine import (
    ExplainabilityEngine,
)


@pytest.fixture
def engine():
    return ExplainabilityEngine()


def test_shortlist_explanation(engine):
    result = engine.explain(
        decision="shortlist",
        matching_features={
            "matched_skills": [
                "Python",
                "SQL",
                "Machine Learning",
            ],
            "missing_skills": [],
            "experience_match": True,
            "education_match": True,
            "ranking_score": 85,
            "llm_score": 90,
        },
    )

    assert result["decision"] == "shortlist"
    assert result["strengths"]
    assert result["gaps"] == []
    assert result["reasons"]


def test_missing_skills_are_reported(engine):
    result = engine.explain(
        decision="review",
        matching_features={
            "matched_skills": [
                "Python",
                "SQL",
            ],
            "missing_skills": [
                "Docker",
                "Kubernetes",
            ],
        },
    )

    assert result["decision"] == "review"

    assert any(
        "Docker" in reason
        for reason in result["gaps"]
    )

    assert any(
        "Kubernetes" in reason
        for reason in result["gaps"]
    )


def test_experience_gap_is_reported(engine):
    result = engine.explain(
        decision="review",
        matching_features={
            "experience_match": False,
            "experience_gap": {
                "required_years": 5,
                "candidate_years": 3,
                "gap_years": 2,
            },
        },
    )

    assert any(
        "2 years" in gap
        for gap in result["gaps"]
    )


def test_experience_match_is_reported(engine):
    result = engine.explain(
        decision="shortlist",
        matching_features={
            "experience_match": True,
        },
    )

    assert (
        "Required experience is satisfied."
        in result["strengths"]
    )


def test_education_match_is_reported(engine):
    result = engine.explain(
        decision="shortlist",
        matching_features={
            "education_match": True,
        },
    )

    assert (
        "Education requirements are satisfied."
        in result["strengths"]
    )


def test_education_gap_is_reported(engine):
    result = engine.explain(
        decision="reject",
        matching_features={
            "education_match": False,
        },
    )

    assert (
        "Education requirements are not satisfied."
        in result["gaps"]
    )


def test_ranking_score_is_included(engine):
    result = engine.explain(
        decision="shortlist",
        matching_features={
            "ranking_score": 87.5,
        },
    )

    assert any(
        "87.50" in reason
        for reason in result["strengths"]
    )


def test_llm_score_is_included(engine):
    result = engine.explain(
        decision="shortlist",
        matching_features={
            "llm_score": 91.25,
        },
    )

    assert any(
        "91.25" in reason
        for reason in result["strengths"]
    )


def test_explicit_reasons_are_preserved(engine):
    result = engine.explain(
        decision="review",
        matching_features={
            "reasons": [
                "Strong domain experience.",
                "Good technical alignment.",
            ],
        },
    )

    assert (
        "Strong domain experience."
        in result["reasons"]
    )

    assert (
        "Good technical alignment."
        in result["reasons"]
    )


def test_duplicate_reasons_are_not_added(engine):
    result = engine.explain(
        decision="shortlist",
        matching_features={
            "experience_match": True,
            "reasons": [
                "Required experience is satisfied.",
            ],
        },
    )

    assert result["reasons"].count(
        "Required experience is satisfied."
    ) == 1


def test_empty_features_are_supported(engine):
    result = engine.explain(
        decision="review",
        matching_features={},
    )

    assert result["decision"] == "review"
    assert result["strengths"] == []
    assert result["gaps"] == []
    assert result["reasons"] == []


def test_invalid_decision_raises_error(engine):
    with pytest.raises(ValueError):
        engine.explain(
            decision="unknown",
            matching_features={},
        )


def test_non_string_decision_raises_error(engine):
    with pytest.raises(TypeError):
        engine.explain(
            decision=123,
            matching_features={},
        )


def test_non_dict_features_raise_error(engine):
    with pytest.raises(TypeError):
        engine.explain(
            decision="shortlist",
            matching_features=[],
        )


def test_certification_match_is_reported(engine):
    result = engine.explain(
        decision="shortlist",
        matching_features={
            "certification_match": True,
        },
    )

    assert (
        "Required certification requirements are satisfied."
        in result["strengths"]
    )


def test_certification_gap_is_reported(engine):
    result = engine.explain(
        decision="reject",
        matching_features={
            "certification_match": False,
        },
    )

    assert (
        "Certification requirements are not satisfied."
        in result["gaps"]
    )


def test_summary_contains_decision(engine):
    result = engine.explain(
        decision="shortlist",
        matching_features={
            "matched_skills": ["Python"],
        },
    )

    assert "shortlisted" in result["summary"].lower()


def test_no_unsupported_claims_are_generated(engine):
    result = engine.explain(
        decision="review",
        matching_features={},
    )

    assert result["strengths"] == []
    assert result["gaps"] == []
    assert result["reasons"] == []