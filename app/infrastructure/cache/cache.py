from __future__ import annotations

import hashlib
import pickle
from pathlib import Path
from typing import Any


class Cache:
    """
    Persistent filesystem cache.

    Cache keys are converted into SHA-256 filenames so that arbitrary
    keys cannot create unsafe filesystem paths.
    """

    VERSION = 1

    def __init__(
        self,
        cache_dir: str | Path,
    ) -> None:
        self.cache_dir = Path(cache_dir)

        self.cache_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    @staticmethod
    def _normalize_key(key: str) -> str:
        if not isinstance(key, str):
            raise TypeError(
                "cache key must be a string"
            )

        if not key.strip():
            raise ValueError(
                "cache key must not be empty"
            )

        return key.strip()

    def _path_for_key(
        self,
        key: str,
    ) -> Path:
        key = self._normalize_key(key)

        digest = hashlib.sha256(
            f"{self.VERSION}:{key}".encode(
                "utf-8"
            )
        ).hexdigest()

        return self.cache_dir / f"{digest}.cache"

    def exists(
        self,
        key: str,
    ) -> bool:
        return self._path_for_key(key).exists()

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        path = self._path_for_key(key)

        if not path.exists():
            return default

        try:
            with path.open("rb") as file:
                payload = pickle.load(file)
        except (
            OSError,
            EOFError,
            pickle.PickleError,
        ):
            return default

        if not isinstance(payload, dict):
            return default

        if payload.get("version") != self.VERSION:
            return default

        return payload.get(
            "value",
            default,
        )

    def set(
        self,
        key: str,
        value: Any,
    ) -> None:
        path = self._path_for_key(key)

        temporary_path = path.with_suffix(
            ".tmp"
        )

        payload = {
            "version": self.VERSION,
            "value": value,
        }

        with temporary_path.open("wb") as file:
            pickle.dump(
                payload,
                file,
                protocol=pickle.HIGHEST_PROTOCOL,
            )

        temporary_path.replace(path)

    def delete(
        self,
        key: str,
    ) -> bool:
        path = self._path_for_key(key)

        if not path.exists():
            return False

        path.unlink()

        return True

    def clear(self) -> None:
        for path in self.cache_dir.glob(
            "*.cache"
        ):
            path.unlink()