from pathlib import Path
from app.core.schemas import DocumentType, RawDocument
from app.ingestion.document_validator import DocumentValidator
from app.ingestion.pdf_loader import PDFLoader
from app.ingestion.docx_loader import DOCXLoader
from app.ingestion.txt_loader import TXTLoader


class ResumeLoader:
    """
    Loads resumes from supported source formats and converts them
    into the canonical RawDocument representation.
    """

    def __init__(self):
        self.validator = DocumentValidator()
        self.loaders = {
            ".pdf" : PDFLoader(),
            ".docx" : DOCXLoader(),
            ".txt" : TXTLoader(),
        }

    def load(
        self,
        file_path: str | Path,
    ) -> RawDocument:

        path = Path(file_path)

        # Validate before attempting extraction.
        validation = self.validator.validate(path)

        if not validation.is_valid:
            raise ValueError(
                f"Document validation failed for '{path}': "
                + "; ".join(validation.errors)
            )
        
        loader = self.loaders.get(path.suffix.lower())
        
        if loader is None:
            raise ValueError(
                f"No loader registered for {path.suffix}"
            )
        
        return loader.load(
            str(path),
            DocumentType.RESUME
        )

    def _load_pdf(self, path: Path) -> RawDocument:
        import fitz

        pages = []

        with fitz.open(path) as document:
            for page_number, page in enumerate(document, start=1):
                text = page.get_text("text")

                pages.append(
                    {
                        "page_number": page_number,
                        "text": text,
                    }
                )

        return self._build_document(path, pages)

    def _load_docx(self, path: Path) -> RawDocument:
        from docx import Document

        document = Document(path)

        text = "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        )

        pages = [
            {
                "page_number": 1,
                "text": text,
            }
        ]

        return self._build_document(path, pages)

    def _load_txt(self, path: Path) -> RawDocument:
        text = path.read_text(encoding="utf-8")

        pages = [
            {
                "page_number": 1,
                "text": text,
            }
        ]

        return self._build_document(path, pages)

    @staticmethod
    def _build_document(
        path: Path,
        pages: list[dict],
    ) -> RawDocument:

        # Reuse your existing RawDocument construction here.
        #
        # This section MUST match the schema you already created.
        return RawDocument.from_file(
            file_path=str(path),
            document_type=DocumentType.RESUME,
            pages=pages,
        )