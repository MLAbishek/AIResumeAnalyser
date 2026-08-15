import pytest

from app.decision.gap_analysis import (
    GapAnalysisEngine,
)


@pytest.fixture
def engine():
    return GapAnalysisEngine()


def test_all_required_skills_are_matched(engine):
    result = engine.analyze(
        jd={
            "required_skills": [
                "Python",
                "SQL",
                "Docker",
            ]
        },
        resume={
            "skills": [
                "Python",
                "SQL",
                "Docker",
            ]
        },
    )

    assert result["matched_skills"] == [
        "docker",
        "python",
        "sql",
    ]

    assert result["missing_skills"] == []
    assert result["skill_gap_count"] == 0
    assert result["has_gap"] is False


def test_missing_skill_is_detected(engine):
    result = engine.analyze(
        jd={
            "required_skills": [
                "Python",
                "SQL",
                "Docker",
            ]
        },
        resume={
            "skills": [
                "Python",
                "SQL",
            ]
        },
    )

    assert result["missing_skills"] == ["docker"]
    assert result["skill_gap_count"] == 1
    assert result["has_gap"] is True


def test_multiple_missing_skills_are_detected(engine):
    result = engine.analyze(
        jd={
            "required_skills": [
                "Python",
                "SQL",
                "Docker",
                "Kubernetes",
            ]
        },
        resume={
            "skills": [
                "Python",
            ]
        },
    )

    assert result["missing_skills"] == [
        "docker",
        "kubernetes",
        "sql",
    ]


def test_skill_matching_is_case_insensitive(engine):
    result = engine.analyze(
        jd={
            "required_skills": [
                "Python",
                "Machine Learning",
            ]
        },
        resume={
            "skills": [
                "python",
                "machine learning",
            ]
        },
    )

    assert result["missing_skills"] == []
    assert result["skill_gap_count"] == 0


def test_skill_whitespace_is_normalized(engine):
    result = engine.analyze(
        jd={
            "required_skills": [
                "Machine   Learning",
            ]
        },
        resume={
            "skills": [
                "  machine learning  ",
            ]
        },
    )

    assert result["missing_skills"] == []


def test_exact_experience_meets_requirement(engine):
    result = engine.analyze(
        jd={
            "minimum_experience_years": 3
        },
        resume={
            "experience_years": 3
        },
    )

    gap = result["experience_gap"]

    assert gap["required_years"] == 3
    assert gap["candidate_years"] == 3
    assert gap["gap_years"] == 0
    assert gap["has_gap"] is False
    assert gap["meets_requirement"] is True


def test_experience_gap_is_detected(engine):
    result = engine.analyze(
        jd={
            "minimum_experience_years": 5
        },
        resume={
            "experience_years": 3
        },
    )

    gap = result["experience_gap"]

    assert gap["required_years"] == 5
    assert gap["candidate_years"] == 3
    assert gap["gap_years"] == 2
    assert gap["has_gap"] is True
    assert gap["meets_requirement"] is False


def test_excess_experience_has_no_gap(engine):
    result = engine.analyze(
        jd={
            "minimum_experience_years": 3
        },
        resume={
            "experience_years": 7
        },
    )

    gap = result["experience_gap"]

    assert gap["gap_years"] == 0
    assert gap["has_gap"] is False
    assert gap["meets_requirement"] is True


def test_no_experience_requirement(engine):
    result = engine.analyze(
        jd={},
        resume={
            "experience_years": 5
        },
    )

    gap = result["experience_gap"]

    assert gap["required_years"] == 0
    assert gap["gap_years"] == 0
    assert gap["has_gap"] is False


def test_missing_education_is_detected(engine):
    result = engine.analyze(
        jd={
            "required_education": [
                "Computer Science",
                "Mathematics",
            ]
        },
        resume={
            "education": [
                "Computer Science",
            ]
        },
    )

    gap = result["education_gap"]

    assert gap["missing"] == ["mathematics"]
    assert gap["has_gap"] is True


def test_education_requirement_is_met(engine):
    result = engine.analyze(
        jd={
            "required_education": [
                "Computer Science",
            ]
        },
        resume={
            "education": [
                "Computer Science",
            ]
        },
    )

    gap = result["education_gap"]

    assert gap["missing"] == []
    assert gap["has_gap"] is False
    assert gap["meets_requirement"] is True


def test_missing_certification_is_detected(engine):
    result = engine.analyze(
        jd={
            "required_certifications": [
                "AWS Certified Developer",
            ]
        },
        resume={
            "certifications": []
        },
    )

    gap = result["certification_gap"]

    assert gap["missing"] == [
        "aws certified developer"
    ]
    assert gap["has_gap"] is True


def test_certification_requirement_is_met(engine):
    result = engine.analyze(
        jd={
            "required_certifications": [
                "AWS Certified Developer",
            ]
        },
        resume={
            "certifications": [
                "AWS Certified Developer",
            ]
        },
    )

    gap = result["certification_gap"]

    assert gap["missing"] == []
    assert gap["has_gap"] is False


def test_no_requirements_means_no_gap(engine):
    result = engine.analyze(
        jd={},
        resume={},
    )

    assert result["matched_skills"] == []
    assert result["missing_skills"] == []
    assert result["skill_gap_count"] == 0
    assert result["has_gap"] is False


def test_invalid_jd_type_raises_error(engine):
    with pytest.raises(TypeError):
        engine.analyze(
            jd=[],
            resume={},
        )


def test_invalid_resume_type_raises_error(engine):
    with pytest.raises(TypeError):
        engine.analyze(
            jd={},
            resume=[],
        )