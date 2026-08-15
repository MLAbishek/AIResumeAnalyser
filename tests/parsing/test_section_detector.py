import pytest

from app.core.schemas import (
    DocumentType,
    RawDocument,
    RawDocumentPage,
)

from app.parsing.section_detector import SectionDetector


@pytest.fixture
def resume_document():
    text = """
    John Doe

    john@example.com
    Chennai, India

    Professional Summary:
    Machine Learning engineer with experience in computer vision.

    Skills:
    Python
    PyTorch
    OpenCV

    Experience:
    ML Engineer | ABC Technologies
    Jan 2023 - Present

    Education:
    B.Tech Computer Science

    Projects:
    Resume Screening System

    Certifications:
    AWS Certified Developer
    """

    return RawDocument(
        document_id="resume_section_test",
        document_type=DocumentType.RESUME,
        source_path="resume.txt",
        pages=[
            RawDocumentPage(
                page_number=1,
                text=text,
            )
        ],
        raw_text=text,
    )


@pytest.fixture
def jd_document():
    text = """
    Software Engineer

    Summary:
    We are looking for a software engineer.

    Responsibilities:
    - Build scalable backend services
    - Write maintainable code

    Requirements:
    - 3+ years of experience
    - Python
    - REST APIs

    Preferred Qualifications:
    - Docker
    - Kubernetes

    Education:
    Bachelor's degree in Computer Science

    Certifications:
    AWS certification
    """

    return RawDocument(
        document_id="jd_section_test",
        document_type=DocumentType.JOB_DESCRIPTION,
        source_path="jd.txt",
        pages=[
            RawDocumentPage(
                page_number=1,
                text=text,
            )
        ],
        raw_text=text,
    )


def test_detect_resume_sections(resume_document):
    result = SectionDetector().detect(
        resume_document
    )

    names = [
        section.name
        for section in result.sections
    ]

    assert names == [
        "summary",
        "skills",
        "experience",
        "education",
        "projects",
        "certifications",
    ]


def test_detect_jd_sections(jd_document):
    result = SectionDetector().detect(
        jd_document
    )

    names = [
        section.name
        for section in result.sections
    ]

    assert names == [
        "summary",
        "responsibilities",
        "required_qualifications",
        "preferred_qualifications",
        "education",
        "certifications",
    ]


def test_section_text_is_preserved(resume_document):
    result = SectionDetector().detect(
        resume_document
    )

    skills = next(
        section
        for section in result.sections
        if section.name == "skills"
    )

    assert "Python" in skills.text
    assert "PyTorch" in skills.text
    assert "OpenCV" in skills.text


def test_section_boundaries(resume_document):
    result = SectionDetector().detect(
        resume_document
    )

    sections = result.sections

    for section in sections:
        assert section.start_line is not None
        assert section.end_line is not None
        assert section.start_line <= section.end_line


def test_markdown_heading_is_detected():
    document = RawDocument(
        document_id="markdown_test",
        document_type=DocumentType.RESUME,
        source_path="resume.md",
        pages=[],
        raw_text="""
# Skills
Python
PyTorch

## Education
B.Tech Computer Science
""",
    )

    result = SectionDetector().detect(document)

    assert result.sections[0].name == "skills"
    assert result.sections[1].name == "education"


def test_heading_colon_is_supported():
    document = RawDocument(
        document_id="colon_test",
        document_type=DocumentType.RESUME,
        source_path="resume.txt",
        pages=[],
        raw_text="""
Skills:
Python
PyTorch
""",
    )

    result = SectionDetector().detect(document)

    assert len(result.sections) == 1
    assert result.sections[0].name == "skills"


def test_empty_document_is_rejected():
    document = RawDocument(
        document_id="empty_test",
        document_type=DocumentType.RESUME,
        source_path="empty.txt",
        pages=[],
        raw_text="",
    )

    with pytest.raises(ValueError):
        SectionDetector().detect(document)


def test_unknown_sections_are_not_falsely_detected():
    document = RawDocument(
        document_id="unknown_test",
        document_type=DocumentType.RESUME,
        source_path="resume.txt",
        pages=[],
        raw_text="""
John Doe

Random information here.

Something completely custom:
This should not become a recognized section.
""",
    )

    result = SectionDetector().detect(document)

    assert len(result.sections) == 0