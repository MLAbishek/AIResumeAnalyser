"""
End-to-end regression test for the matching-quality investigation:
a real Frontend Developer Intern JD (prose-style requirement
sentences) screened against a real, substantially-overlapping
candidate resume was incorrectly producing eligible=False,
decision=reject, final_score=0, with nearly every requirement
listed as a gap.

This reproduces that exact JD/resume pair (trimmed to their real
content) through the live ScreeningService and asserts the corrected
outcome: eligible, non-zero score, matched skills present and not
listed as gaps, education recognized.
"""

from app.core.schemas import (
    Education,
    Experience,
    JobDescription,
    Project,
    Resume,
)
from app.services.llm_service import LLMExplanationService
from app.services.screening_service import ScreeningService


def _frontend_intern_job() -> JobDescription:
    return JobDescription(
        job_id="JD-FRONTEND-INTERN-001",
        title="Frontend Developer Intern",
        summary=(
            "We are looking for a Frontend Developer Intern to "
            "join our development team and contribute to building "
            "responsive, accessible, and user-friendly web "
            "applications."
        ),
        required_skills=[
            "Good understanding of HTML, CSS, and JavaScript.",
            "Familiarity with React.js or another modern frontend "
            "framework.",
            "Understanding of responsive web design.",
            "Basic knowledge of REST APIs and JSON.",
            "Familiarity with Git and GitHub.",
            "Understanding of JavaScript concepts such as ES6+, "
            "DOM manipulation, promises, and asynchronous "
            "programming.",
            "Good problem-solving and debugging skills.",
            "Experience with TypeScript.",
            "Familiarity with Tailwind CSS, Bootstrap, or similar "
            "UI frameworks.",
            "Experience with Vite or modern frontend build tools.",
            "Basic understanding of accessibility and web "
            "performance.",
            "Familiarity with component libraries such as "
            "shadcn/ui or Material UI.",
            "Experience integrating authentication or third-party "
            "APIs.",
            "Personal, academic, or open-source frontend projects.",
        ],
        education=[
            "Currently pursuing or recently completed a "
            "Bachelor's degree in Computer Science, Information "
            "Technology, Artificial",
            "Intelligence, or a related field., Students and "
            "fresh graduates are encouraged to apply.",
        ],
        raw_text=(
            "Frontend Developer Intern - see required_skills/"
            "education for the real extracted requirements."
        ),
    )


def _arjun_kumar_resume() -> Resume:
    return Resume(
        resume_id="RESUME-ARJUN-KUMAR-001",
        name="Arjun Kumar",
        skills=[
            "JavaScript",
            "TypeScript",
            "HTML5",
            "CSS3",
            "React.js",
            "React Router",
            "Tailwind CSS",
            "Responsive Design",
            "React Hooks",
            "Context API",
            "REST APIs",
            "JSON",
            "Axios",
            "Git",
            "GitHub",
            "Vite",
            "VS Code",
            "Figma",
            "MySQL",
            "Firebase",
            "Authentication",
            "Form Validation",
            "Browser DevTools",
        ],
        job_titles=["Frontend Developer Intern"],
        experience=[
            Experience(
                role="Frontend Developer Intern",
                company="Prior Experience",
                start_date="2026-03-19",
                end_date="2026-08-19",
            ),
        ],
        education=[
            Education(
                degree="B.Tech",
                institution="ABC Institute of Technology, Chennai",
                field="Computer Science / Information Technology, "
                "CGPA: 8.7/10",
            ),
        ],
        projects=[
            Project(name="E-Commerce Web Application"),
            Project(name="Task Management Dashboard"),
            Project(name="Portfolio Website"),
        ],
        raw_text="Arjun Kumar - Frontend Developer Intern resume.",
    )


