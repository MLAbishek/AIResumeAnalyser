"""
Deterministic extractors for resume fields.
"""

from __future__ import annotations

import re

from app.core.schemas import Education, Experience


def clean_text(text: str) -> str:
    """Normalize whitespace."""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_name(header: str) -> str | None:
    """
    Extract candidate name from the resume header.

    Uses the first meaningful line unless it looks like
    an email, phone number, URL, or common heading.
    """
    if not header:
        return None

    ignored_patterns = [
        r"@",
        r"https?://",
        r"www\.",
        r"\+?\d[\d\s().-]{7,}",
    ]

    for line in header.splitlines():
        line = line.strip()

        if not line:
            continue

        if any(re.search(pattern, line, re.I) for pattern in ignored_patterns):
            continue

        if line.casefold() in {
            "resume",
            "curriculum vitae",
            "cv",
        }:
            continue

        # A reasonable name should not be excessively long.
        if 2 <= len(line.split()) <= 6 and len(line) <= 100:
            return line

    return None


def extract_summary(sections: dict[str, str]) -> str | None:
    """Extract professional summary."""
    summary = sections.get("summary")

    if not summary:
        return None

    return clean_text(summary)


def extract_list_items(text: str) -> list[str]:
    """
    Extract bullet/list items.

    Supports:
    - item
    * item
    • item
    1. item
    1) item
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

    return deduplicate(items)


def extract_skills(text: str) -> list[str]:
    """
    Extract skills from a skills section.

    Does not normalize skill names.
    """
    if not text:
        return []

    items = extract_list_items(text)

    # If bullets exist, preserve them.
    if len(items) > 1:
        result = []

        for item in items:
            # Handle bullet containing multiple comma-separated skills.
            parts = re.split(r"[,;|]", item)

            for part in parts:
                part = clean_text(part)

                if part:
                    result.append(part)

        return deduplicate(result)

    # Handle comma/semicolon/pipe-separated skills.
    parts = re.split(r"[,;|]", text)

    return deduplicate(
        [
            clean_text(part)
            for part in parts
            if clean_text(part)
        ]
    )


def extract_experience(text: str) -> list[Experience]:
    """
    Extract experience entries from a resume.

    Supports common formats where the role/company line appears
    immediately before the date range.

    Example:

        ML Engineer | ABC Technologies
        Jan 2023 - Present
        - Developed computer vision models

        Software Engineer | XYZ Solutions
        Jun 2021 - Dec 2022
        - Developed backend services
    """
    if not text:
        return []

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    date_pattern = re.compile(
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

    # Find all date-range lines first.
    date_matches = []

    for index, line in enumerate(lines):
        match = date_pattern.search(line)

        if match:
            date_matches.append(
                (index, match)
            )

    experiences: list[Experience] = []

    for position, (date_index, match) in enumerate(date_matches):

        start_date = match.group(1)
        end_date = match.group(2)

        # The line immediately before the date range normally
        # contains role + company.
        role_company_index = date_index - 1

        if role_company_index < 0:
            continue

        role_company_line = lines[role_company_index]

        # Don't treat another date line as role/company.
        if date_pattern.search(role_company_line):
            continue

        role, company = _split_role_company(
            role_company_line
        )

        # Description begins immediately after the date line.
        description_start = date_index + 1

        # The next date range marks the next experience.
        if position + 1 < len(date_matches):
            next_date_index = date_matches[position + 1][0]

            # The line immediately before the next date is the
            # next role/company line, so exclude it.
            description_end = next_date_index - 1
        else:
            description_end = len(lines)

        description_lines = lines[
            description_start:description_end
        ]

        # Remove accidental section headings.
        description_lines = [
            line
            for line in description_lines
            if not _looks_like_section_heading(line)
        ]

        description = (
            "\n".join(description_lines).strip()
            or None
        )

        experiences.append(
            Experience(
                company=company,
                role=role,
                start_date=start_date,
                end_date=end_date,
                description=description,
            )
        )

    return experiences


def _split_role_company(text: str) -> tuple[str | None, str | None]:
    """
    Split common 'Role | Company' or 'Role - Company' formats.
    """
    parts = re.split(r"\s*[|@]\s*|\s+[-–—]\s+", text, maxsplit=1)

    if len(parts) == 2:
        return clean_text(parts[0]), clean_text(parts[1])

    return clean_text(text), None


def extract_education(text: str) -> list[Education]:
    """
    Extract education entries using common degree/date patterns.
    """
    if not text:
        return []

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    results: list[Education] = []

    degree_pattern = re.compile(
        r"(?i)"
        r"(bachelor|master|b\.?tech|m\.?tech|b\.?e\.?|m\.?e\.?|"
        r"bsc|msc|b\.?sc|m\.?sc|mba|phd|doctorate|associate)"
    )

    date_pattern = re.compile(
        r"(?i)"
        r"(\d{4})\s*(?:-|–|—|to)\s*(\d{4}|present|current)"
    )

    for line in lines:
        degree_match = degree_pattern.search(line)

        if not degree_match:
            continue

        date_match = date_pattern.search(line)

        start_date = None
        end_date = None

        if date_match:
            start_date = date_match.group(1)
            end_date = date_match.group(2)

        degree = degree_match.group(0)

        before_degree = line[:degree_match.start()].strip(
            " ,-–—|"
        )

        after_degree = line[degree_match.end():].strip(
            " ,-–—|"
        )

        institution = before_degree or None
        field = after_degree or None

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


def extract_certifications(text: str) -> list[str]:
    """Extract certifications."""
    return extract_list_items_or_split(text)


def extract_projects(text: str) -> list[str]:
    """Extract project descriptions."""
    return extract_list_items_or_split(text)


def extract_job_titles(experiences: list[Experience]) -> list[str]:
    """Extract roles from experience entries."""
    return deduplicate(
        [
            experience.role
            for experience in experiences
            if experience.role
        ]
    )


def calculate_total_experience_years(
    experiences: list[Experience],
) -> float | None:
    """
    Calculate approximate total experience from date ranges.

    Returns None if no usable date ranges exist.
    """
    import datetime

    total_months = 0

    current = datetime.date.today()

    for experience in experiences:
        if not experience.start_date:
            continue

        start = parse_date(experience.start_date)

        if start is None:
            continue

        if experience.end_date:
            end = parse_date(experience.end_date)
        else:
            end = current

        if end is None:
            continue

        months = (
            (end.year - start.year) * 12
            + end.month
            - start.month
        )

        if months > 0:
            total_months += months

    if total_months == 0:
        return None

    return round(total_months / 12, 1)


def parse_date(value: str):
    """Parse supported resume date formats."""
    import datetime

    value = value.strip().lower()

    if value in {"present", "current"}:
        return datetime.date.today()

    match = re.search(r"(\d{4})", value)

    if not match:
        return None

    year = int(match.group(1))

    month_match = re.search(
        r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)",
        value,
    )

    if month_match:
        months = {
            "jan": 1,
            "feb": 2,
            "mar": 3,
            "apr": 4,
            "may": 5,
            "jun": 6,
            "jul": 7,
            "aug": 8,
            "sep": 9,
            "sept": 9,
            "oct": 10,
            "nov": 11,
            "dec": 12,
        }

        month = months[month_match.group(1)]
    else:
        month = 1

    return datetime.date(year, month, 1)


def extract_list_items_or_split(text: str) -> list[str]:
    """Extract bullets or separated values."""
    if not text:
        return []

    items = extract_list_items(text)

    if items:
        return items

    parts = re.split(r"[,;|]", text)

    return deduplicate(
        [
            clean_text(part)
            for part in parts
            if clean_text(part)
        ]
    )


def deduplicate(items: list[str]) -> list[str]:
    """Case-insensitive stable deduplication."""
    seen = set()
    result = []

    for item in items:
        key = item.casefold()

        if key not in seen:
            seen.add(key)
            result.append(item)

    return result


def _looks_like_section_heading(line: str) -> bool:
    """Detect common section boundaries."""
    headings = {
        "skills",
        "education",
        "experience",
        "work experience",
        "professional experience",
        "certifications",
        "projects",
        "summary",
        "profile",
    }

    return line.casefold().rstrip(":") in headings