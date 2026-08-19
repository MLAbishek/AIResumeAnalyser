"""
Targeted regression tests for the JD matching-quality investigation:
a JD requirement was frequently a full prose sentence ("Good
understanding of HTML, CSS, and JavaScript.") rather than an atomic
skill, and the skill matcher was comparing entire sentences against
resume skills verbatim - so nothing ever matched, eligibility always
failed, and every requirement showed as a gap even for a
substantially-overlapping candidate.

These tests cover extract_requirement_concepts()/_many() (splitting
a requirement sentence into atomic, canonical concepts) and the
alias/false-positive-safety additions to SKILL_ALIASES.
"""

from app.normalization.skill_normalizer import SkillNormalizer


class TestSentenceToAtomicConcepts:
    def test_html_css_javascript_sentence(self):
        normalizer = SkillNormalizer()

        result = normalizer.extract_requirement_concepts(
            "Good understanding of HTML, CSS, and JavaScript."
        )

        assert "html" in result
        assert "css" in result
        assert "javascript" in result

    def test_react_or_frontend_framework_sentence(self):
        normalizer = SkillNormalizer()

        result = normalizer.extract_requirement_concepts(
            "Familiarity with React.js or another modern "
            "frontend framework."
        )

        assert "react" in result

    def test_rest_apis_and_json_sentence(self):
        normalizer = SkillNormalizer()

        result = normalizer.extract_requirement_concepts(
            "Basic knowledge of REST APIs and JSON."
        )

        assert "rest" in result
        assert "json" in result

    def test_git_and_github_sentence(self):
        normalizer = SkillNormalizer()

        result = normalizer.extract_requirement_concepts(
            "Familiarity with Git and GitHub."
        )

        assert "git" in result
        assert "github" in result

    def test_a_single_atomic_skill_still_works(self):
        normalizer = SkillNormalizer()

        assert normalizer.extract_requirement_concepts(
            "Docker"
        ) == ["docker"]

    def test_unmatched_sentence_is_kept_as_a_single_fallback_by_default(
        self,
    ):
        normalizer = SkillNormalizer()

        result = normalizer.extract_requirement_concepts(
            "Good problem-solving and debugging skills."
        )

        assert result == [
            "good problem-solving and debugging skills"
        ]

    def test_unmatched_sentence_is_dropped_when_fallback_disabled(
        self,
    ):
        normalizer = SkillNormalizer()

        result = normalizer.extract_requirement_concepts(
            "Good problem-solving and debugging skills.",
            keep_unmatched_fallback=False,
        )

        assert result == []

    def test_many_flattens_and_dedupes_across_sentences(self):
        normalizer = SkillNormalizer()

        result = normalizer.extract_requirement_concepts_many(
            [
                "Good understanding of HTML, CSS, and JavaScript.",
                "Understanding of JavaScript concepts such as "
                "ES6+, DOM manipulation, promises, and "
                "asynchronous programming.",
            ]
        )

        assert result.count("javascript") == 1


class TestAliasCoverageForFrontendVocabulary:
    def test_html_and_html5_share_a_canonical_form(self):
        normalizer = SkillNormalizer()

        assert normalizer.normalize("HTML") == normalizer.normalize(
            "HTML5"
        )

    def test_css_and_css3_share_a_canonical_form(self):
        normalizer = SkillNormalizer()

        assert normalizer.normalize("CSS") == normalizer.normalize(
            "CSS3"
        )

    def test_react_and_react_js_share_a_canonical_form(self):
        normalizer = SkillNormalizer()

        assert normalizer.normalize(
            "React"
        ) == normalizer.normalize("React.js")

    def test_rest_api_and_rest_apis_share_a_canonical_form(self):
        normalizer = SkillNormalizer()

        assert normalizer.normalize(
            "REST API"
        ) == normalizer.normalize("REST APIs")

    def test_responsive_design_and_responsive_web_design_match(
        self,
    ):
        normalizer = SkillNormalizer()

        assert normalizer.normalize(
            "Responsive Design"
        ) == normalizer.normalize("Responsive Web Design")

    def test_tailwind_and_tailwind_css_match(self):
        normalizer = SkillNormalizer()

        assert normalizer.normalize(
            "Tailwind"
        ) == normalizer.normalize("Tailwind CSS")

    def test_java_is_never_confused_with_javascript(self):
        normalizer = SkillNormalizer()

        assert normalizer.normalize(
            "Java"
        ) != normalizer.normalize("JavaScript")

    def test_java_does_not_match_inside_a_javascript_sentence(self):
        normalizer = SkillNormalizer()

        result = normalizer.extract_requirement_concepts(
            "Good understanding of HTML, CSS, and JavaScript."
        )

        assert "java" not in result
        assert "javascript" in result


class TestSoftRequirementSignalDetection:
    def test_familiarity_with_is_a_soft_signal(self):
        normalizer = SkillNormalizer()

        assert normalizer.is_soft_requirement_signal(
            "Familiarity with Git and GitHub."
        )

    def test_basic_knowledge_of_is_a_soft_signal(self):
        normalizer = SkillNormalizer()

        assert normalizer.is_soft_requirement_signal(
            "Basic knowledge of REST APIs and JSON."
        )

    def test_good_understanding_of_is_not_a_soft_signal(self):
        normalizer = SkillNormalizer()

        assert not normalizer.is_soft_requirement_signal(
            "Good understanding of HTML, CSS, and JavaScript."
        )

    def test_a_bare_atomic_skill_is_not_a_soft_signal(self):
        normalizer = SkillNormalizer()

        assert not normalizer.is_soft_requirement_signal(
            "Docker"
        )
