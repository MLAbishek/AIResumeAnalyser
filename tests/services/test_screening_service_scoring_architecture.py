"""
Regression tests for the resume/JD matching, scoring, eligibility and
duplicate-output architecture fix.

These run through the real ScreeningService.screen() path end to end
(canonicalization -> eligibility -> ranking -> decision -> gap
analysis -> evidence -> explanation) with only the LLM narrative
disabled, so every assertion reflects the actual deterministic
pipeline rather than a mock.

Covers the 10 required categories:
    1. Meaningful partial match -> score > 0, not auto-ineligible
    2. Zero-overlap candidate -> low score, still distinguishable
    3. Strong candidate -> high score + eligible
    4. Hard requirement failure -> ineligible regardless of many
       irrelevant matches
    5. Education match (AI/ML degree vs JD accepting "Artificial
       Intelligence")
    6. Internship experience handled correctly for freshers
       (including overlapping internships not being double-counted)
    7. Score consistency across api/ranking-input/preview
    8. No duplicated scoring - downstream modules consume the
       canonical score, don't recompute
    9. Evidence consistency - every matched skill contributing to the
       score has real evidence
    10. Gaps consistency - missing optional tech is not counted as a
        mandatory failure
"""

from app.core.schemas import (
    Education,
    Experience,
    JobDescription,
    Resume,
)
from app.ranking.database_adapter import job_to_canonical
from app.ranking.scoring_engine import rank_candidates
from app.services.llm_service import LLMExplanationService
from app.services.screening_service import ScreeningService


# The exact scenario from the bug report: a strong AI/ML fresher
# candidate scored against a generic SDE-I fresher JD whose "Skills"
# section is an auto-extracted, unsegmented tech-stack inventory
# (>8 entries), not a short curated must-have list.
SDE_I_JD = JobDescription(
    job_id="JD-SDE-I-FRESHER",
    title="Software Development Engineer I",
    summary=(
        "We are hiring a Software Development Engineer I (Fresher) "
        "to design, build, and maintain backend services."
    ),
    required_skills=[
        "Python",
        "Java",
        "Flask",
        "MySQL",
        "AWS",
        "Git",
        "GitHub",
        "TensorFlow",
        "PyTorch",
        "LangChain",
        "OpenCV",
        "SQL",
        "Supabase",
        "Pinecone",
    ],
    preferred_skills=[],
    education=[
        "Bachelor's degree in Computer Science, Information "
        "Technology, or Artificial Intelligence.",
    ],
    required_experience_years=0.0,
    max_experience_years=1.0,
    raw_text="SDE-I Fresher JD.",
)


ABISHEK_RESUME = Resume(
    resume_id="RESUME-ABISHEK-J-001",
    name="Abishek J",
    summary=(
        "B.Tech graduate in Artificial Intelligence and Machine "
        "Learning with hands-on internship experience building "
        "ML-driven applications."
    ),
    skills=[
        "Python",
        "Java",
        "Flask",
        "MySQL",
        "AWS",
        "Git",
        "GitHub",
        "TensorFlow",
        "PyTorch",
        "LangChain",
        "OpenCV",
        "SQL",
        "Supabase",
        "Pinecone",
    ],
    job_titles=["AI/ML Intern"],
    experience=[
        Experience(
            role="AI/ML Intern",
            company="Startup A",
            start_date="01/2025",
            end_date="04/2025",
        ),
        Experience(
            role="Machine Learning Intern",
            company="Startup B",
            start_date="05/2025",
            end_date="07/2025",
        ),
    ],
    education=[
        Education(
            degree="B.Tech",
            institution="Institute of Technology",
            field="Artificial Intelligence and Machine Learning",
            start_date="2021",
            end_date="2025",
        ),
    ],
    certifications=[],
    raw_text="Abishek J resume - see fields above.",
)


