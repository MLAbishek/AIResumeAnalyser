from pydantic import BaseModel, Field


class JobCreateRequest(BaseModel):
    job_id: str
    title: str | None = None
    description: str | None = None
    location: str | None = None
    job_type: str | None = None

    raw_text: str

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

    education_requirements: list[dict] = Field(
        default_factory=list
    )

    required_certifications: list[str] = Field(
        default_factory=list
    )

    responsibilities: list[str] = Field(
        default_factory=list
    )

    required_experience_months: int = Field(
        default=0,
        ge=0,
    )


class JobResponse(BaseModel):
    job_id: str
    title: str | None = None
    description: str | None = None
    location: str | None = None
    job_type: str | None = None

    raw_text: str

    required_skills: list[str]
    preferred_skills: list[str]

    required_technologies: list[str]
    preferred_technologies: list[str]

    education_requirements: list[dict]
    required_certifications: list[str]
    responsibilities: list[str]

    required_experience_months: int
    status: str = "open"