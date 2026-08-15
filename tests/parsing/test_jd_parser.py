import pytest

from app.core.schemas import (
    DocumentType,
    RawDocument,
    RawDocumentPage,
)

from app.parsing.jd_parser import JDParser


@pytest.fixture
def sample_jd():
    text = """
    Software Engineer

    Location: Bangalore
    Employment Type: Full-time

    Summary:
    We are looking for a Software Engineer to build scalable applications.

    Responsibilities:
    - Design and develop backend services
    - Write clean and maintainable code
    - Collaborate with cross-functional teams

    Requirements:
    - 3+ years of experience in software development
    - Strong Python skills
    - Experience with REST APIs

    Preferred Qualifications:
    - Experience with Docker
    - Experience with Kubernetes

    Education:
    - Bachelor's degree in Computer Science

    Certifications:
    - AWS Certified Developer
    """

    return RawDocument(
        document_id="jd_test_001",
        document_type=DocumentType.JOB_DESCRIPTION,
        source_path="data/raw/jd001.txt",
        pages=[
            RawDocumentPage(
                page_number=1,
                text=text,
            )
        ],
        raw_text=text,
    )


def test_parse_returns_job_description(sample_jd):
    parser = JDParser()

    result = parser.parse(sample_jd)

    assert result.job_id.startswith("jd_")
    assert result.title == "Software Engineer"
    assert result.location == "Bangalore"
    assert result.job_type == "Full-time"


def test_extract_summary(sample_jd):
    result = JDParser().parse(sample_jd)

    assert result.summary is not None
    assert "scalable applications" in result.summary


def test_extract_experience(sample_jd):
    result = JDParser().parse(sample_jd)

    assert result.required_experience_years == 3.0


def test_extract_responsibilities(sample_jd):
    result = JDParser().parse(sample_jd)

    assert len(result.responsibilities) == 3
    assert "Design and develop backend services" in result.responsibilities


def test_extract_required_skills(sample_jd):
    result = JDParser().parse(sample_jd)

    assert "Strong Python skills" in result.required_skills
    assert "Experience with REST APIs" in result.required_skills


def test_extract_preferred_skills(sample_jd):
    result = JDParser().parse(sample_jd)

    assert "Experience with Docker" in result.preferred_skills
    assert "Experience with Kubernetes" in result.preferred_skills


def test_extract_education(sample_jd):
    result = JDParser().parse(sample_jd)

    assert "Bachelor's degree in Computer Science" in result.education


def test_extract_certifications(sample_jd):
    result = JDParser().parse(sample_jd)

    assert "AWS Certified Developer" in result.certifications


def test_preserves_raw_text(sample_jd):
    result = JDParser().parse(sample_jd)

    assert result.raw_text == sample_jd.raw_text.strip()


def test_rejects_resume_document(sample_jd):
    sample_jd.document_type = DocumentType.RESUME

    with pytest.raises(ValueError):
        JDParser().parse(sample_jd)


def test_rejects_empty_document(sample_jd):
    sample_jd.raw_text = ""

    with pytest.raises(ValueError):
        JDParser().parse(sample_jd)


def test_job_id_is_deterministic(sample_jd):
    parser = JDParser()

    result1 = parser.parse(sample_jd)
    result2 = parser.parse(sample_jd)

    assert result1.job_id == result2.job_id


def test_parser_does_not_normalize_skills(sample_jd):
    sample_jd.raw_text = """
    Machine Learning Engineer

    Skills:
    - Py Torch
    - Tensor Flow
    """

    result = JDParser().parse(sample_jd)

    assert any(
        skill.casefold() == "py torch"
        for skill in result.required_skills
    )

    assert not any(
        skill.casefold() == "pytorch"
        for skill in result.required_skills
    )