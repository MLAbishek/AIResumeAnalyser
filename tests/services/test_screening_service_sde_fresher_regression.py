"""
Targeted regression tests for the SDE-Fresher JD + Rahul Sharma
resume matching-quality failure, run through the real
ScreeningService.screen() path (no mocking of eligibility/ranking/
gap analysis/evidence - only the LLM is disabled, per the task's
explicit "do not modify the LLM integration" scope).

Covers:
    13. Preferred requirements not affecting eligibility
    14. Satisfied requirements not appearing in gaps
    15. Evidence uses actual resume data
    16. The exact Rahul Sharma + SDE-Fresher JD regression
"""

from app.core.schemas import (
    CanonicalEducation,
    CanonicalJob,
    CanonicalJobEducationRequirement,
    CanonicalJobExperienceRequirement,
    CanonicalResume,
    Education,
    Experience,
    JobDescription,
    Resume,
)
from app.ranking.education_scorer import score_education
from app.services.llm_service import LLMExplanationService
from app.services.screening_service import ScreeningService


SDE_FRESHER_JD = JobDescription(
    job_id="JD-SDE-FRESHER-001",
    title="Software Development Engineer (SDE) – Fresher",
    summary=(
        "We are looking for a Software Development Engineer (SDE) "
        "- Fresher to join our engineering team."
    ),
    required_skills=[
        "Strong programming skills in at least one language such "
        "as Java, Python, C++, or C#.",
        "Good understanding of Data Structures and Algorithms.",
        "Strong knowledge of Object-Oriented Programming.",
        "Understanding of DBMS, SQL, and relational databases.",
        "Familiarity with REST APIs and web application "
        "fundamentals.",
        "Understanding of software development and debugging "
        "practices.",
        "Familiarity with Git and version control.",
        "Strong problem-solving and analytical skills.",
    ],
    preferred_skills=[
        "Experience with Spring Boot, FastAPI, Django, or similar "
        "backend frameworks.",
        "Knowledge of PostgreSQL, MySQL, MongoDB, or Redis.",
        "Familiarity with Docker and Linux.",
        "Basic understanding of cloud platforms such as AWS, "
        "Azure, or GCP.",
        "Knowledge of unit testing and CI/CD.",
        "Exposure to system design and common software design "
        "patterns.",
        "Experience with personal, academic, internship, or "
        "open-source projects.",
    ],
    education=[
        "Bachelor's degree or currently pursuing a degree in "
        "Computer Science, Information Technology, Software "
        "Engineering, Artificial Intelligence, or related field.",
        "Fresh graduates and candidates with 0–1 year of "
        "experience are eligible.",
    ],
    required_experience_years=0.0,
    max_experience_years=1.0,
    raw_text="Software Development Engineer (SDE) - Fresher JD.",
)


RAHUL_SHARMA_RESUME = Resume(
    resume_id="RESUME-RAHUL-SHARMA-001",
    name="Rahul Sharma",
    summary=(
        "Software Development Engineer with a strong foundation "
        "in Data Structures, Algorithms, Object-Oriented "
        "Programming, and backend development."
    ),
    skills=[
        "Java",
        "Python",
        "C++",
        "SQL",
        "Data Structures & Algorithms",
        "OOP",
        "DBMS",
        "Operating Systems",
        "Computer Networks",
        "Spring Boot",
        "REST APIs",
        "FastAPI",
        "MySQL",
        "PostgreSQL",
        "MongoDB",
        "Git",
        "GitHub",
        "Docker",
        "Linux",
        "Postman",
        "Design Patterns",
        "Unit Testing",
    ],
    job_titles=["Software Development Intern"],
    experience=[
        Experience(
            role="Software Development Intern",
            company="XYZ Technologies",
            start_date="01/2026",
            end_date="06/2026",
        ),
    ],
    education=[
        Education(
            degree="B.Tech",
            institution="ABC Institute of Technology Bengaluru",
            field="Computer Science and Engineering",
            start_date="2023",
            end_date="2027",
        ),
    ],
    certifications=[
        "Java Programming and Software Engineering Fundamentals",
        "Data Structures and Algorithms",
    ],
    raw_text="Rahul Sharma resume - see fields above.",
)


def _screen():
    service = ScreeningService(
        llm_service=LLMExplanationService(enabled=False)
    )
    result = service.screen(
        job_description=SDE_FRESHER_JD,
        resumes=[RAHUL_SHARMA_RESUME],
    )
    return result["results"][0]


