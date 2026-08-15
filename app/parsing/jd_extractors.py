"""
Deterministic extractors for Job Description fields.
"""

from __future__ import annotations

import re


def clean_text(text: str) -> str:
    """Normalize whitespace without changing semantic content."""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_title(text: str) -> str | None:
    """
    Extract a job title from common title labels.

    Examples:
        Job Title: Software Engineer
        Position: ML Engineer
        Role: Data Scientist
    """
    patterns = [
        r"(?im)^\s*job\s*title\s*[:\-]\s*(.+)$",
        r"(?im)^\s*position\s*[:\-]\s*(.+)$",
        r"(?im)^\s*role\s*[:\-]\s*(.+)$",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            return clean_text(match.group(1))

    return None


def extract_location(text: str) -> str | None:
    """Extract location from common location labels."""
    patterns = [
        r"(?im)^\s*location\s*[:\-]\s*(.+)$",
        r"(?im)^\s*job\s*location\s*[:\-]\s*(.+)$",
        r"(?im)^\s*work\s*location\s*[:\-]\s*(.+)$",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            return clean_text(match.group(1))

    return None


def extract_job_type(text: str) -> str | None:
    """Extract employment/job type."""
    patterns = [
        r"(?im)^\s*employment\s*type\s*[:\-]\s*(.+)$",
        r"(?im)^\s*job\s*type\s*[:\-]\s*(.+)$",
        r"(?im)^\s*type\s*[:\-]\s*(.+)$",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            return clean_text(match.group(1))

    # Handle common standalone values.
    job_types = [
        "full-time",
        "full time",
        "part-time",
        "part time",
        "contract",
        "internship",
        "temporary",
        "freelance",
    ]

    lowered = text.lower()

    for job_type in job_types:
        if job_type in lowered:
            return job_type

    return None


def extract_experience_years(text: str) -> float | None:
    """
    Extract minimum required experience.

    Examples:
        3 years of experience
        3+ years experience
        minimum 3 years
        at least 2 years
    """
    patterns = [
        r"(?i)(?:minimum|at least|required)?\s*(\d+(?:\.\d+)?)\s*\+?\s*years?\s+(?:of\s+)?experience",
        r"(?i)(\d+(?:\.\d+)?)\s*-\s*\d+(?:\.\d+)?\s*years?\s+(?:of\s+)?experience",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            return float(match.group(1))

    return None


def extract_list_items(text: str) -> list[str]:
    """
    Extract bullet/list items from section text.

    Supports:
        - item
        * item
        • item
        1. item
        2) item
    """
    if not text:
        return []

    items = []

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        line = re.sub(
            r"^(?:[-*•▪◦‣]|\d+[.)])\s*",
            "",
            line,
        ).strip()

        if line:
            items.append(line)

    return _deduplicate(items)


def extract_skills(text: str) -> list[str]:
    """
    Extract skills from a skills section.

    This intentionally does not normalize skill names.
    """
    if not text:
        return []

    items = extract_list_items(text)

    if len(items) > 1:
        return items

    # Handle comma/semicolon separated skill lists.
    parts = re.split(r"[,;|]", text)

    result = []

    for part in parts:
        part = clean_text(part)

        if part and len(part) <= 100:
            result.append(part)

    return _deduplicate(result)


def extract_education(text: str) -> list[str]:
    """Extract education requirements."""
    if not text:
        return []

    items = extract_list_items(text)

    if items:
        return items

    return [clean_text(text)]


def extract_certifications(text: str) -> list[str]:
    """Extract certification requirements."""
    if not text:
        return []

    items = extract_list_items(text)

    if items:
        return items

    parts = re.split(r"[,;|]", text)

    return _deduplicate(
        [clean_text(part) for part in parts if clean_text(part)]
    )


def extract_responsibilities(text: str) -> list[str]:
    """Extract responsibility statements."""
    return extract_list_items(text)


def extract_summary(sections: dict[str, str]) -> str | None:
    """Extract summary/overview text."""
    summary = sections.get("summary")

    if summary:
        return clean_text(summary)

    return None


def extract_required_skills(
    sections: dict[str, str],
) -> list[str]:
    """Extract skills explicitly associated with required criteria."""
    candidates = []

    for section_name in (
        "skills",
        "required_qualifications",
        "experience",
    ):
        text = sections.get(section_name)

        if text:
            candidates.extend(extract_skills(text))

    return _deduplicate(candidates)


def extract_preferred_skills(
    sections: dict[str, str],
) -> list[str]:
    """Extract skills from preferred qualification sections."""
    text = sections.get("preferred_qualifications")

    if not text:
        return []

    return extract_skills(text)


def _deduplicate(items: list[str]) -> list[str]:
    """Case-insensitive stable deduplication."""
    seen = set()
    result = []

    for item in items:
        key = item.casefold()

        if key not in seen:
            seen.add(key)
            result.append(item)

    return result