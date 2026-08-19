"""
Regression tests for specific resume-parsing bugs discovered while
investigating why data/raw/resumes/resume_001.pdf produced garbage/
missing structured data. Each test reproduces the failure shape with
synthetic (but realistic) text rather than depending on the PDF
library's exact output, so these stay fast and deterministic; the
real PDF is covered separately by tests/api/test_real_document_parsing_api.py.
"""

from app.core.schemas import DocumentType, RawDocument, RawDocumentPage
from app.parsing.resume_parse import ResumeParser


def _document(text: str) -> RawDocument:
    return RawDocument(
        document_id="regression-resume",
        document_type=DocumentType.RESUME,
        source_path="synthetic.txt",
        pages=[RawDocumentPage(page_number=1, text=text)],
        raw_text=text,
    )


class TestNameExtractionRegression:
    def test_does_not_pick_a_bare_social_link_line_as_the_name(
        self,
    ):
        # Header format that previously broke name extraction: no
        # space between first/last name, followed by a line that
        # mixes an email with bare (schemeless) social links, then a
        # location line that used to be wrongly picked as the name.
        text = (
            "AbishekJ\n"
            "j.abishek3123@gmail.com linkedin.com/in/j-abishek\n"
            "github.com/MLAbishek Chennai, India\n"
            "WORK EXPERIENCE\n"
            "Engineer\n"
            "Acme\n"
            "Jan 2023 - Present\n"
        )

        result = ResumeParser().parse(_document(text))

        assert result.name == "AbishekJ"

    def test_two_word_name_still_works(self):
        text = "Jane Doe\njane@example.com\n\nSKILLS\nPython\n"

        result = ResumeParser().parse(_document(text))

        assert result.name == "Jane Doe"


class TestEmailPhoneExtractionRegression:
    def test_extracts_email_from_header(self):
        text = "John Smith\njohn.smith@example.com\n\nSKILLS\nSQL\n"

        result = ResumeParser().parse(_document(text))

        assert result.email == "john.smith@example.com"

    def test_extracts_phone_when_present(self):
        text = (
            "John Smith\n"
            "john@example.com | +1 (415) 555-0132\n"
            "\nSKILLS\nSQL\n"
        )

        result = ResumeParser().parse(_document(text))

        assert result.phone is not None
        assert sum(c.isdigit() for c in result.phone) >= 7

    def test_phone_stays_none_when_genuinely_absent(self):
        # Mirrors resume_001.pdf, which has no phone number
        # anywhere in its text at all.
        text = "John Smith\njohn@example.com\n\nSKILLS\nSQL\n"

        result = ResumeParser().parse(_document(text))

        assert result.phone is None


class TestSkillsCategoryLabelRegression:
    def test_strips_category_label_glued_to_first_skill(self):
        # PDF text extraction commonly puts the category label and
        # its values on separate lines, or leaves them on the same
        # line - either way the label must not leak into the first
        # extracted skill.
        text = (
            "Jane Doe\n\n"
            "SKILLS\n"
            "Programming Languages: Python, Java\n"
            "Frameworks:\n"
            "Flask, Django\n"
        )

        result = ResumeParser().parse(_document(text))

        assert "Python" in result.skills
        assert "Java" in result.skills
        assert "Flask" in result.skills
        assert "Django" in result.skills
        assert "Programming Languages: Python" not in result.skills
        assert "Programming Languages" not in result.skills
        assert "Frameworks" not in result.skills

    def test_strips_black_circle_bullets_and_zero_width_space(self):
        # jd001.pdf's real bullet character is "●" (U+25CF), often
        # immediately followed by a zero-width space (U+200B) in
        # PyMuPDF's extraction - the old bullet regex only handled
        # "•" (U+2022) and left "●" in the extracted skill text.
        text = (
            "Jane Doe\n\n"
            "SKILLS\n"
            "●​Python\n"
            "●​SQL\n"
        )

        result = ResumeParser().parse(_document(text))

        assert "Python" in result.skills
        assert "SQL" in result.skills
        assert not any("●" in skill for skill in result.skills)


