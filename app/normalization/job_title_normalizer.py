from typing import Iterable

from app.normalization.normalizer_utils import normalize_text


class JobTitleNormalizer:
    """
    Deterministically maps extracted job title variants
    to canonical job titles.
    """

    TITLE_ALIASES = {
        # Software Engineering
        "swe": "software engineer",
        "software engineer": "software engineer",
        "software developer": "software engineer",
        "software development engineer": "software engineer",
        "software dev": "software engineer",
        "software programmer": "software engineer",

        # Senior Software Engineering
        "senior software engineer": "senior software engineer",
        "senior software developer": "senior software engineer",
        "senior swe": "senior software engineer",

        # Junior Software Engineering
        "junior software engineer": "junior software engineer",
        "junior software developer": "junior software engineer",
        "junior swe": "junior software engineer",

        # Full Stack
        "full stack developer": "full stack developer",
        "full-stack developer": "full stack developer",
        "full stack engineer": "full stack developer",
        "full-stack engineer": "full stack developer",

        # Frontend
        "frontend developer": "frontend developer",
        "front end developer": "frontend developer",
        "frontend engineer": "frontend developer",
        "front end engineer": "frontend developer",

        # Backend
        "backend developer": "backend developer",
        "back end developer": "backend developer",
        "backend engineer": "backend developer",
        "back end engineer": "backend developer",

        # Data
        "data scientist": "data scientist",
        "data science": "data scientist",

        "data analyst": "data analyst",
        "business data analyst": "data analyst",

        # ML / AI
        "machine learning engineer": "machine learning engineer",
        "ml engineer": "machine learning engineer",
        "machine learning developer": "machine learning engineer",

        "ai engineer": "ai engineer",
        "artificial intelligence engineer": "ai engineer",
        "ai developer": "ai engineer",

        # DevOps
        "devops engineer": "devops engineer",
        "dev ops engineer": "devops engineer",

        # Cloud
        "cloud engineer": "cloud engineer",
        "cloud developer": "cloud engineer",

        # QA
        "qa engineer": "qa engineer",
        "quality assurance engineer": "qa engineer",
        "test engineer": "qa engineer",

        # Management
        "engineering manager": "engineering manager",
        "software engineering manager": "engineering manager",

        # Product
        "product manager": "product manager",
        "product management": "product manager",
    }

    def normalize(self, title: str) -> str:
        """
        Normalize a single job title.
        """

        normalized = normalize_text(title)

        return self.TITLE_ALIASES.get(
            normalized,
            normalized,
        )

    def normalize_many(self, titles: Iterable[str]) -> list[str]:
        """
        Normalize multiple titles and remove duplicates
        while preserving order.
        """

        result = []
        seen = set()

        for title in titles:
            canonical = self.normalize(title)

            if canonical and canonical not in seen:
                result.append(canonical)
                seen.add(canonical)

        return result