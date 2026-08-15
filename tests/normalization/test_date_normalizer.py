from datetime import date

import pytest

from app.normalization.date_normalizer import (
    DateDurationNormalizer,
)


@pytest.fixture
def normalizer():
    return DateDurationNormalizer()


def test_month_year_date(normalizer):
    assert (
        normalizer.normalize_month_year("January 2020")
        == date(2020, 1, 1)
    )


def test_abbreviated_month(normalizer):
    assert (
        normalizer.normalize_month_year("Jan 2020")
        == date(2020, 1, 1)
    )


def test_numeric_month_year(normalizer):
    assert (
        normalizer.normalize_month_year("06/2021")
        == date(2021, 6, 1)
    )


def test_year_only(normalizer):
    assert (
        normalizer.normalize_month_year("2020")
        == date(2020, 1, 1)
    )


def test_present_date(normalizer):
    reference = date(2026, 8, 15)

    assert (
        normalizer.normalize_end_date(
            "Present",
            reference_date=reference,
        )
        == reference
    )


def test_current_date(normalizer):
    reference = date(2026, 8, 15)

    assert (
        normalizer.normalize_end_date(
            "Current",
            reference_date=reference,
        )
        == reference
    )


def test_duration_months(normalizer):
    start = date(2020, 1, 1)
    end = date(2022, 3, 1)

    assert (
        normalizer.calculate_duration_months(
            start,
            end,
        )
        == 26
    )


def test_duration_years_and_months(normalizer):
    result = normalizer.normalize_range(
        "January 2020",
        "March 2022",
    )

    assert result.duration_months == 26
    assert result.duration_years == 2
    assert result.remaining_months == 2


def test_same_month(normalizer):
    result = normalizer.normalize_range(
        "January 2020",
        "January 2020",
    )

    assert result.duration_months == 0


def test_end_before_start(normalizer):
    with pytest.raises(ValueError):
        normalizer.normalize_range(
            "January 2022",
            "January 2020",
        )


def test_invalid_month(normalizer):
    with pytest.raises(ValueError):
        normalizer.normalize_month_year("13/2020")


def test_invalid_date_format(normalizer):
    with pytest.raises(ValueError):
        normalizer.normalize_month_year("not a date")