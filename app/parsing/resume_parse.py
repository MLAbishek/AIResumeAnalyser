"""
Resume parser.

Converts RawDocument -> Resume.
"""

from __future__ import annotations

import hashlib

from app.core.schemas import (
    DocumentType,
    RawDocument,
    Resume,
)

from app.parsing.resume_extractors import (
    calculate_total_experience_years,
    extract_certifications,
    extract_education,
    extract_email,
    extract_experience,
    extract_job_titles,
    extract_name,
    extract_phone,
    extract_projects,
    extract_skills,
    extract_summary,
)

from app.parsing.resume_sections import split_into_sections


class ResumeParser:
    """Deterministic parser for resume documents."""

    def parse(self, document: RawDocument) -> Resume:
        """
        Parse a RawDocument into a Resume.

        Raises:
            ValueError: if document type is wrong or text is empty.
        """
        if document.document_type != DocumentType.RESUME:
            raise ValueError(
                "ResumeParser only accepts RESUME documents."
            )

        raw_text = document.raw_text.strip()

        if not raw_text:
            raise ValueError(
                "Cannot parse a resume with empty text."
            )

        sections = split_into_sections(raw_text)

        experiences = extract_experience(
            sections.get("experience", "")
        )

        education = extract_education(
            sections.get("education", "")
        )

        skills = extract_skills(
            sections.get("skills", "")
        )

        certifications = extract_certifications(
            sections.get("certifications", "")
        )

        projects = extract_projects(
            sections.get("projects", "")
        )

        job_titles = extract_job_titles(experiences)

        header = sections.get("header", "")

        return Resume(
            resume_id=self._generate_resume_id(document),
            name=extract_name(header),
            email=extract_email(header),
            phone=extract_phone(header),
            summary=extract_summary(sections),
            skills=skills,
            experience=experiences,
            education=education,
            certifications=certifications,
            projects=projects,
            job_titles=job_titles,
            total_experience_years=calculate_total_experience_years(
                experiences
            ),
            raw_text=raw_text,
        )

    @staticmethod
    def _generate_resume_id(
        document: RawDocument,
    ) -> str:
        """Generate deterministic resume ID."""
        digest = hashlib.sha256(
            document.document_id.encode("utf-8")
        ).hexdigest()[:16]

        return f"resume_{digest}"