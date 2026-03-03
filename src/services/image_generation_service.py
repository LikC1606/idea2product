"""Image generation service - pluggable providers for text-to-image (e.g. DALL-E, generic HTTP APIs)."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Any, Dict
import json
import re

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ImageGenerationProvider(ABC):
    """Abstract provider for text-to-image generation."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        size: Optional[str] = None,
        n: int = 1,
    ) -> List[bytes]:
        """
        Generate image(s) from a text prompt.

        Args:
            prompt: Text description for the image.
            size: Optional size hint (e.g. "1024x1024", provider-specific).
            n: Number of images to generate (default 1).

        Returns:
            List of image payloads as bytes (e.g. PNG/JPEG).
        """
        pass


class OpenAIImageProvider(ImageGenerationProvider):
    """Generate images via OpenAI Images API (DALL-E)."""

    def __init__(
        self,
        api_key: str,
        model: str = "dall-e-3",
        base_url: Optional[str] = None,
        timeout: int = 120,
    ):
        self._client = None
        self._api_key = api_key
        self._model = model
        self._base_url = base_url or "https://api.openai.com/v1"
        self._timeout = timeout

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
                timeout=self._timeout,
            )
        return self._client

    def generate(
        self,
        prompt: str,
        *,
        size: Optional[str] = None,
        n: int = 1,
    ) -> List[bytes]:
        size = size or "1024x1024"
        if self._model == "dall-e-3":
            n = 1  # DALL-E 3 only supports n=1
        client = self._get_client()
        response = client.images.generate(
            model=self._model,
            prompt=prompt,
            n=n,
            size=size,
            response_format="b64_json",
        )
        import base64
        result = []
        for img in response.data:
            if getattr(img, "b64_json", None):
                result.append(base64.b64decode(img.b64_json))
            else:
                logger.warning("OpenAI image response missing b64_json")
        return result


class GenericHTTPImageProvider(ImageGenerationProvider):
    """
    Call any HTTP image-generation API via config.

    Expects JSON request body with a "prompt" field (or configurable key),
    and response that contains image URL(s) or base64 data. Fetches URLs to bytes.
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        *,
        method: str = "POST",
        prompt_key: str = "prompt",
        response_image_path: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        timeout: int = 120,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.method = method.upper()
        self.prompt_key = prompt_key
        # JSON path to image URL or b64 in response, e.g. "data[0].url" or "image_b64"
        self.response_image_path = response_image_path or "data[0].url"
        self.extra_headers = dict(extra_headers or {})
        self.timeout = timeout

    def generate(
        self,
        prompt: str,
        *,
        size: Optional[str] = None,
        n: int = 1,
    ) -> List[bytes]:
        import urllib.request
        import urllib.error
        import base64

        payload: Dict[str, Any] = {self.prompt_key: prompt}
        if size:
            payload["size"] = size
        if n != 1:
            payload["n"] = n

        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json", **self.extra_headers}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        req = urllib.request.Request(
            self.base_url,
            data=data,
            headers=headers,
            method=self.method,
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            logger.warning(f"Image API HTTP error: {e.code} {e.reason}")
            raise
        except Exception as e:
            logger.warning(f"Image API request failed: {e}")
            raise

        try:
            out = json.loads(body)
        except json.JSONDecodeError:
            logger.warning("Image API response is not JSON")
            raise ValueError("Image API response is not JSON")

        images = self._extract_images(out)
        result = []
        for item in images:
            if isinstance(item, bytes):
                result.append(item)
            elif isinstance(item, str):
            # URL or data URL
                if item.startswith("data:"):
                    b64 = item.split(",", 1)[-1]
                    result.append(base64.b64decode(b64))
                else:
                    result.append(self._fetch_url(item))
            else:
                logger.warning("Unexpected image item type")
        return result

    def _extract_images(self, data: Any) -> List[Any]:
        """Resolve response_image_path (e.g. 'data[0].url') to a list of URLs or bytes."""
        path = self.response_image_path
        if not path:
            return []
        parts = re.split(r"\.|\[|\]", path)
        parts = [p.strip() for p in parts if p.strip()]
        cur = data
        for p in parts:
            if cur is None:
                return []
            if isinstance(cur, list) and p.isdigit():
                cur = cur[int(p)]
            elif isinstance(cur, dict):
                cur = cur.get(p)
            else:
                return []
        if isinstance(cur, list):
            return cur
        return [cur]

    def _fetch_url(self, url: str) -> bytes:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "Idea2Product/1.0"})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return resp.read()


def get_image_provider(settings: Any) -> Optional[ImageGenerationProvider]:
    """
    Return an ImageGenerationProvider from settings, or None if disabled.

    Uses enable_image_generation and image_generation_provider ("openai" | "generic_http").
    """
    if not getattr(settings, "enable_image_generation", False):
        return None
    provider = getattr(settings, "image_generation_provider", "openai") or "openai"
    if provider == "openai":
        api_key = getattr(settings, "openai_api_key", None) or getattr(settings, "image_generation_api_key", None)
        if not api_key:
            logger.warning("Image generation enabled but no API key (openai_api_key or image_generation_api_key)")
            return None
        model = getattr(settings, "image_generation_openai_model", "dall-e-3")
        base_url = getattr(settings, "openai_base_url", None) or getattr(settings, "image_generation_base_url", None)
        return OpenAIImageProvider(
            api_key=api_key,
            model=model,
            base_url=base_url,
            timeout=getattr(settings, "llm_timeout_seconds", 120),
        )
    if provider == "generic_http":
        base_url = getattr(settings, "image_generation_base_url", None)
        if not base_url:
            logger.warning("Image generation provider is generic_http but image_generation_base_url is not set")
            return None
        api_key = getattr(settings, "image_generation_api_key", None)
        extra_headers = getattr(settings, "image_generation_extra_headers", None)
        if isinstance(extra_headers, str):
            try:
                extra_headers = json.loads(extra_headers)
            except json.JSONDecodeError:
                extra_headers = None
        return GenericHTTPImageProvider(
            base_url=base_url,
            api_key=api_key,
            prompt_key=getattr(settings, "image_generation_prompt_key", "prompt"),
            response_image_path=getattr(settings, "image_generation_response_image_path", None),
            extra_headers=extra_headers,
            timeout=getattr(settings, "image_generation_timeout", 120),
        )
    logger.warning(f"Unknown image_generation_provider: {provider}")
    return None
