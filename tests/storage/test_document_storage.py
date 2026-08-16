from pathlib import Path

import pytest

from app.core.schemas import (
    DocumentType,
    RawDocument,
    RawDocumentPage,
)
from app.storage.document_storage import DocumentStorage
from app.storage.exceptions import (
    DocumentAlreadyExistsError,
    DocumentNotFoundError,
)


def test_store_and_retrieve_raw_document(tmp_path):
    source = tmp_path / "resume.txt"

    content = b"Python developer with 5 years experience."

    source.write_bytes(content)

    storage = DocumentStorage(
        tmp_path / "storage"
    )

    metadata = storage.store_raw(
        source
    )

    assert metadata.file_name == "resume.txt"
    assert metadata.file_size == len(content)
    assert metadata.content_type == "text/plain"
    assert metadata.checksum is not None

    document_id = metadata.checksum

    assert storage.raw_exists(
        document_id
    )

    assert (
        storage.retrieve_raw(document_id)
        == content
    )


def test_store_processed_document(tmp_path):
    storage = DocumentStorage(
        tmp_path / "storage"
    )

    document = RawDocument(
        document_id="doc-001",
        document_type=DocumentType.RESUME,
        source_path="resume.txt",
        pages=[
            RawDocumentPage(
                page_number=1,
                text="Python developer",
            )
        ],
        raw_text="Python developer",
    )

    path = storage.store_processed(
        document
    )

    assert path.exists()

    restored = storage.retrieve_processed(
        "doc-001"
    )

    assert restored.document_id == "doc-001"
    assert restored.raw_text == "Python developer"
    assert len(restored.pages) == 1


def test_duplicate_raw_document_rejected(tmp_path):
    source = tmp_path / "resume.txt"
    source.write_text(
        "Python developer",
        encoding="utf-8",
    )

    storage = DocumentStorage(
        tmp_path / "storage"
    )

    metadata = storage.store_raw(
        source
    )

    with pytest.raises(
        DocumentAlreadyExistsError
    ):
        storage.store_raw(
            source,
            document_id=metadata.checksum,
        )


def test_missing_raw_document_rejected(tmp_path):
    storage = DocumentStorage(
        tmp_path / "storage"
    )

    with pytest.raises(
        DocumentNotFoundError
    ):
        storage.retrieve_raw(
            "does-not-exist"
        )


def test_missing_processed_document_rejected(tmp_path):
    storage = DocumentStorage(
        tmp_path / "storage"
    )

    with pytest.raises(
        DocumentNotFoundError
    ):
        storage.retrieve_processed(
            "does-not-exist"
        )


def test_delete_document(tmp_path):
    source = tmp_path / "resume.txt"
    source.write_text(
        "Python developer",
        encoding="utf-8",
    )

    storage = DocumentStorage(
        tmp_path / "storage"
    )

    metadata = storage.store_raw(
        source
    )

    document = RawDocument(
        document_id=metadata.checksum,
        document_type=DocumentType.RESUME,
        source_path=str(source),
        pages=[
            RawDocumentPage(
                page_number=1,
                text="Python developer",
            )
        ],
        raw_text="Python developer",
    )

    storage.store_processed(
        document
    )

    storage.delete(
        metadata.checksum
    )

    assert not storage.raw_exists(
        metadata.checksum
    )

    assert not storage.processed_exists(
        metadata.checksum
    )