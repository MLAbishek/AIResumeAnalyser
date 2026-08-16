from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable , Literal

from pydantic import BaseModel, Field


class RequirementAssessment(BaseModel):
    requirement: str
    status: Literal[
        "met",
        "partially_met",
        "not_met",
        "unknown",
    ]
    evidence: str = ""


class CandidateEvaluation(BaseModel):
    """
    Structured output produced by the LLM candidate evaluator.

    Score is intentionally 0-100 because this is the contract
    consumed by the decision layer.
    """

    score: float = Field(ge=0.0, le=100.0)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    requirement_assessment: list[RequirementAssessment] = Field(
        default_factory=list
    )
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)


@dataclass
class EvaluationContext:
    job: dict[str, Any]
    resume: dict[str, Any]
    ranking_score: float | None = None
    ranking_features: dict[str, Any] | None = None
    evidence: list[dict[str, Any]] | None = None


LLMCallable = Callable[[str], Any]


class LLMCandidateEvaluator:
    """
    Module 39.

    Performs contextual candidate evaluation using an injected
    LLM callable.

    The evaluator does not make the final hiring decision.
    """

    def __init__(self, llm_callable: LLMCallable):
        if not callable(llm_callable):
            raise TypeError("llm_callable must be callable")

        self.llm_callable = llm_callable

    def evaluate(
        self,
        job: dict[str, Any],
        resume: dict[str, Any],
        ranking_score: float | None = None,
        ranking_features: dict[str, Any] | None = None,
        evidence: list[dict[str, Any]] | None = None,
    ) -> CandidateEvaluation:

        if not isinstance(job, dict):
            raise TypeError("job must be a dictionary")

        if not isinstance(resume, dict):
            raise TypeError("resume must be a dictionary")

        if ranking_score is not None:
            ranking_score = float(ranking_score)

            if 0.0 <= ranking_score <= 1.0:
                ranking_score *= 100.0

            if not 0.0 <= ranking_score <= 100.0:
                raise ValueError(
                    "ranking_score must be between 0 and 100 "
                    "or between 0 and 1"
                )

        context = EvaluationContext(
            job=job,
            resume=resume,
            ranking_score=ranking_score,
            ranking_features=ranking_features,
            evidence=evidence or [],
        )

        prompt = self._build_prompt(context)

        raw_response = self.llm_callable(prompt)

        return self._parse_response(raw_response)

    def _build_prompt(
        self,
        context: EvaluationContext,
    ) -> str:

        payload = {
            "job": context.job,
            "resume": context.resume,
            "ranking_score": context.ranking_score,
            "ranking_features": context.ranking_features or {},
            "evidence": context.evidence or [],
        }

        return (
            "Evaluate the candidate against the job description.\n\n"
            "Rules:\n"
            "1. Use only information supplied in the job, resume, "
            "ranking features, and evidence.\n"
            "2. Do not invent qualifications or experience.\n"
            "3. Distinguish clearly between demonstrated evidence "
            "and missing information.\n"
            "4. Do not make the final hiring decision.\n"
            "5. Return ONLY valid JSON.\n"
            "6. score must be between 0 and 100.\n"
            "7. confidence must be between 0 and 1.\n\n"
            "Required JSON structure:\n"
            "{\n"
            '  "score": 0-100,\n'
            '  "strengths": ["..."],\n'
            '  "weaknesses": ["..."],\n'
            '  "requirement_assessment": [\n'
            '    {\n'
            '      "requirement": "...",\n'
            '      "status": "met|partially_met|not_met|unknown",\n'
            '      "evidence": "..."\n'
            "    }\n"
            "  ],\n"
            '  "reasoning": "...",\n'
            '  "confidence": 0-1\n'
            "}\n\n"
            "Candidate evaluation context:\n"
            + json.dumps(payload, default=str)
        )

    @staticmethod
    def _parse_response(
        response: Any,
    ) -> CandidateEvaluation:

        if isinstance(response, CandidateEvaluation):
            return response

        if isinstance(response, str):
            try:
                response = json.loads(response)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    "LLM returned invalid JSON"
                ) from exc

        if not isinstance(response, dict):
            raise TypeError(
                "LLM response must be a dictionary, JSON string, "
                "or CandidateEvaluation"
            )

        return CandidateEvaluation.model_validate(response)