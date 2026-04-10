"""Application-level exceptions with user-friendly messages."""


class DocumentProcessingError(Exception):
    """Raised when a document cannot be processed (corrupt, empty, unsupported encoding)."""
    pass
