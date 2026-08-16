from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.api.schemas.screening import (
    ScreeningRequest,
    ScreeningResponse,
)
from app.services.screening_persistence_service import (
    ScreeningPersistenceService,
)
from app.services.screening_service import (
    ScreeningService,
)
from app.auth.dependencies import require_role


router = APIRouter(
    prefix="/screen",
    tags=["screening"],
)


@router.post(
    "",
    response_model=ScreeningResponse,
    dependencies=[
        Depends(require_role("admin", "recruiter"))
    ],
)
def screen_candidates(
    request: ScreeningRequest,
    db: Session = Depends(get_db),
    current_user= Depends(
        require_role("admin","recruiter")
    )
):
    try:
        service = ScreeningService()

        result = service.screen(
            job_description=request.job_description,
            resumes=request.resumes,
        )

        persistence = ScreeningPersistenceService(
            db
        )

        persistence.persist(
            job_id=result["job_id"],
            results=result["results"],
        )

        return result

    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc