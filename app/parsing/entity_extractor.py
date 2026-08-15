"""
Module 10 - Entity Extraction.

Extracts structured entities from a SectionedDocument.

This module extracts entities but does not normalize them.
"""

from __future__ import annotations

import re

from app.core.schemas import (
    DocumentSection,
    EntityType,
    ExtractedEntities,
    ExtractedEntity,
    SectionedDocument,
)


class EntityExtractor:
    """Extract entities from sectioned resume/JD text."""

    def extract(
        self,
        document: SectionedDocument,
    ) -> ExtractedEntities:

        entities: list[ExtractedEntity] = []

        for section in document.sections:
            entities.extend(
                self._extract_from_section(section)
            )

        entities = self._deduplicate(entities)

        return ExtractedEntities(
            document_id=document.document_id,
            entities=entities,
        )

    def _extract_from_section(
        self,
        section: DocumentSection,
    ) -> list[ExtractedEntity]:

        entities: list[ExtractedEntity] = []

        if section.name == "skills":
            entities.extend(
                self._extract_skill_entities(section)
            )

        elif section.name == "experience":
            entities.extend(
                self._extract_experience_entities(section)
            )

        elif section.name == "education":
            entities.extend(
                self._extract_education_entities(section)
            )

        elif section.name == "certifications":
            entities.extend(
                self._extract_certification_entities(section)
            )

        elif section.name == "projects":
            entities.extend(
                self._extract_project_entities(section)
            )

        elif section.name in {
            "summary",
            "responsibilities",
            "required_qualifications",
            "preferred_qualifications",
        }:
            entities.extend(
                self._extract_general_entities(section)
            )

        return entities

    # ---------------------------------------------------------
    # SKILLS
    # ---------------------------------------------------------

    def _extract_skill_entities(
        self,
        section: DocumentSection,
    ) -> list[ExtractedEntity]:

        entities = []

        for item in self._split_items(section.text):
            entities.append(
                ExtractedEntity(
                    entity_type=EntityType.SKILL,
                    text=item,
                    section=section.name,
                )
            )

            # Technologies inside skill lists.
            for technology in self._extract_technologies(item):
                entities.append(
                    ExtractedEntity(
                        entity_type=EntityType.TECHNOLOGY,
                        text=technology,
                        section=section.name,
                    )
                )

        return entities

    # ---------------------------------------------------------
    # EXPERIENCE
    # ---------------------------------------------------------

    def _extract_experience_entities(
        self,
        section: DocumentSection,
    ) -> list[ExtractedEntity]:

        entities = []

        lines = [
            line.strip()
            for line in section.text.splitlines()
            if line.strip()
        ]

        for line in lines:

            # Job title / company format:
            #
            # ML Engineer | ABC Technologies
            #
            if "|" in line:
                parts = [
                    part.strip()
                    for part in line.split("|", 1)
                ]

                if len(parts) == 2:
                    role, company = parts

                    if role:
                        entities.append(
                            ExtractedEntity(
                                entity_type=EntityType.JOB_TITLE,
                                text=role,
                                section=section.name,
                            )
                        )

                    if company:
                        entities.append(
                            ExtractedEntity(
                                entity_type=EntityType.COMPANY,
                                text=company,
                                section=section.name,
                            )
                        )

            # Dates
            for date in self._extract_dates(line):
                entities.append(
                    ExtractedEntity(
                        entity_type=EntityType.DATE,
                        text=date,
                        section=section.name,
                    )
                )

            # Also inspect technology mentions.
            for technology in self._extract_technologies(line):
                entities.append(
                    ExtractedEntity(
                        entity_type=EntityType.TECHNOLOGY,
                        text=technology,
                        section=section.name,
                    )
                )

        return entities

    # ---------------------------------------------------------
    # EDUCATION
    # ---------------------------------------------------------

    def _extract_education_entities(
        self,
        section: DocumentSection,
    ) -> list[ExtractedEntity]:

        entities = []

        for line in section.text.splitlines():
            line = line.strip()

            if not line:
                continue

            for degree in self._extract_degrees(line):
                entities.append(
                    ExtractedEntity(
                        entity_type=EntityType.DEGREE,
                        text=degree,
                        section=section.name,
                    )
                )

            for date in self._extract_dates(line):
                entities.append(
                    ExtractedEntity(
                        entity_type=EntityType.DATE,
                        text=date,
                        section=section.name,
                    )
                )

        return entities

    # ---------------------------------------------------------
    # CERTIFICATIONS
    # ---------------------------------------------------------

    def _extract_certification_entities(
        self,
        section: DocumentSection,
    ) -> list[ExtractedEntity]:

        entities = []

        for item in self._split_items(section.text):
            entities.append(
                ExtractedEntity(
                    entity_type=EntityType.CERTIFICATION,
                    text=item,
                    section=section.name,
                )
            )

        return entities

    # ---------------------------------------------------------
    # PROJECTS / GENERAL TEXT
    # ---------------------------------------------------------

    def _extract_project_entities(
        self,
        section: DocumentSection,
    ) -> list[ExtractedEntity]:

        entities = []

        for line in section.text.splitlines():
            line = line.strip()

            if not line:
                continue

            for technology in self._extract_technologies(line):
                entities.append(
                    ExtractedEntity(
                        entity_type=EntityType.TECHNOLOGY,
                        text=technology,
                        section=section.name,
                    )
                )

        return entities

    def _extract_general_entities(
        self,
        section: DocumentSection,
    ) -> list[ExtractedEntity]:

        entities = []

        for line in section.text.splitlines():
            line = line.strip()

            if not line:
                continue

            for technology in self._extract_technologies(line):
                entities.append(
                    ExtractedEntity(
                        entity_type=EntityType.TECHNOLOGY,
                        text=technology,
                        section=section.name,
                    )
                )

            for date in self._extract_dates(line):
                entities.append(
                    ExtractedEntity(
                        entity_type=EntityType.DATE,
                        text=date,
                        section=section.name,
                    )
                )

        return entities

    # ---------------------------------------------------------
    # GENERIC EXTRACTORS
    # ---------------------------------------------------------

    @staticmethod
    def _split_items(text: str) -> list[str]:
        """Split bullets and comma/semicolon-separated values."""

        items = []

        for line in text.splitlines():
            line = line.strip()

            if not line:
                continue

            line = re.sub(
                r"^(?:[-*•▪◦‣]|\d+[.)])\s*",
                "",
                line,
            ).strip()

            if not line:
                continue

            parts = re.split(
                r"\s*[,;|]\s*",
                line,
            )

            for part in parts:
                part = part.strip()

                if part:
                    items.append(part)

        return items

    @staticmethod
    def _extract_dates(text: str) -> list[str]:
        """Extract common month/year and year ranges."""

        pattern = re.compile(
            r"(?i)"
            r"(?:"
            r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)"
            r"[a-z]*\s+\d{4}"
            r"|"
            r"\d{1,2}/\d{4}"
            r"|"
            r"\b\d{4}\b"
            r")"
        )

        return pattern.findall(text)

    @staticmethod
    def _extract_degrees(text: str) -> list[str]:
        """Extract common academic degree names."""

        patterns = [
            r"\bB\.?\s?Tech\b",
            r"\bM\.?\s?Tech\b",
            r"\bB\.?\s?E\.?\b",
            r"\bM\.?\s?E\.?\b",
            r"\bB\.?\s?Sc\.?\b",
            r"\bM\.?\s?Sc\.?\b",
            r"\bB\.?\s?S\.?\b",
            r"\bM\.?\s?S\.?\b",
            r"\bB\.?\s?A\.?\b",
            r"\bM\.?\s?A\.?\b",
            r"\bMBA\b",
            r"\bPh\.?\s?D\.?\b",
            r"\bBachelor(?:'s)?\b",
            r"\bMaster(?:'s)?\b",
            r"\bDoctorate\b",
            r"\bAssociate(?:'s)?\b",
        ]

        results = []

        for pattern in patterns:
            results.extend(
                re.findall(
                    pattern,
                    text,
                    re.IGNORECASE,
                )
            )

        return results

    @staticmethod
    def _extract_technologies(text: str) -> list[str]:
        """
        Extract well-known technologies.

        This is intentionally a small deterministic vocabulary.
        Future versions can replace/augment this with a larger
        ontology or NER model.
        """

        technologies = [
            "Python",
            "Java",
            "JavaScript",
            "TypeScript",
            "C++",
            "C#",
            "Go",
            "Rust",
            "Ruby",
            "PHP",
            "SQL",
            "PyTorch",
            "TensorFlow",
            "Keras",
            "OpenCV",
            "scikit-learn",
            "Pandas",
            "NumPy",
            "Docker",
            "Kubernetes",
            "AWS",
            "Azure",
            "GCP",
            "Git",
            "GitHub",
            "Jenkins",
            "Kafka",
            "Spark",
            "Hadoop",
            "React",
            "Angular",
            "Vue",
            "FastAPI",
            "Django",
            "Flask",
            "PostgreSQL",
            "MySQL",
            "MongoDB",
            "Redis",
        ]

        results = []

        for technology in technologies:
            pattern = rf"(?<!\w){re.escape(technology)}(?!\w)"

            if re.search(
                pattern,
                text,
                re.IGNORECASE,
            ):
                results.append(technology)

        return results

    @staticmethod
    def _deduplicate(
        entities: list[ExtractedEntity],
    ) -> list[ExtractedEntity]:

        seen = set()
        result = []

        for entity in entities:
            key = (
                entity.entity_type,
                entity.text.casefold(),
                entity.section,
            )

            if key not in seen:
                seen.add(key)
                result.append(entity)

        return result