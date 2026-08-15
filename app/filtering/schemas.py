from pydantic import BaseModel,Field
from app.core.schemas import CanonicalJobEducationRequirement

class EligibilityCriteria(BaseModel):
    required_skills:list[str]=Field(default_factory=list)
    required_technologies:list[str]=Field(default_factory=list)
    minimum_experience_months:int=Field(
        default=0,
        ge=0,
    )
    required_education: list[CanonicalJobEducationRequirement] = Field(
        default_factory=list
    )
    required_certifications:list[str]=Field(default_factory=list)
    location:str|None =None
    work_mode:str|None=None
    work_authorization_required:bool=False

class SkillMatchResult(BaseModel):
    matched_skills:list[str]=Field(
        default_factory=list
    )

    missing_skills:list[str]=Field(
        default_factory=list
    )

    eligible:bool
    reasons: list[str] = Field(default_factory=list)
class ExperienceMatchResult(BaseModel):
    required_months:int=Field(
        default=0,
        ge=0,
    )
    candidate_months:int=Field(
        default=0,
        ge=0,
    )
    relevant_months:int=Field(
        default=0,
        ge=0,
    )
    seniority_match:bool|None= None
    eligible:bool
    reasons:list[str]= Field(
        default_factory=list
    )
class EducationCertificationResult(BaseModel):
    
    matched_education: list[str] = Field(
        default_factory=list
    )

    missing_education: list[str] = Field(
        default_factory=list
    )

    matched_certifications: list[str] = Field(
        default_factory=list
    )

    missing_certifications: list[str] = Field(
        default_factory=list
    )

    eligible: bool

    reasons: list[str] = Field(
        default_factory=list
    )

class LocationAuthorizationResult(BaseModel):
    location_match:bool
    authorization_match:bool
    eligible:bool
    reasons:list[str]= Field(
        default_factory=list
    )
class EligibilityResult(BaseModel):
    eligible: bool

    skill_match: SkillMatchResult
    experience_match: ExperienceMatchResult
    education_certification: EducationCertificationResult
    location_authorization: LocationAuthorizationResult

    reasons: list[str] = Field(
        default_factory=list
    )