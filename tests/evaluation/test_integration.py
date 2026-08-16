import pytest
from app.decision.final_decision import FinalDecisionEngine
from app.evaluation.evaluator import LLMCandidateEvaluator
from app.evaluation.validator import (
    EvaluationValidationError,
    StructuredOutputValidator,
)
from app.decision.final_decision import FinalDecisionEngine
from app.evaluation.evaluator import LLMCandidateEvaluator
from app.evaluation.validator import StructuredOutputValidator


def test_evaluation_to_final_decision_pipeline():

    def fake_llm(prompt):
        return {
            "score": 84,
            "strengths": [
                "Strong Python experience",
                "Relevant backend experience",
            ],
            "weaknesses": [
                "Limited Kubernetes evidence",
            ],
            "requirement_assessment": [
                {
                    "requirement": "Python",
                    "status": "met",
                    "evidence": "Python listed in skills",
                },
                {
                    "requirement": "Kubernetes",
                    "status": "partially_met",
                    "evidence": "Limited Kubernetes evidence",
                },
            ],
            "reasoning": "Strong overall candidate alignment.",
            "confidence": 0.91,
        }

    evaluator = LLMCandidateEvaluator(fake_llm)

    evaluation = evaluator.evaluate(
        job={
            "required_skills": [
                "Python",
                "Kubernetes",
            ]
        },
        resume={
            "skills": [
                "Python",
                "FastAPI",
            ]
        },
        ranking_score=0.82,
    )

    validator = StructuredOutputValidator()

    validated = validator.validate_dict(evaluation)

    assert validated["score"] == 84
    assert validated["confidence"] == 0.91

    decision_engine = FinalDecisionEngine(
        shortlist_threshold=75,
        review_threshold=50,
        ranking_weight=0.7,
        llm_weight=0.3,
    )

    decision = decision_engine.decide(
        eligibility={
            "eligible": True,
        },
        ranking={
            "score": 82,
        },
        llm_evaluation=validated,
    )

    assert decision.decision == "shortlist"
    assert decision.eligibility is True
    assert decision.final_score == 82.6


def test_ineligible_candidate_is_rejected_even_with_high_llm_score():

    evaluator = LLMCandidateEvaluator(
        lambda prompt: {
            "score": 95,
            "strengths": ["Excellent technical skills"],
            "weaknesses": [],
            "requirement_assessment": [],
            "reasoning": "Very strong candidate.",
            "confidence": 0.95,
        }
    )

    evaluation = evaluator.evaluate(
        job={},
        resume={},
        ranking_score=0.95,
    )

    validated = StructuredOutputValidator().validate_dict(
        evaluation
    )

    decision = FinalDecisionEngine().decide(
        eligibility={"eligible": False},
        ranking={"score": 95},
        llm_evaluation=validated,
    )

    assert decision.decision == "reject"
    assert decision.eligibility is False


def test_low_llm_score_can_reduce_final_score_to_review():

    evaluator = LLMCandidateEvaluator(
        lambda prompt: {
            "score": 40,
            "strengths": [],
            "weaknesses": ["Major skill gaps"],
            "requirement_assessment": [],
            "reasoning": "Candidate has significant gaps.",
            "confidence": 0.9,
        }
    )

    evaluation = evaluator.evaluate(
        job={},
        resume={},
        ranking_score=0.8,
    )

    validated = StructuredOutputValidator().validate_dict(
        evaluation
    )

    decision = FinalDecisionEngine().decide(
        eligibility={"eligible": True},
        ranking={"score": 80},
        llm_evaluation=validated,
    )

    # 80 * .7 + 40 * .3 = 68
    assert decision.final_score == 68.0
    assert decision.decision == "review"


def test_malformed_llm_output_does_not_reach_decision_engine():

    evaluator = LLMCandidateEvaluator(
        lambda prompt: {
            "score": 150,
            "strengths": [],
            "weaknesses": [],
            "requirement_assessment": [],
            "reasoning": "Invalid output.",
            "confidence": 0.9,
        }
    )

    with pytest.raises(ValueError):
        evaluator.evaluate(
            job={},
            resume={},
        )


def test_invalid_requirement_status_is_rejected():

    validator = StructuredOutputValidator()

    invalid_evaluation = {
        "score": 80,
        "strengths": ["Python"],
        "weaknesses": [],
        "requirement_assessment": [
            {
                "requirement": "Python",
                "status": "maybe",
                "evidence": "Python listed",
            }
        ],
        "reasoning": "Good candidate.",
        "confidence": 0.8,
    }

    with pytest.raises(EvaluationValidationError):
        validator.validate(invalid_evaluation)


def test_missing_required_field_is_rejected():

    validator = StructuredOutputValidator()

    invalid_evaluation = {
        "score": 80,
        "strengths": ["Python"],
        "weaknesses": [],
        "requirement_assessment": [],
        "confidence": 0.8,
    }

    with pytest.raises(EvaluationValidationError):
        validator.validate(invalid_evaluation)