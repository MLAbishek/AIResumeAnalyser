"""
Targeted tests for the process-wide shared EmbeddingGenerator
registry set by the FastAPI lifespan handler at startup.
"""

import pytest

from app.retrieval.embeddings import EmbeddingGenerator
from app.services import embedding_registry


@pytest.fixture(autouse=True)
def _reset_registry():
    embedding_registry.set_shared_embedding_generator(None)
    yield
    embedding_registry.set_shared_embedding_generator(None)


class FakeModel:
    def encode(self, *args, **kwargs):
        return [[0.1, 0.2]]

    def get_sentence_embedding_dimension(self):
        return 2


class TestRegistry:
    def test_get_before_set_raises_clear_error(self):
        with pytest.raises(RuntimeError, match="No embedding model"):
            embedding_registry.get_shared_embedding_generator()

    def test_set_then_get_returns_the_same_instance(self):
        generator = EmbeddingGenerator(model=FakeModel())

        embedding_registry.set_shared_embedding_generator(generator)

        assert (
            embedding_registry.get_shared_embedding_generator()
            is generator
        )

    def test_set_none_clears_it(self):
        generator = EmbeddingGenerator(model=FakeModel())
        embedding_registry.set_shared_embedding_generator(generator)

        embedding_registry.set_shared_embedding_generator(None)

        with pytest.raises(RuntimeError):
            embedding_registry.get_shared_embedding_generator()
