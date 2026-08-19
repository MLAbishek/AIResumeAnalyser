from app.core.config import settings
from app.storage.document_storage import DocumentStorage


def get_resume_storage() -> DocumentStorage:
    """
    The single, shared location where candidates' original uploaded
    resume files (PDF/DOCX/TXT) are persisted, keyed by the same
    deterministic `resume_id` already used to identify the parsed
    Resume row - see app/parsing/resume_parse.py. Kept in its own
    subtree so resume files never collide with any other document
    type this storage class might later be used for.
    """

    return DocumentStorage(
        settings.data_dir / "storage" / "resumes"
    )
