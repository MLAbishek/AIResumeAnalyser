from app.filtering.eligibility import (
    check_skills,
    check_experience,
    check_education_certification,
    check_location,
    check_location_authorization,
    check_eligibility,
)

from app.filtering.schemas import (
    EligibilityCriteria,
    CanonicalJobEducationRequirement,
)


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


def test_check_education_and_certification_match():

    criteria = EligibilityCriteria(
        required_education=[
            CanonicalJobEducationRequirement(
                degree="B.Tech",
                required=True
            )
        ],
        required_certifications=[
            "AWS Certified Developer"
        ]
    )

    result = check_education_certification(
        candidate_education="B.Tech Computer Science",
        candidate_certifications=[
            "AWS Certified Developer"
        ],
        criteria=criteria
    )

    assert result.eligible is True


def test_check_education_missing():

    criteria = EligibilityCriteria(
        required_education=[
            CanonicalJobEducationRequirement(
                degree="B.Tech",
                required=True
            )
        ]
    )

    result = check_education_certification(
        candidate_education="B.Sc Computer Science",
        candidate_certifications=[],
        criteria=criteria
    )

    assert result.eligible is False


def test_check_education_case_insensitive():

    criteria = EligibilityCriteria(
        required_education=[
            CanonicalJobEducationRequirement(
                degree="B.Tech",
                required=True
            )
        ]
    )

    result = check_education_certification(
        candidate_education="b.tech computer science",
        candidate_certifications=[],
        criteria=criteria
    )

    assert result.eligible is True


def test_check_education_degree_and_field_match():

    criteria = EligibilityCriteria(
        required_education=[
            CanonicalJobEducationRequirement(
                degree="B.Tech",
                field_of_study="Computer Science",
                required=True
            )
        ]
    )

    result = check_education_certification(
        candidate_education="B.Tech Computer Science",
        candidate_certifications=[],
        criteria=criteria
    )

    assert result.eligible is True


def test_check_education_field_missing():

    criteria = EligibilityCriteria(
        required_education=[
            CanonicalJobEducationRequirement(
                degree="B.Tech",
                field_of_study="Computer Science",
                required=True
            )
        ]
    )

    result = check_education_certification(
        candidate_education="B.Tech Mechanical Engineering",
        candidate_certifications=[],
        criteria=criteria
    )

    assert result.eligible is False


def test_check_certification_match():

    criteria = EligibilityCriteria(
        required_certifications=[
            "AWS Certified Developer"
        ]
    )

    result = check_education_certification(
        candidate_education="B.Tech",
        candidate_certifications=[
            "AWS Certified Developer"
        ],
        criteria=criteria
    )

    assert result.eligible is True


def test_check_certification_missing():

    criteria = EligibilityCriteria(
        required_certifications=[
            "AWS Certified Developer"
        ]
    )

    result = check_education_certification(
        candidate_education="B.Tech",
        candidate_certifications=[],
        criteria=criteria
    )

    assert result.eligible is False


def test_check_certification_case_insensitive():

    criteria = EligibilityCriteria(
        required_certifications=[
            "AWS Certified Developer"
        ]
    )

    result = check_education_certification(
        candidate_education="B.Tech",
        candidate_certifications=[
            "aws certified developer"
        ],
        criteria=criteria
    )

    assert result.eligible is True


def test_check_multiple_certifications():

    criteria = EligibilityCriteria(
        required_certifications=[
            "AWS Certified Developer",
            "Azure Developer Associate"
        ]
    )

    result = check_education_certification(
        candidate_education="B.Tech",
        candidate_certifications=[
            "AWS Certified Developer",
            "Azure Developer Associate"
        ],
        criteria=criteria
    )

    assert result.eligible is True


def test_check_location_match():

    criteria = EligibilityCriteria(
        location="Chennai"
    )

    result, reason = check_location(
        candidate_location="Chennai",
        criteria=criteria
    )

    assert result is True
    assert "satisfied" in reason


def test_check_location_case_insensitive():

    criteria = EligibilityCriteria(
        location="Chennai"
    )

    result, reason = check_location(
        candidate_location="chennai",
        criteria=criteria
    )

    assert result is True


def test_check_location_mismatch():

    criteria = EligibilityCriteria(
        location="Chennai"
    )

    result, reason = check_location(
        candidate_location="Bangalore",
        criteria=criteria
    )

    assert result is False
    assert "does not match" in reason


def test_check_location_no_requirement():

    criteria = EligibilityCriteria()

    result, reason = check_location(
        candidate_location="Chennai",
        criteria=criteria
    )

    assert result is True


def test_check_authorization_match():

    criteria = EligibilityCriteria(
        work_authorization_required=True
    )

    result = check_location_authorization(
        candidate_location="Chennai",
        candidate_authorization=True,
        criteria=criteria
    )

    assert result.eligible is True


def test_check_authorization_missing():

    criteria = EligibilityCriteria(
        work_authorization_required=True
    )

    result = check_location_authorization(
        candidate_location="Chennai",
        candidate_authorization=False,
        criteria=criteria
    )

    assert result.eligible is False


def test_check_authorization_not_required():

    criteria = EligibilityCriteria(
        work_authorization_required=False
    )

    result = check_location_authorization(
        candidate_location="Chennai",
        candidate_authorization=False,
        criteria=criteria
    )

    assert result.eligible is True


def test_check_eligibility_all_requirements_match():

    criteria = EligibilityCriteria(
        required_skills=[
            "Java",
            "Python"
        ],
        minimum_experience_months=24,
        required_education=[
            CanonicalJobEducationRequirement(
                degree="B.Tech",
                field_of_study="Computer Science",
                required=True
            )
        ],
        required_certifications=[
            "AWS Certified Developer"
        ],
        location="Chennai",
        work_authorization_required=True
    )

    class Candidate:
        skills = [
            "Java",
            "Python"
        ]
        experience_months = 36
        education = "B.Tech Computer Science"
        certifications = [
            "AWS Certified Developer"
        ]
        location = "Chennai"
        authorization = True

    result = check_eligibility(
        candidate=Candidate(),
        criteria=criteria
    )

    assert result.eligible is True
    assert result.skill_match.eligible is True
    assert result.experience_match.eligible is True
    assert result.education_certification.eligible is True
    assert result.location_authorization.eligible is True


def test_check_eligibility_fails_missing_skill():

    criteria = EligibilityCriteria(
        required_skills=[
            "Java",
            "Python"
        ]
    )

    class Candidate:
        skills = [
            "Java"
        ]
        experience_months = 36
        education = ""
        certifications = []
        location = ""
        authorization = True

    result = check_eligibility(
        candidate=Candidate(),
        criteria=criteria
    )

    assert result.eligible is False
    assert result.skill_match.eligible is False