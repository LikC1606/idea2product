"""Project-level exceptions for Idea2Product."""


class Idea2ProductError(Exception):
    """Base exception for Idea2Product."""

    pass


class LLMServiceError(Idea2ProductError):
    """LLM API call failed."""

    pass


class TransientLLMError(LLMServiceError):
    """Retryable/transient LLM failure (timeout, 429, 5xx, network)."""

    pass


class PermanentLLMError(LLMServiceError):
    """Non-retryable LLM failure (invalid request/auth/model not found)."""

    pass


class GenerationCancelledError(Idea2ProductError):
    """Generation task cancelled by user."""

    pass


class GenerationTimeoutError(Idea2ProductError):
    """Generation exceeded allowed wall-clock budget."""

    pass


class StageExecutionError(Idea2ProductError):
    """A pipeline stage failed.

    Attributes:
        stage: Stage number (2, 3, or 4).
        message: Error message.
        partial_context: Optional partial context when available.
    """

    def __init__(self, message: str, stage: int = None, partial_context=None):
        super().__init__(message)
        self.stage = stage
        self.partial_context = partial_context


class ArtifactIOError(Idea2ProductError):
    """File read/write failure."""

    pass


class PreviewServiceError(Idea2ProductError):
    """Preview subprocess or port allocation failed."""

    pass
