from dataclasses import dataclass
from datetime import date
import re


@dataclass(frozen=True)
class NormalizedDateRange:
    start_date: date
    end_date: date
    duration_months: int

    @property
    def duration_years(self) -> int:
        return self.duration_months // 12

    @property
    def remaining_months(self) -> int:
        return self.duration_months % 12


class DateDurationNormalizer:
    """
    Normalizes extracted experience dates and calculates
    duration in calendar months.
    """

    MONTHS = {
        "january": 1,
        "jan": 1,
        "february": 2,
        "feb": 2,
        "march": 3,
        "mar": 3,
        "april": 4,
        "apr": 4,
        "may": 5,
        "june": 6,
        "jun": 6,
        "july": 7,
        "jul": 7,
        "august": 8,
        "aug": 8,
        "september": 9,
        "sep": 9,
        "sept": 9,
        "october": 10,
        "oct": 10,
        "november": 11,
        "nov": 11,
        "december": 12,
        "dec": 12,
    }

    PRESENT_VALUES = {
        "present",
        "current",
        "now",
        "ongoing",
    }

    def normalize_month_year(
        self,
        value: str,
    ) -> date:
        """
        Convert month/year expressions into the first day
        of the corresponding month.

        Examples:
            January 2020 -> 2020-01-01
            Jan 2020     -> 2020-01-01
            01/2020      -> 2020-01-01
        """

        value = value.strip().lower()

        # MM/YYYY
        match = re.fullmatch(
            r"(\d{1,2})\s*/\s*(\d{4})",
            value,
        )

        if match:
            month = int(match.group(1))
            year = int(match.group(2))

            self._validate_month(month)

            return date(year, month, 1)

        # Month YYYY
        match = re.fullmatch(
            r"([a-z]+)\s+(\d{4})",
            value,
        )

        if match:
            month_name = match.group(1)
            year = int(match.group(2))

            if month_name not in self.MONTHS:
                raise ValueError(
                    f"Unknown month: {month_name}"
                )

            return date(
                year,
                self.MONTHS[month_name],
                1,
            )

        # YYYY
        match = re.fullmatch(
            r"(\d{4})",
            value,
        )

        if match:
            year = int(match.group(1))

            return date(year, 1, 1)

        raise ValueError(
            f"Unsupported date format: {value}"
        )

    def normalize_end_date(
        self,
        value: str,
        reference_date: date | None = None,
    ) -> date:
        """
        Normalize an end date.

        'Present', 'Current', 'Now', and 'Ongoing'
        resolve to reference_date.
        """

        normalized = value.strip().lower()

        if normalized in self.PRESENT_VALUES:
            return reference_date or date.today()

        return self.normalize_month_year(value)

    def calculate_duration_months(
        self,
        start_date: date,
        end_date: date,
    ) -> int:
        """
        Calculate calendar duration in months.
        """

        if end_date < start_date:
            raise ValueError(
                "End date cannot be before start date"
            )

        months = (
            (end_date.year - start_date.year) * 12
            + end_date.month
            - start_date.month
        )

        return months

    def normalize_range(
        self,
        start_value: str,
        end_value: str,
        reference_date: date | None = None,
    ) -> NormalizedDateRange:
        """
        Normalize a start/end experience range.
        """

        start_date = self.normalize_month_year(
            start_value
        )

        end_date = self.normalize_end_date(
            end_value,
            reference_date=reference_date,
        )

        duration_months = self.calculate_duration_months(
            start_date,
            end_date,
        )

        return NormalizedDateRange(
            start_date=start_date,
            end_date=end_date,
            duration_months=duration_months,
        )

    @staticmethod
    def _validate_month(month: int) -> None:
        if not 1 <= month <= 12:
            raise ValueError(
                f"Invalid month: {month}"
            )