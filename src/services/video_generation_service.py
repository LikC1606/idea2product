"""Video generation service abstractions.

These providers are intentionally lightweight and configuration-driven. They are
designed to be wired from Stage 3/4 using ExternalModelSpec produced in Stage 2.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Any, Dict


class VideoGenerationProvider(ABC):
    """Abstract provider for text-to-video or script-to-video models."""

    @abstractmethod
    def generate_video(
        self,
        prompt: str,
        *,
        duration_seconds: Optional[int] = None,
        format: str = "mp4",
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Generate a video file from prompt and return local Path."""


class GenericHTTPVideoProvider(VideoGenerationProvider):
    """Generic HTTP client for video generation APIs (e.g., text-to-video services).

    Concrete HTTP wiring (URL paths, request/response schema) should be configured
    via settings and/or ExternalModelSpec, not hard-coded here.
    """

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

    def generate_video(
        self,
        prompt: str,
        *,
        duration_seconds: Optional[int] = None,
        format: str = "mp4",
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> Path:
        raise NotImplementedError(
            "GenericHTTPVideoProvider.generate_video must be wired to a concrete API "
            "in a higher-level service or adapter."
        )


def get_video_provider(settings: Any, spec: Optional[Any] = None) -> Optional[VideoGenerationProvider]:
    """Factory for VideoGenerationProvider based on settings and optional ExternalModelSpec.

    Current implementation only checks configuration and returns None when disabled.
    Concrete HTTP wiring can be added incrementally without changing Stage 2.
    """
    enabled = getattr(settings, "enable_video_generation", False)
    if not enabled:
        return None
    provider = getattr(settings, "video_generation_provider", "generic_http")
    if provider != "generic_http":
        return None
    base_url = getattr(settings, "video_generation_base_url", None)
    if spec is not None and getattr(spec, "base_url_hint", None):
        base_url = getattr(spec, "base_url_hint", base_url)
    if not base_url:
        return None
    api_key = getattr(settings, "video_generation_api_key", None)
    timeout = getattr(settings, "video_generation_timeout", 300)
    extra_headers_str = getattr(settings, "video_generation_extra_headers", None)
    extra_headers: Dict[str, str] = {}
    if extra_headers_str:
        try:
            import json

            parsed = json.loads(extra_headers_str)
            if isinstance(parsed, dict):
                extra_headers = {str(k): str(v) for k, v in parsed.items()}
        except Exception:
            extra_headers = {}
    return GenericHTTPVideoProvider(
        base_url=base_url,
        api_key=api_key,
        timeout=timeout,
        extra_headers=extra_headers,
    )

