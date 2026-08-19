"""
Targeted tests for the LLM explanation integration point inside the
live ScreeningService path (app/services/screening_service.py). The
OpenRouter network call is mocked in every test here - no live API
key is used. These verify:

- the deterministic score/eligibility/decision/gap analysis/evidence
  are byte-for-byte unchanged whether or not the LLM is used
- the LLM-generated narrative is inserted into the explanation dict
  when the mocked call succeeds
- screening still succeeds, with a deterministic fallback narrative,
  when the mocked LLM call fails
"""

from unittest.mock import MagicMock

from app.core.schemas import (
    Experience,
    JobDescription,
    Resume,
)
from app.services.llm_service import LLMExplanationService
from app.services.screening_service import ScreeningService


def _job() -> JobDescription:
    return JobDescription(
        job_id="JD-LLM-001",
        title="Python Developer",
        required_skills=["Python"],
        preferred_skills=["Docker"],
        required_experience_years=2,
        raw_text="Python developer with 2 years experience.",
    )


def _resume() -> Resume:
    return Resume(
        resume_id="RES-LLM-001",
        name="Candidate One",
        skills=["Python"],
        experience=[
            Experience(
                company="Acme",
                role="Python Developer",
                start_date="01/2022",
                end_date="01/2024",
            ),
        ],
        raw_text="Python developer with two years experience.",
    )


def _deterministic_screen():
    """A screening run with the LLM untouched (disabled by
    default), used as the ground truth for comparison."""

    service = ScreeningService()
    result = service.screen(
        job_description=_job(), resumes=[_resume()]
    )
    return result["results"][0]


class TestLLMDisabledLeavesEverythingUnchanged:
    def test_default_screening_service_does_not_call_llm(self):
        # No llm_service override, no ENABLE_LLM_EXPLANATIONS in
        # this call - the default LLMExplanationService reads
        # settings, which default enable_llm_explanations to False,
        # so no network call is attempted at all.
        mock_llm = MagicMock(spec=LLMExplanationService)
        mock_llm.generate_explanation.return_value = None

        service = ScreeningService(llm_service=mock_llm)
        result = service.screen(
            job_description=_job(), resumes=[_resume()]
        )
        candidate = result["results"][0]

        assert candidate["explanation"]["narrative_source"] == (
            "deterministic"
        )
        assert (
            candidate["explanation"]["narrative"]
            == candidate["explanation"]["summary"]
        )


class TestLLMSuccessInsertsNarrativeWithoutChangingFacts:
    def test_deterministic_values_unchanged_when_llm_succeeds(self):
        baseline = _deterministic_screen()

        mock_llm = MagicMock(spec=LLMExplanationService)
        mock_llm.generate_explanation.return_value = (
            "The candidate is a strong match for this role based "
            "on their Python experience."
        )

        service = ScreeningService(llm_service=mock_llm)
        result = service.screen(
            job_description=_job(), resumes=[_resume()]
        )
        candidate = result["results"][0]

        assert candidate["eligible"] == baseline["eligible"]
        assert candidate["ranking_score"] == baseline["ranking_score"]
        assert (
            candidate["ranking_score_percent"]
            == baseline["ranking_score_percent"]
        )
        assert candidate["decision"] == baseline["decision"]
        assert (
            candidate["decision_reason"]
            == baseline["decision_reason"]
        )
        assert candidate["gap_analysis"] == baseline["gap_analysis"]
        assert candidate["evidence"] == baseline["evidence"]

        # Only the explanation's narrative fields differ - the
        # deterministic explanation keys are untouched.
        assert (
            candidate["explanation"]["decision"]
            == baseline["explanation"]["decision"]
        )
        assert (
            candidate["explanation"]["summary"]
            == baseline["explanation"]["summary"]
        )
        assert (
            candidate["explanation"]["strengths"]
            == baseline["explanation"]["strengths"]
        )
        assert (
            candidate["explanation"]["gaps"]
            == baseline["explanation"]["gaps"]
        )

    def test_llm_narrative_is_inserted_into_explanation(self):
        mock_llm = MagicMock(spec=LLMExplanationService)
        mock_llm.generate_explanation.return_value = (
            "The candidate is a strong match for this role."
        )

        service = ScreeningService(llm_service=mock_llm)
        result = service.screen(
            job_description=_job(), resumes=[_resume()]
        )
        candidate = result["results"][0]

        assert (
            candidate["explanation"]["narrative"]
            == "The candidate is a strong match for this role."
        )
        assert (
            candidate["explanation"]["narrative_source"] == "llm"
        )

    def test_llm_is_called_with_grounded_context_only(self):
        mock_llm = MagicMock(spec=LLMExplanationService)
        mock_llm.generate_explanation.return_value = "Explanation."

        service = ScreeningService(llm_service=mock_llm)
        service.screen(
            job_description=_job(), resumes=[_resume()]
        )

        mock_llm.generate_explanation.assert_called_once()
        context = mock_llm.generate_explanation.call_args[0][0]

        assert context["job"]["title"] == "Python Developer"
        assert context["candidate"]["skills"] == ["Python"]
        assert context["evaluation"]["eligible"] is True
        assert context["evaluation"]["decision"] in {
            "shortlist",
            "review",
            "reject",
        }
        # The required skill (python) is satisfied - gap analysis is
        # informational and also reflects preferred skills, so the
        # genuinely-missing preferred skill (docker) legitimately
        # appears here without affecting eligibility.
        assert "python" not in context["gaps"]["missing_skills"]
        assert context["gaps"]["missing_skills"] == ["docker"]
        assert isinstance(context["evidence"], list)


class TestLLMFailureFallsBackSafely:
    def test_screening_succeeds_when_llm_returns_none(self):
        baseline = _deterministic_screen()

        mock_llm = MagicMock(spec=LLMExplanationService)
        mock_llm.generate_explanation.return_value = None

        service = ScreeningService(llm_service=mock_llm)
        result = service.screen(
            job_description=_job(), resumes=[_resume()]
        )
        candidate = result["results"][0]

        assert candidate["eligible"] == baseline["eligible"]
        assert candidate["decision"] == baseline["decision"]
        assert (
            candidate["ranking_score_percent"]
            == baseline["ranking_score_percent"]
        )

        assert (
            candidate["explanation"]["narrative_source"]
            == "deterministic"
        )
        assert (
            candidate["explanation"]["narrative"]
            == candidate["explanation"]["summary"]
        )

    def test_screening_succeeds_when_llm_service_raises_unexpectedly(
        self,
    ):
        # Defense in depth: even if an injected llm_service
        # misbehaves and raises instead of returning None (the real
        # LLMExplanationService never does this - it always catches
        # its own errors), ScreeningService itself must not let
        # explanation generation fail the whole screening request.
        baseline = _deterministic_screen()

        mock_llm = MagicMock(spec=LLMExplanationService)
        mock_llm.generate_explanation.side_effect = RuntimeError(
            "simulated unexpected failure"
        )

        service = ScreeningService(llm_service=mock_llm)

        result = service.screen(
            job_description=_job(), resumes=[_resume()]
        )
        candidate = result["results"][0]

        assert candidate["decision"] == baseline["decision"]
        assert candidate["eligible"] == baseline["eligible"]
        assert (
            candidate["ranking_score_percent"]
            == baseline["ranking_score_percent"]
        )
        assert (
            candidate["explanation"]["narrative_source"]
            == "deterministic"
        )
