from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.health import router as health_router
from app.api.routes.screening import router as screening_router
from app.api.routes.ranking import router as ranking_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.resumes import router as resumes_router
from app.api.routes.screenings import router as screenings_router
from app.api.routes.auth import router as auth_router
from app.api.routes.candidate import router as candidate_router
from app.api.routes.applications import (
    router as applications_router,
)

app = FastAPI(
    title="Semantic Resume Screening System",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    health_router,
    prefix="/api",
)

app.include_router(
    screening_router,
    prefix="/api",
)

app.include_router(
    ranking_router,
    prefix="/api",
)

app.include_router(
    jobs_router,
    prefix="/api",
)

app.include_router(
    resumes_router,
    prefix="/api",
)

app.include_router(
    screenings_router,
    prefix="/api",
)

app.include_router(
    auth_router,
    prefix="/api",
)

app.include_router(
    candidate_router,
    prefix="/api",
)

app.include_router(
    applications_router,
    prefix="/api",
)