class TestExactSDEFresherRahulRegression:
    """16. The exact Rahul Sharma + SDE-Fresher JD regression."""

    def test_candidate_is_eligible(self):
        candidate = _screen()

        assert candidate["eligible"] is True

    def test_decision_is_not_reject(self):
        candidate = _screen()

        assert candidate["decision"] != "reject"

    def test_final_score_is_meaningfully_non_zero(self):
        candidate = _screen()

        assert candidate["ranking_score"] is not None
        assert candidate["ranking_score_percent"] > 0.0

    def test_experience_eligibility_is_satisfied(self):
        candidate = _screen()

        assert (
            candidate["eligibility"]["experience_match"]["eligible"]
            is True
        )
        assert (
            candidate["eligibility"]["experience_match"][
                "required_months"
            ]
            == 0
        )

    def test_education_eligibility_is_satisfied(self):
        candidate = _screen()

        assert (
            candidate["eligibility"]["education_certification"][
                "eligible"
            ]
            is True
        )

    def test_required_skill_groups_are_satisfied(self):
        candidate = _screen()

        assert (
            candidate["eligibility"]["skill_match"]["eligible"]
            is True
        )
        assert candidate["eligibility"]["skill_match"][
            "missing_skills"
        ] == []


class TestPreferredRequirementsDoNotAffectEligibility:
    """13. Preferred requirements must never make the candidate
    ineligible, even when entirely absent."""

    def test_candidate_missing_all_preferred_skills_stays_eligible(
        self,
    ):
        job = SDE_FRESHER_JD.model_copy(
            update={"job_id": "JD-SDE-FRESHER-NO-PREFERRED"}
        )
        resume = Resume(
            resume_id="RESUME-MINIMAL-001",
            name="Minimal Candidate",
            skills=["Java", "Data Structures & Algorithms", "OOP"],
            experience=[],
            education=[
                Education(
                    degree="B.Tech",
                    institution="Some University",
                    field="Computer Science",
                )
            ],
            raw_text="Minimal candidate resume.",
        )

        service = ScreeningService(
            llm_service=LLMExplanationService(enabled=False)
        )
        result = service.screen(
            job_description=job, resumes=[resume]
        )
        candidate = result["results"][0]

        # No Spring Boot/FastAPI/Django, no Postgres/MySQL/Mongo/
        # Redis, no Docker/Linux, no cloud, no CI/CD - none of that
        # may block eligibility.
        assert candidate["eligible"] is True


class TestGapAnalysisConsistency:
    """14. A requirement satisfied during eligibility/matching must
    not appear as a gap."""

    def test_matched_required_and_preferred_skills_are_not_gaps(
        self,
    ):
        candidate = _screen()

        matched = candidate["gap_analysis"]["matched_skills"]
        missing = candidate["gap_analysis"]["missing_skills"]

        for skill in (
            "java",
            "dsa",
            "oop",
            "dbms",
            "sql",
            "rest",
            "git",
            "spring boot",
            "postgresql",
            "docker",
        ):
            assert skill in matched, (
                f"expected {skill!r} to be matched, not missing"
            )
            assert skill not in missing, (
                f"expected {skill!r} to not appear as a gap"
            )


class TestEvidenceUsesActualResumeData:
    """15. Evidence must cite real candidate data, never fabricate
    it."""

    def test_evidence_cites_specific_matched_skills(self):
        candidate = _screen()

        claims = {item["claim"] for item in candidate["evidence"]}

        assert "Candidate has java." in claims
        assert "Candidate has spring boot." in claims
        assert "Candidate has dsa." in claims

    def test_no_evidence_for_skills_the_candidate_lacks(self):
        candidate = _screen()

        claims_text = " ".join(
            item["claim"] for item in candidate["evidence"]
        )

        # Candidate never mentions cloud platforms - evidence must
        # not claim otherwise.
        assert "aws" not in claims_text.lower()
        assert "azure" not in claims_text.lower()


class TestEducationScorerConsistencyWithEligibility:
    """Ranking's education_scorer must reach the same conclusion as
    eligibility's education_certification check for the same
    generic "currently pursuing a bachelor's degree" requirement."""

    def test_score_education_recognizes_currently_pursuing_btech(
        self,
    ):
        job = CanonicalJob(
            job_id="job-1",
            education=[
                CanonicalJobEducationRequirement(
                    degree=(
                        "bachelor's degree or currently pursuing "
                        "a degree in computer science, information "
                        "technology, software engineering, "
                        "artificial intelligence, or related field."
                    ),
                    required=True,
                )
            ],
            experience=CanonicalJobExperienceRequirement(),
        )

        resume = CanonicalResume(
            resume_id="resume-1",
            education=[
                CanonicalEducation(
                    degree="b.tech",
                    institution="abc institute of technology",
                    field_of_study=(
                        "computer science and engineering"
                    ),
                )
            ],
        )

        assert score_education(job, resume) == 1.0
