"""Audio (TTS / music) generation service abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Any, Dict


class AudioGenerationProvider(ABC):
    """Abstract provider for audio generation (TTS, music, sound effects)."""

    @abstractmethod
    def generate_audio(
        self,
        text: str,
        *,
        voice: Optional[str] = None,
        format: str = "mp3",
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Generate an audio file and return local Path."""


class GenericHTTPAudioProvider(AudioGenerationProvider):
    """Generic HTTP client for audio generation (TTS/music) APIs."""

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: int = 120,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.extra_headers = extra_headers or {}

    def generate_audio(
        self,
        text: str,
        *,
        voice: Optional[str] = None,
        format: str = "mp3",
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> Path:
        raise NotImplementedError(
            "GenericHTTPAudioProvider.generate_audio must be wired to a concrete API "
            "in a higher-level service or adapter."
        )


def get_audio_provider(settings: Any, spec: Optional[Any] = None) -> Optional[AudioGenerationProvider]:
    """Factory for AudioGenerationProvider based on settings and optional ExternalModelSpec."""
    enabled = getattr(settings, "enable_audio_generation", False)
    if not enabled:
        return None
    provider = getattr(settings, "audio_generation_provider", "generic_http")
    if provider != "generic_http":
        return None
    base_url = getattr(settings, "audio_generation_base_url", None)
    if spec is not None and getattr(spec, "base_url_hint", None):
        base_url = getattr(spec, "base_url_hint", base_url)
    if not base_url:
        return None
    api_key = getattr(settings, "audio_generation_api_key", None)
    timeout = getattr(settings, "audio_generation_timeout", 120)
    extra_headers_str = getattr(settings, "audio_generation_extra_headers", None)
    extra_headers: Dict[str, str] = {}
    if extra_headers_str:
        try:
            import json

            parsed = json.loads(extra_headers_str)
            if isinstance(parsed, dict):
                extra_headers = {str(k): str(v) for k, v in parsed.items()}
        except Exception:
            extra_headers = {}
    return GenericHTTPAudioProvider(
        base_url=base_url,
        api_key=api_key,
        timeout=timeout,
        extra_headers=extra_headers,
    )

