from collections.abc import Generator
from typing import TYPE_CHECKING

from fastapi import Request
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal

if TYPE_CHECKING:
    from app.services.resume_index_service import ResumeIndexService


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def get_resume_index_service(
    request: Request,
) -> "ResumeIndexService | None":
    """
    FastAPI dependency returning the single ResumeIndexService
    instance constructed once at application startup (see
    app/lifespan.py) and stored on app.state. Route handlers must
    use this - via Depends(get_resume_index_service) - instead of
    constructing their own ResumeIndexService/EmbeddingGenerator/
    ModelService, which is exactly what previously caused the
    embedding model to be reloaded on requests.

    Returns None if the application's lifespan has not run - this
    is expected, not an error, when the app is driven by a bare
    `TestClient(app)` (no `with` block), which deliberately skips
    ASGI lifespan events for test speed (see tests/api/conftest.py).
    Callers must treat None as "vector indexing unavailable right
    now" and skip it gracefully, the same way any other indexing
    failure is already handled - never fall back to constructing a
    ResumeIndexService here, which would silently reintroduce a
    real, uncached model load on the request path.
    """

    return getattr(
        request.app.state, "resume_index_service", None
    )