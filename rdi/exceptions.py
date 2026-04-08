"""Exception hierarchy for the RDI Framework.

All RDI-specific exceptions inherit from RDIError, the base exception class.
This allows callers to catch RDIError for broad error handling or catch
specific subclasses for targeted recovery.
"""


class RDIError(Exception):
    """Base exception for all RDI pipeline errors."""


class ModelLoadError(RDIError):
    """Raised when an ML model fails to load.

    Attributes:
        model_name: Name or path of the model that failed to load.
    """

    def __init__(self, message: str, model_name: str = "") -> None:
        super().__init__(message)
        self.model_name = model_name


class C2PAToolNotFoundError(RDIError):
    """Raised when c2patool CLI is not available on the system PATH."""


class LedgerIOError(RDIError):
    """Raised on ledger file I/O failures.

    Attributes:
        file_path: Path to the ledger file that caused the error.
    """

    def __init__(self, message: str, file_path: str = "") -> None:
        super().__init__(message)
        self.file_path = file_path


class LedgerIntegrityError(RDIError):
    """Raised when ledger chain verification fails.

    Attributes:
        index: Index of the first corrupted entry, if known.
        description: Human-readable description of the integrity failure.
    """

    def __init__(
        self,
        message: str,
        index: int | None = None,
        description: str | None = None,
    ) -> None:
        super().__init__(message)
        self.index = index
        self.description = description


class ValidationError(RDIError):
    """Raised on invalid input to pipeline components."""
