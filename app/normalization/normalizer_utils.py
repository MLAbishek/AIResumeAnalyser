import re
import unicodedata


def _term_pattern(term: str) -> re.Pattern:
    """
    Build a safe word-boundary regex for one vocabulary term.

    A plain `\\b` is only meaningful next to a word character, so a
    term like "es6+" (ends in a non-word character) or "shadcn/ui"
    only gets a boundary on the side that actually has one - this is
    what keeps "java" from ever matching inside "javascript" while
    still correctly matching terms with symbols in them.
    """

    escaped = re.escape(term)
    start = r"\b" if term[0].isalnum() else ""
    end = r"\b" if term[-1].isalnum() else ""

    return re.compile(start + escaped + end)


def find_known_terms(
    text: str,
    vocabulary: dict[str, str],
) -> list[str]:
    """
    Scan already-normalized text for occurrences of any vocabulary
    term, matched on safe word boundaries, and return the canonical
    values they map to - deduplicated, in left-to-right order of
    first appearance in the text.

    `vocabulary` maps a known term (e.g. "html5") to its canonical
    form (e.g. "html"). Used to pull known concepts out of a longer
    requirement sentence without any free-form NLP or fuzzy matching.

    When one matched term's span is fully contained inside another
    matched term's span at the SAME text position (e.g. "css" is a
    genuine standalone word inside "tailwind css", so both would
    otherwise match), only the longer/more specific term is kept -
    a compound term like "tailwind css" is a distinct concept from
    plain "css", and letting the shorter match win would misreport
    which specific one a sentence actually named.
    """

    candidates = []

    for term, canonical in vocabulary.items():
        match = _term_pattern(term).search(text)

        if match:
            candidates.append(
                (match.start(), match.end(), canonical)
            )

    kept = [
        (start, end, canonical)
        for start, end, canonical in candidates
        if not any(
            other_start <= start
            and end <= other_end
            and (other_start, other_end) != (start, end)
            for other_start, other_end, _ in candidates
        )
    ]

    kept.sort(key=lambda item: item[0])

    found = []
    seen = set()

    for _, _, canonical in kept:
        if canonical not in seen:
            found.append(canonical)
            seen.add(canonical)

    return found


REQUIREMENT_GROUP_SEPARATOR = "|"


def split_requirement_group(entry: str) -> list[str]:
    """
    Split one canonical requirement entry into its alternatives.

    A JD requirement is either a single mandatory concept ("python",
    no separator - the overwhelmingly common case) or a group of
    interchangeable alternatives encoded as
    "java|python|c++|c#" (built by
    SkillNormalizer.extract_requirement_groups(): "at least one
    language such as X, Y, or Z" means satisfying ANY ONE, not ALL).
    Satisfying ANY alternative in the returned list satisfies the
    whole entry.

    A plain entry with no separator returns a single-item list, so
    every existing caller that already treats each requirement
    string as one atomic, always-mandatory value keeps working
    unchanged - this is purely additive.
    """

    if REQUIREMENT_GROUP_SEPARATOR not in entry:
        return [entry]

    return [
        alternative
        for alternative in entry.split(
            REQUIREMENT_GROUP_SEPARATOR
        )
        if alternative
    ]


def normalize_text(value: str) -> str:
    """
    Normalize text for deterministic matching.

    Steps:
    1. Unicode normalization
    2. Lowercase
    3. Normalize separators
    4. Collapse whitespace
    5. Strip surrounding whitespace
    """

    if not isinstance(value, str):
        raise TypeError("value must be a string")

    value = unicodedata.normalize("NFKC", value)

    value = value.lower().strip()

    value = re.sub(r"[\u2010-\u2015]", "-", value)

    value = re.sub(r"\s+", " ", value)

    return value