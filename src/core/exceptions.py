"""Project-level exceptions for Idea2Product."""


class Idea2ProductError(Exception):
    """Base exception for Idea2Product."""

    pass


class LLMServiceError(Idea2ProductError):
    """LLM API call failed."""

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
