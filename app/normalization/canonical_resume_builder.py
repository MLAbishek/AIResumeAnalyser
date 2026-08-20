from typing import Any

from app.core.schemas import (
    CanonicalEducation,
    CanonicalExperience,
    CanonicalResume,
)
from app.normalization.date_normalizer import (
    DateDurationNormalizer,
)
from app.normalization.entity_normalizer import (
    EntityNormalizer,
)
from app.normalization.job_title_normalizer import (
    JobTitleNormalizer,
)
from app.normalization.skill_normalizer import (
    SkillNormalizer,
)


class CanonicalResumeBuilder:
    """
    Builds a CanonicalResume from parsed resume data.

    This class is intentionally deterministic.
    """

    def __init__(
        self,
        skill_normalizer: SkillNormalizer | None = None,
        job_title_normalizer: JobTitleNormalizer | None = None,
        entity_normalizer: EntityNormalizer | None = None,
        date_normalizer: DateDurationNormalizer | None = None,
    ):
        self.skill_normalizer = (
            skill_normalizer or SkillNormalizer()
        )

        self.job_title_normalizer = (
            job_title_normalizer or JobTitleNormalizer()
        )

        self.entity_normalizer = (
            entity_normalizer or EntityNormalizer()
        )

        self.date_normalizer = (
            date_normalizer or DateDurationNormalizer()
        )

    def build(
        self,
        parsed_resume: dict[str, Any],
    ) -> CanonicalResume:
        """
        Convert parsed + extracted resume data into
        a CanonicalResume.

        The builder accepts a dictionary so it can be
        adapted to the project's existing parser output
        without coupling the canonical layer to one parser.
        """

        resume_id = self._required(
            parsed_resume,
            "resume_id",
        )

        skills = self.skill_normalizer.normalize_many(
            parsed_resume.get("skills", [])
        )

        job_titles = self.job_title_normalizer.normalize_many(
            parsed_resume.get("job_titles", [])
        )

        organizations = (
            self.entity_normalizer.normalize_organizations(
                parsed_resume.get("organizations", [])
            )
        )

        technologies = (
            self.entity_normalizer.normalize_technologies(
                parsed_resume.get("technologies", [])
            )
        )

        experiences = self._build_experiences(
            parsed_resume.get("experiences", [])
        )

        education = self._build_education(
            parsed_resume.get("education", [])
        )

        total_experience_months = (
            self._merge_experience_months(experiences)
        )

        return CanonicalResume(
            resume_id=resume_id,
            name=parsed_resume.get("name"),
            email=parsed_resume.get("email"),
            phone=parsed_resume.get("phone"),
            summary=parsed_resume.get("summary"),
            skills=skills,
            job_titles=job_titles,
            organizations=organizations,
            technologies=technologies,
            experiences=experiences,
            education=education,
            total_experience_months=total_experience_months,
        )

    @staticmethod
    def _merge_experience_months(
        experiences: list[CanonicalExperience],
    ) -> int:
        """
        Total experience as the union of covered calendar months,
        not the naive sum of each entry's duration - two roles held
        concurrently (e.g. overlapping internships, or a part-time
        role during a full-time one) must not double-count the
        overlapping months. A candidate's real total experience can
        never exceed the actual calendar time that elapsed.

        Each entry's [start_date, end_date) is treated as a
        half-open month range - the same convention
        DateDurationNormalizer.calculate_duration_months already
        uses - so a single non-overlapping entry's contribution here
        is identical to its own duration_months.
        """

        if not experiences:
            return 0

        intervals = sorted(
            (
                min(start, end),
                max(start, end),
            )
            for start, end in (
                (
                    experience.start_date.year * 12
                    + experience.start_date.month,
                    experience.end_date.year * 12
                    + experience.end_date.month,
                )
                for experience in experiences
            )
        )

        merged: list[list[int]] = []

        for start, end in intervals:
            if merged and start <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end])

        return sum(end - start for start, end in merged)

    def _build_experiences(
        self,
        experiences: list[dict[str, Any]],
    ) -> list[CanonicalExperience]:
        result = []

        for experience in experiences:
            title = self.job_title_normalizer.normalize(
                self._required(
                    experience,
                    "job_title",
                )
            )

            company = self.entity_normalizer.normalize_organization(
                self._required(
                    experience,
                    "company",
                )
            )

            date_range = self.date_normalizer.normalize_range(
                self._required(
                    experience,
                    "start_date",
                ),
                self._required(
                    experience,
                    "end_date",
                ),
                reference_date=experience.get(
                    "reference_date"
                ),
            )

            result.append(
                CanonicalExperience(
                    job_title=title,
                    company=company,
                    start_date=date_range.start_date,
                    end_date=date_range.end_date,
                    duration_months=date_range.duration_months,
                )
            )

        return result

    def _build_education(
        self,
        education_entries: list[dict[str, Any]],
    ) -> list[CanonicalEducation]:
        result = []

        for education in education_entries:
            result.append(
                CanonicalEducation(
                    degree=education.get(
                        "degree",
                        "",
                    ).strip().lower(),
                    institution=education.get(
                        "institution",
                        "",
                    ).strip().lower(),
                    field_of_study=self._optional_normalize(
                        education.get("field_of_study")
                    ),
                    start_date=self._parse_optional_date(
                        education.get("start_date")
                    ),
                    end_date=self._parse_optional_date(
                        education.get("end_date")
                    ),
                )
            )

        return result

    def _parse_optional_date(
        self,
        value: str | None,
    ):
        if not value:
            return None

        return self.date_normalizer.normalize_month_year(
            value
        )

    @staticmethod
    def _optional_normalize(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip().lower()

        return value or None

    @staticmethod
    def _required(
        data: dict[str, Any],
        key: str,
    ):
        value = data.get(key)

        if value is None or value == "":
            raise ValueError(
                f"Missing required field: {key}"
            )

        return value