class TestFrontendInternRealCaseRegression:
    def test_candidate_is_eligible(self):
        service = ScreeningService(
            llm_service=LLMExplanationService(enabled=False)
        )

        result = service.screen(
            job_description=_frontend_intern_job(),
            resumes=[_arjun_kumar_resume()],
        )
        candidate = result["results"][0]

        assert candidate["eligible"] is True

    def test_decision_is_not_reject(self):
        service = ScreeningService(
            llm_service=LLMExplanationService(enabled=False)
        )

        result = service.screen(
            job_description=_frontend_intern_job(),
            resumes=[_arjun_kumar_resume()],
        )
        candidate = result["results"][0]

        assert candidate["decision"] != "reject"

    def test_final_score_is_meaningfully_non_zero(self):
        service = ScreeningService(
            llm_service=LLMExplanationService(enabled=False)
        )

        result = service.screen(
            job_description=_frontend_intern_job(),
            resumes=[_arjun_kumar_resume()],
        )
        candidate = result["results"][0]

        assert candidate["ranking_score"] is not None
        assert candidate["ranking_score_percent"] > 50.0

    def test_education_is_recognized_as_satisfied(self):
        service = ScreeningService(
            llm_service=LLMExplanationService(enabled=False)
        )

        result = service.screen(
            job_description=_frontend_intern_job(),
            resumes=[_arjun_kumar_resume()],
        )
        candidate = result["results"][0]

        assert (
            candidate["eligibility"]["education_certification"][
                "eligible"
            ]
            is True
        )

    def test_matched_skills_do_not_appear_in_gaps(self):
        service = ScreeningService(
            llm_service=LLMExplanationService(enabled=False)
        )

        result = service.screen(
            job_description=_frontend_intern_job(),
            resumes=[_arjun_kumar_resume()],
        )
        candidate = result["results"][0]

        missing = candidate["gap_analysis"]["missing_skills"]
        matched = candidate["gap_analysis"]["matched_skills"]

        for skill in (
            "typescript",
            "react",
            "tailwind css",
            "git",
            "github",
            "vite",
            "javascript",
            "html",
            "css",
        ):
            assert skill in matched, (
                f"expected {skill!r} to be matched"
            )
            assert skill not in missing, (
                f"expected {skill!r} to not be a gap"
            )

    def test_evidence_reflects_real_matched_skills(self):
        service = ScreeningService(
            llm_service=LLMExplanationService(enabled=False)
        )

        result = service.screen(
            job_description=_frontend_intern_job(),
            resumes=[_arjun_kumar_resume()],
        )
        candidate = result["results"][0]

        evidence_claims = {
            item["claim"] for item in candidate["evidence"]
        }

        assert "Candidate has typescript." in evidence_claims
        assert "Candidate has react." in evidence_claims

    def test_no_certification_requirement_does_not_block_eligibility(
        self,
    ):
        service = ScreeningService(
            llm_service=LLMExplanationService(enabled=False)
        )

        result = service.screen(
            job_description=_frontend_intern_job(),
            resumes=[_arjun_kumar_resume()],
        )
        candidate = result["results"][0]

        assert (
            candidate["eligibility"]["education_certification"][
                "eligible"
            ]
            is True
        )

    def test_deterministic_result_unaffected_by_llm_enabled_flag(
        self,
    ):
        # The matching result must be identical whether or not the
        # LLM is enabled - the LLM only adds a narrative field.
        disabled_service = ScreeningService(
            llm_service=LLMExplanationService(enabled=False)
        )
        disabled_result = disabled_service.screen(
            job_description=_frontend_intern_job(),
            resumes=[_arjun_kumar_resume()],
        )["results"][0]

        from unittest.mock import MagicMock

        mock_llm = MagicMock(spec=LLMExplanationService)
        mock_llm.generate_explanation.return_value = (
            "A narrative explanation."
        )
        enabled_service = ScreeningService(llm_service=mock_llm)
        enabled_result = enabled_service.screen(
            job_description=_frontend_intern_job(),
            resumes=[_arjun_kumar_resume()],
        )["results"][0]

        assert (
            disabled_result["eligible"] == enabled_result["eligible"]
        )
        assert (
            disabled_result["decision"] == enabled_result["decision"]
        )
        assert (
            disabled_result["ranking_score_percent"]
            == enabled_result["ranking_score_percent"]
        )
