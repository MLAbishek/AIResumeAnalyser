from pathlib import Path
from dataclasses import dataclass, field
import pypdf 


@dataclass
class Page:
    page_number: int
    text: str


@dataclass
class RawDocument:
    document_id: str
    document_type: str
    pages: list[Page] = field(default_factory=list)

    @property
    def text(self) -> str:
        """Combines text from all pages into a single full string."""
        return "\n\n".join(page.text for page in self.pages)


class PDFLoader:
    def load(
        self,
        file_path: str,
        document_id: str | None = None
    ) -> RawDocument:
        path = Path(file_path)

        # 1. Validate extension FIRST so non-PDFs raise ValueError
        if path.suffix.lower() != ".pdf":
            raise ValueError(f"Expected a .pdf file, got: {path.suffix}")

        # 2. Check existence SECOND so missing PDFs raise FileNotFoundError
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        # Fall back to file stem if no document_id provided
        doc_id = document_id or path.stem

        pages: list[Page] = []

        with open(path, "rb") as f:
            reader = pypdf.PdfReader(f)
            for idx, page in enumerate(reader.pages, start=1):
                extracted_text = page.extract_text() or ""
                pages.append(
                    Page(
                        page_number=idx,
                        text=extracted_text.strip()
                    )
                )

        return RawDocument(
            document_id=doc_id,
            document_type="pdf",
            pages=pages
        )