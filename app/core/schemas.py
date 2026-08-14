from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

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