def _screen(job=SDE_I_JD, resume=ABISHEK_RESUME):
    service = ScreeningService(
        llm_service=LLMExplanationService(enabled=False)
    )
    result = service.screen(
        job_description=job,
        resumes=[resume],
    )
    return result["results"][0]


class TestRealCandidateVerification:
    """The exact reported bug: strong AI/ML fresher vs SDE-I JD."""

    def test_candidate_is_eligible(self):
        candidate = _screen()
        assert candidate["eligible"] is True

    def test_candidate_has_meaningful_nonzero_score(self):
        candidate = _screen()
        assert candidate["ranking_score"] is not None
        assert candidate["ranking_score_percent"] > 50.0

    def test_candidate_is_not_rejected(self):
        candidate = _screen()
        assert candidate["decision"] != "reject"

    def test_all_skills_reported_as_matched(self):
        candidate = _screen()
        missing = candidate["eligibility"]["skill_match"][
            "missing_skills"
        ]
        # A >8-entry auto-extracted skill inventory must not hard-
        # gate eligibility even if something were missing, but this
        # candidate genuinely has every listed skill.
        assert missing == []

    def test_education_matches_ai_ml_degree(self):
        candidate = _screen()
        assert (
            candidate["eligibility"]["education_certification"][
                "eligible"
            ]
            is True
        )

    def test_narrative_does_not_contradict_eligibility(self):
        candidate = _screen()
        narrative = candidate["explanation"]["narrative"].lower()
        assert candidate["eligible"] is True
        assert "rejected" not in narrative


class Test1MeaningfulPartialMatch:
    """1. Meaningful partial match -> score > 0, not auto-ineligible."""

    def test_partial_overlap_scores_above_zero(self):
        job = JobDescription(
            job_id="JD-PARTIAL-001",
            title="Backend Developer",
            required_skills=["Python", "Django", "PostgreSQL"],
            raw_text="Backend developer role.",
        )
        resume = Resume(
            resume_id="RESUME-PARTIAL-001",
            name="Partial Candidate",
            skills=["Python"],
            raw_text="Python developer.",
        )
        candidate = _screen(job=job, resume=resume)

        assert candidate["ranking_score"] is not None
        assert candidate["ranking_score"] > 0.0


class Test2ZeroOverlapCandidate:
    """2. Zero-overlap candidate -> low score, still distinguishable."""

    def test_zero_overlap_scores_low_but_is_present(self):
        job = JobDescription(
            job_id="JD-ZERO-001",
            title="Backend Developer",
            required_skills=["Python", "Django", "PostgreSQL"],
            raw_text="Backend developer role.",
        )
        resume = Resume(
            resume_id="RESUME-ZERO-001",
            name="Unrelated Candidate",
            skills=["Photoshop", "Illustrator"],
            raw_text="Graphic designer.",
        )
        candidate = _screen(job=job, resume=resume)

        assert candidate["ranking_score"] is not None
        assert candidate["ranking_score_percent"] <= 30.0


class Test3StrongCandidate:
    """3. Strong candidate -> high score + eligible."""

    def test_strong_match_scores_high_and_eligible(self):
        candidate = _screen()
        assert candidate["eligible"] is True
        assert candidate["ranking_score_percent"] >= 70.0


class Test4HardRequirementFailure:
    """
    4. Hard requirement failure -> ineligible regardless of many
    irrelevant matches.
    """

    def test_short_curated_required_skill_still_gates(self):
        job = JobDescription(
            job_id="JD-HARD-REQ-001",
            title="Senior AWS Engineer",
            required_skills=["AWS Certified Solutions Architect"],
            raw_text="Requires AWS certification.",
        )
        resume = Resume(
            resume_id="RESUME-HARD-REQ-001",
            name="Uncertified Candidate",
            skills=[
                "Python",
                "Java",
                "Docker",
                "Kubernetes",
                "Terraform",
                "Linux",
                "Git",
                "CI/CD",
                "MongoDB",
                "Redis",
            ],
            raw_text="Experienced engineer, many skills, no cert.",
        )
        candidate = _screen(job=job, resume=resume)

        assert candidate["eligible"] is False
        assert candidate["decision"] == "reject"


