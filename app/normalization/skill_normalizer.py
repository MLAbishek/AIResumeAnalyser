import re
from typing import Iterable

from app.normalization.normalizer_utils import (
    find_known_terms,
    normalize_text,
)


class SkillNormalizer:
    """
    Deterministically maps extracted skill variants
    to canonical skill names.
    """

    SKILL_ALIASES = {
        # Python
        "python": "python",
        "python3": "python",
        "py": "python",

        # PyTorch
        "pytorch": "pytorch",
        "py torch": "pytorch",
        "py-torch": "pytorch",

        # TensorFlow
        "tensorflow": "tensorflow",
        "tensor flow": "tensorflow",
        "tf": "tensorflow",

        # General-purpose programming languages. "java" and "c" are
        # short, common-word-adjacent tokens, so these rely entirely
        # on find_known_terms()'s safe word-boundary matching (\b on
        # both sides for alphanumeric terms) - "java" cannot match
        # inside "javascript" for the same reason "java" != "javascript"
        # already held for the existing javascript/java script alias
        # below. Bare single-letter "c"/"r" are deliberately excluded
        # (unacceptable false-positive risk even with word boundaries -
        # "c" would match the article "a" is not one, but stray
        # single-letter tokens are common enough in prose/formatting
        # to be unsafe).
        "java": "java",
        "c++": "c++",
        "cpp": "c++",
        "c#": "c#",
        "csharp": "c#",
        "c sharp": "c#",
        "golang": "go",
        "go lang": "go",
        "kotlin": "kotlin",
        "swift": "swift",
        "rust": "rust",
        "ruby": "ruby",
        "php": "php",
        "scala": "scala",

        # JavaScript
        "javascript": "javascript",
        "java script": "javascript",
        # Note: bare "js" is deliberately NOT aliased here (unlike
        # entity_normalizer.py's exact-match technology list, where
        # it's safe). find_known_terms() scans whole sentences on
        # word boundaries, and "." is a non-word character - so a
        # bare "js" alias falsely matches the "js" inside "React.js",
        # "Node.js", "Vue.js", etc., since \b treats the period as a
        # delimiter. Same reasoning for "ts" below and "next.ts"/
        # "index.ts"-style mentions.

        # TypeScript
        "typescript": "typescript",
        "type script": "typescript",

        # React
        "react": "react",
        "reactjs": "react",
        "react.js": "react",
        "react js": "react",

        # Node
        "node": "node.js",
        "nodejs": "node.js",
        "node.js": "node.js",
        "node js": "node.js",

        # Databases
        "postgres": "postgresql",
        "postgresql": "postgresql",
        "postgre sql": "postgresql",

        "mysql": "mysql",
        "mongo": "mongodb",
        "mongodb": "mongodb",
        "mongo db": "mongodb",

        "redis": "redis",

        "sql": "sql",
        "dbms": "dbms",
        "relational database": "relational databases",
        "relational databases": "relational databases",
        "nosql": "nosql",
        "nosql database": "nosql",
        "nosql databases": "nosql",

        # Core CS concepts commonly phrased as multi-word requirement
        # phrases rather than single tokens - matched as whole
        # phrases so e.g. "algorithms" alone (too generic/ambiguous
        # on its own) is never treated as a standalone match.
        "data structures and algorithms": "dsa",
        "data structures & algorithms": "dsa",
        "dsa": "dsa",

        "object oriented programming": "oop",
        "object-oriented programming": "oop",
        "oop": "oop",

        "operating systems": "operating systems",
        "computer networks": "computer networks",

        # Version control - treated as synonymous with knowing Git,
        # the overwhelmingly dominant real-world tool, rather than a
        # separate unverifiable concept a candidate could never be
        # credited for.
        "version control": "git",

        # Cloud
        "aws": "aws",
        "amazon web services": "aws",

        "gcp": "gcp",
        "google cloud": "gcp",
        "google cloud platform": "gcp",

        "azure": "azure",
        "microsoft azure": "azure",

        # Git
        "git": "git",
        "github": "github",
        "git hub": "github",
        "gitlab": "gitlab",
        "git lab": "gitlab",

        # Containers
        "docker": "docker",
        "docker container": "docker",

        "kubernetes": "kubernetes",
        "k8s": "kubernetes",

        # APIs
        "rest": "rest",
        "rest api": "rest",
        "restful api": "rest",

        "graphql": "graphql",
        "graph ql": "graphql",

        # ML
        "machine learning": "machine learning",
        "ml": "machine learning",

        "deep learning": "deep learning",
        "dl": "deep learning",

        "natural language processing": "nlp",
        "nlp": "nlp",

        "large language models": "llm",
        "large language model": "llm",
        "llm": "llm",

        # HTML / CSS
        "html": "html",
        "html5": "html",

        "css": "css",
        "css3": "css",

        # REST / JSON
        "rest api": "rest",
        "rest apis": "rest",
        "restful api": "rest",
        "restful apis": "rest",

        "json": "json",

        # Backend frameworks. Bare "spring" is deliberately excluded
        # (common English word - "bring energy and spring", "spring
        # cleaning" - unsafe even with word boundaries); only the
        # specific, unambiguous "spring boot"/"springboot" forms are
        # recognized.
        "spring boot": "spring boot",
        "springboot": "spring boot",

        "fastapi": "fastapi",
        "fast api": "fastapi",

        "django": "django",
        "flask": "flask",

        # Software engineering practices commonly listed as
        # requirement phrases rather than single tokens.
        "unit testing": "unit testing",
        "unit tests": "unit testing",

        "ci/cd": "ci/cd",
        "ci cd": "ci/cd",
        "continuous integration": "ci/cd",
        "continuous deployment": "ci/cd",
        "continuous delivery": "ci/cd",

        "system design": "system design",

        "design patterns": "design patterns",
        "design pattern": "design patterns",

        "linux": "linux",

        # Frontend build tooling / frameworks
        "vite": "vite",

        "tailwind": "tailwind css",
        "tailwind css": "tailwind css",

        "bootstrap": "bootstrap",

        "material ui": "material ui",
        "mui": "material ui",

        "shadcn/ui": "shadcn/ui",
        "shadcn": "shadcn/ui",

        "frontend framework": "frontend framework",
        "frontend frameworks": "frontend framework",

        "frontend build tool": "frontend build tools",
        "frontend build tools": "frontend build tools",

        # Note: "frontend projects" (a personal/academic/OSS project
        # history requirement) is deliberately NOT in this
        # vocabulary - it is a projects-history requirement, not a
        # technology/skill name, so it is never treated as an
        # atomic "skill" to match against a candidate's skill list.
        # It is left as an unmatched, non-blocking line (see
        # extract_requirement_concepts's keep_unmatched_fallback).

        # JS language concepts
        "es6": "es6+",
        "es6+": "es6+",
        "dom manipulation": "dom manipulation",
        "promises": "promises",
        "asynchronous programming": "asynchronous programming",

        # Web quality concepts
        "accessibility": "accessibility",
        "web performance": "web performance",
        "responsive design": "responsive design",
        "responsive web design": "responsive design",

        # Integration concepts
        "authentication": "authentication",
        "third-party api": "third-party apis",
        "third-party apis": "third-party apis",
        "third party api": "third-party apis",
        "third party apis": "third-party apis",

        # Note: soft skills like "problem-solving" and "debugging"
        # are deliberately NOT in this vocabulary either, for the
        # same reason - they describe an ability, not a technology,
        # and no resume skill list can be deterministically checked
        # against them.
    }

    # Phrasing that signals a JD line is a soft/flexible expectation
    # rather than a hard must-have - common, generalizable JD writing
    # conventions (not specific to any one job posting). A line
    # starting with one of these is treated as a preferred, not
    # required, requirement for eligibility-gating purposes: it
    # still counts toward ranking's skill_score and remains fully
    # visible for gap-analysis/evidence, it just does not block
    # eligibility on its own the way a genuinely required skill does.
    SOFT_REQUIREMENT_PREFIXES = (
        "familiarity with",
        "familiar with",
        "basic knowledge of",
        "basic understanding of",
        "understanding of",
        "exposure to",
        "experience with",
        "experience in",
        "experience integrating",
        "nice to have",
        "bonus",
        "preferred",
        "knowledge of",
    )

    def is_soft_requirement_signal(
        self,
        requirement_text: str,
    ) -> bool:
        """
        Whether a requirement line's own phrasing signals a soft/
        flexible expectation ("Familiarity with...", "Basic
        knowledge of...") as opposed to a hard must-have ("Good
        understanding of...", "Strong X", or a bare skill name with
        no qualifying phrase at all).
        """

        normalized = normalize_text(requirement_text)

        return normalized.startswith(
            self.SOFT_REQUIREMENT_PREFIXES
        )

    def normalize(self, skill: str) -> str:
        """
        Normalize a single skill.
        """

        normalized = normalize_text(skill)

        return self.SKILL_ALIASES.get(
            normalized,
            normalized,
        )

    def normalize_many(self, skills: Iterable[str]) -> list[str]:
        """
        Normalize multiple skills and remove duplicates
        while preserving order.
        """

        result = []
        seen = set()

        for skill in skills:
            canonical = self.normalize(skill)

            if canonical and canonical not in seen:
                result.append(canonical)
                seen.add(canonical)

        return result

    def extract_requirement_concepts(
        self,
        requirement_text: str,
        *,
        keep_unmatched_fallback: bool = True,
    ) -> list[str]:
        """
        Extract atomic, canonical skill/technology concepts from a
        requirement string that may be a single skill ("Docker") or
        a full requirement sentence ("Good understanding of HTML,
        CSS, and JavaScript.") - both are common in real JDs.

        Scans the text for any known vocabulary term (the same
        SKILL_ALIASES used by normalize()) on safe word boundaries,
        so "Java" never matches inside "JavaScript". If no known
        term is found at all - e.g. a purely descriptive requirement
        like "Good problem-solving and debugging skills." that
        happens to contain no recognized vocabulary - the whole
        cleaned sentence is kept as a single entry by default
        (useful for informational/ranking purposes, where showing an
        unmatched requirement as a visible gap is valuable). Pass
        keep_unmatched_fallback=False to drop it instead - intended
        for hard eligibility gating, where an unverifiable, free-text
        requirement should never be able to single-handedly reject a
        candidate no automated skill-matcher could ever satisfy.
        """

        normalized_text = normalize_text(requirement_text)

        matches = find_known_terms(
            normalized_text,
            self.SKILL_ALIASES,
        )

        if matches:
            return matches

        if not keep_unmatched_fallback:
            return []

        fallback = normalized_text.rstrip(".").strip()

        return [fallback] if fallback else []

    def extract_requirement_concepts_many(
        self,
        requirements: Iterable[str],
        *,
        keep_unmatched_fallback: bool = True,
    ) -> list[str]:
        """
        Apply extract_requirement_concepts() to a list of
        requirement strings and flatten the results into one
        deduplicated, order-preserving list of atomic concepts.
        """

        result = []
        seen = set()

        for requirement in requirements:
            for concept in self.extract_requirement_concepts(
                requirement,
                keep_unmatched_fallback=keep_unmatched_fallback,
            ):
                if concept not in seen:
                    result.append(concept)
                    seen.add(concept)

        return result

    def extract_requirement_groups(
        self,
        requirement_text: str,
        *,
        keep_unmatched_fallback: bool = True,
    ) -> list[str]:
        """
        Like extract_requirement_concepts(), but preserves
        alternative ("X, Y, or Z"/"at least one of...") requirement
        semantics instead of flattening every concept a sentence
        mentions into independently-mandatory atoms.

        A sentence mentioning multiple concepts joined by "or" (and
        not also "and", which would make the "or" ambiguous) is
        represented as ONE group entry, pipe-joined
        (e.g. "java|python|c++|c#" for "at least one language such
        as Java, Python, C++, or C#") - see
        normalizer_utils.split_requirement_group() for how callers
        decode this. Satisfying ANY ONE alternative in a group
        satisfies the whole entry.

        A sentence using "and" (or mentioning only one concept)
        still yields independent, individually-mandatory entries -
        unchanged from extract_requirement_concepts(). This is what
        keeps "Strong knowledge of Java and Spring Boot." requiring
        BOTH, while "Java, Python, C++, or C#" requires only one.
        """

        normalized_text = normalize_text(requirement_text)

        matches = find_known_terms(
            normalized_text,
            self.SKILL_ALIASES,
        )

        if not matches:
            if not keep_unmatched_fallback:
                return []

            fallback = normalized_text.rstrip(".").strip()

            return [fallback] if fallback else []

        if len(matches) == 1:
            return matches

        has_or = re.search(r"\bor\b", normalized_text) is not None
        has_and = re.search(r"\band\b", normalized_text) is not None

        if has_or and not has_and:
            # One alternatives group - satisfying any one concept
            # satisfies this whole requirement entry.
            unique_alternatives = list(dict.fromkeys(matches))

            return ["|".join(unique_alternatives)]

        # "and"-joined (or ambiguous) - each concept is independently
        # mandatory, exactly like extract_requirement_concepts().
        return matches

    def extract_requirement_groups_many(
        self,
        requirements: Iterable[str],
        *,
        keep_unmatched_fallback: bool = True,
    ) -> list[str]:
        """
        Apply extract_requirement_groups() to a list of requirement
        strings and flatten the results into one deduplicated,
        order-preserving list of requirement entries (each either a
        single mandatory concept or a pipe-joined alternatives
        group).
        """

        result = []
        seen = set()

        for requirement in requirements:
            for entry in self.extract_requirement_groups(
                requirement,
                keep_unmatched_fallback=keep_unmatched_fallback,
            ):
                if entry not in seen:
                    result.append(entry)
                    seen.add(entry)

        return result