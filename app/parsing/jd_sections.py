"""
Job Description section detection.

Responsible only for identifying sections in a JD.
It does not normalize skills or extract canonical entities.
"""

from __future__ import annotations

import re


# Canonical section names mapped to common JD headings.
SECTION_ALIASES = {
    "summary": {
        "summary",
        "job summary",
        "role summary",
        "position summary",
        "about the role",
        "about this role",
        "overview",
        "description",
        "job description",
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
        "what we're looking for",
        "what we are looking for",
    },
    "preferred_qualifications": {
        "preferred qualifications",
        "desired qualifications",
        "nice to have",
        "nice-to-have",
        "preferred requirements",
        "good to have",
    },
    "skills": {
        "skills",
        "technical skills",
        "required skills",
        "technical requirements",
        "technologies",
        "technology",
        "tech stack",
    },
    "education": {
        "education",
        "educational qualifications",
        "academic qualifications",
        "degree requirements",
    },
    "certifications": {
        "certifications",
        "certificates",
        "licenses",
        "licences",
    },
    "experience": {
        "experience",
        "work experience",
        "professional experience",
        "experience required",
        "years of experience",
    },
    "benefits": {
        "benefits",
        "perks",
        "what we offer",
        "employee benefits",
        "what you'll gain",
        "what you will gain",
        "what you'll get",
        "what you'll learn",
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
        "type",
    },
}


def normalize_heading(text: str) -> str:
    """Normalize a potential section heading."""
    text = text.strip().lower()
    # PDFs commonly use "smart" typographic quotes - normalize to
    # plain ASCII so e.g. "What You'll Gain" matches the alias set
    # regardless of which apostrophe character the source used.
    text = text.replace("’", "'").replace("‘", "'")
    text = re.sub(r"[:\-–—]+$", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_section_heading(line: str) -> str | None:
    """
    Return the canonical section name if a line looks like a known heading.
    """
    normalized = normalize_heading(line)

    if not normalized:
        return None

    for canonical_name, aliases in SECTION_ALIASES.items():
        if normalized in aliases:
            return canonical_name

    return None


def split_into_sections(text: str) -> dict[str, str]:
    """
    Split raw JD text into named sections.

    Unknown text before the first recognized heading is stored as
    'header'.
    """
    sections: dict[str, list[str]] = {}
    current_section = "header"

    sections[current_section] = []

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