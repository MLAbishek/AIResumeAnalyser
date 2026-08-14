from pathlib import Path
from dataclasses import dataclass


@dataclass
class ValidationResult:
    is_valid: bool
    file_path: str
    file_type: str | None = None
    errors: list[str] | None = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class DocumentValidator:
    """
    Validates resume/JD source files before ingestion.

    Responsibilities:
    - File existence
    - File type
    - File size
    - Empty file detection
    - Basic format/corruption checks
    """

    SUPPORTED_EXTENSIONS = {
        ".pdf",
        ".docx",
        ".txt",
    }

    def __init__(self, max_file_size_mb: int = 10):
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024

    def validate(self, file_path: str | Path) -> ValidationResult:
        path = Path(file_path)
        errors: list[str] = []

        # 1. Existence
        if not path.exists():
            return ValidationResult(
                is_valid=False,
                file_path=str(path),
                errors=["File does not exist"],
            )

        # 2. Must be a regular file
        if not path.is_file():
            return ValidationResult(
                is_valid=False,
                file_path=str(path),
                errors=["Path is not a file"],
            )

        # 3. Extension
        extension = path.suffix.lower()

        if extension not in self.SUPPORTED_EXTENSIONS:
            errors.append(
                f"Unsupported file type: {extension or 'no extension'}"
            )

        # 4. File size
        file_size = path.stat().st_size

        if file_size == 0:
            errors.append("File is empty")

        elif file_size > self.max_file_size_bytes:
            errors.append(
                f"File exceeds maximum size of "
                f"{self.max_file_size_bytes // (1024 * 1024)} MB"
            )

        # 5. Basic format validation
        if not errors:
            format_error = self._validate_format(path, extension)

            if format_error:
                errors.append(format_error)

        return ValidationResult(
            is_valid=len(errors) == 0,
            file_path=str(path),
            file_type=extension,
            errors=errors,
        )

    def _validate_format(
        self,
        path: Path,
        extension: str,
    ) -> str | None:

        try:
            if extension == ".pdf":
                return self._validate_pdf(path)

            if extension == ".docx":
                return self._validate_docx(path)

            if extension == ".txt":
                return self._validate_txt(path)

        except Exception as exc:
            return f"Corrupted or unreadable document: {exc}"

        return None

    @staticmethod
    def _validate_pdf(path: Path) -> str | None:
        import fitz

        with fitz.open(path) as document:
            if document.page_count == 0:
                return "PDF contains no pages"

        return None

    @staticmethod
    def _validate_docx(path: Path) -> str | None:
        from docx import Document

        document = Document(path)

        # A DOCX can technically contain no paragraphs,
        # so this is only a structural validation.
        if document is None:
            return "Unable to read DOCX document"

        return None

    @staticmethod
    def _validate_txt(path: Path) -> str | None:
        # Verify that the file can be decoded as UTF-8.
        path.read_text(encoding="utf-8")

        return None