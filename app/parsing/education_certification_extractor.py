"""
Module 12 - Education & Certification Extraction.

Extracts structured education and certification information
from resume sections.

This module does not normalize degrees, institutions, or
certification names.
"""

from __future__ import annotations

import re

from app.core.schemas import Education


class EducationCertificationExtractor:
    """Extract education and certification records."""

    DEGREE_PATTERN = re.compile(
        r"(?i)"
        r"\b("
        r"B\.?\s*Tech"
        r"|M\.?\s*Tech"
        r"|B\.?\s*E"
        r"|M\.?\s*E"
        r"|B\.?\s*Sc"
        r"|M\.?\s*Sc"
        r"|B\.?\s*S"
        r"|M\.?\s*S"
        r"|B\.?\s*A"
        r"|M\.?\s*A"
        r"|MBA"
        r"|Ph\.?\s*D"
        r"|Bachelor(?:'s)?"
        r"|Master(?:'s)?"
        r"|Doctorate"
        r"|Associate(?:'s)?"
        r")\b"
    )

    DATE_RANGE_PATTERN = re.compile(
        r"(?i)"
        r"("
        r"\d{4}"
        r"|"
        r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)"
        r"[a-z]*\s+\d{4}"
        r")"
        r"\s*(?:-|–|—|to)\s*"
        r"("
        r"\d{4}"
        r"|"
        r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)"
        r"[a-z]*\s+\d{4}"
        r"|present|current"
        r")"
    )

    YEAR_PATTERN = re.compile(r"\b\d{4}\b")

    def extract_education(
        self,
        text: str,
    ) -> list[Education]:
        """Extract education records."""
        if not text or not text.strip():
            return []

        lines = self._clean_lines(text)

        results = []

        for line in lines:
            degree_match = self.DEGREE_PATTERN.search(line)

            if not degree_match:
                continue

            degree = degree_match.group(1)

            start_date, end_date = (
                self._extract_dates(line)
            )

            institution, field = (
                self._extract_institution_and_field(
                    line=line,
                    degree_start=degree_match.start(),
                    degree_end=degree_match.end(),
                )
            )

            results.append(
                Education(
                    institution=institution,
                    degree=degree,
                    field=field,
                    start_date=start_date,
                    end_date=end_date,
                )
            )

        return results

    def extract_certifications(
        self,
        text: str,
    ) -> list[str]:
        """Extract certification names."""
        if not text or not text.strip():
            return []

        items = []

        for line in self._clean_lines(text):
            line = re.sub(
                r"^(?:[-*•▪◦‣]|\d+[.)])\s*",
                "",
                line,
            ).strip()

            if not line:
                continue

            # Support comma/semicolon-separated certifications.
            parts = re.split(
                r"\s*[,;|]\s*",
                line,
            )

            for part in parts:
                part = part.strip()

                if part:
                    items.append(part)

        return self._deduplicate(items)

    @staticmethod
    def _clean_lines(text: str) -> list[str]:
        return [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

    @classmethod
    def _extract_dates(
        cls,
        text: str,
    ) -> tuple[str | None, str | None]:

        match = cls.DATE_RANGE_PATTERN.search(text)

        if match:
            return (
                match.group(1),
                match.group(2),
            )

        years = cls.YEAR_PATTERN.findall(text)

        if len(years) >= 2:
            return (
                years[0],
                years[1],
            )

        if len(years) == 1:
            return years[0], None

        return None, None

    @staticmethod
    def _extract_institution_and_field(
        line: str,
        degree_start: int,
        degree_end: int,
    ) -> tuple[str | None, str | None]:
        """
        Extract institution and field around a degree.

        Example:

            ABC University - B.Tech Computer Science - 2017 - 2021

        becomes:

            institution = ABC University
            degree      = B.Tech
            field       = Computer Science
        """

        before_degree = line[:degree_start].strip(
            " ,-–—|"
        )

        after_degree = line[degree_end:].strip(
            " ,-–—|"
        )

        # Remove date information from field.
        after_degree = re.sub(
            r"\b\d{4}\b",
            "",
            after_degree,
        )

        after_degree = re.sub(
            r"\s*(?:-|–|—|to)\s*",
            " ",
            after_degree,
        ).strip()

        institution = (
            before_degree
            if before_degree
            else None
        )

        field = (
            after_degree
            if after_degree
            else None
        )

        return institution, field

    @staticmethod
    def _deduplicate(
        items: list[str],
    ) -> list[str]:

        seen = set()
        result = []

        for item in items:
            key = item.casefold()

            if key not in seen:
                seen.add(key)
                result.append(item)

        return result