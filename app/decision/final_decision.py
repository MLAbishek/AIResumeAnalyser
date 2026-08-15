from dataclasses import dataclass
from typing import Any


@dataclass
class FinalDecision:
    """
    Final structured decision for a candidate.
    """

    decision: str
    final_score: float
    eligibility: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "final_score": self.final_score,
            "eligibility": self.eligibility,
            "reason": self.reason,
        }


class FinalDecisionEngine:
    """
    Combines eligibility, ranking, and LLM evaluation
    into a deterministic final candidate decision.

    Decision flow:

        Ineligible -> reject

        Eligible + high score -> shortlist

        Eligible + medium score -> review

        Eligible + low score -> reject
    """

    def __init__(
        self,
        shortlist_threshold: float = 75.0,
        review_threshold: float = 50.0,
        ranking_weight: float = 0.7,
        llm_weight: float = 0.3,
    ):
        if shortlist_threshold < review_threshold:
            raise ValueError(
                "shortlist_threshold must be greater than "
                "or equal to review_threshold"
            )

        if ranking_weight < 0 or llm_weight < 0:
            raise ValueError(
                "Weights cannot be negative"
            )

        if ranking_weight + llm_weight == 0:
            raise ValueError(
                "At least one score weight must be greater than zero"
            )

        self.shortlist_threshold = shortlist_threshold
        self.review_threshold = review_threshold
        self.ranking_weight = ranking_weight
        self.llm_weight = llm_weight

    def decide(
        self,
        eligibility: dict[str, Any],
        ranking: dict[str, Any],
        llm_evaluation: dict[str, Any],
    ) -> FinalDecision:
        """
        Produce the final candidate decision.

        Parameters
        ----------
        eligibility:
            Output from the eligibility layer.

        ranking:
            Output from the ranking layer.

        llm_evaluation:
            Structured output from the LLM evaluation layer.
        """

        eligible = self._extract_eligibility(
            eligibility
        )

        ranking_score = self._extract_score(
            ranking,
            "ranking",
        )

        llm_score = self._extract_score(
            llm_evaluation,
            "llm evaluation",
        )

        final_score = self._calculate_final_score(
            ranking_score,
            llm_score,
        )

        if not eligible:
            return FinalDecision(
                decision="reject",
                final_score=final_score,
                eligibility=False,
                reason=(
                    "Candidate does not satisfy "
                    "mandatory eligibility requirements."
                ),
            )

        if final_score >= self.shortlist_threshold:
            return FinalDecision(
                decision="shortlist",
                final_score=final_score,
                eligibility=True,
                reason=(
                    "Candidate satisfies eligibility "
                    "requirements and meets the shortlist threshold."
                ),
            )

        if final_score >= self.review_threshold:
            return FinalDecision(
                decision="review",
                final_score=final_score,
                eligibility=True,
                reason=(
                    "Candidate is eligible but the score "
                    "requires further review."
                ),
            )

        return FinalDecision(
            decision="reject",
            final_score=final_score,
            eligibility=True,
            reason=(
                "Candidate score is below the review threshold."
            ),
        )

    def _extract_eligibility(
        self,
        eligibility: dict[str, Any],
    ) -> bool:
        """
        Extract eligibility from the existing eligibility output.
        """

        if "eligible" in eligibility:
            return bool(eligibility["eligible"])

        if "is_eligible" in eligibility:
            return bool(eligibility["is_eligible"])

        if "passed" in eligibility:
            return bool(eligibility["passed"])

        raise KeyError(
            "Eligibility output must contain one of: "
            "'eligible', 'is_eligible', or 'passed'"
        )

    def _extract_score(
        self,
        result: dict[str, Any],
        source_name: str,
    ) -> float:
        """
        Extract score from ranking/LLM output.

        Supports common score field names so the decision
        layer can integrate with existing modules.
        """

        possible_fields = (
            "score",
            "final_score",
            "ranking_score",
            "llm_score",
            "overall_score",
        )

        for field in possible_fields:
            if field in result:
                try:
                    score = float(result[field])
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"Invalid {source_name} score: "
                        f"{result[field]!r}"
                    ) from exc

                if not 0 <= score <= 100:
                    raise ValueError(
                        f"{source_name} score must be "
                        f"between 0 and 100"
                    )

                return score

        raise KeyError(
            f"{source_name} output does not contain a score"
        )

    def _calculate_final_score(
        self,
        ranking_score: float,
        llm_score: float,
    ) -> float:
        """
        Calculate weighted final score.
        """

        total_weight = (
            self.ranking_weight +
            self.llm_weight
        )

        normalized_ranking_weight = (
            self.ranking_weight / total_weight
        )

        normalized_llm_weight = (
            self.llm_weight / total_weight
        )

        return round(
            (
                ranking_score
                * normalized_ranking_weight
            )
            +
            (
                llm_score
                * normalized_llm_weight
            ),
            2,
        )