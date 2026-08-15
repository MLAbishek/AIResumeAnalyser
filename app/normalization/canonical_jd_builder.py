from pydantic import BaseModel, Field
from typing import Any

from app.core.schemas import (
    CanonicalJob,
    CanonicalJobEducationRequirement,
    CanonicalJobExperienceRequirement,
)
from app.normalization.entity_normalizer import EntityNormalizer
from app.normalization.job_title_normalizer import JobTitleNormalizer
from app.normalization.skill_normalizer import SkillNormalizer


class CanonicalJobBuilder:
    """
    Builds a CanonicalJob from parsed and extracted JD data.

    The builder is deterministic and delegates normalization
    to the existing normalization modules.
    """

    def __init__(
        self,
        skill_normalizer: SkillNormalizer | None = None,
        job_title_normalizer: JobTitleNormalizer | None = None,
        entity_normalizer: EntityNormalizer | None = None,
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

    def build(
        self,
        parsed_jd: dict[str, Any],
    ) -> CanonicalJob:
        """
        Convert parsed and extracted JD data into CanonicalJob.
        """

        job_id = self._required(
            parsed_jd,
            "job_id",
        )

        title = parsed_jd.get("title")

        if title:
            title = self.job_title_normalizer.normalize(title)

        required_skills = self.skill_normalizer.normalize_many(
            parsed_jd.get("required_skills", [])
        )

        preferred_skills = self.skill_normalizer.normalize_many(
            parsed_jd.get("preferred_skills", [])
        )

        required_technologies = (
            self.entity_normalizer.normalize_technologies(
                parsed_jd.get("required_technologies", [])
            )
        )

        preferred_technologies = (
            self.entity_normalizer.normalize_technologies(
                parsed_jd.get("preferred_technologies", [])
            )
        )

        organizations = (
            self.entity_normalizer.normalize_organizations(
                parsed_jd.get("organizations", [])
            )
        )

        experience = self._build_experience_requirement(
            parsed_jd.get("experience", {})
        )

        education = self._build_education_requirements(
            parsed_jd.get("education", [])
        )

        return CanonicalJob(
            job_id=job_id,
            title=title,
            description=parsed_jd.get("description"),
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            required_technologies=required_technologies,
            preferred_technologies=preferred_technologies,
            organizations=organizations,
            experience=experience,
            education=education,
        )

    @staticmethod
    def _build_experience_requirement(
        experience: dict[str, Any],
    ) -> CanonicalJobExperienceRequirement:

        minimum_months = experience.get(
            "minimum_months",
            0,
        )

        maximum_months = experience.get(
            "maximum_months"
        )

        if minimum_months < 0:
            raise ValueError(
                "minimum_months cannot be negative"
            )

        if maximum_months is not None:
            if maximum_months < 0:
                raise ValueError(
                    "maximum_months cannot be negative"
                )

            if maximum_months < minimum_months:
                raise ValueError(
                    "maximum_months cannot be less "
                    "than minimum_months"
                )

        return CanonicalJobExperienceRequirement(
            minimum_months=minimum_months,
            maximum_months=maximum_months,
        )

    @staticmethod
    def _build_education_requirements(
        education: list[dict[str, Any]],
    ) -> list[CanonicalJobEducationRequirement]:

        result = []

        for requirement in education:
            degree = requirement.get("degree")
            field_of_study = requirement.get(
                "field_of_study"
            )

            if degree:
                degree = degree.strip().lower()

            if field_of_study:
                field_of_study = (
                    field_of_study.strip().lower()
                )

            result.append(
                CanonicalJobEducationRequirement(
                    degree=degree,
                    field_of_study=field_of_study,
                    required=requirement.get(
                        "required",
                        False,
                    ),
                )
            )

        return result

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