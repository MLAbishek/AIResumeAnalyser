import numpy as np
import pytest

from app.infrastructure.cache import Cache


def test_set_and_get(tmp_path):
    cache = Cache(tmp_path)

    cache.set(
        "embedding:test",
        {
            "value": 123,
        },
    )

    assert cache.get(
        "embedding:test"
    ) == {
        "value": 123,
    }


def test_missing_key_returns_default(tmp_path):
    cache = Cache(tmp_path)

    assert cache.get(
        "missing",
        default="fallback",
    ) == "fallback"


def test_exists(tmp_path):
    cache = Cache(tmp_path)

    assert not cache.exists("key")

    cache.set(
        "key",
        "value",
    )

    assert cache.exists("key")


def test_delete(tmp_path):
    cache = Cache(tmp_path)

    cache.set(
        "key",
        "value",
    )

    assert cache.delete("key")
    assert not cache.exists("key")


def test_delete_missing_key_returns_false(tmp_path):
    cache = Cache(tmp_path)

    assert not cache.delete("missing")


def test_clear(tmp_path):
    cache = Cache(tmp_path)

    cache.set("one", 1)
    cache.set("two", 2)

    cache.clear()

    assert not cache.exists("one")
    assert not cache.exists("two")


def test_numpy_embeddings_are_supported(tmp_path):
    cache = Cache(tmp_path)

    vector = np.array(
        [0.1, 0.2, 0.3],
        dtype=np.float32,
    )

    cache.set(
        "embedding:abc",
        vector,
    )

    restored = cache.get(
        "embedding:abc"
    )

    assert isinstance(
        restored,
        np.ndarray,
    )

    assert restored.dtype == np.float32
    assert np.array_equal(
        restored,
        vector,
    )


def test_empty_key_is_rejected(tmp_path):
    cache = Cache(tmp_path)

    with pytest.raises(ValueError):
        cache.set(
            "",
            "value",
        )


def test_non_string_key_is_rejected(tmp_path):
    cache = Cache(tmp_path)

    with pytest.raises(TypeError):
        cache.set(
            123,
            "value",
        )


def test_complex_objects_are_supported(tmp_path):
    cache = Cache(tmp_path)

    value = {
        "resume_id": "RES-001",
        "skills": [
            "Python",
            "Docker",
        ],
        "metadata": {
            "source": "resume.pdf",
        },
    }

    cache.set(
        "parsed:RES-001",
        value,
    )

    assert cache.get(
        "parsed:RES-001"
    ) == value


def test_cache_keys_are_filesystem_safe(tmp_path):
    cache = Cache(tmp_path)

    cache.set(
        "resume/Candidate A?embedding",
        "value",
    )

    assert cache.get(
        "resume/Candidate A?embedding"
    ) == "value"

    files = list(
        tmp_path.glob("*.cache")
    )

    assert len(files) == 1