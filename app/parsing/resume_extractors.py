"""
Deterministic extractors for resume fields.
"""

from __future__ import annotations

import re

from app.core.schemas import Education, Experience, Project


def clean_text(text: str) -> str:
    """Normalize whitespace."""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_name(header: str) -> str | None:
    """
    Extract candidate name from the resume header.

    Uses the first meaningful line unless it looks like an email,
    phone number, URL/handle, or common heading/section label.
    """
    if not header:
        return None

    ignored_patterns = [
        r"@",
        r"https?://",
        r"www\.",
        r"\+?\d[\d\s().-]{7,}",
        # Bare domain-style links/handles with no scheme, e.g.
        # "linkedin.com/in/...", "github.com/...",
        # "leetcode.com/u/..." - a "/" almost never appears in a
        # real name, and these commonly sit right next to the name
        # in a resume header.
        r"/",
        r"\b(?:linkedin|github|gitlab|leetcode|hackerrank|"
        r"stackoverflow|twitter|behance|kaggle|portfolio)\b",
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

        word_count = len(line.split())

        # A reasonable name should not be excessively long. A
        # single "word" is also accepted (word_count == 1): some
        # PDF text extraction loses the space between a first and
        # last name (e.g. "John Smith" -> "JohnSmith"), so a short,
        # purely-alphabetic first line is still a plausible name.
        if word_count == 1:
            if line.isalpha() and 2 <= len(line) <= 60:
                return line

            continue

        if 2 <= word_count <= 6 and len(line) <= 100:
            return line

    return None


def extract_email(header: str) -> str | None:
    """Extract the candidate's email address from the header."""
    if not header:
        return None

    match = re.search(
        r"[\w.+-]+@[\w-]+\.[\w.-]+",
        header,
    )

    return match.group(0) if match else None


def extract_phone(header: str) -> str | None:
    """
    Extract a phone number from the header, if one is present.

    Requires at least 7 digits so it doesn't mistake years, zip
    codes, or other short digit runs for a phone number.
    """
    if not header:
        return None

    pattern = re.compile(
        r"(?<!\w)"
        r"(\+?\d{1,3}[\s.-]?)?"
        r"(\(?\d{2,4}\)?[\s.-]?){2,4}\d{2,4}"
        r"(?!\w)"
    )

    for match in pattern.finditer(header):
        candidate = match.group(0).strip()
        digits = re.sub(r"\D", "", candidate)

        if 7 <= len(digits) <= 15:
            return candidate

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
            r"^(?:[-*•●▪◦‣]|\d+[.)])[\s​]*",
            "",
            line,
        ).strip()

        if line:
            items.append(line)

    return deduplicate(items)


