"""Presentation (PPT) generation service abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Any, Dict


class PresentationGenerationProvider(ABC):
    """Abstract provider for slide deck generation (PPT/PPTX)."""

    @abstractmethod
    def generate_ppt(
        self,
        slides_spec: Dict[str, Any],
        *,
        format: str = "pptx",
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Generate a slide deck from a structured spec and return local Path."""


class GenericHTTPPresentationProvider(PresentationGenerationProvider):
    """Generic HTTP client for PPT generation APIs."""

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: int = 300,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.extra_headers = extra_headers or {}

    def generate_ppt(
        self,
        slides_spec: Dict[str, Any],
        *,
        format: str = "pptx",
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> Path:
        raise NotImplementedError(
            "GenericHTTPPresentationProvider.generate_ppt must be wired to a concrete API "
            "or local generator in a higher-level service."
        )


def get_ppt_provider(settings: Any, spec: Optional[Any] = None) -> Optional[PresentationGenerationProvider]:
    """Factory for PresentationGenerationProvider based on settings and optional ExternalModelSpec."""
    enabled = getattr(settings, "enable_ppt_generation", False)
    if not enabled:
        return None
    provider = getattr(settings, "ppt_generation_provider", "generic_http")
    if provider != "generic_http":
        return None
    base_url = getattr(settings, "ppt_generation_base_url", None)
    if spec is not None and getattr(spec, "base_url_hint", None):
        base_url = getattr(spec, "base_url_hint", base_url)
    if not base_url:
        return None
    api_key = getattr(settings, "ppt_generation_api_key", None)
    timeout = getattr(settings, "ppt_generation_timeout", 300)
    extra_headers_str = getattr(settings, "ppt_generation_extra_headers", None)
    extra_headers: Dict[str, str] = {}
    if extra_headers_str:
        try:
            import json

            parsed = json.loads(extra_headers_str)
            if isinstance(parsed, dict):
                extra_headers = {str(k): str(v) for k, v in parsed.items()}
        except Exception:
            extra_headers = {}
    return GenericHTTPPresentationProvider(
        base_url=base_url,
        api_key=api_key,
        timeout=timeout,
        extra_headers=extra_headers,
    )

