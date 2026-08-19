"""
Targeted regression tests for alternative ("X, Y, or Z") vs mandatory
("X and Y") requirement semantics, and the vocabulary/normalization
gaps discovered via the real SDE-Fresher JD + Rahul Sharma resume
failure: OR-groups were previously flattened into independently-
mandatory atoms, and common concepts (programming languages, DSA,
OOP, DBMS, backend frameworks) were missing from the vocabulary
entirely, causing sentences to fall through as one opaque,
unmatchable string.
"""

from app.filtering.eligibility import check_skills
from app.filtering.schemas import EligibilityCriteria
from app.normalization.normalizer_utils import (
    split_requirement_group,
)
from app.normalization.skill_normalizer import SkillNormalizer


class TestORLanguageRequirement:
    """1. OR language requirement: Java OR Python OR C++ OR C#."""

    def test_extraction_produces_one_alternatives_group(self):
        normalizer = SkillNormalizer()

        result = normalizer.extract_requirement_groups(
            "Strong programming skills in at least one language "
            "such as Java, Python, C++, or C#."
        )

        assert result == ["java|python|c++|c#"]

    def test_candidate_with_only_one_alternative_is_eligible(self):
        criteria = EligibilityCriteria(
            required_skills=["java|python|c++|c#"]
        )

        result = check_skills(
            candidate_skills=["Java"], criteria=criteria
        )

        assert result.eligible is True
        assert result.missing_skills == []

    def test_candidate_with_none_of_the_alternatives_is_ineligible(
        self,
    ):
        criteria = EligibilityCriteria(
            required_skills=["java|python|c++|c#"]
        )

        result = check_skills(
            candidate_skills=["Ruby"], criteria=criteria
        )

        assert result.eligible is False
        assert result.missing_skills == [
            "java or python or c++ or c#"
        ]


class TestANDRequirement:
    """2. AND requirement: Java AND Spring Boot (both mandatory)."""

    def test_extraction_produces_independent_atoms(self):
        normalizer = SkillNormalizer()

        result = normalizer.extract_requirement_groups(
            "Strong knowledge of Java and Spring Boot."
        )

        assert set(result) == {"java", "spring boot"}

    def test_candidate_missing_one_of_two_is_ineligible(self):
        criteria = EligibilityCriteria(
            required_skills=["java", "spring boot"]
        )

        result = check_skills(
            candidate_skills=["Java"], criteria=criteria
        )

        assert result.eligible is False
        assert "spring boot" in result.missing_skills

    def test_candidate_with_both_is_eligible(self):
        criteria = EligibilityCriteria(
            required_skills=["java", "spring boot"]
        )

        result = check_skills(
            candidate_skills=["Java", "Spring Boot"],
            criteria=criteria,
        )

        assert result.eligible is True


class TestORFrameworkRequirement:
    """3. OR framework requirement: Spring Boot OR FastAPI OR Django."""

    def test_extraction_produces_one_alternatives_group(self):
        normalizer = SkillNormalizer()

        result = normalizer.extract_requirement_groups(
            "Experience with Spring Boot, FastAPI, Django, or "
            "similar backend frameworks."
        )

        assert result == ["spring boot|fastapi|django"]

    def test_candidate_with_fastapi_only_satisfies_the_group(self):
        criteria = EligibilityCriteria(
            required_skills=["spring boot|fastapi|django"]
        )

        result = check_skills(
            candidate_skills=["FastAPI"], criteria=criteria
        )

        assert result.eligible is True
        assert result.matched_skills == ["fastapi"]


class TestORDatabaseRequirement:
    """4. OR database requirement: PostgreSQL OR MySQL OR MongoDB OR Redis."""

    def test_extraction_produces_one_alternatives_group(self):
        normalizer = SkillNormalizer()

        result = normalizer.extract_requirement_groups(
            "Knowledge of PostgreSQL, MySQL, MongoDB, or Redis."
        )

        assert result == ["postgresql|mysql|mongodb|redis"]

    def test_candidate_with_two_of_four_still_satisfies(self):
        criteria = EligibilityCriteria(
            required_skills=["postgresql|mysql|mongodb|redis"]
        )

        result = check_skills(
            candidate_skills=["MySQL", "PostgreSQL"],
            criteria=criteria,
        )

        assert result.eligible is True


class TestConceptNormalization:
    """5-9. DSA / OOP / DBMS+SQL / REST / Git normalization."""

    def test_dsa_normalization(self):
        normalizer = SkillNormalizer()

        assert normalizer.extract_requirement_concepts(
            "Good understanding of Data Structures and Algorithms."
        ) == ["dsa"]

        assert (
            normalizer.normalize("Data Structures & Algorithms")
            == "dsa"
        )

    def test_oop_normalization(self):
        normalizer = SkillNormalizer()

        assert normalizer.extract_requirement_concepts(
            "Strong knowledge of Object-Oriented Programming."
        ) == ["oop"]

        assert normalizer.normalize("OOP") == "oop"

    def test_dbms_and_sql_normalization(self):
        normalizer = SkillNormalizer()

        result = normalizer.extract_requirement_concepts(
            "Understanding of DBMS, SQL, and relational databases."
        )

        assert "dbms" in result
        assert "sql" in result
        assert "relational databases" in result

    def test_rest_api_normalization(self):
        normalizer = SkillNormalizer()

        result = normalizer.extract_requirement_concepts(
            "Familiarity with REST APIs and web application "
            "fundamentals."
        )

        assert "rest" in result

    def test_git_and_version_control_normalization(self):
        normalizer = SkillNormalizer()

        assert normalizer.normalize("Git") == "git"
        # "version control" is treated as synonymous with Git - the
        # dominant real-world tool - rather than a separate,
        # unverifiable concept.
        assert normalizer.normalize("version control") == "git"

        result = normalizer.extract_requirement_concepts(
            "Familiarity with Git and version control."
        )

        assert result == ["git"]


class TestSoftProblemSolvingRequirement:
    """10. Soft problem-solving requirement must not become a hard
    technology gate."""

    def test_problem_solving_sentence_has_no_known_concept(self):
        normalizer = SkillNormalizer()

        # No concrete technology vocabulary term is found in this
        # sentence - it is a soft capability, not a technology.
        result = normalizer.extract_requirement_concepts(
            "Strong problem-solving and analytical skills.",
            keep_unmatched_fallback=False,
        )

        assert result == []

    def test_problem_solving_is_dropped_from_hard_requirements(
        self,
    ):
        normalizer = SkillNormalizer()

        result = normalizer.extract_requirement_groups(
            "Strong problem-solving and analytical skills.",
            keep_unmatched_fallback=False,
        )

        assert result == []


class TestSplitRequirementGroupHelper:
    def test_plain_entry_returns_single_item_list(self):
        assert split_requirement_group("python") == ["python"]

    def test_grouped_entry_splits_on_pipe(self):
        assert split_requirement_group("java|python|c++") == [
            "java",
            "python",
            "c++",
        ]
