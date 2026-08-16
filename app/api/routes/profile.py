from fastapi import APIRouter, HTTPException

from app.api.schemas.profile import CandidateProfileResponse
from app.api.repository import InMemoryRepository
from app.api.schemas import CandidateProfileResponse


router = APIRouter(
    prefix="/profile",
    tags=["profile"],
)

repository = InMemoryRepository()
service = CandidateProfileService(repository)


@router.get(
    "/{jd_id}/{candidate_id}",
    response_model=CandidateProfileResponse,
)
def get_candidate_profile(
    jd_id: str,
    candidate_id: str,
):
    try:
        return service.get_profile(
            candidate_id=candidate_id,
            jd_id=jd_id,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc