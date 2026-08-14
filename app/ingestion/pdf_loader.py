from pathlib import Path
from app.core.schemas import DocumentType, RawDocument, RawDocumentPage
from app.core.document_manager import DocumentManager
import pypdf 

class PDFLoader:
    def __init__(self):
        self.document_manager = DocumentManager()
    def load(
        self,
        file_path: str,
        document_type : DocumentType | None = None,
        document_id : str | None = None
    ) -> RawDocument:
        path = Path(file_path)

        # 1. Validate extension FIRST so non-PDFs raise ValueError
        if path.suffix.lower() != ".pdf":
            raise ValueError(f"Expected a .pdf file, got: {path.suffix}")

        # 2. Check existence SECOND so missing PDFs raise FileNotFoundError
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        if document_type is None:
            raise ValueError("document_type is required for a valid PDF")

        # Fall back to file stem if no document_id provided
        if document_id is None:
            document_id, metadata = self.document_manager.create_document_metadata(file_path)
        else:
            metadata = self.document_manager.build_metadata(file_path)

        pages: list[RawDocumentPage] = []

        with open(path, "rb") as f:
            reader = pypdf.PdfReader(f)
            for idx, page in enumerate(reader.pages, start=1):
                extracted_text = page.extract_text() or ""
                pages.append(
                    RawDocumentPage(
                        page_number=idx,
                        text=extracted_text.strip()
                    )
                )

        return RawDocument(
            document_id=document_id,
            document_type=document_type,
            source_path = str(path),
            pages = pages,
            raw_text="\n\n".join(page.text for page in pages),
            metadata=metadata,
        )