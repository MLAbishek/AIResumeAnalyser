import pytest
from app.ingestion.pdf_loader import PDFLoader


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