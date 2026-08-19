from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ResumeExperienceCreate(BaseModel):
    job_title: str
    company: str
    start_date: date
    end_date: date
    duration_months: int = Field(
        default=0,
        ge=0,
    )


class ResumeEducationCreate(BaseModel):
    degree: str
    institution: str
    field_of_study: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class ResumeProjectCreate(BaseModel):
    name: str
    description: str | None = None
    technologies: list[str] = Field(
        default_factory=list,
    )


class ResumeCreateRequest(BaseModel):
    resume_id: str = Field(
        min_length=1,
        max_length=100,
    )

    name: str | None = None
    email: str | None = None
    phone: str | None = None
    summary: str | None = None

    skills: list[str] = Field(
        default_factory=list,
    )

    job_titles: list[str] = Field(
        default_factory=list,
    )

    organizations: list[str] = Field(
        default_factory=list,
    )

    technologies: list[str] = Field(
        default_factory=list,
    )

    certifications: list[str] = Field(
        default_factory=list,
    )

    total_experience_months: int = Field(
        default=0,
        ge=0,
    )

    raw_text: str | None = None

    experiences: list[ResumeExperienceCreate] = Field(
        default_factory=list,
    )

    education: list[ResumeEducationCreate] = Field(
        default_factory=list,
    )

    projects: list[ResumeProjectCreate] = Field(
        default_factory=list,
    )


class ResumeExperienceResponse(
    ResumeExperienceCreate
):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int


class ResumeEducationResponse(
    ResumeEducationCreate
):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int


class ResumeProjectResponse(
    ResumeProjectCreate
):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int


class ResumeResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    resume_id: str
    name: str | None
    email: str | None
    phone: str | None
    summary: str | None

    skills: list[str]
    job_titles: list[str]
    organizations: list[str]
    technologies: list[str]
    certifications: list[str]

    total_experience_months: int
    raw_text: str | None

    experiences: list[ResumeExperienceResponse]
    education: list[ResumeEducationResponse]
    projects: list[ResumeProjectResponse]