import pytest

from app.decision.evidence_citation import (
    EvidenceCitationEngine,
)


@pytest.fixture
def engine():
    return EvidenceCitationEngine()


def test_skill_evidence_is_created(engine):
    result = engine.build_references(
        parsed_resume={
            "skills": [
                "Python",
                "SQL",
            ]
        },
        parsed_jd={
            "required_skills": [
                "Python",
            ]
        },
    )

    assert len(result) == 1
    assert result[0]["source"] == "resume"
    assert result[0]["section"] == "skills"
    assert result[0]["evidence"] == "Python"


def test_missing_skill_has_no_evidence(engine):
    result = engine.build_references(
        parsed_resume={
            "skills": [
                "Python",
            ]
        },
        parsed_jd={
            "required_skills": [
                "Docker",
            ]
        },
    )

    assert result == []


def test_skill_matching_is_case_insensitive(engine):
    result = engine.build_references(
        parsed_resume={
            "skills": [
                "python",
            ]
        },
        parsed_jd={
            "required_skills": [
                "Python",
            ]
        },
    )

    assert len(result) == 1
    assert result[0]["evidence"] == "python"


def test_multiple_skill_evidence_is_created(engine):
    result = engine.build_references(
        parsed_resume={
            "skills": [
                "Python",
                "SQL",
                "Docker",
            ]
        },
        parsed_jd={
            "required_skills": [
                "Python",
                "SQL",
                "Docker",
            ]
        },
    )

    assert len(result) == 3


def test_experience_evidence_is_created(engine):
    result = engine.build_references(
        parsed_resume={
            "experience_years": 4
        },
        parsed_jd={
            "minimum_experience_years": 3
        },
    )

    assert len(result) == 1
    assert result[0]["source"] == "resume"
    assert result[0]["section"] == "experience"
    assert result[0]["evidence"] == "4 years"


def test_experience_without_jd_requirement_is_supported(engine):
    result = engine.build_references(
        parsed_resume={
            "experience_years": 5
        },
        parsed_jd={},
    )

    assert len(result) == 1
    assert result[0]["section"] == "experience"


def test_missing_experience_produces_no_evidence(engine):
    result = engine.build_references(
        parsed_resume={},
        parsed_jd={
            "minimum_experience_years": 3
        },
    )

    assert result == []


def test_education_evidence_is_created(engine):
    result = engine.build_references(
        parsed_resume={
            "education": [
                "B.Tech Computer Science"
            ]
        },
        parsed_jd={
            "required_education": [
                "Computer Science"
            ]
        },
    )

    assert len(result) == 1
    assert result[0]["section"] == "education"
    assert (
        "Computer Science"
        in result[0]["evidence"]
    )


def test_certification_evidence_is_created(engine):
    result = engine.build_references(
        parsed_resume={
            "certifications": [
                "AWS Certified Developer"
            ]
        },
        parsed_jd={
            "required_certifications": [
                "AWS Certified Developer"
            ]
        },
    )

    assert len(result) == 1
    assert result[0]["section"] == "certifications"
    assert (
        "AWS Certified Developer"
        in result[0]["evidence"]
    )


def test_ranking_evidence_is_created(engine):
    result = engine.build_references(
        parsed_resume={},
        parsed_jd={},
        evaluation={
            "ranking_score": 85
        },
    )

    assert len(result) == 1
    assert result[0]["source"] == "ranking"
    assert result[0]["evidence"] == "85"


def test_llm_evidence_is_created(engine):
    result = engine.build_references(
        parsed_resume={},
        parsed_jd={},
        evaluation={
            "llm_score": 90
        },
    )

    assert len(result) == 1
    assert result[0]["source"] == "llm_evaluation"
    assert result[0]["evidence"] == "90"


def test_final_score_evidence_is_created(engine):
    result = engine.build_references(
        parsed_resume={},
        parsed_jd={},
        evaluation={
            "final_score": 87.5
        },
    )

    assert len(result) == 1
    assert result[0]["source"] == "decision"
    assert result[0]["evidence"] == "87.5"


def test_all_evidence_sources_are_combined(engine):
    result = engine.build_references(
        parsed_resume={
            "skills": ["Python"],
            "experience_years": 4,
            "education": [
                "B.Tech Computer Science"
            ],
            "certifications": [
                "AWS Certified Developer"
            ],
        },
        parsed_jd={
            "required_skills": ["Python"],
            "minimum_experience_years": 3,
            "required_education": [
                "Computer Science"
            ],
            "required_certifications": [
                "AWS Certified Developer"
            ],
        },
        evaluation={
            "ranking_score": 85,
            "llm_score": 90,
            "final_score": 86.5,
        },
    )

    assert len(result) == 7

    sources = {
        item["source"]
        for item in result
    }

    assert "resume" in sources
    assert "ranking" in sources
    assert "llm_evaluation" in sources
    assert "decision" in sources


def test_empty_inputs_return_empty_evidence(engine):
    result = engine.build_references(
        parsed_resume={},
        parsed_jd={},
    )

    assert result == []


def test_invalid_resume_type_raises_error(engine):
    with pytest.raises(TypeError):
        engine.build_references(
            parsed_resume=[],
            parsed_jd={},
        )


def test_invalid_jd_type_raises_error(engine):
    with pytest.raises(TypeError):
        engine.build_references(
            parsed_resume={},
            parsed_jd=[],
        )


def test_invalid_evaluation_type_raises_error(engine):
    with pytest.raises(TypeError):
        engine.build_references(
            parsed_resume={},
            parsed_jd={},
            evaluation=[],
        )


def test_evidence_has_required_fields(engine):
    result = engine.build_references(
        parsed_resume={
            "skills": ["Python"]
        },
        parsed_jd={
            "required_skills": ["Python"]
        },
    )

    evidence = result[0]

    assert set(evidence.keys()) == {
        "claim",
        "source",
        "section",
        "evidence",
    }


def test_evidence_does_not_invent_missing_information(engine):
    result = engine.build_references(
        parsed_resume={
            "skills": ["Python"]
        },
        parsed_jd={
            "required_skills": [
                "Python",
                "Docker",
            ]
        },
    )

    assert len(result) == 1
    assert "Docker" not in result[0]["evidence"]