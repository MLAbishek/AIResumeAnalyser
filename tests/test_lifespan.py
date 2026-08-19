"""
Targeted test for the FastAPI lifespan handler: the embedding model
must be loaded exactly once at startup, before any request would be
served, and app.state must expose the shared model/embedding/index
services afterward. sentence_transformers.SentenceTransformer is
mocked so this never loads the real BGE-M3 model.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from fastapi import FastAPI

from app.lifespan import lifespan
from app.services import embedding_registry
from app.services.resume_index_service import ResumeIndexService


def _fake_sentence_transformer():
    fake = MagicMock()
    fake.encode.return_value = np.zeros((1, 4), dtype=np.float32)
    fake.get_sentence_embedding_dimension.return_value = 4
    return fake


@pytest.fixture(autouse=True)
def _reset_registry():
    embedding_registry.set_shared_embedding_generator(None)
    yield
    embedding_registry.set_shared_embedding_generator(None)


@pytest.mark.anyio
async def test_lifespan_loads_model_exactly_once_and_populates_state():
    app = FastAPI()
    fake_st = _fake_sentence_transformer()

    with patch(
        "torch.cuda.is_available", return_value=False
    ), patch(
        "sentence_transformers.SentenceTransformer",
        return_value=fake_st,
    ) as mock_constructor:
        async with lifespan(app):
            mock_constructor.assert_called_once()

            assert app.state.model_service.is_loaded is True
            assert app.state.model_service.device == "cpu"

            assert app.state.embedding_generator is not None

            assert isinstance(
                app.state.resume_index_service, ResumeIndexService
            )

            assert (
                embedding_registry.get_shared_embedding_generator()
                is app.state.embedding_generator
            )

    # After the context manager exits (shutdown), the model is
    # released and the registry is cleared.
    assert app.state.model_service.is_loaded is False

    with pytest.raises(RuntimeError):
        embedding_registry.get_shared_embedding_generator()


@pytest.fixture
def anyio_backend():
    return "asyncio"
