import pytest

from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.connection import engine


@pytest.fixture(autouse=True)
def _disable_live_llm_calls_by_default(monkeypatch):
    """
    Force LLM explanation generation off for every test by default,
    regardless of what ENABLE_LLM_EXPLANATIONS is set to in the
    local .env file. Tests must never make live network calls to
    OpenRouter simply because a developer's .env happens to have the
    feature enabled for manual/demo use. Tests that specifically
    exercise the LLM integration construct their own
    LLMExplanationService with an explicit `enabled=`/mocked client
    instead of relying on this global setting, so they are
    unaffected by this override.
    """

    monkeypatch.setattr(
        settings, "enable_llm_explanations", False
    )


@pytest.fixture(autouse=True)
def _disable_live_embedding_model_by_default(monkeypatch):
    """
    Force semantic scoring onto the fast deterministic lexical
    fallback for every test by default, regardless of
    ENABLE_SEMANTIC_SEARCH in the local .env file. Tests must never
    download/load the real BGE-M3 model just because a developer's
    .env happens to have it enabled for manual/demo use. Tests that
    specifically exercise the embedding path construct their own
    SemanticMatchingService with an injected/mocked embedder instead
    of relying on this global setting, so they are unaffected by
    this override.
    """

    monkeypatch.setattr(
        settings, "enable_semantic_search", False
    )


@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()

    session = Session(
        bind=connection,
        expire_on_commit=False,
    )

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()