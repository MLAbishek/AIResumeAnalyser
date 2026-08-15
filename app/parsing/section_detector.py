"""
Module 9 - Section Detection.

Identifies logical sections in resume and job-description text.

This module does not extract entities such as skills, degrees,
companies, or job titles. It only determines where sections begin
and end.
"""

from __future__ import annotations

import re

from app.core.schemas import (
    DocumentSection,
    DocumentType,
    RawDocument,
    SectionedDocument,
)


SECTION_ALIASES = {
    "summary": {
        "summary",
        "professional summary",
        "career summary",
        "profile",
        "professional profile",
        "objective",
        "career objective",
        "about me",
        "about the role",
        "role summary",
        "job summary",
        "overview",
    },

    "skills": {
        "skills",
        "technical skills",
        "key skills",
        "core skills",
        "professional skills",
        "technical competencies",
        "competencies",
        "technologies",
        "technical expertise",
        "tech stack",
    },

    "experience": {
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "work history",
        "professional history",
    },

    "education": {
        "education",
        "educational background",
        "academic background",
        "academic qualifications",
        "educational qualifications",
        "degree",
        "degrees",
    },

    "projects": {
        "projects",
        "personal projects",
        "academic projects",
        "key projects",
        "project experience",
    },

    "certifications": {
        "certifications",
        "certificates",
        "licenses",
        "licences",
        "professional certifications",
    },

    "responsibilities": {
        "responsibilities",
        "key responsibilities",
        "roles and responsibilities",
        "duties",
        "key duties",
        "what you'll do",
        "what you will do",
        "your responsibilities",
    },

    "required_qualifications": {
        "requirements",
        "required qualifications",
        "minimum qualifications",
        "basic qualifications",
        "qualifications",
        "must have",
        "required requirements",
        "what we're looking for",
        "what we are looking for",
    },

    "preferred_qualifications": {
        "preferred qualifications",
        "desired qualifications",
        "preferred requirements",
        "nice to have",
        "nice-to-have",
        "good to have",
    },

    "benefits": {
        "benefits",
        "perks",
        "what we offer",
        "employee benefits",
    },

    "location": {
        "location",
        "job location",
        "work location",
        "workplace",
    },

    "employment_type": {
        "employment type",
        "job type",
        "employment",
    },
}


class SectionDetector:
    """
    Detect logical sections in a RawDocument.

    Works for both resumes and job descriptions.
    """

    def detect(
        self,
        document: RawDocument,
    ) -> SectionedDocument:
        """
        Detect sections from a RawDocument.
        """
        if not document.raw_text.strip():
            raise ValueError(
                "Cannot detect sections in empty document."
            )

        sections = self._detect_sections(
            document.raw_text
        )

        return SectionedDocument(
            document_id=document.document_id,
            document_type=document.document_type,
            sections=sections,
            raw_text=document.raw_text,
        )

    def _detect_sections(
        self,
        text: str,
    ) -> list[DocumentSection]:
        lines = text.splitlines()

        detected: list[tuple[int, str]] = []

        for index, line in enumerate(lines):
            section_name = self._detect_heading(line)

            if section_name:
                detected.append(
                    (index, section_name)
                )

        sections: list[DocumentSection] = []

        for position, (start_index, section_name) in enumerate(
            detected
        ):
            if position + 1 < len(detected):
                next_start = detected[position + 1][0]
                end_index = next_start - 1
            else:
                end_index = len(lines) - 1

            section_lines = lines[
                start_index + 1 : end_index + 1
            ]

            section_text = "\n".join(
                line.strip()
                for line in section_lines
                if line.strip()
            ).strip()

            sections.append(
                DocumentSection(
                    name=section_name,
                    text=section_text,
                    start_line=start_index,
                    end_line=end_index,
                )
            )

        return sections

    @staticmethod
    def _normalize_heading(line: str) -> str:
        """
        Normalize a possible heading without changing its meaning.
        """
        value = line.strip().lower()

        # Remove common markdown heading markers.
        value = re.sub(r"^#{1,6}\s*", "", value)

        # Remove trailing punctuation.
        value = re.sub(r"[:\-–—]+$", "", value)

        # Normalize whitespace.
        value = re.sub(r"\s+", " ", value)

        return value.strip()

    @classmethod
    def _detect_heading(
        cls,
        line: str,
    ) -> str | None:
        """
        Return canonical section name if line is a recognized heading.
        """
        normalized = cls._normalize_heading(line)

        if not normalized:
            return None

        for canonical_name, aliases in SECTION_ALIASES.items():
            if normalized in aliases:
                return canonical_name

        return None