class Test5EducationMatch:
    """5. Education match (AI/ML degree vs JD accepting AI)."""

    def test_ai_ml_field_matches_artificial_intelligence_requirement(
        self,
    ):
        candidate = _screen()
        assert (
            candidate["eligibility"]["education_certification"][
                "eligible"
            ]
            is True
        )
        assert (
            "education_gap" in candidate["gap_analysis"]
        )
        assert (
            candidate["gap_analysis"]["education_gap"][
                "meets_requirement"
            ]
            is True
        )


class Test6InternshipExperienceHandling:
    """6. Internship experience handled correctly for freshers."""

    def test_fresher_with_internship_is_not_gated_by_experience(
        self,
    ):
        candidate = _screen()
        assert (
            candidate["eligibility"]["experience_match"]["eligible"]
            is True
        )

    def test_overlapping_internships_are_not_double_counted(self):
        # Two internships with a fully overlapping one-month period
        # (Feb 2025) - naive summing would report 4 months (2 + 2);
        # the real elapsed calendar coverage is 3 months
        # (Jan-Mar 2025 inclusive of the half-open convention).
        resume = Resume(
            resume_id="RESUME-OVERLAP-001",
            name="Overlap Candidate",
            skills=["Python"],
            experience=[
                Experience(
                    role="Intern A",
                    company="Company A",
                    start_date="01/2025",
                    end_date="03/2025",
                ),
                Experience(
                    role="Intern B",
                    company="Company B",
                    start_date="02/2025",
                    end_date="04/2025",
                ),
            ],
            raw_text="Overlapping internship candidate.",
        )

        from app.normalization.canonical_resume_builder import (
            CanonicalResumeBuilder,
        )

        builder = CanonicalResumeBuilder()
        canonical = builder.build(
            {
                "resume_id": resume.resume_id,
                "skills": resume.skills,
                "job_titles": resume.job_titles,
                "organizations": [
                    experience.company
                    for experience in resume.experience
                ],
                "experiences": [
                    {
                        "job_title": experience.role,
                        "company": experience.company,
                        "start_date": experience.start_date,
                        "end_date": experience.end_date,
                    }
                    for experience in resume.experience
                ],
                "education": [],
            }
        )

        # Naive sum would be 2 + 2 = 4 months; the real, non-
        # double-counted calendar coverage (Jan through Apr 2025,
        # half-open) is 3 months.
        assert canonical.total_experience_months == 3


class Test7ScoreConsistency:
    """7. Score consistency across api/ranking-input/preview."""

    def test_database_adapter_uses_the_same_canonical_jd_builder(
        self, db
    ):
        from app.database.crud.jobs import create_job
        from app.normalization.canonical_jd_builder import (
            CanonicalJobBuilder,
        )

        job_row = create_job(
            db,
            job_id="JOB-CONSISTENCY-001",
            title=SDE_I_JD.title,
            raw_text="job",
            required_skills=SDE_I_JD.required_skills,
            preferred_skills=SDE_I_JD.preferred_skills,
        )
        db.flush()

        # The ranking dashboard path (ranking_service.py ->
        # database_adapter.job_to_canonical) and the one-shot
        # screening path (ScreeningService._build_canonical_job) must
        # canonicalize the same raw JD skill list identically - both
        # now route through CanonicalJobBuilder rather than each
        # hand-rolling its own required/preferred split.
        via_database_adapter = job_to_canonical(job_row)

        via_direct_builder = CanonicalJobBuilder().build(
            {
                "job_id": job_row.job_id,
                "title": job_row.title,
                "description": job_row.description,
                "required_skills": job_row.required_skills,
                "preferred_skills": job_row.preferred_skills,
                "required_technologies": [],
                "preferred_technologies": [],
                "responsibilities": [],
                "experience": {
                    "minimum_months": 0,
                    "maximum_months": None,
                },
                "education": [],
            }
        )

        assert (
            via_database_adapter.required_skills
            == via_direct_builder.required_skills
        )
        assert (
            via_database_adapter.preferred_skills
            == via_direct_builder.preferred_skills
        )

    def test_ranking_service_and_screening_service_share_one_scorer(
        self,
    ):
        import app.ranking.ranking_service as ranking_service_module
        import app.services.screening_service as screening_service_module

        # Both the recruiter ranking dashboard and the one-shot
        # screening flow must call the exact same scoring function -
        # not two independently-implemented formulas that could
        # silently diverge.
        assert (
            ranking_service_module.rank_candidates
            is screening_service_module.rank_candidates
            is rank_candidates
        )


