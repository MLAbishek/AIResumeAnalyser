"""
Module 11 - Experience Extraction.

Converts resume experience-section text into structured
Experience objects.

This module does not normalize company names, job titles,
dates, or skills.
"""

from __future__ import annotations

import re

from app.core.schemas import Experience


class ExperienceExtractor:
    """Extract structured employment/project experience."""

    DATE_RANGE_PATTERN = re.compile(
        r"(?i)"
        r"("
        r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)"
        r"[a-z]*\s+\d{4}"
        r"|"
        r"\d{1,2}/\d{4}"
        r"|"
        r"\d{4}"
        r")"
        r"\s*(?:-|–|—|to)\s*"
        r"("
        r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)"
        r"[a-z]*\s+\d{4}"
        r"|"
        r"\d{1,2}/\d{4}"
        r"|"
        r"\d{4}"
        r"|present|current"
        r")"
    )

    def extract(self, text: str) -> list[Experience]:
        """
        Extract experience records from section text.
        """
        if not text or not text.strip():
            return []

        lines = self._clean_lines(text)

        date_positions = self._find_date_ranges(lines)

        if not date_positions:
            return self._fallback_extract(lines)

        experiences = []

        for index, (date_index, match) in enumerate(
            date_positions
        ):
            experience = self._build_experience(
                lines=lines,
                date_index=date_index,
                match=match,
                next_date_index=(
                    date_positions[index + 1][0]
                    if index + 1 < len(date_positions)
                    else None
                ),
            )

            if experience:
                experiences.append(experience)

        return experiences

    @staticmethod
    def _clean_lines(text: str) -> list[str]:
        """Remove empty lines while preserving content."""
        return [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

    @classmethod
    def _find_date_ranges(
        cls,
        lines: list[str],
    ) -> list[tuple[int, re.Match]]:
        """Find all employment date ranges."""
        results = []

        for index, line in enumerate(lines):
            match = cls.DATE_RANGE_PATTERN.search(line)

            if match:
                results.append(
                    (index, match)
                )

        return results

    def _build_experience(
        self,
        lines: list[str],
        date_index: int,
        match: re.Match,
        next_date_index: int | None,
    ) -> Experience | None:
        """
        Build an Experience object around a date range.
        """

        start_date = match.group(1)
        end_date = match.group(2)

        role = None
        company = None

        # Usually the line immediately before the date
        # contains role and company.
        if date_index > 0:
            header_line = lines[date_index - 1]

            if not self._is_bullet(header_line):
                role, company = self._parse_role_company(
                    header_line
                )

        # Description begins after date line.
        description_start = date_index + 1

        if next_date_index is not None:
            # The line immediately before the next date is
            # normally the next role/company header.
            description_end = next_date_index - 1
        else:
            description_end = len(lines)

        description_lines = lines[
            description_start:description_end
        ]

        # Never treat another obvious role/company line as
        # part of the description.
        description_lines = [
            line
            for line in description_lines
            if not self._looks_like_role_company(line)
        ]

        description = "\n".join(
            description_lines
        ).strip()

        return Experience(
            company=company,
            role=role,
            start_date=start_date,
            end_date=end_date,
            description=description or None,
        )

    @staticmethod
    def _parse_role_company(
        line: str,
    ) -> tuple[str | None, str | None]:
        """
        Parse common role/company formats.

        Supported:

            ML Engineer | ABC Technologies
            ML Engineer - ABC Technologies
            ML Engineer @ ABC Technologies
        """

        separators = [
            r"\s*\|\s*",
            r"\s+@\s+",
            r"\s+[-–—]\s+",
        ]

        for separator in separators:
            parts = re.split(
                separator,
                line,
                maxsplit=1,
            )

            if len(parts) == 2:
                role = parts[0].strip()
                company = parts[1].strip()

                return (
                    role or None,
                    company or None,
                )

        # If there is no recognizable separator,
        # treat the entire line as the role.
        return line.strip() or None, None

    @staticmethod
    def _is_bullet(line: str) -> bool:
        """Check whether a line is a bullet."""
        return bool(
            re.match(
                r"^(?:[-*•▪◦‣]|\d+[.)])\s+",
                line,
            )
        )

    @classmethod
    def _looks_like_role_company(
        cls,
        line: str,
    ) -> bool:
        """
        Detect lines that look like another experience header.
        """
        if cls._is_bullet(line):
            return False

        if "|" in line:
            return True

        if re.search(
            r"\s+@\s+",
            line,
        ):
            return True

        return bool(
            re.search(
                r"\s[-–—]\s",
                line,
            )
        )

    @staticmethod
    def _fallback_extract(
        lines: list[str],
    ) -> list[Experience]:
        """
        Fallback when no date ranges are available.

        Treat bullet groups as descriptions and preceding
        non-bullet lines as role/company headers.
        """

        experiences = []
        current_header = None
        current_description = []

        for line in lines:

            if not ExperienceExtractor._is_bullet(line):
                if current_header is not None:
                    experiences.append(
                        Experience(
                            role=current_header,
                            company=None,
                            description=(
                                "\n".join(
                                    current_description
                                ).strip()
                                or None
                            ),
                        )
                    )

                current_header = line
                current_description = []

            else:
                current_description.append(
                    line
                )

        if current_header is not None:
            experiences.append(
                Experience(
                    role=current_header,
                    company=None,
                    description=(
                        "\n".join(
                            current_description
                        ).strip()
                        or None
                    ),
                )
            )

        return experiences