class TestEducationExtractionRegression:
    def test_degree_pattern_does_not_false_match_inside_achievements(
        self,
    ):
        # "M.E." without word boundaries matched the bare substring
        # "me" inside "ACHIEVEMENTS", producing a garbage education
        # entry (institution="AWARDS & ACHIEVE", degree="ME").
        text = (
            "Jane Doe\n\n"
            "EDUCATION\n"
            "State University\n"
            "B.Tech Computer Science\n"
            "Sep 2020 - Expected 2024\n"
            "AWARDS & ACHIEVEMENTS\n"
            "Finalist in a national hackathon.\n"
        )

        result = ResumeParser().parse(_document(text))

        assert len(result.education) == 1
        assert result.education[0].degree == "B.Tech"
        assert result.education[0].institution == "State University"
        assert not any(
            "ACHIEVE" in (edu.institution or "")
            for edu in result.education
        )

    def test_institution_on_line_before_degree_is_captured(self):
        # Common two-line template: institution name, then degree +
        # field on the next line, with no separator on either line
        # tying them together.
        text = (
            "Jane Doe\n\n"
            "EDUCATION\n"
            "St. Joseph's College of Engineering\n"
            "B.Tech Artificial Intelligence and Machine Learning\n"
            "Sep 2023 - Expected 2027\n"
        )

        result = ResumeParser().parse(_document(text))

        assert len(result.education) == 1
        entry = result.education[0]
        assert entry.institution == "St. Joseph's College of Engineering"
        assert entry.degree == "B.Tech"
        assert entry.field == "Artificial Intelligence and Machine Learning"
        assert entry.start_date == "2023"
        assert entry.end_date == "2027"

    def test_awards_heading_is_recognized_and_excludes_from_education(
        self,
    ):
        text = (
            "Jane Doe\n\n"
            "EDUCATION\n"
            "State University\n"
            "B.Tech Computer Science\n"
            "AWARDS & ACHIEVEMENTS\n"
            "Won first place.\n"
        )

        result = ResumeParser().parse(_document(text))

        assert len(result.education) == 1


class TestExperienceExtractionRegression:
    def test_role_and_company_on_separate_lines_are_not_swapped(
        self,
    ):
        # Common two-line template: title line, then company line,
        # then the date range - previously the whole company-only
        # line was misread as the role, and the actual title line
        # was dropped entirely.
        text = (
            "Jane Doe\n\n"
            "WORK EXPERIENCE\n"
            "Deep Learning Intern\n"
            "Authenta AI\n"
            "Aug 2025 - Feb 2026\n"
            "Built deepfake detection models.\n"
        )

        result = ResumeParser().parse(_document(text))

        assert len(result.experience) == 1
        assert result.experience[0].role == "Deep Learning Intern"
        assert result.experience[0].company == "Authenta AI"

    def test_two_separate_line_experiences_do_not_bleed_into_each_other(
        self,
    ):
        text = (
            "Jane Doe\n\n"
            "WORK EXPERIENCE\n"
            "Deep Learning Intern\n"
            "Authenta AI\n"
            "Aug 2025 - Feb 2026\n"
            "Built deepfake detection models.\n"
            "AI Research Intern\n"
            "Foviatech\n"
            "May 2025 - Jul 2025\n"
            "Wrote research proposals.\n"
        )

        result = ResumeParser().parse(_document(text))

        assert len(result.experience) == 2
        assert result.experience[0].role == "Deep Learning Intern"
        assert result.experience[0].company == "Authenta AI"
        assert result.experience[1].role == "AI Research Intern"
        assert result.experience[1].company == "Foviatech"
        # The second entry's title line must not have leaked into
        # the first entry's description.
        assert "AI Research Intern" not in (
            result.experience[0].description or ""
        )

    def test_single_line_role_company_format_still_works(self):
        text = (
            "Jane Doe\n\n"
            "WORK EXPERIENCE\n"
            "ML Engineer | ABC Technologies\n"
            "Jan 2023 - Present\n"
            "- Built models\n"
        )

        result = ResumeParser().parse(_document(text))

        assert len(result.experience) == 1
        assert result.experience[0].role == "ML Engineer"
        assert result.experience[0].company == "ABC Technologies"

    def test_plural_experience_heading_is_recognized(self):
        # "WORK EXPERIENCES" (plural) previously did not match the
        # "work experience" alias at all, so the whole section was
        # never even isolated - everything fell into the header.
        text = (
            "Jane Doe\n\n"
            "WORK EXPERIENCES\n"
            "ML Engineer\n"
            "ABC Technologies\n"
            "Jan 2023 - Present\n"
        )

        result = ResumeParser().parse(_document(text))

        assert len(result.experience) == 1
        assert result.experience[0].role == "ML Engineer"


class TestProjectExtractionRegression:
    def test_bullet_only_line_then_title_then_techstack(self):
        text = (
            "Jane Doe\n\n"
            "PROJECTS\n"
            "|\n"
            "Resume Screening System\n"
            "GitHub\n"
            "An AI-assisted resume screening platform.\n"
            "Techstack: Python, FastAPI\n"
        )

        result = ResumeParser().parse(_document(text))

        assert len(result.projects) == 1
        project = result.projects[0]
        assert project.name == "Resume Screening System"
        assert "GitHub" not in (project.description or "")
        assert project.technologies == ["Python", "FastAPI"]

    def test_simple_bulleted_project_names_still_work(self):
        text = (
            "Jane Doe\n\n"
            "PROJECTS\n"
            "- Resume Screening System\n"
            "- Image Classification Platform\n"
        )

        result = ResumeParser().parse(_document(text))

        names = [p.name for p in result.projects]
        assert "Resume Screening System" in names
        assert "Image Classification Platform" in names
