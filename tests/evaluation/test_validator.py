import pytest

from app.evaluation.evaluator import CandidateEvaluation
from app.evaluation.validator import (
    EvaluationValidationError,
    StructuredOutputValidator,
)


def valid_evaluation():
    return {
        "score": 84,
        "strengths": ["Strong Python experience"],
        "weaknesses": ["Limited Kubernetes evidence"],
        "requirement_assessment": [
            {
                "requirement": "Python",
                "status": "met",
                "evidence": "Python listed in skills",
            }
        ],
        "reasoning": "Strong overall alignment.",
        "confidence": 0.9,
    }


def test_valid_evaluation():

    validator = StructuredOutputValidator()

    result = validator.validate(
        valid_evaluation()
    )

    assert isinstance(result, CandidateEvaluation)
    assert result.score == 84


def test_validate_json_string():

    validator = StructuredOutputValidator()

    result = validator.validate(
        """
        {
            "score": 80,
            "strengths": ["Python"],
            "weaknesses": [],
            "requirement_assessment": [],
            "reasoning": "Good fit.",
            "confidence": 0.8
        }
        """
    )

    assert result.score == 80


def test_invalid_score_is_rejected():

    validator = StructuredOutputValidator()

    evaluation = valid_evaluation()
    evaluation["score"] = 120

    with pytest.raises(EvaluationValidationError):
        validator.validate(evaluation)


def test_invalid_confidence_is_rejected():

    validator = StructuredOutputValidator()

    evaluation = valid_evaluation()
    evaluation["confidence"] = 1.5

    with pytest.raises(EvaluationValidationError):
        validator.validate(evaluation)


def test_missing_reasoning_is_rejected():

    validator = StructuredOutputValidator()

    evaluation = valid_evaluation()
    del evaluation["reasoning"]

    with pytest.raises(EvaluationValidationError):
        validator.validate(evaluation)


def test_invalid_requirement_status_is_currently_rejected():

    validator = StructuredOutputValidator()

    evaluation = valid_evaluation()
    evaluation["requirement_assessment"][0]["status"] = "random"

    # This test intentionally documents the desired strict contract.
    # It will require the status field to be an enum in the next patch.
    with pytest.raises(EvaluationValidationError):
        validator.validate(evaluation)