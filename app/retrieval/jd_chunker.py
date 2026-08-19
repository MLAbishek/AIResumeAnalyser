"""
Job description chunking for retrieval.

Mirrors resume_chunker.py's design (section-aware, deterministic
chunk IDs) for the JD side, which previously had no chunking
counterpart. Converts a CanonicalJob into semantically meaningful
retrieval chunks so semantic matching can compare specific JD
requirement sections against specific resume sections, rather than
one giant blob of text against another.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1

from app.core.schemas import CanonicalJob


@dataclass(frozen=True)
class JDChunk:
    """
    One retrieval-friendly semantic unit from a canonical job
    description.

    Attributes:
        chunk_id: Deterministic unique identifier for this chunk.
        job_id: ID of the source job description.
        section: Semantic section from which the chunk originated.
        text: Normalized text used by retrieval.
        position: Original ordering of the chunk within the JD.
    """

    chunk_id: str
    job_id: str
    section: str
    text: str
    position: int


class JDChunker:
    """
    Convert CanonicalJob objects into retrieval-friendly chunks.
    """

    def chunk(self, job: CanonicalJob) -> list[JDChunk]:
        """
        Convert one canonical job description into ordered semantic
        chunks. Empty sections are ignored.
        """
        chunks: list[JDChunk] = []

        self._add_text_chunk(
            chunks=chunks,
            job=job,
            section="description",
            text=job.title,
        )

        self._add_text_chunk(
            chunks=chunks,
            job=job,
            section="description",
            text=job.description,
        )

        self._add_list_chunk(
            chunks=chunks,
            job=job,
            section="responsibilities",
            values=job.responsibilities,
        )

        self._add_list_chunk(
            chunks=chunks,
            job=job,
            section="required_skills",
            values=job.required_skills,
        )

        self._add_list_chunk(
            chunks=chunks,
            job=job,
            section="preferred_skills",
            values=job.preferred_skills,
        )

        self._add_list_chunk(
            chunks=chunks,
            job=job,
            section="technologies",
            values=[
                *job.required_technologies,
                *job.preferred_technologies,
            ],
        )

        self._add_list_chunk(
            chunks=chunks,
            job=job,
            section="education",
            values=[
                " ".join(
                    part
                    for part in (
                        requirement.degree,
                        requirement.field_of_study,
                    )
                    if part
                )
                for requirement in job.education
                if requirement.degree
                or requirement.field_of_study
            ],
        )

        return chunks

    @staticmethod
    def _normalize_text(text: str | None) -> str:
        if not text:
            return ""

        return " ".join(text.split()).strip()

    def _add_text_chunk(
        self,
        chunks: list[JDChunk],
        job: CanonicalJob,
        section: str,
        text: str | None,
    ) -> None:
        normalized = self._normalize_text(text)

        if not normalized:
            return

        self._append_chunk(
            chunks=chunks,
            job=job,
            section=section,
            text=normalized,
        )

    def _add_list_chunk(
        self,
        chunks: list[JDChunk],
        job: CanonicalJob,
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
            job=job,
            section=section,
            text=text,
        )

    @staticmethod
    def _append_chunk(
        chunks: list[JDChunk],
        job: CanonicalJob,
        section: str,
        text: str,
    ) -> None:
        position = len(chunks)

        raw_id = f"{job.job_id}|{section}|{position}|{text}"
        chunk_id = sha1(raw_id.encode("utf-8")).hexdigest()

        chunks.append(
            JDChunk(
                chunk_id=chunk_id,
                job_id=job.job_id,
                section=section,
                text=text,
                position=position,
            )
        )
