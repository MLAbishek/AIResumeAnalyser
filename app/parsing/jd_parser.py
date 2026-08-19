"""
Job Description parser.

Converts a RawDocument containing a Job Description into
a structured JobDescription model.
"""

from __future__ import annotations

import hashlib
import uuid

from app.core.schemas import (
    DocumentType,
    JobDescription,
    RawDocument,
)

from app.parsing.jd_extractors import (
    extract_certifications,
    extract_education,
    extract_education_from_text,
    extract_experience_range,
    extract_job_type,
    extract_location,
    extract_preferred_skills,
    extract_required_skills,
    extract_responsibilities,
    extract_summary,
    extract_title,
)

from app.parsing.jd_sections import split_into_sections


class JDParser:
    """
    Parse a RawDocument into a structured JobDescription.

    The parser is deterministic and does not perform normalization.
    """

    def parse(self, document: RawDocument) -> JobDescription:
        """
        Parse a RawDocument containing a Job Description.

        Raises:
            ValueError: If the document is not a Job Description
                        or contains no usable text.
        """
        if document.document_type != DocumentType.JOB_DESCRIPTION:
            raise ValueError(
                "JDParser only accepts JOB_DESCRIPTION documents."
            )

        raw_text = document.raw_text.strip()

        if not raw_text:
            raise ValueError(
                "Cannot parse a Job Description with empty text."
            )

        sections = split_into_sections(raw_text)

        title = extract_title(raw_text)

        # Some JDs put the title as the first non-empty line.
        if title is None:
            title = self._extract_first_line_title(raw_text)

        job_id = self._generate_job_id(document)

        minimum_experience_years, maximum_experience_years = (
            extract_experience_range(raw_text)
        )

        return JobDescription(
            job_id=job_id,
            title=title,
            summary=extract_summary(sections),
            required_skills=extract_required_skills(sections),
            preferred_skills=extract_preferred_skills(sections),
            required_experience_years=minimum_experience_years,
            max_experience_years=maximum_experience_years,
            education=(
                extract_education(
                    sections.get("education", "")
                )
                # Some JDs state education requirements inline
                # (e.g. an "Eligibility:" line) rather than under a
                # dedicated "Education:" heading.
                or extract_education_from_text(raw_text)
            ),
            certifications=extract_certifications(
                sections.get("certifications", "")
            ),
            responsibilities=extract_responsibilities(
                sections.get("responsibilities", "")
            ),
            location=extract_location(raw_text),
            job_type=extract_job_type(raw_text),
            raw_text=raw_text,
        )

    @staticmethod
    def _extract_first_line_title(text: str) -> str | None:
        """
        Use the first meaningful line as a fallback title.

        Avoid treating obvious section headings as titles.
        """
        for line in text.splitlines():
            line = line.strip()

            if not line:
                continue

            lowered = line.casefold()

            if lowered in {
                "job description",
                "description",
                "summary",
                "requirements",
                "responsibilities",
                "qualifications",
            }:
                continue

            if len(line) <= 120:
                return line

            break

        return None

    @staticmethod
    def _generate_job_id(document: RawDocument) -> str:
        """
        Generate a deterministic ID from the document ID.

        This ensures repeated parsing of the same document
        produces the same job ID.
        """
        digest = hashlib.sha256(
            document.document_id.encode("utf-8")
        ).hexdigest()[:16]

        return f"jd_{digest}"