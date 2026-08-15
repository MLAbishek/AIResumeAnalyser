from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import date

class DocumentType(str, Enum):
    RESUME = "resume"
    JOB_DESCRIPTION = "job_description"
    
class DocumentMetadata(BaseModel):
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    content_type: Optional[str] = None
    checksum: Optional[str] = None
    created_at: Optional[str] = None
    modified_at: Optional[str] = None

class JobDescription(BaseModel):
    job_id: str
    title: Optional[str] = None
    summary: Optional[str] = None

    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)

    required_experience_years: Optional[float] = None

    education: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)

    responsibilities: list[str] = Field(default_factory=list)

    location: Optional[str] = None
    job_type: Optional[str] = None

    raw_text: str


class Experience(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None


class Education(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class Resume(BaseModel):
    resume_id: str

    name: Optional[str] = None
    summary: Optional[str] = None

    skills: list[str] = Field(default_factory=list)

    experience: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)

    certifications: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)

    job_titles: list[str] = Field(default_factory=list)

    total_experience_years: Optional[float] = None

    raw_text: str


class RawDocumentPage(BaseModel):
    page_number: int
    text: str


class RawDocument(BaseModel):
    document_id: str
    document_type: DocumentType
    source_path: str

    pages: list[RawDocumentPage] = Field(default_factory=list)

    raw_text: str

    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)


class CleanedDocumentPage(BaseModel):
    page_number: int
    text: str


class CleanedDocument(BaseModel):
    document_id: str
    document_type: DocumentType
    source_path: str

    pages: list[CleanedDocumentPage] = Field(default_factory=list)

    text: str

    metadata: dict = Field(default_factory=dict)


class CanonicalExperience(BaseModel):
    """
    Standardized representation of one work experience.
    """

    job_title: str
    company: str
    start_date: date
    end_date: date
    duration_months: int = Field(ge=0)


class CanonicalEducation(BaseModel):
    """
    Standardized representation of one education entry.
    """

    degree: str
    institution: str
    field_of_study: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class CanonicalResume(BaseModel):
    """
    Canonical representation of a resume used by
    downstream matching and eligibility modules.
    """

    resume_id: str

    name: str | None = None
    email: str | None = None
    phone: str | None = None

    summary: str | None = None

    skills: list[str] = Field(default_factory=list)
    job_titles: list[str] = Field(default_factory=list)

    organizations: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)

    experiences: list[CanonicalExperience] = Field(
        default_factory=list
    )

    education: list[CanonicalEducation] = Field(
        default_factory=list
    )

    total_experience_months: int = Field(
        default=0,
        ge=0,
    )


class CanonicalJobExperienceRequirement(BaseModel):
    """Standardized experience requirement for a job."""

    minimum_months: int = Field(default=0, ge=0)
    maximum_months: int | None = Field(default=None, ge=0)


class CanonicalJobEducationRequirement(BaseModel):
    """Standardized education requirement for a job."""

    degree: str | None = None
    field_of_study: str | None = None
    required: bool = False


class CanonicalJob(BaseModel):
    """
    Canonical representation of a job description.

    This is the primary JD representation consumed by
    deterministic eligibility filtering and downstream
    matching modules.
    """

    job_id: str

    title: str | None = None

    description: str | None = None

    required_skills: list[str] = Field(
        default_factory=list
    )

    preferred_skills: list[str] = Field(
        default_factory=list
    )

    required_technologies: list[str] = Field(
        default_factory=list
    )

    preferred_technologies: list[str] = Field(
        default_factory=list
    )

    organizations: list[str] = Field(
        default_factory=list
    )

    experience: CanonicalJobExperienceRequirement = Field(
        default_factory=CanonicalJobExperienceRequirement
    )

    education: list[CanonicalJobEducationRequirement] = Field(
        default_factory=list
    )