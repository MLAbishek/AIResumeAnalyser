from pydantic import BaseModel, Field

from app.core.schemas import CanonicalJob, CanonicalResume


class MatchFeatureVector(BaseModel):
    """
    Measurable matching features for a job-candidate pair.
    """

    skill_score: float = Field(ge=0.0, le=1.0)
    experience_score: float = Field(ge=0.0, le=1.0)
    seniority_score: float = Field(ge=0.0, le=1.0)
    education_score: float = Field(ge=0.0, le=1.0)
    semantic_score: float = Field(ge=0.0, le=1.0)


def extract_features(
    job: CanonicalJob,
    resume: CanonicalResume,
) -> MatchFeatureVector:
    """
    Extract measurable matching features for a JD-candidate pair.
    """

    from app.ranking.skill_match_scorer import score_skills
    from app.ranking.experience_scorer import score_experience
    from app.ranking.seniority_scorer import score_seniority
    from app.ranking.education_scorer import score_education
    from app.ranking.semantic_scorer import score_semantic

    return MatchFeatureVector(
        skill_score=score_skills(job, resume),
        experience_score=score_experience(job, resume),
        seniority_score=score_seniority(job, resume),
        education_score=score_education(job, resume),
        semantic_score=score_semantic(job, resume),
    )