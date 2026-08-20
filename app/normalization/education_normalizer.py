from app.normalization.normalizer_utils import (
    find_known_terms,
    normalize_text,
)


class EducationNormalizer:
    """
    Deterministically matches education requirements against
    candidate education, handling the common cases raw substring
    comparison misses:

    - a JD stated generically ("Bachelor's degree") must recognize
      any specific bachelor's-level qualification (B.Tech, B.Sc,
      B.E., BCA, ...) as satisfying it
    - a JD's acceptable field list ("Computer Science, Information
      Technology, Artificial Intelligence, or a related field") must
      match a candidate field expressed differently
      ("Computer Science / Information Technology")

    A specific-type requirement ("B.Tech" exactly) is intentionally
    NOT treated as interchangeable with a different specific type
    ("B.Sc") - only a genuinely generic requirement is broadened to
    match any degree at that level. This keeps existing exact/
    substring matching behavior unchanged and only adds new coverage
    for generic phrasing.
    """

    # Broad/generic phrasing only - deliberately excludes specific
    # abbreviations so a JD asking for one specific degree type is
    # never silently satisfied by a different specific type.
    GENERIC_LEVEL_TERMS = {
        "bachelor": "bachelor",
        "bachelors": "bachelor",
        "bachelor's": "bachelor",
        "bachelor's degree": "bachelor",
        "bachelors degree": "bachelor",
        "undergraduate degree": "bachelor",
        "undergraduate": "bachelor",
        "master": "master",
        "masters": "master",
        "master's": "master",
        "master's degree": "master",
        "masters degree": "master",
        "postgraduate degree": "master",
        "postgraduate": "master",
        "doctorate": "doctorate",
        "phd": "doctorate",
        "ph.d": "doctorate",
        "ph.d.": "doctorate",
    }

    # Specific degree-type markers, used only to interpret what
    # level a CANDIDATE's actual degree is at. Bare 2-letter forms
    # ("be", "me", "ba", "ma") are deliberately omitted - they are
    # ordinary English words and unsafe to match on word boundaries
    # alone (see the JD-parser false-positive this project already
    # hit with "would be given").
    SPECIFIC_TYPE_LEVELS = {
        "b.tech": "bachelor",
        "btech": "bachelor",
        "b.e.": "bachelor",
        "b.sc": "bachelor",
        "b.sc.": "bachelor",
        "bsc": "bachelor",
        "bca": "bachelor",
        "b.com": "bachelor",
        "bcom": "bachelor",
        "b.a.": "bachelor",
        "bachelor of technology": "bachelor",
        "bachelor of engineering": "bachelor",
        "bachelor of science": "bachelor",
        "m.tech": "master",
        "mtech": "master",
        "m.e.": "master",
        "m.sc": "master",
        "m.sc.": "master",
        "msc": "master",
        "mca": "master",
        "mba": "master",
        "m.com": "master",
        "mcom": "master",
        "master of technology": "master",
        "master of science": "master",
        "master of business administration": "master",
    }

    FIELD_KEYWORDS = {
        "computer science": "computer science",
        "information technology": "information technology",
        "artificial intelligence": "artificial intelligence",
        "machine learning": "machine learning",
        # Bare "AI"/"ML" abbreviations - extremely common in JDs
        # ("AI/ML", "AI & ML") and candidate degree titles. Safe to
        # match as standalone tokens: find_known_terms only matches
        # on word boundaries, so these never match mid-word (e.g.
        # "domain", "html").
        "ai": "artificial intelligence",
        "ml": "machine learning",
        "data science": "data science",
        "software engineering": "software engineering",
        "computer engineering": "computer engineering",
        "information science": "information science",
        "information systems": "information systems",
        "electronics and communication": "electronics and communication",
        "electronics engineering": "electronics engineering",
        "electrical engineering": "electrical engineering",
        "mechanical engineering": "mechanical engineering",
        "civil engineering": "civil engineering",
        "mathematics": "mathematics",
        "statistics": "statistics",
    }

    def requirement_satisfied(
        self,
        requirement_degree: str | None,
        requirement_field: str | None,
        candidate_degree: str | None,
        candidate_field: str | None = None,
    ) -> bool:
        """
        Determine whether a candidate's education satisfies one JD
        education requirement.

        `requirement_degree` may be a clean, short degree name
        ("B.Tech") or a full free-text requirement sentence (JD
        parsers commonly extract requirements as prose, with no
        separate field). Both shapes are handled.
        """

        candidate_text = normalize_text(
            " ".join(
                part
                for part in [candidate_degree, candidate_field]
                if part
            )
        ) if (candidate_degree or candidate_field) else ""

        degree_match = True

        if requirement_degree:
            requirement_degree_normalized = normalize_text(
                requirement_degree
            )

            degree_match = (
                requirement_degree_normalized in candidate_text
            )

            if not degree_match:
                degree_match = self._generic_level_matches(
                    requirement_degree_normalized,
                    candidate_text,
                )

        field_match = True

        if requirement_field:
            requirement_field_normalized = normalize_text(
                requirement_field
            )

            field_match = (
                requirement_field_normalized in candidate_text
            )

            if not field_match:
                field_match = self._field_overlap(
                    requirement_field_normalized,
                    candidate_text,
                )
        elif requirement_degree and self._mentions_any_field(
            normalize_text(requirement_degree)
        ):
            # Free-text requirement (whole sentence in
            # requirement_degree, no separate field) - still check
            # whether any field keyword it mentions appears in the
            # candidate's education text.
            field_match = self._field_overlap(
                normalize_text(requirement_degree),
                candidate_text,
            )

        return degree_match and field_match

    def _generic_level_matches(
        self,
        requirement_text: str,
        candidate_text: str,
    ) -> bool:
        requirement_levels = find_known_terms(
            requirement_text,
            self.GENERIC_LEVEL_TERMS,
        )

        if not requirement_levels:
            return False

        candidate_levels = set(
            find_known_terms(
                candidate_text,
                {
                    **self.GENERIC_LEVEL_TERMS,
                    **self.SPECIFIC_TYPE_LEVELS,
                },
            )
        )

        return bool(set(requirement_levels) & candidate_levels)

    def _field_overlap(
        self,
        requirement_text: str,
        candidate_text: str,
    ) -> bool:
        requirement_fields = set(
            find_known_terms(
                requirement_text,
                self.FIELD_KEYWORDS,
            )
        )

        if not requirement_fields:
            return False

        candidate_fields = set(
            find_known_terms(
                candidate_text,
                self.FIELD_KEYWORDS,
            )
        )

        return bool(requirement_fields & candidate_fields)

    def _mentions_any_field(self, text: str) -> bool:
        return bool(
            find_known_terms(text, self.FIELD_KEYWORDS)
        )