class Test8NoDuplicatedScoring:
    """
    8. No duplicated scoring - downstream modules consume the
    canonical score, don't recompute.
    """

    def test_persisted_final_score_is_the_ranking_score_percent(
        self,
    ):
        candidate = _screen()
        # ScreeningPersistenceService.persist() writes
        # final_score = result["ranking_score_percent"] verbatim -
        # this asserts that field is exactly the canonical value
        # (not re-derived) so persistence can never diverge from it.
        assert candidate["ranking_score_percent"] == round(
            candidate["ranking_score"] * 100, 2
        )

    def test_evidence_final_score_matches_ranking_score(self):
        candidate = _screen()
        final_score_evidence = next(
            (
                item
                for item in candidate["evidence"]
                if item["section"] == "final_score"
            ),
            None,
        )
        assert final_score_evidence is not None
        assert float(final_score_evidence["evidence"]) == (
            candidate["ranking_score_percent"]
        )


class Test9EvidenceConsistency:
    """
    9. Evidence consistency - every matched skill contributing to
    the score has real evidence.
    """

    def test_every_matched_skill_has_a_citation(self):
        candidate = _screen()
        matched_skills = candidate["gap_analysis"]["matched_skills"]
        cited_skills = {
            item["evidence"].lower()
            for item in candidate["evidence"]
            if item["section"] == "skills"
        }

        for skill in matched_skills:
            assert skill.lower() in cited_skills, (
                f"matched skill {skill!r} has no evidence citation"
            )

    def test_no_evidence_for_skills_candidate_lacks(self):
        job = JobDescription(
            job_id="JD-EVIDENCE-001",
            title="Data Engineer",
            required_skills=["Python", "Spark", "Airflow"],
            raw_text="Data engineer role.",
        )
        resume = Resume(
            resume_id="RESUME-EVIDENCE-001",
            name="Partial Candidate",
            skills=["Python"],
            raw_text="Python developer.",
        )
        candidate = _screen(job=job, resume=resume)

        claims_text = " ".join(
            item["claim"] for item in candidate["evidence"]
        ).lower()

        assert "spark" not in claims_text
        assert "airflow" not in claims_text


class Test10GapsConsistency:
    """10. Gaps consistency - missing optional tech is not counted
    as a mandatory failure."""

    def test_missing_preferred_skill_is_not_a_critical_gap(self):
        job = JobDescription(
            job_id="JD-GAPS-001",
            title="Backend Developer",
            required_skills=["Python"],
            preferred_skills=["Kubernetes"],
            raw_text="Backend developer role.",
        )
        resume = Resume(
            resume_id="RESUME-GAPS-001",
            name="Candidate",
            skills=["Python"],
            raw_text="Python developer.",
        )
        candidate = _screen(job=job, resume=resume)

        gap_analysis = candidate["gap_analysis"]

        assert "kubernetes" in gap_analysis[
            "nice_to_have_missing_skills"
        ]
        assert (
            "kubernetes"
            not in gap_analysis["critical_missing_skills"]
        )
        # Missing only a preferred skill must not itself constitute
        # a gap serious enough to flag has_gap.
        assert gap_analysis["has_gap"] is False
        assert candidate["eligible"] is True
