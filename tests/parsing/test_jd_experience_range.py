"""
Targeted regression test for BUG CLASS 3: "Fresh graduates and
candidates with 0-1 year of experience are eligible." was being
parsed as a 12-month MINIMUM requirement (the pattern matching a
bare "N years" phrase greedily matched the upper bound "1" out of
the "0-1" range, ignoring the lower bound entirely), rejecting a
6-month-experienced fresher candidate outright.
"""

from app.parsing.jd_extractors import (
    extract_experience_range,
    extract_experience_years,
)


class TestZeroToOneYearRange:
    """11. "0-1 year" experience range."""

    def test_en_dash_range_extracts_zero_as_minimum(self):
        text = (
            "Fresh graduates and candidates with 0–1 year of "
            "experience are eligible."
        )

        minimum, maximum = extract_experience_range(text)

        assert minimum == 0.0
        assert maximum == 1.0

    def test_ascii_hyphen_range_extracts_zero_as_minimum(self):
        minimum, maximum = extract_experience_range(
            "0-1 years of experience required."
        )

        assert minimum == 0.0
        assert maximum == 1.0

    def test_extract_experience_years_returns_the_minimum_not_max(
        self,
    ):
        # This is the exact regression: the old code returned 1.0
        # (later multiplied into a 12-month minimum requirement)
        # instead of 0.0.
        text = (
            "Fresh graduates and candidates with 0–1 year of "
            "experience are eligible."
        )

        assert extract_experience_years(text) == 0.0


class TestExistingSingleValuePatternsUnaffected:
    def test_plus_years_still_works(self):
        minimum, maximum = extract_experience_range(
            "3+ years of experience in software development"
        )

        assert minimum == 3.0
        assert maximum is None

    def test_minimum_phrasing_still_works(self):
        minimum, maximum = extract_experience_range(
            "minimum 3 years of experience"
        )

        assert minimum == 3.0
        assert maximum is None

    def test_at_least_phrasing_still_works(self):
        minimum, maximum = extract_experience_range(
            "at least 2 years of experience required"
        )

        assert minimum == 2.0
        assert maximum is None

    def test_no_experience_statement_returns_none(self):
        minimum, maximum = extract_experience_range(
            "We are a fast-growing engineering team."
        )

        assert minimum is None
        assert maximum is None
