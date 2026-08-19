"""
Process-wide accessor for the single shared EmbeddingGenerator
instance, set exactly once by the FastAPI lifespan handler at
startup (see app/lifespan.py).

Why this exists: several service classes several layers below any
route handler - ResumeIndexService, SemanticMatchingService,
BulkSemanticRetrievalService, and the ranking layer's
semantic_scorer dispatcher - each need access to the SAME
already-loaded embedding model. They are constructed via plain
Python composition deep inside ScreeningService/CandidateMatchService
call chains, not as FastAPI route parameters, so FastAPI's own
Depends() injection tree cannot reach them directly without
threading a parameter through four or five unrelated layers of
service construction.

This module is the deliberate, narrow alternative: one explicitly-
set, explicitly-typed, testable module-level slot - not the
scattered set of ad-hoc "lazy singletons" this replaces (previously,
several files each independently did
`self.embedder = embedder or EmbeddingGenerator()`, and every one of
those call sites was capable of triggering its own separate model
load - the exact bug reported as "loading weights on every upload").

Route-handler-level code should prefer real FastAPI Depends()
injection instead (see app/api/dependencies.py's
get_resume_index_service) - this registry is specifically for the
non-route-reachable service layer.
"""

from __future__ import annotations

from app.retrieval.embeddings import EmbeddingGenerator

_shared_embedding_generator: EmbeddingGenerator | None = None


def set_shared_embedding_generator(
    generator: EmbeddingGenerator | None,
) -> None:
    """
    Set (or, at shutdown, clear) the process-wide embedding
    generator. Called exactly once at startup and once at shutdown
    by the FastAPI lifespan handler - not intended to be called from
    request-handling code.
    """
    global _shared_embedding_generator
    _shared_embedding_generator = generator


def get_shared_embedding_generator() -> EmbeddingGenerator:
    """
    Return the process-wide embedding generator set by the FastAPI
    lifespan handler at startup.

    Raises RuntimeError if called before the application has
    finished starting up. This should be unreachable in normal
    operation, and is a signal to fix the calling code rather than a
    condition to design a fallback around - standalone scripts and
    tests should construct EmbeddingGenerator/ModelService explicitly
    instead of relying on this registry.
    """
    if _shared_embedding_generator is None:
        raise RuntimeError(
            "No embedding model has been loaded yet. "
            "ModelService.load() must run during FastAPI startup "
            "(see app/lifespan.py) before any code calls "
            "get_shared_embedding_generator(). Standalone scripts "
            "and tests should construct EmbeddingGenerator/"
            "ModelService explicitly instead of using this registry."
        )

    return _shared_embedding_generator
