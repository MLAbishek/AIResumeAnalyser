"""
Resume section detection.

Identifies common resume sections without performing
normalization or semantic matching.
"""

from __future__ import annotations

import re


SECTION_ALIASES = {
    "summary": {
        "summary",
        "professional summary",
        "profile",
        "professional profile",
        "career summary",
        "objective",
        "career objective",
        "about me",
    },
    "skills": {
        "skills",
        "technical skills",
        "core skills",
        "key skills",
        "technical competencies",
        "competencies",
        "technologies",
        "technical expertise",
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
        "qualifications",
    },
    "certifications": {
        "certifications",
        "certificates",
        "licenses",
        "licences",
    },
    "projects": {
        "projects",
        "personal projects",
        "academic projects",
        "key projects",
        "project experience",
    },
}


def normalize_heading(text: str) -> str:
    """Normalize a possible section heading."""
    text = text.strip().lower()
    text = re.sub(r"[:\-–—]+$", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_section_heading(line: str) -> str | None:
    """Return canonical section name for a recognized heading."""
    normalized = normalize_heading(line)

    if not normalized:
        return None

    for section, aliases in SECTION_ALIASES.items():
        if normalized in aliases:
            return section

    return None


def split_into_sections(text: str) -> dict[str, str]:
    """
    Split resume text into logical sections.

    Content before the first recognized section is stored
    under 'header'.
    """
    sections: dict[str, list[str]] = {
        "header": []
    }

    current_section = "header"

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        heading = detect_section_heading(line)

        if heading:
            current_section = heading
            sections.setdefault(current_section, [])
            continue

        sections.setdefault(current_section, []).append(line)

    return {
        section: "\n".join(lines).strip()
        for section, lines in sections.items()
        if lines
    }