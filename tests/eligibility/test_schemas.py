from app.filtering.eligibility import (
    check_skills,
    check_experience,
)

from app.filtering.schemas import EligibilityCriteria


def test_check_skills_all_match():

    criteria = EligibilityCriteria(
        required_skills=[
            "Java",
            "Python",
            "SQL"
        ]
    )

    result = check_skills(
        candidate_skills=[
            "Java",
            "Python",
            "SQL"
        ],
        criteria=criteria
    )

    assert result.eligible is True
    assert result.missing_skills == []

    assert set(result.matched_skills) == {
        "Java",
        "Python",
        "SQL"
    }


def test_check_skills_missing_skill():

    criteria = EligibilityCriteria(
        required_skills=[
            "Java",
            "Python",
            "SQL"
        ]
    )

    result = check_skills(
        candidate_skills=[
            "Java",
            "Python"
        ],
        criteria=criteria
    )

    assert result.eligible is False
    assert "SQL" in result.missing_skills

    assert set(result.matched_skills) == {
        "Java",
        "Python"
    }


def test_check_skills_case_insensitive():

    criteria = EligibilityCriteria(
        required_skills=[
            "Java",
            "Python"
        ]
    )

    result = check_skills(
        candidate_skills=[
            "java",
            "PYTHON"
        ],
        criteria=criteria
    )

    assert result.eligible is True
    assert result.missing_skills == []


def test_check_skills_extra_candidate_skill():

    criteria = EligibilityCriteria(
        required_skills=[
            "Java",
            "SQL"
        ]
    )

    result = check_skills(
        candidate_skills=[
            "Java",
            "SQL",
            "Python"
        ],
        criteria=criteria
    )

    assert result.eligible is True
    assert result.missing_skills == []

    assert set(result.matched_skills) == {
        "Java",
        "SQL"
    }

def test_check_experience_more_than_required():

    criteria = EligibilityCriteria(
        minimum_experience_months=24
    )

    result = check_experience(
        candidate_experience_months=36,
        criteria=criteria
    )

    assert result.eligible is True
    assert result.required_months == 24
    assert result.candidate_months == 36
    assert result.relevant_months == 36


def test_check_experience_exact_requirement():

    criteria = EligibilityCriteria(
        minimum_experience_months=24
    )

    result = check_experience(
        candidate_experience_months=24,
        criteria=criteria
    )

    assert result.eligible is True
    assert result.required_months == 24
    assert result.candidate_months == 24
    assert result.relevant_months == 24


def test_check_experience_less_than_required():

    criteria = EligibilityCriteria(
        minimum_experience_months=24
    )

    result = check_experience(
        candidate_experience_months=12,
        criteria=criteria
    )

    assert result.eligible is False
    assert result.required_months == 24
    assert result.candidate_months == 12
    assert result.relevant_months == 12