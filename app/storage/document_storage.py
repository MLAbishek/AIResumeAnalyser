from pathlib import Path
from typing import BinaryIO
import mimetypes
from app.core.document_manager import DocumentManager
from app.core.schemas import (
    DocumentMetadata,
    RawDocument,
)

from app.storage.exceptions import (
    DocumentAlreadyExistsError,
    DocumentNotFoundError,
)


class DocumentStorage:
    """
    Persistent filesystem-backed storage for original and
    processed documents.

    Storage layout:

        root/
            raw/
                <document_id>.<extension>

            processed/
                <document_id>.json
    """

    def __init__(
        self,
        root_path: str | Path = "data/storage",
    ):
        self.root = Path(root_path)

        self.raw_root = self.root / "raw"
        self.processed_root = self.root / "processed"

        self.raw_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.processed_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.document_manager = DocumentManager()

    def store_raw(
        self,
        file_path: str | Path,
        *,
        document_id: str | None = None,
    ) -> DocumentMetadata:
        """
        Persist the original document.

        The document ID defaults to the SHA-256 checksum.
        """

        source = Path(file_path)

        if not source.exists():
            raise FileNotFoundError(
                f"File not found: {source}"
            )

        if not source.is_file():
            raise ValueError(
                f"Path is not a file: {source}"
            )

        if document_id is None:
            document_id = (
                self.document_manager.generate_document_id(
                    str(source)
                )
            )

        metadata = self._build_metadata(source)

        destination = (
            self.raw_root
            / f"{document_id}{source.suffix.lower()}"
        )

        if destination.exists():
            raise DocumentAlreadyExistsError(
                f"Document already exists: {document_id}"
            )

        destination.write_bytes(
            source.read_bytes()
        )

        return metadata

    def store_processed(
        self,
        document: RawDocument,
    ) -> Path:
        """
        Persist the processed RawDocument representation.
        """

        destination = (
            self.processed_root
            / f"{document.document_id}.json"
        )

        if destination.exists():
            raise DocumentAlreadyExistsError(
                f"Processed document already exists: "
                f"{document.document_id}"
            )

        destination.write_text(
            document.model_dump_json(indent=2),
            encoding="utf-8",
        )

        return destination

    def retrieve_raw(
        self,
        document_id: str,
    ) -> bytes:
        """
        Retrieve original document bytes by document ID.
        """

        matches = list(
            self.raw_root.glob(
                f"{document_id}.*"
            )
        )

        if not matches:
            raise DocumentNotFoundError(
                f"Raw document not found: {document_id}"
            )

        return matches[0].read_bytes()

    def retrieve_processed(
        self,
        document_id: str,
    ) -> RawDocument:
        """
        Retrieve the processed RawDocument.
        """

        path = (
            self.processed_root
            / f"{document_id}.json"
        )

        if not path.exists():
            raise DocumentNotFoundError(
                f"Processed document not found: "
                f"{document_id}"
            )

        return RawDocument.model_validate_json(
            path.read_text(
                encoding="utf-8"
            )
        )

    def raw_exists(
        self,
        document_id: str,
    ) -> bool:
        return any(
            self.raw_root.glob(
                f"{document_id}.*"
            )
        )

    def processed_exists(
        self,
        document_id: str,
    ) -> bool:
        return (
            self.processed_root
            / f"{document_id}.json"
        ).exists()

    def delete(
        self,
        document_id: str,
    ) -> None:
        """
        Delete both raw and processed representations.
        """

        raw_matches = list(
            self.raw_root.glob(
                f"{document_id}.*"
            )
        )

        for path in raw_matches:
            path.unlink()

        processed = (
            self.processed_root
            / f"{document_id}.json"
        )

        if processed.exists():
            processed.unlink()

    @staticmethod
    def _build_metadata(
        path: Path,
    ) -> DocumentMetadata:
        import mimetypes

        stat = path.stat()

        content_type, _ = (
            mimetypes.guess_type(
                path.name
            )
        )

        manager = DocumentManager()

        return DocumentMetadata(
            file_name=path.name,
            file_size=stat.st_size,
            content_type=(
                mimetypes.guess_type(path.name)[0]
                or "application/octet-stream"
            ),
            checksum=manager.calculate_checksum(
                str(path)
            ),
        )