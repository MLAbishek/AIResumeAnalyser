"""
Regression tests for specific JD-parsing bugs discovered while
investigating why data/raw/jd/jd001.pdf produced almost entirely
empty structured fields. Synthetic (but realistic) text is used so
these stay fast and deterministic; the real PDF is covered separately
by tests/api/test_real_document_parsing_api.py.
"""

from app.core.schemas import DocumentType, RawDocument, RawDocumentPage
from app.parsing.jd_extractors import extract_education_from_text
from app.parsing.jd_parser import JDParser


def _document(text: str) -> RawDocument:
    return RawDocument(
        document_id="regression-jd",
        document_type=DocumentType.JOB_DESCRIPTION,
        source_path="synthetic.txt",
        pages=[RawDocumentPage(page_number=1, text=text)],
        raw_text=text,
    )


class TestBulletCharacterRegression:
    def test_black_circle_bullets_with_zero_width_space_are_stripped(
        self,
    ):
        # jd001.pdf's actual bullet character, extracted by PyMuPDF,
        # is "●" (U+25CF) frequently followed by a zero-width space
        # (U+200B) - the old bullet-strip regex only recognized "•"
        # (U+2022) and left "● " glued onto every requirement.
        text = (
            "Java Developer Intern\n\n"
            "Required Skills:\n"
            "●​Strong understanding of Java fundamentals\n"
            "●​Basic knowledge of databases\n"
        )

        result = JDParser().parse(_document(text))

        assert (
            "Strong understanding of Java fundamentals"
            in result.required_skills
        )
        assert "Basic knowledge of databases" in result.required_skills
        assert not any(
            "●" in skill for skill in result.required_skills
        )


class TestCurlyApostropheHeadingRegression:
    def test_curly_apostrophe_benefits_heading_is_recognized(self):
        # PDFs generated from Word/Google Docs frequently use a
        # curly right single-quote (U+2019) rather than a straight
        # apostrophe in headings like "What You'll Gain" - the old
        # normalizer only matched the straight-apostrophe alias, so
        # the whole section fell through as unrecognized raw text.
        text = (
            "Java Developer Intern\n\n"
            "What You’ll Gain:\n"
            "Hands-on mentorship from senior engineers\n"
        )

        result = JDParser().parse(_document(text))

        assert result.raw_text is not None


class TestEducationFallbackRegression:
    def test_finds_degree_mentioned_inline_outside_a_dedicated_section(
        self,
    ):
        # jd001.pdf states its eligibility requirement inline in
        # prose ("Eligibility: B.E./B.Tech/B.Sc./BCA students...")
        # rather than under a dedicated "Education:" heading, so the
        # section-scoped extractor found nothing at all.
        text = (
            "Eligibility: B.E./B.Tech/B.Sc./BCA students in their "
            "final year or recent graduates are welcome to apply.\n"
        )

        matches = extract_education_from_text(text)

        assert len(matches) >= 1
        assert any("B.E." in match or "B.Tech" in match for match in matches)

    def test_does_not_false_match_the_common_word_be(self):
        # The fallback pattern's short-abbreviation branch (b.e./m.e.)
        # initially had optional periods, so it matched the bare word
        # "be" inside ordinary prose like "would be given" - this
        # produced garbage education-requirement entries which are
        # exactly the kind of fabricated-looking noise the pipeline
        # must not introduce.
        text = (
            "Based on performance during the internship, the "
            "possibility of a full-time offer would be given to "
            "outstanding interns. Note: We will also be doing "
            "periodic performance reviews.\n"
        )

        matches = extract_education_from_text(text)

        assert matches == []

    def test_dedicated_education_section_takes_priority_over_fallback(
        self,
    ):
        text = (
            "Software Engineer\n\n"
            "Education:\n"
            "- Bachelor's degree in Computer Science\n\n"
            "Benefits:\n"
            "This role would be a great fit for recent graduates.\n"
        )

        result = JDParser().parse(_document(text))

        assert result.education == [
            "Bachelor's degree in Computer Science"
        ]


class TestStructuredFieldsFromCleanlyExtractedText:
    def test_title_location_and_job_type_from_clean_multiline_text(
        self,
    ):
        # Reproduces the shape of text PyMuPDF now produces for
        # jd001.pdf (clean line breaks) as opposed to the
        # one-word-per-line fragmentation the previous pypdf-based
        # extraction produced, which prevented any of these
        # line-anchored patterns from matching at all.
        text = (
            "Java Developer Intern\n\n"
            "Location: Chennai, Work from Office\n"
            "Employment Type: Full-time\n\n"
            "We are looking for a passionate and driven Java "
            "Developer Intern to join our team.\n"
        )

        result = JDParser().parse(_document(text))

        assert result.title == "Java Developer Intern"
        assert result.location == "Chennai, Work from Office"
        assert result.job_type == "Full-time"
        # Summary extraction requires a dedicated "Summary:" section
        # (covered separately in test_jd_parser.py); this text has
        # none, so the header sentence is preserved in raw_text
        # instead, honestly, rather than being fabricated as a
        # summary.
        assert "passionate and driven" in result.raw_text
