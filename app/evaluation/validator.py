from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.evaluation.evaluator import CandidateEvaluation


class EvaluationValidationError(ValueError):
    """
    Raised when an LLM candidate evaluation is invalid.
    """


class StructuredOutputValidator:
    """

    Validates structured output produced by Module 39.
    """

    def validate(
        self,
        evaluation: Any,
    ) -> CandidateEvaluation:

        if isinstance(evaluation, CandidateEvaluation):
            return evaluation

        if isinstance(evaluation, str):
            try:
                return CandidateEvaluation.model_validate_json(
                    evaluation
                )
            except ValidationError as exc:
                raise EvaluationValidationError(
                    "LLM evaluation failed schema validation"
                ) from exc

        if not isinstance(evaluation, dict):
            raise EvaluationValidationError(
                "Evaluation output must be a dictionary, "
                "JSON string, or CandidateEvaluation"
            )

        try:
            return CandidateEvaluation.model_validate(
                evaluation
            )
        except ValidationError as exc:
            raise EvaluationValidationError(
                "LLM evaluation failed schema validation"
            ) from exc

    def validate_dict(
        self,
        evaluation: Any,
    ) -> dict[str, Any]:

        validated = self.validate(evaluation)

        return validated.model_dump()