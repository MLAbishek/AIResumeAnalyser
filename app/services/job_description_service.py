from pathlib import Path

from app.core.schemas import DocumentType, JobDescription, RawDocument
from app.ingestion.document_validator import DocumentValidator
from app.ingestion.docx_loader import DOCXLoader
from app.ingestion.pdf_loader import PDFLoader
from app.ingestion.txt_loader import TXTLoader
from app.parsing.jd_parser import JDParser


class JobDescriptionExtractionError(Exception):
    """
    Raised when an uploaded job description file cannot be turned
    into usable text - corrupted/malformed document, or a
    structurally valid file with no readable text at all.
    """

    pass


# Reuses the exact same generic, format-specific loaders that
# ResumeLoader (app/ingestion/resume_loader.py) already uses for
# resumes - PDFLoader/DOCXLoader/TXTLoader are not resume-specific,
# they simply stamp whichever DocumentType they're given onto the
# resulting RawDocument. No PDF/DOCX/TXT extraction logic is
# duplicated here.
_LOADERS = {
    ".pdf": PDFLoader(),
    ".docx": DOCXLoader(),
    ".txt": TXTLoader(),
}


def _load_document(file_path: str | Path) -> RawDocument:
    path = Path(file_path)

    validation = DocumentValidator().validate(path)

    if not validation.is_valid:
        raise JobDescriptionExtractionError(
            "; ".join(validation.errors)
        )

    loader = _LOADERS.get(path.suffix.lower())

    if loader is None:
        raise JobDescriptionExtractionError(
            f"No loader registered for {path.suffix}"
        )

    try:
        document = loader.load(
            str(path),
            DocumentType.JOB_DESCRIPTION,
        )
    except (ValueError, FileNotFoundError) as exc:
        raise JobDescriptionExtractionError(str(exc)) from exc

    if not document.raw_text.strip():
        raise JobDescriptionExtractionError(
            "The uploaded job description does not contain "
            "readable text."
        )

    return document


def extract_job_description(file_path: str | Path) -> str:
    """
    Extract plain job description text from an uploaded PDF, DOCX,
    or TXT file.

    Raises:
        JobDescriptionExtractionError: if the file is corrupted,
            malformed, or contains no readable text.
    """

    return _load_document(file_path).raw_text.strip()


def parse_job_description(file_path: str | Path) -> JobDescription:
    """
    Extract AND parse an uploaded PDF/DOCX/TXT job description into
    the same structured JobDescription representation already used
    for JSON-submitted jobs - reusing the existing JDParser rather
    than persisting only raw text and discarding everything else it
    is able to extract (title, required/preferred skills, location,
    job type, education, certifications, responsibilities).

    Raises:
        JobDescriptionExtractionError: if the file is corrupted,
            malformed, or contains no readable text.
    """

    document = _load_document(file_path)

    try:
        return JDParser().parse(document)
    except ValueError as exc:
        raise JobDescriptionExtractionError(str(exc)) from exc
