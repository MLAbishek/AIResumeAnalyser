import pytest

from app.parsing.experience_extractor import (
    ExperienceExtractor,
)


@pytest.fixture
def experience_text():
    return """
    ML Engineer | ABC Technologies
    Jan 2023 - Present
    - Developed computer vision models
    - Built deep learning pipelines
    - Improved model performance

    Software Engineer | XYZ Solutions
    Jun 2021 - Dec 2022
    - Developed backend services
    - Built REST APIs
    """


def test_extracts_multiple_experiences(experience_text):
    result = ExperienceExtractor().extract(
        experience_text
    )

    assert len(result) == 2


def test_extracts_first_role(experience_text):
    result = ExperienceExtractor().extract(
        experience_text
    )

    first = result[0]

    assert first.role == "ML Engineer"
    assert first.company == "ABC Technologies"


def test_extracts_first_dates(experience_text):
    result = ExperienceExtractor().extract(
        experience_text
    )

    first = result[0]

    assert first.start_date == "Jan 2023"
    assert first.end_date == "Present"


def test_extracts_first_description(experience_text):
    result = ExperienceExtractor().extract(
        experience_text
    )

    first = result[0]

    assert "Developed computer vision models" in (
        first.description
    )

    assert "Built deep learning pipelines" in (
        first.description
    )


def test_extracts_second_experience(experience_text):
    result = ExperienceExtractor().extract(
        experience_text
    )

    second = result[1]

    assert second.role == "Software Engineer"
    assert second.company == "XYZ Solutions"

    assert second.start_date == "Jun 2021"
    assert second.end_date == "Dec 2022"


def test_experiences_do_not_bleed_into_each_other(
    experience_text,
):
    result = ExperienceExtractor().extract(
        experience_text
    )

    first = result[0]

    assert "Software Engineer" not in (
        first.description or ""
    )

    assert "XYZ Solutions" not in (
        first.description or ""
    )


def test_empty_text_returns_empty_list():
    result = ExperienceExtractor().extract("")

    assert result == []


def test_whitespace_returns_empty_list():
    result = ExperienceExtractor().extract(
        "   \n   "
    )

    assert result == []


def test_supports_year_only_dates():
    text = """
    Data Scientist | ABC Corp
    2020 - 2023
    - Built machine learning models
    """

    result = ExperienceExtractor().extract(text)

    assert len(result) == 1
    assert result[0].start_date == "2020"
    assert result[0].end_date == "2023"


def test_supports_numeric_dates():
    text = """
    ML Engineer | ABC Corp
    01/2022 - 06/2024
    - Developed ML systems
    """

    result = ExperienceExtractor().extract(text)

    assert len(result) == 1
    assert result[0].start_date == "01/2022"
    assert result[0].end_date == "06/2024"


def test_supports_to_date_separator():
    text = """
    Developer | ABC Corp
    Jan 2020 to Mar 2022
    - Developed software
    """

    result = ExperienceExtractor().extract(text)

    assert len(result) == 1
    assert result[0].start_date == "Jan 2020"
    assert result[0].end_date == "Mar 2022"


def test_supports_role_company_without_separator():
    text = """
    Data Scientist
    Jan 2022 - Present
    - Built predictive models
    """

    result = ExperienceExtractor().extract(text)

    assert len(result) == 1
    assert result[0].role == "Data Scientist"
    assert result[0].company is None


def test_does_not_normalize_role_or_company():
    text = """
    ML Eng. | ABC Tech Pvt Ltd
    2022 - Present
    - Built ML systems
    """

    result = ExperienceExtractor().extract(text)

    assert result[0].role == "ML Eng."
    assert result[0].company == "ABC Tech Pvt Ltd"