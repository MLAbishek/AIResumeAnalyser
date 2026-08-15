from dataclasses import dataclass


@dataclass
class DecisionPolicy:
    shortlist_threshold: float = 75.0
    review_threshold: float = 50.0


class ThresholdPolicyEngine:
    """
    Applies configurable thresholds to determine
    shortlist, review, or reject decisions.
    """

    def __init__(self, policy: DecisionPolicy | None = None):
        self.policy = policy or DecisionPolicy()

    def evaluate(
        self,
        candidate_score: float,
        eligible: bool,
    ) -> dict:
        """
        Evaluate a candidate using eligibility and score thresholds.
        """

        if not eligible:
            return {
                "decision": "reject",
                "threshold_met": False,
                "reason": "Candidate is not eligible.",
            }

        if candidate_score >= self.policy.shortlist_threshold:
            return {
                "decision": "shortlist",
                "threshold_met": True,
                "reason": "Candidate score meets the shortlist threshold.",
            }

        if candidate_score >= self.policy.review_threshold:
            return {
                "decision": "review",
                "threshold_met": True,
                "reason": "Candidate score meets the review threshold.",
            }

        return {
            "decision": "reject",
            "threshold_met": False,
            "reason": "Candidate score is below the review threshold.",
        }

    def get_policy(self) -> dict:
        """
        Return the currently configured policy.
        """

        return {
            "shortlist_threshold": self.policy.shortlist_threshold,
            "review_threshold": self.policy.review_threshold,
        }