"""
Targeted regression tests for EducationNormalizer: the JD stated a
generic "Bachelor's degree in Computer Science, Information
Technology, Artificial Intelligence, or a related field" while the
candidate had a specific "B.Tech" in "Computer Science / Information
Technology" - raw substring comparison never recognized these as the
same requirement.
"""

from app.normalization.education_normalizer import EducationNormalizer


class TestGenericLevelRecognizesSpecificTypes:
    def test_generic_bachelor_requirement_matches_btech(self):
        normalizer = EducationNormalizer()

        assert normalizer.requirement_satisfied(
            requirement_degree="Bachelor's degree",
            requirement_field=None,
            candidate_degree="B.Tech",
        )

    def test_generic_bachelor_requirement_matches_bsc(self):
        normalizer = EducationNormalizer()

        assert normalizer.requirement_satisfied(
            requirement_degree="Bachelor's degree",
            requirement_field=None,
            candidate_degree="B.Sc",
        )

    def test_generic_master_requirement_matches_mtech(self):
        normalizer = EducationNormalizer()

        assert normalizer.requirement_satisfied(
            requirement_degree="Master's degree",
            requirement_field=None,
            candidate_degree="M.Tech",
        )

    def test_generic_bachelor_requirement_does_not_match_masters(
        self,
    ):
        normalizer = EducationNormalizer()

        assert not normalizer.requirement_satisfied(
            requirement_degree="Bachelor's degree",
            requirement_field=None,
            candidate_degree="M.Tech",
        )


class TestSpecificTypeRequirementsStayStrict:
    def test_specific_btech_requirement_rejects_bsc(self):
        # A JD asking for one specific degree type must NOT be
        # satisfied by a different specific type - only a generic
        # requirement should broaden to any degree at that level.
        normalizer = EducationNormalizer()

        assert not normalizer.requirement_satisfied(
            requirement_degree="B.Tech",
            requirement_field=None,
            candidate_degree="B.Sc",
        )

    def test_specific_btech_requirement_matches_btech(self):
        normalizer = EducationNormalizer()

        assert normalizer.requirement_satisfied(
            requirement_degree="B.Tech",
            requirement_field=None,
            candidate_degree="B.Tech",
        )


class TestFieldKeywordOverlap:
    def test_field_overlap_recognizes_shared_keyword(self):
        normalizer = EducationNormalizer()

        assert normalizer.requirement_satisfied(
            requirement_degree=None,
            requirement_field="Computer Science",
            candidate_degree="B.Tech",
            candidate_field=(
                "Computer Science / Information Technology"
            ),
        )

    def test_field_overlap_rejects_unrelated_field(self):
        normalizer = EducationNormalizer()

        assert not normalizer.requirement_satisfied(
            requirement_degree=None,
            requirement_field="Computer Science",
            candidate_degree="B.Tech",
            candidate_field="Mechanical Engineering",
        )

    def test_free_text_jd_requirement_matches_real_case(self):
        # Reproduces the real JD's messy, prose-extracted education
        # requirement fragment (degree and field intermingled in one
        # sentence, no separate structured field).
        normalizer = EducationNormalizer()

        requirement_text = (
            "Currently pursuing or recently completed a "
            "Bachelor's degree in Computer Science, Information "
            "Technology, Artificial Intelligence, or a related "
            "field."
        )

        assert normalizer.requirement_satisfied(
            requirement_degree=requirement_text,
            requirement_field=None,
            candidate_degree="B.Tech",
            candidate_field=(
                "Computer Science / Information Technology, "
                "CGPA: 8.7/10"
            ),
        )

    def test_free_text_jd_requirement_rejects_unrelated_candidate(
        self,
    ):
        normalizer = EducationNormalizer()

        requirement_text = (
            "Currently pursuing or recently completed a "
            "Bachelor's degree in Computer Science, Information "
            "Technology, Artificial Intelligence, or a related "
            "field."
        )

        assert not normalizer.requirement_satisfied(
            requirement_degree=requirement_text,
            requirement_field=None,
            candidate_degree="B.Com",
            candidate_field="Accounting and Finance",
        )


class TestCurrentlyPursuingDegree:
    """12. "Currently pursuing" a bachelor's degree must be
    recognized as satisfying the requirement - a fresher/current
    student is not disqualified just for not having graduated yet.
    """

    def test_currently_pursuing_candidate_satisfies_requirement(
        self,
    ):
        normalizer = EducationNormalizer()

        requirement_text = (
            "Bachelor's degree or currently pursuing a degree in "
            "Computer Science, Information Technology, Software "
            "Engineering, Artificial Intelligence, or related "
            "field."
        )

        assert normalizer.requirement_satisfied(
            requirement_degree=requirement_text,
            requirement_field=None,
            candidate_degree="B.Tech",
            candidate_field=(
                "Computer Science and Engineering, "
                "CGPA: 8.8/10 2023 - 2027"
            ),
        )
