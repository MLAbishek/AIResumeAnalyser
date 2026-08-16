class DocumentStorageError(Exception):
    """Base exception for document storage errors."""


class DocumentNotFoundError(DocumentStorageError):
    """Raised when a requested document does not exist."""


class DocumentAlreadyExistsError(DocumentStorageError):
    """Raised when attempting to store an existing document."""