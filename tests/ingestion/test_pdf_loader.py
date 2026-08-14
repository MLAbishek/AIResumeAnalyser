import pytest
from app.ingestion.pdf_loader import PDFLoader
from app.core.schemas import DocumentType, RawDocument

def test_pdf_loader_rejects_non_pdf(tmp_path):
    # Create a temporary non-PDF file
    dummy_file = tmp_path / "resume_001.txt"
    dummy_file.write_text("This is plain text, not a PDF.")

    loader = PDFLoader()

    with pytest.raises(ValueError):
        loader.load(str(dummy_file))


def test_pdf_loader_invalid_path():
    loader = PDFLoader()

    with pytest.raises(FileNotFoundError):
        loader.load("data/raw/resumes/non_existent.pdf")



def test_pdf_loader_returns_raw_document():
    loader = PDFLoader()

    document = loader.load(
        "data/raw/resumes/resume_001.pdf",
        document_type=DocumentType.RESUME,
    )

    assert isinstance(document, RawDocument)
    assert document.document_type == DocumentType.RESUME

    assert document.document_id == document.metadata.checksum
    assert document.metadata.file_name == "resume_001.pdf"
    assert document.metadata.content_type == "application/pdf"

    assert len(document.pages) > 0
    assert document.raw_text
    assert document.pages[0].page_number == 1