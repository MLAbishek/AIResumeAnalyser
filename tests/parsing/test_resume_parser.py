import pytest

from app.core.schemas import (
    DocumentType,
    RawDocument,
    RawDocumentPage,
)

from app.parsing.resume_parse import ResumeParser


@pytest.fixture
def sample_resume():
    text = """
    Adhithya J

    adhithya@example.com
    Chennai, India

    Professional Summary:
    Machine Learning enthusiast with experience building computer vision
    and deep learning applications.

    Skills:
    Python, PyTorch, TensorFlow, OpenCV, SQL

    Experience:
    ML Engineer | ABC Technologies
    Jan 2023 - Present
    - Developed computer vision models
    - Built deep learning pipelines
    - Improved model performance

    Software Engineer | XYZ Solutions
    Jun 2021 - Dec 2022
    - Developed backend services
    - Built REST APIs

    Education:
    ABC University - B.Tech Computer Science - 2017 - 2021

    Certifications:
    AWS Certified Cloud Practitioner

    Projects:
    - Resume Screening System
    - Image Classification Platform
    """

    return RawDocument(
        document_id="resume_test_001",
        document_type=DocumentType.RESUME,
        source_path="data/raw/resumes/resume_001.txt",
        pages=[
            RawDocumentPage(
                page_number=1,
                text=text,
            )
        ],
        raw_text=text,
    )


def test_parse_returns_resume(sample_resume):
    result = ResumeParser().parse(sample_resume)

    assert result.resume_id.startswith("resume_")
    assert result.name == "Adhithya J"


def test_extract_summary(sample_resume):
    result = ResumeParser().parse(sample_resume)

    assert result.summary is not None
    assert "Machine Learning enthusiast" in result.summary


def test_extract_skills(sample_resume):
    result = ResumeParser().parse(sample_resume)

    assert "Python" in result.skills
    assert "PyTorch" in result.skills
    assert "TensorFlow" in result.skills
    assert "OpenCV" in result.skills


def test_extract_experience(sample_resume):
    result = ResumeParser().parse(sample_resume)

    assert len(result.experience) == 2

    assert result.experience[0].role == "ML Engineer"
    assert result.experience[0].company == "ABC Technologies"

    assert result.experience[1].role == "Software Engineer"
    assert result.experience[1].company == "XYZ Solutions"


def test_extract_job_titles(sample_resume):
    result = ResumeParser().parse(sample_resume)

    assert "ML Engineer" in result.job_titles
    assert "Software Engineer" in result.job_titles


def test_extract_education(sample_resume):
    result = ResumeParser().parse(sample_resume)

    assert len(result.education) >= 1


def test_extract_certifications(sample_resume):
    result = ResumeParser().parse(sample_resume)

    assert "AWS Certified Cloud Practitioner" in result.certifications


def test_extract_projects(sample_resume):
    result = ResumeParser().parse(sample_resume)

    assert "Resume Screening System" in result.projects
    assert "Image Classification Platform" in result.projects


def test_preserves_raw_text(sample_resume):
    result = ResumeParser().parse(sample_resume)

    assert result.raw_text == sample_resume.raw_text.strip()


def test_resume_id_is_deterministic(sample_resume):
    parser = ResumeParser()

    result1 = parser.parse(sample_resume)
    result2 = parser.parse(sample_resume)

    assert result1.resume_id == result2.resume_id


def test_rejects_job_description(sample_resume):
    sample_resume.document_type = DocumentType.JOB_DESCRIPTION

    with pytest.raises(ValueError):
        ResumeParser().parse(sample_resume)


def test_rejects_empty_resume(sample_resume):
    sample_resume.raw_text = ""

    with pytest.raises(ValueError):
        ResumeParser().parse(sample_resume)


def test_parser_does_not_normalize_skills(sample_resume):
    sample_resume.raw_text = """
    John Doe

    Skills:
    Py Torch, Tensor Flow, Open CV
    """

    result = ResumeParser().parse(sample_resume)

    assert "Py Torch" in result.skills
    assert "Tensor Flow" in result.skills
    assert "Open CV" in result.skills

    assert "PyTorch" not in result.skills