"""
Targeted tests for ModelService: device selection, load-once
semantics, inference-only execution, and thread-safety of the
one-time load. sentence_transformers.SentenceTransformer is mocked
throughout - these never download/load the real BGE-M3 model.
"""

import threading
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.services.model_service import (
    ModelNotLoadedError,
    ModelService,
)


def _fake_sentence_transformer():
    fake = MagicMock()
    fake.encode.return_value = np.array(
        [[0.1, 0.2, 0.3]], dtype=np.float32
    )
    return fake


class TestDeviceSelection:
    def test_uses_cuda_when_available(self):
        service = ModelService(model_name="fake-model")
        fake_st = _fake_sentence_transformer()

        with patch(
            "torch.cuda.is_available", return_value=True
        ), patch(
            "sentence_transformers.SentenceTransformer",
            return_value=fake_st,
        ) as mock_constructor:
            service.load()

        assert service.device == "cuda"
        mock_constructor.assert_called_once_with(
            "fake-model", device="cuda"
        )

    def test_uses_cpu_when_cuda_unavailable(self):
        service = ModelService(model_name="fake-model")
        fake_st = _fake_sentence_transformer()

        with patch(
            "torch.cuda.is_available", return_value=False
        ), patch(
            "sentence_transformers.SentenceTransformer",
            return_value=fake_st,
        ) as mock_constructor:
            service.load()

        assert service.device == "cpu"
        mock_constructor.assert_called_once_with(
            "fake-model", device="cpu"
        )

    def test_device_raises_before_load(self):
        service = ModelService(model_name="fake-model")

        with pytest.raises(ModelNotLoadedError):
            _ = service.device


class TestLoadOnceSemantics:
    def test_load_is_idempotent(self):
        service = ModelService(model_name="fake-model")
        fake_st = _fake_sentence_transformer()

        with patch(
            "torch.cuda.is_available", return_value=False
        ), patch(
            "sentence_transformers.SentenceTransformer",
            return_value=fake_st,
        ) as mock_constructor:
            service.load()
            service.load()
            service.load()

        mock_constructor.assert_called_once()

    def test_load_calls_eval(self):
        service = ModelService(model_name="fake-model")
        fake_st = _fake_sentence_transformer()

        with patch(
            "torch.cuda.is_available", return_value=False
        ), patch(
            "sentence_transformers.SentenceTransformer",
            return_value=fake_st,
        ):
            service.load()

        fake_st.eval.assert_called_once()

    def test_concurrent_load_calls_construct_the_model_once(self):
        # Simulates multiple FastAPI worker threads racing to
        # trigger the model load at the same time.
        service = ModelService(model_name="fake-model")
        fake_st = _fake_sentence_transformer()

        with patch(
            "torch.cuda.is_available", return_value=False
        ), patch(
            "sentence_transformers.SentenceTransformer",
            return_value=fake_st,
        ) as mock_constructor:
            threads = [
                threading.Thread(target=service.load)
                for _ in range(8)
            ]

            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

        mock_constructor.assert_called_once()

    def test_injected_model_skips_loading_entirely(self):
        fake_model = _fake_sentence_transformer()
        service = ModelService(
            model_name="fake-model",
            model=fake_model,
            device="cpu",
        )

        assert service.is_loaded is True
        assert service.device == "cpu"

        with patch(
            "sentence_transformers.SentenceTransformer"
        ) as mock_constructor:
            service.load()

        mock_constructor.assert_not_called()


class TestInference:
    def test_encode_raises_before_load(self):
        service = ModelService(model_name="fake-model")

        with pytest.raises(ModelNotLoadedError):
            service.encode(["some text"])

    def test_encode_returns_numpy_array(self):
        fake_model = _fake_sentence_transformer()
        service = ModelService(
            model_name="fake-model",
            model=fake_model,
            device="cpu",
        )

        result = service.encode(["some text"])

        assert isinstance(result, np.ndarray)
        assert result.dtype == np.float32

    def test_encode_uses_inference_mode(self):
        fake_model = _fake_sentence_transformer()
        service = ModelService(
            model_name="fake-model",
            model=fake_model,
            device="cpu",
        )

        with patch(
            "torch.inference_mode"
        ) as mock_inference_mode:
            service.encode(["some text"])

        mock_inference_mode.assert_called_once()

    def test_raw_model_raises_before_load(self):
        service = ModelService(model_name="fake-model")

        with pytest.raises(ModelNotLoadedError):
            _ = service.raw_model


class TestUnload:
    def test_unload_resets_state(self):
        fake_model = _fake_sentence_transformer()
        service = ModelService(
            model_name="fake-model",
            model=fake_model,
            device="cpu",
        )

        service.unload()

        assert service.is_loaded is False
        with pytest.raises(ModelNotLoadedError):
            _ = service.device
