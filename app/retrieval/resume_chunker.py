"""
Resume chunking for retrieval.

Converts a CanonicalResume into deterministic, semantically meaningful
retrieval chunks while preserving resume and section metadata.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1
from typing import Iterable

from app.core.schemas import (
    CanonicalEducation,
    CanonicalExperience,
    CanonicalResume,
)


@dataclass(frozen=True)
class ResumeChunk:
    """
    One retrieval-friendly semantic unit from a canonical resume.

    Attributes:
        chunk_id: Deterministic unique identifier for this chunk.
        resume_id: ID of the source resume/candidate.
        section: Semantic section from which the chunk originated.
        text: Normalized text used by retrieval.
        position: Original ordering of the chunk within the resume.
        metadata: Additional provenance information.
    """

    chunk_id: str
    resume_id: str
    section: str
    text: str
    position: int
    metadata: dict[str, object]


class ResumeChunker:
    """
    Convert CanonicalResume objects into retrieval-friendly chunks.

    The chunker is section-aware rather than character-based. This preserves
    semantic boundaries such as experience and education entries.
    """

    def chunk(self, resume: CanonicalResume) -> list[ResumeChunk]:
        """
        Convert one canonical resume into ordered semantic chunks.

        Empty sections are ignored.

        Args:
            resume: Canonical resume to chunk.

        Returns:
            Deterministically ordered list of ResumeChunk objects.
        """
        chunks: list[ResumeChunk] = []

        self._add_text_chunk(
            chunks=chunks,
            resume=resume,
            section="summary",
            text=resume.summary,
            metadata={},
        )

        self._add_list_chunk(
            chunks=chunks,
            resume=resume,
            section="skills",
            values=resume.skills,
        )

        self._add_list_chunk(
            chunks=chunks,
            resume=resume,
            section="job_titles",
            values=resume.job_titles,
        )

        self._add_list_chunk(
            chunks=chunks,
            resume=resume,
            section="organizations",
            values=resume.organizations,
        )

        self._add_list_chunk(
            chunks=chunks,
            resume=resume,
            section="technologies",
            values=resume.technologies,
        )

        for index, experience in enumerate(resume.experiences):
            self._add_experience_chunk(
                chunks=chunks,
                resume=resume,
                experience=experience,
                index=index,
            )

        for index, education in enumerate(resume.education):
            self._add_education_chunk(
                chunks=chunks,
                resume=resume,
                education=education,
                index=index,
            )

        return chunks

    def chunk_many(
        self,
        resumes: Iterable[CanonicalResume],
    ) -> list[ResumeChunk]:
        """
        Chunk multiple resumes while preserving candidate identity.

        Args:
            resumes: Iterable of canonical resumes.

        Returns:
            Flattened list of chunks.
        """
        chunks: list[ResumeChunk] = []

        for resume in resumes:
            chunks.extend(self.chunk(resume))

        return chunks

    @staticmethod
    def _normalize_text(text: str | None) -> str:
        """
        Normalize whitespace without changing meaningful content.
        """
        if not text:
            return ""

        return " ".join(text.split()).strip()

    def _add_text_chunk(
        self,
        chunks: list[ResumeChunk],
        resume: CanonicalResume,
        section: str,
        text: str | None,
        metadata: dict[str, object],
    ) -> None:
        normalized = self._normalize_text(text)

        if not normalized:
            return

        self._append_chunk(
            chunks=chunks,
            resume=resume,
            section=section,
            text=normalized,
            metadata=metadata,
        )

    def _add_list_chunk(
        self,
        chunks: list[ResumeChunk],
        resume: CanonicalResume,
        section: str,
        values: list[str],
    ) -> None:
        cleaned = [
            self._normalize_text(value)
            for value in values
            if self._normalize_text(value)
        ]

        if not cleaned:
            return

        text = " | ".join(cleaned)

        self._append_chunk(
            chunks=chunks,
            resume=resume,
            section=section,
            text=text,
            metadata={"count": len(cleaned)},
        )

    def _add_experience_chunk(
        self,
        chunks: list[ResumeChunk],
        resume: CanonicalResume,
        experience: CanonicalExperience,
        index: int,
    ) -> None:
        text_parts = [
            f"Job title: {experience.job_title}",
            f"Company: {experience.company}",
            f"Duration: {experience.duration_months} months",
        ]

        text = " | ".join(
            self._normalize_text(part)
            for part in text_parts
            if self._normalize_text(part)
        )

        self._append_chunk(
            chunks=chunks,
            resume=resume,
            section="experience",
            text=text,
            metadata={
                "experience_index": index,
                "job_title": experience.job_title,
                "company": experience.company,
                "start_date": experience.start_date.isoformat(),
                "end_date": experience.end_date.isoformat(),
                "duration_months": experience.duration_months,
            },
        )

    def _add_education_chunk(
        self,
        chunks: list[ResumeChunk],
        resume: CanonicalResume,
        education: CanonicalEducation,
        index: int,
    ) -> None:
        text_parts = [
            f"Degree: {education.degree}",
            f"Institution: {education.institution}",
        ]

        if education.field_of_study:
            text_parts.append(
                f"Field of study: {education.field_of_study}"
            )

        if education.start_date:
            text_parts.append(
                f"Start date: {education.start_date.isoformat()}"
            )

        if education.end_date:
            text_parts.append(
                f"End date: {education.end_date.isoformat()}"
            )

        text = " | ".join(
            self._normalize_text(part)
            for part in text_parts
            if self._normalize_text(part)
        )

        self._append_chunk(
            chunks=chunks,
            resume=resume,
            section="education",
            text=text,
            metadata={
                "education_index": index,
                "degree": education.degree,
                "institution": education.institution,
                "field_of_study": education.field_of_study,
            },
        )

    @staticmethod
    def _append_chunk(
        chunks: list[ResumeChunk],
        resume: CanonicalResume,
        section: str,
        text: str,
        metadata: dict[str, object],
    ) -> None:
        position = len(chunks)

        # Include the content in the hash so that different chunks
        # cannot accidentally receive the same ID.
        raw_id = f"{resume.resume_id}|{section}|{position}|{text}"
        chunk_id = sha1(raw_id.encode("utf-8")).hexdigest()

        chunks.append(
            ResumeChunk(
                chunk_id=chunk_id,
                resume_id=resume.resume_id,
                section=section,
                text=text,
                position=position,
                metadata=dict(metadata),
            )
        )