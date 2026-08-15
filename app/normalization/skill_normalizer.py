from typing import Iterable

from app.normalization.normalizer_utils import normalize_text


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

        # JavaScript
        "javascript": "javascript",
        "java script": "javascript",
        "js": "javascript",

        # TypeScript
        "typescript": "typescript",
        "type script": "typescript",
        "ts": "typescript",

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
    }

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