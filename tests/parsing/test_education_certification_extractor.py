import pytest

from app.parsing.education_certification_extractor import (
    EducationCertificationExtractor,
)


@pytest.fixture
def extractor():
    return EducationCertificationExtractor()


def test_extract_btech_education(extractor):
    text = """
    ABC University - B.Tech Computer Science - 2017 - 2021
    """

    result = extractor.extract_education(text)

    assert len(result) == 1

    education = result[0]

    assert education.institution == "ABC University"
    assert education.degree == "B.Tech"
    assert education.field == "Computer Science"
    assert education.start_date == "2017"
    assert education.end_date == "2021"


def test_extract_masters_education(extractor):
    text = """
    XYZ University - Master's Data Science - 2021 - 2023
    """

    result = extractor.extract_education(text)

    assert len(result) == 1

    education = result[0]

    assert education.institution == "XYZ University"
    assert education.degree == "Master's"
    assert education.field == "Data Science"
    assert education.start_date == "2021"
    assert education.end_date == "2023"


def test_extract_multiple_education_records(extractor):
    text = """
    ABC University - B.Tech Computer Science - 2017 - 2021
    XYZ University - MBA - 2022 - 2024
    """

    result = extractor.extract_education(text)

    assert len(result) == 2


def test_extract_education_with_present(extractor):
    text = """
    ABC University - M.Tech AI - 2024 - Present
    """

    result = extractor.extract_education(text)

    assert len(result) == 1

    assert result[0].start_date == "2024"
    assert result[0].end_date == "Present"


def test_extract_certifications(extractor):
    text = """
    - AWS Certified Developer
    - TensorFlow Developer Certificate
    """

    result = extractor.extract_certifications(text)

    assert result == [
        "AWS Certified Developer",
        "TensorFlow Developer Certificate",
    ]


def test_extract_comma_separated_certifications(extractor):
    text = """
    AWS Certified Developer,
    TensorFlow Developer Certificate
    """

    result = extractor.extract_certifications(text)

    assert "AWS Certified Developer" in result
    assert "TensorFlow Developer Certificate" in result


def test_deduplicates_certifications(extractor):
    text = """
    AWS Certified Developer
    AWS Certified Developer
    """

    result = extractor.extract_certifications(text)

    assert result == [
        "AWS Certified Developer"
    ]


def test_empty_education(extractor):
    assert extractor.extract_education("") == []


def test_empty_certifications(extractor):
    assert extractor.extract_certifications("") == []


def test_education_without_dates(extractor):
    text = """
    ABC University - B.Tech Computer Science
    """

    result = extractor.extract_education(text)

    assert len(result) == 1

    assert result[0].institution == "ABC University"
    assert result[0].degree == "B.Tech"
    assert result[0].field == "Computer Science"
    assert result[0].start_date is None
    assert result[0].end_date is None


def test_does_not_normalize_degree(extractor):
    text = """
    ABC University - BTech Computer Science - 2017 - 2021
    """

    result = extractor.extract_education(text)

    assert len(result) == 1
    assert result[0].degree == "BTech"