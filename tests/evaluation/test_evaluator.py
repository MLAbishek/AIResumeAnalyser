import pytest

from app.evaluation.evaluator import (
    CandidateEvaluation,
    LLMCandidateEvaluator,
)


def valid_llm_response():
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
        "reasoning": (
            "The candidate demonstrates strong alignment "
            "with the core technical requirements."
        ),
        "confidence": 0.91,
    }


def test_evaluator_returns_structured_evaluation():

    def fake_llm(prompt):
        assert "Evaluate the candidate" in prompt
        return valid_llm_response()

    evaluator = LLMCandidateEvaluator(fake_llm)

    result = evaluator.evaluate(
        job={"required_skills": ["Python"]},
        resume={"skills": ["Python"]},
    )

    assert isinstance(result, CandidateEvaluation)
    assert result.score == 84
    assert result.confidence == 0.91
    assert len(result.strengths) == 2


def test_evaluator_converts_normalized_ranking_score():

    received_prompt = {}

    def fake_llm(prompt):
        received_prompt["prompt"] = prompt
        return valid_llm_response()

    evaluator = LLMCandidateEvaluator(fake_llm)

    evaluator.evaluate(
        job={},
        resume={},
        ranking_score=0.82,
    )

    assert '"ranking_score": 82.0' in received_prompt["prompt"]


def test_evaluator_accepts_percentage_ranking_score():

    received_prompt = {}

    def fake_llm(prompt):
        received_prompt["prompt"] = prompt
        return valid_llm_response()

    evaluator = LLMCandidateEvaluator(fake_llm)

    evaluator.evaluate(
        job={},
        resume={},
        ranking_score=82,
    )

    assert '"ranking_score": 82.0' in received_prompt["prompt"]


def test_evaluator_rejects_invalid_llm_score():

    def fake_llm(prompt):
        return {
            **valid_llm_response(),
            "score": 101,
        }

    evaluator = LLMCandidateEvaluator(fake_llm)

    with pytest.raises(ValueError):
        evaluator.evaluate(
            job={},
            resume={},
        )


def test_evaluator_rejects_invalid_json():

    def fake_llm(prompt):
        return "this is not json"

    evaluator = LLMCandidateEvaluator(fake_llm)

    with pytest.raises(ValueError, match="invalid JSON"):
        evaluator.evaluate(
            job={},
            resume={},
        )


def test_evaluator_rejects_non_dictionary_job():

    evaluator = LLMCandidateEvaluator(
        lambda prompt: valid_llm_response()
    )

    with pytest.raises(TypeError):
        evaluator.evaluate(
            job=[],
            resume={},
        )