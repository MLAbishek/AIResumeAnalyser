from pathlib import Path

from app.ingestion.document_validator import DocumentValidator


def test_valid_txt_file(tmp_path: Path):
    file = tmp_path / "resume.txt"
    file.write_text(
        "John Doe\nPython Developer\n5 years experience",
        encoding="utf-8",
    )

    validator = DocumentValidator()

    result = validator.validate(file)

    assert result.is_valid is True
    assert result.file_type == ".txt"
    assert result.errors == []


def test_missing_file(tmp_path: Path):
    file = tmp_path / "missing.txt"

    validator = DocumentValidator()

    result = validator.validate(file)

    assert result.is_valid is False
    assert "File does not exist" in result.errors


def test_empty_file(tmp_path: Path):
    file = tmp_path / "empty.txt"
    file.touch()

    validator = DocumentValidator()

    result = validator.validate(file)

    assert result.is_valid is False
    assert "File is empty" in result.errors


def test_unsupported_file_type(tmp_path: Path):
    file = tmp_path / "resume.exe"
    file.write_bytes(b"fake executable")

    validator = DocumentValidator()

    result = validator.validate(file)

    assert result.is_valid is False
    assert any(
        "Unsupported file type" in error
        for error in result.errors
    )


def test_oversized_file(tmp_path: Path):
    file = tmp_path / "large.txt"

    file.write_bytes(b"x" * 1024)

    validator = DocumentValidator(
        max_file_size_mb=0
    )

    result = validator.validate(file)

    assert result.is_valid is False
    assert any(
        "exceeds maximum size" in error
        for error in result.errors
    )


def test_invalid_utf8_txt(tmp_path: Path):
    file = tmp_path / "invalid.txt"

    file.write_bytes(b"\xff\xfe\xfa\xfb")

    validator = DocumentValidator()

    result = validator.validate(file)

    assert result.is_valid is False
    assert any(
        "Corrupted" in error
        for error in result.errors
    )