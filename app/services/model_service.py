"""
Owns the embedding model's device selection, one-time loading, and
inference lifecycle.

This is the ONLY place a SentenceTransformer/BGE-M3 model is ever
constructed from a model name. It is created once, in FastAPI's
lifespan handler (see app/lifespan.py), and shared for the lifetime
of the process - no route, service, or per-request code path is
allowed to construct its own model instance from scratch.

CPU-first, CUDA-later: device selection is a single
torch.cuda.is_available() check made once, at load time. Nothing
else in the application needs to change when the deployment
environment gains a CUDA GPU - the same code path picks it up
automatically the next time the process starts.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class ModelNotLoadedError(RuntimeError):
    """
    Raised if inference is attempted before ModelService.load() has
    completed.

    This should be unreachable in normal operation: the FastAPI
    lifespan handler calls load() once, synchronously, before the
    app starts accepting any requests (see app/lifespan.py). Seeing
    this error means a code path is bypassing that lifecycle -
    e.g. a standalone script constructing ModelService without
    calling load(), or a bug in the lifespan wiring - and should be
    treated as a programming error to fix, not a runtime condition
    to design a fallback around.
    """


class ModelService:
    """
    Loads and owns exactly one embedding model instance for the
    life of the process.

    Usage:

        model_service = ModelService(model_name="BAAI/bge-m3")
        model_service.load()          # once, at startup
        ...
        vectors = model_service.encode(["some text"])   # per request

    A pre-built model can be injected (model=...) for tests, in
    which case load() becomes a no-op - this mirrors the same
    testability pattern already used by EmbeddingGenerator.
    """

    def __init__(
        self,
        model_name: str,
        model: Any | None = None,
        device: str | None = None,
    ) -> None:
        if not model_name.strip():
            raise ValueError("model_name must not be empty")

        self.model_name = model_name
        self._model = model
        self._device = device if model is not None else None
        # Guards the one-time load below against a rare race where
        # two threads both observe `_model is None` before either
        # has finished loading - see load()'s double-checked-lock.
        self._load_lock = threading.Lock()

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def device(self) -> str:
        if self._device is None:
            raise ModelNotLoadedError(
                "ModelService.device accessed before load() "
                "completed."
            )
        return self._device

    def load(self) -> None:
        """
        Load the model exactly once, selecting CUDA automatically if
        available and falling back to CPU otherwise. Safe to call
        more than once - every call after the first is a fast no-op,
        so callers never need to guard calls to it themselves.

        Intended to be called exactly once, from the FastAPI
        lifespan handler at startup. Never call this from a request
        handler, a per-request service method, or resume/matching
        processing code - doing so is exactly the bug this class
        exists to prevent.
        """
        if self._model is not None:
            return

        with self._load_lock:
            if self._model is not None:
                return

            import torch
            from sentence_transformers import SentenceTransformer

            cuda_available = torch.cuda.is_available()
            device = "cuda" if cuda_available else "cpu"

            logger.info(
                "Loading embedding model. model=%s device=%s "
                "cuda_available=%s",
                self.model_name,
                device,
                cuda_available,
            )

            start = time.monotonic()

            model = SentenceTransformer(
                self.model_name,
                device=device,
            )
            model.eval()

            elapsed = time.monotonic() - start

            self._model = model
            self._device = device

            logger.info(
                "Embedding model loaded. model=%s device=%s "
                "load_seconds=%.2f",
                self.model_name,
                device,
                elapsed,
            )

    def unload(self) -> None:
        """
        Release the model. Called on application shutdown, and
        useful in tests that need a clean slate between cases.
        """
        self._model = None
        self._device = None

    def encode(
        self,
        texts: list[str],
        *,
        batch_size: int = 32,
        normalize: bool = True,
    ) -> np.ndarray:
        """
        Run inference-only embedding generation on the already-
        loaded model. Never loads the model itself - see load().

        Wrapped in torch.inference_mode() (stricter and slightly
        faster than torch.no_grad(): it also disables autograd
        version counting, which is safe here since embeddings are
        never used in a backward pass) so this is unambiguously a
        forward-only inference call, on whichever device the model
        was loaded onto.
        """
        if self._model is None:
            raise ModelNotLoadedError(
                "ModelService.encode() called before load(). The "
                "model must be loaded once at application startup "
                "(see app/lifespan.py) before any request is "
                "served."
            )

        import torch

        with torch.inference_mode():
            embeddings = self._model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=normalize,
            )

        return np.asarray(embeddings, dtype=np.float32)

    @property
    def raw_model(self) -> Any:
        """
        Escape hatch for callers that need the underlying model
        object directly (namely EmbeddingGenerator, which checks for
        BGE-M3-specific methods like encode_query() and
        get_sentence_embedding_dimension()). Prefer encode() for
        actual inference calls.
        """
        if self._model is None:
            raise ModelNotLoadedError(
                "ModelService.raw_model accessed before load()."
            )
        return self._model
