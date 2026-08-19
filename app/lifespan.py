"""
FastAPI application lifespan: load the embedding model exactly once
at process startup - before any request is served - and release it
on shutdown.

This is the ONLY place ModelService.load() is called. Everything
downstream (EmbeddingGenerator, ResumeIndexService,
SemanticMatchingService, BulkSemanticRetrievalService, and the
ranking layer's semantic_scorer dispatcher) reuses the one model
instance constructed here for the lifetime of the process - never
re-loading it per request.

`uvicorn --reload` note: reload mode watches source files and, on a
change, kills and restarts the ENTIRE worker process. This lifespan
handler runs again on every such restart, so you will see "Loading
weights..." once per reload during active development - that is
expected and is not the bug this module fixes (the bug was the model
loading again on every REQUEST, not once per process restart).
Reload mode is a development convenience only; it must never be used
in production, where the process - and therefore the loaded model -
should stay up for the deployment's lifetime.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.services import embedding_registry
from app.services.model_service import ModelService
from app.services.resume_index_service import ResumeIndexService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.retrieval.embeddings import EmbeddingGenerator

    model_service = ModelService(model_name=settings.embedding_model)

    logger.info(
        "Application startup: loading embedding model %s...",
        settings.embedding_model,
    )

    # model_service.load() is a blocking, CPU/GPU-bound call (model
    # weight download/deserialization). Startup is the one place a
    # multi-second blocking call is acceptable, but it is still run
    # off the event loop via run_in_executor rather than awaited
    # directly - nothing else needs the loop free yet, but this keeps
    # the pattern correct if more concurrent startup work is added
    # later.
    await asyncio.get_event_loop().run_in_executor(
        None, model_service.load
    )

    app.state.model_service = model_service

    embedding_generator = EmbeddingGenerator(
        model_name=model_service.model_name,
        model=model_service.raw_model,
    )
    app.state.embedding_generator = embedding_generator

    # Deeply-nested, non-route-reachable services (ranking's
    # semantic_scorer, SemanticMatchingService,
    # BulkSemanticRetrievalService) read the shared instance from
    # this registry instead of each constructing their own - see
    # embedding_registry.py's docstring for why.
    embedding_registry.set_shared_embedding_generator(
        embedding_generator
    )

    # The persistent resume vector index is opened once here too,
    # rather than lazily on the first upload - route handlers reach
    # it via Depends(get_resume_index_service), never by
    # constructing their own.
    app.state.resume_index_service = ResumeIndexService(
        embedder=embedding_generator,
    )

    logger.info(
        "Application startup complete. embedding_model=%s device=%s",
        model_service.model_name,
        model_service.device,
    )

    yield

    logger.info("Application shutdown: releasing embedding model.")
    embedding_registry.set_shared_embedding_generator(None)
    model_service.unload()
