from pathlib import Path

from app.core.schemas import DocumentType, RawDocument, RawDocumentPage
from app.core.document_manager import DocumentManager


class TXTLoader:
    def __init__(self):
        self.document_manager = DocumentManager()

    def load(
        self,
        file_path: str,
        document_type: DocumentType | None = None,
        document_id: str | None = None,
    ) -> RawDocument:
        path = Path(file_path)

        # 1. Validate extension
        if path.suffix.lower() != ".txt":
            raise ValueError(
                f"Expected a .txt file, got: {path.suffix}"
            )

        # 2. Check existence
        if not path.exists():
            raise FileNotFoundError(
                f"TXT file not found: {file_path}"
            )

        # 3. Require document type
        if document_type is None:
            raise ValueError(
                "document_type is required for a valid TXT document"
            )

        # 4. Generate metadata and document ID
        if document_id is None:
            document_id, metadata = (
                self.document_manager.create_document_metadata(
                    file_path
                )
            )
        else:
            metadata = self.document_manager.build_metadata(
                file_path
            )

        # 5. Read text
        text = path.read_text(encoding="utf-8")

        # 6. Create canonical page representation
        pages = [
            RawDocumentPage(
                page_number=1,
                text=text.strip(),
            )
        ]

        # 7. Return RawDocument
        return RawDocument(
            document_id=document_id,
            document_type=document_type,
            source_path=str(path),
            pages=pages,
            raw_text="\n\n".join(
                page.text for page in pages
            ),
            metadata=metadata,
        )