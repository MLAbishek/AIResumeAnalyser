import pytest

from app.core.schemas import (
    DocumentSection,
    DocumentType,
    SectionedDocument,
)

from app.parsing.entity_extractor import EntityExtractor


@pytest.fixture
def resume_sections():
    return SectionedDocument(
        document_id="resume_entity_test",
        document_type=DocumentType.RESUME,
        raw_text="sample resume",
        sections=[
            DocumentSection(
                name="skills",
                text="""
                Python, PyTorch, OpenCV, Docker
                """,
                start_line=1,
                end_line=1,
            ),
            DocumentSection(
                name="experience",
                text="""
                ML Engineer | ABC Technologies
                Jan 2023 - Present
                Built computer vision systems using Python and PyTorch.
                """,
                start_line=2,
                end_line=4,
            ),
            DocumentSection(
                name="education",
                text="""
                ABC University - B.Tech Computer Science
                2017 - 2021
                """,
                start_line=5,
                end_line=6,
            ),
            DocumentSection(
                name="certifications",
                text="""
                AWS Certified Developer
                """,
                start_line=7,
                end_line=7,
            ),
        ],
    )


def test_extracts_skills(resume_sections):
    result = EntityExtractor().extract(
        resume_sections
    )

    skills = [
        entity.text
        for entity in result.entities
        if entity.entity_type.value == "skill"
    ]

    assert "Python" in skills
    assert "PyTorch" in skills
    assert "OpenCV" in skills
    assert "Docker" in skills


def test_extracts_technology(resume_sections):
    result = EntityExtractor().extract(
        resume_sections
    )

    technologies = [
        entity.text
        for entity in result.entities
        if entity.entity_type.value == "technology"
    ]

    assert "Python" in technologies
    assert "PyTorch" in technologies
    assert "OpenCV" in technologies
    assert "Docker" in technologies


def test_extracts_company(resume_sections):
    result = EntityExtractor().extract(
        resume_sections
    )

    companies = [
        entity.text
        for entity in result.entities
        if entity.entity_type.value == "company"
    ]

    assert "ABC Technologies" in companies


def test_extracts_job_title(resume_sections):
    result = EntityExtractor().extract(
        resume_sections
    )

    titles = [
        entity.text
        for entity in result.entities
        if entity.entity_type.value == "job_title"
    ]

    assert "ML Engineer" in titles


def test_extracts_dates(resume_sections):
    result = EntityExtractor().extract(
        resume_sections
    )

    dates = [
        entity.text
        for entity in result.entities
        if entity.entity_type.value == "date"
    ]

    assert "Jan 2023" in dates
    assert "2017" in dates
    assert "2021" in dates


def test_extracts_degree(resume_sections):
    result = EntityExtractor().extract(
        resume_sections
    )

    degrees = [
        entity.text
        for entity in result.entities
        if entity.entity_type.value == "degree"
    ]

    assert any(
        degree.casefold() == "b.tech"
        for degree in degrees
    )


def test_extracts_certification(resume_sections):
    result = EntityExtractor().extract(
        resume_sections
    )

    certifications = [
        entity.text
        for entity in result.entities
        if entity.entity_type.value == "certification"
    ]

    assert "AWS Certified Developer" in certifications


def test_entity_contains_section(resume_sections):
    result = EntityExtractor().extract(
        resume_sections
    )

    python_skill = [
        entity
        for entity in result.entities
        if entity.entity_type.value == "skill"
        and entity.text.casefold() == "python"
    ]

    assert len(python_skill) == 1
    assert python_skill[0].section == "skills"


def test_deduplicates_entities(resume_sections):
    resume_sections.sections[0].text = """
    Python, Python, PyTorch
    """

    result = EntityExtractor().extract(
        resume_sections
    )

    python_skills = [
        entity
        for entity in result.entities
        if entity.entity_type.value == "skill"
        and entity.text.casefold() == "python"
    ]

    assert len(python_skills) == 1


def test_preserves_original_entity_text():
    document = SectionedDocument(
        document_id="normalization_test",
        document_type=DocumentType.RESUME,
        raw_text="sample",
        sections=[
            DocumentSection(
                name="skills",
                text="Py Torch",
            )
        ],
    )

    result = EntityExtractor().extract(document)

    assert any(
        entity.text == "Py Torch"
        for entity in result.entities
    )