def _strip_category_label(item: str) -> str:
    """
    Drop a leading "Category Label:" prefix from a skills line.

    Skill lists are commonly grouped by category, e.g.
    "Programming Languages: Python, Java" - without this, the
    label stays glued to the first value after the colon.
    """
    return re.sub(r"^[^:\n]{1,50}:\s*", "", item).strip()


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
            item = _strip_category_label(item)

            # A line that was *only* a category label (e.g. the
            # heading and its values were split onto separate
            # lines by PDF text extraction) leaves nothing here -
            # skip it rather than adding an empty/label-only entry.
            if not item:
                continue

            # Handle bullet containing multiple comma-separated skills.
            parts = re.split(r"[,;|]", item)

            for part in parts:
                part = clean_text(part)

                if part:
                    result.append(part)

        return deduplicate(result)

    # Handle comma/semicolon/pipe-separated skills.
    parts = re.split(r"[,;|]", _strip_category_label(text))

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

    def _header_start(role_company_index: int) -> int:
        """
        Resolve where this entry's role/company header actually
        begins.

        Handles both a single combined line ("Role | Company") and
        the equally common two-line template where the title and
        company sit on separate consecutive lines immediately
        before the date range - in that case there is no "|"/"-"
        separator on the line right before the date, so we look one
        line further back for the title.
        """
        line = lines[role_company_index]
        _, company = _split_role_company(line)

        if company is not None:
            return role_company_index

        previous_index = role_company_index - 1

        if previous_index < 0:
            return role_company_index

        previous_line = lines[previous_index]

        if date_pattern.search(
            previous_line
        ) or _looks_like_section_heading(previous_line):
            return role_company_index

        return previous_index

    def _next_entry_boundary(next_date_index: int) -> int:
        """
        Given the line index of the NEXT experience entry's date
        match, return the index marking where the CURRENT entry's
        description must stop (exclusive) - the first line
        belonging to the next entry's own header, whichever of the
        two header shapes it uses (title+date combined on one line,
        or title/company on the line(s) before a separate date line).
        """
        next_line = lines[next_date_index]
        next_match = date_pattern.search(next_line)

        if next_match:
            next_inline_title = next_line[
                : next_match.start()
            ].strip(" \t-–—|:")

            if next_inline_title and not _looks_like_section_heading(
                next_inline_title
            ):
                return next_date_index

        next_role_company_index = next_date_index - 1

        if next_role_company_index < 0:
            return next_date_index

        if date_pattern.search(lines[next_role_company_index]):
            return next_role_company_index

        return _header_start(next_role_company_index)

    experiences: list[Experience] = []

    for position, (date_index, match) in enumerate(date_matches):

        start_date = match.group(1)
        end_date = match.group(2)

        # Some templates put the title and date on the SAME line
        # ("Software Development Intern Jan 2026 - Jun 2026"), with
        # the company following on the NEXT line - the mirror image
        # of the "title/company before the date" templates handled
        # below. Detect this first: if there is real text before the
        # date match on its own line, that text is the role, and the
        # company (if present) comes after, not before.
        inline_title = lines[date_index][:match.start()].strip(
            " \t-–—|:"
        )

        if inline_title and not _looks_like_section_heading(
            inline_title
        ):
            role = clean_text(inline_title)
            company = None
            header_end = date_index

            next_index = date_index + 1

            if (
                next_index < len(lines)
                and not date_pattern.search(lines[next_index])
                and not _looks_like_section_heading(
                    lines[next_index]
                )
                and not _looks_like_bullet_line(lines[next_index])
            ):
                company = clean_text(lines[next_index])
                header_end = next_index

            description_start = header_end + 1

            if position + 1 < len(date_matches):
                description_end = _next_entry_boundary(
                    date_matches[position + 1][0]
                )
            else:
                description_end = len(lines)

            description_lines = [
                line
                for line in lines[
                    description_start:description_end
                ]
                if not _looks_like_section_heading(line)
            ]

            description = (
                "\n".join(description_lines).strip() or None
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

            continue

        # The line(s) immediately before the date range normally
        # contain role + company.
        role_company_index = date_index - 1

        if role_company_index < 0:
            continue

        role_company_line = lines[role_company_index]

        # Don't treat another date line as role/company.
        if date_pattern.search(role_company_line):
            continue

        header_start = _header_start(role_company_index)

        if header_start != role_company_index:
            # Title and company are on two separate lines: the
            # later line (immediately before the date) is the
            # company, the earlier one is the role/title.
            role = clean_text(lines[header_start])
            company = clean_text(role_company_line)
        else:
            role, company = _split_role_company(
                role_company_line
            )

        # Description begins immediately after the date line.
        description_start = date_index + 1

        # The next date range marks the next experience - exclude
        # whichever line(s) form its role/company header.
        if position + 1 < len(date_matches):
            description_end = _next_entry_boundary(
                date_matches[position + 1][0]
            )
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

    Handles both the "Institution - Degree - Dates" single-line
    format and the equally common multi-line format where the
    institution name and the date range each sit on their own line
    around the degree line.
    """
    if not text:
        return []

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    results: list[Education] = []

    # Word-bounded so e.g. "M.E." can't accidentally match inside an
    # unrelated word like "ACHIEVEMENTS" (which contains "...ie-ve-
    # ME-nts").
    degree_pattern = re.compile(
        r"(?i)\b"
        r"(bachelor|master|b\.?tech|m\.?tech|b\.?e\.?|m\.?e\.?|"
        r"bsc|msc|b\.?sc|m\.?sc|mba|phd|doctorate|associate)"
        r"\b"
    )

    date_pattern = re.compile(
        r"(?i)"
        r"(\d{4})\s*(?:-|–|—|to)\s*"
        r"(?:expected|anticipated|exp\.?)?\s*"
        r"(\d{4}|present|current)"
    )

    def _looks_like_metadata_line(candidate: str) -> bool:
        return bool(
            degree_pattern.search(candidate)
            or date_pattern.search(candidate)
        )

    for index, line in enumerate(lines):
        degree_match = degree_pattern.search(line)

        if not degree_match:
            continue

        degree = degree_match.group(0)

        before_degree = line[:degree_match.start()].strip(
            " ,-–—|"
        )

        after_degree = line[degree_match.end():].strip(
            " ,-–—|"
        )

        institution = before_degree or None
        field = after_degree or None

        # The institution name commonly sits on its own line
        # immediately before the degree line.
        if institution is None and index > 0:
            previous_line = lines[index - 1]

            if not _looks_like_metadata_line(previous_line):
                institution = previous_line

        # The date range commonly sits on its own line immediately
        # before or after the degree line.
        start_date = None
        end_date = None

        for candidate_line in (
            line,
            lines[index + 1] if index + 1 < len(lines) else "",
            lines[index - 1] if index > 0 else "",
        ):
            date_match = date_pattern.search(candidate_line)

            if date_match:
                start_date = date_match.group(1)
                end_date = date_match.group(2)
                break

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


_PROJECT_LINK_LABELS = {
    "github",
    "gitlab",
    "demo",
    "live demo",
    "link",
    "view project",
    "source code",
}

_PROJECT_BULLET_ONLY = re.compile(r"^[-*•●▪◦‣|]$")
_PROJECT_BULLET_PREFIX = re.compile(
    r"^(?:[-*•●▪◦‣|]|\d+[.)])[\s​]*"
)
_PROJECT_TECHSTACK_PREFIX = re.compile(
    r"(?i)^(?:tech\s*stack|technologies(?:\s*used)?|"
    r"tools(?:\s*&?\s*technologies)?)\s*:\s*(.*)$"
)


def extract_projects(text: str) -> list[Project]:
    """
    Extract structured project entries (name, description,
    technologies) from a projects section.

    Supports both a flat bulleted list of project names
    ("- Project Name") and the common template format where a
    bullet marker sits alone on its own line, the project name
    follows on the next line, free-text description lines follow
    that, and a trailing "Techstack: ..." line lists technologies.
    """
    if not text:
        return []

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    projects: list[Project] = []

    current_name: str | None = None
    description_lines: list[str] = []
    technologies: list[str] = []
    awaiting_name = False

    def flush() -> None:
        if current_name:
            projects.append(
                Project(
                    name=current_name,
                    description=(
                        "\n".join(description_lines).strip()
                        or None
                    ),
                    technologies=technologies,
                )
            )

    for line in lines:
        techstack_match = _PROJECT_TECHSTACK_PREFIX.match(line)

        if techstack_match:
            technologies = [
                clean_text(part)
                for part in re.split(
                    r"[,;]", techstack_match.group(1)
                )
                if clean_text(part)
            ]
            continue

        if _PROJECT_BULLET_ONLY.match(line):
            # A bullet marker alone on its own line - the project
            # name is the next non-bullet line.
            flush()
            current_name = None
            description_lines = []
            technologies = []
            awaiting_name = True
            continue

        bullet_stripped = _PROJECT_BULLET_PREFIX.sub(
            "", line
        ).strip()

        if (
            bullet_stripped
            and bullet_stripped != line
        ):
            # Bullet marker and project name on the same line.
            flush()
            current_name = bullet_stripped
            description_lines = []
            technologies = []
            awaiting_name = False
            continue

        if awaiting_name:
            current_name = line
            awaiting_name = False
            continue

        if current_name is None:
            # No project has started yet and this line isn't a
            # bullet - nothing to attach it to.
            continue

        if line.casefold() in _PROJECT_LINK_LABELS:
            # A bare hyperlink-icon label (e.g. "GitHub", "Demo"),
            # not real project content.
            continue

        description_lines.append(line)

    flush()

    return projects


def extract_job_titles(experiences: list[Experience]) -> list[str]:
    """Extract roles from experience entries."""
    return deduplicate(
        [
            experience.role
            for experience in experiences
            if experience.role
        ]
    )


def calculate_duration_months(
    start_date: str | None,
    end_date: str | None,
) -> int | None:
    """
    Calculate the number of months between two resume date strings
    (e.g. "Aug 2025", "2023", "Present"). Returns None if the range
    can't be resolved.
    """
    import datetime

    if not start_date:
        return None

    start = parse_date(start_date)

    if start is None:
        return None

    end = (
        parse_date(end_date)
        if end_date
        else datetime.date.today()
    )

    if end is None:
        return None

    months = (
        (end.year - start.year) * 12
        + end.month
        - start.month
    )

    return months if months > 0 else None


def calculate_total_experience_years(
    experiences: list[Experience],
) -> float | None:
    """
    Calculate approximate total experience from date ranges.

    Returns None if no usable date ranges exist.
    """
    total_months = 0

    for experience in experiences:
        months = calculate_duration_months(
            experience.start_date,
            experience.end_date,
        )

        if months:
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


def _looks_like_bullet_line(line: str) -> bool:
    """
    Detect a bullet/list-item line, so it's never mistaken for a
    company name (e.g. when a title+date header line is immediately
    followed by a description bullet rather than a company line).
    """
    return bool(
        re.match(r"^(?:[-*•●▪◦‣]|\d+[.)])[\s​]*", line)
    )