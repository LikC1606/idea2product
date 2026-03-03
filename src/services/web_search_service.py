"""Web search service for Stage 2 model discovery (e.g. search for API documentation)."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import urllib.request
import urllib.error
import json

from src.utils.logger import get_logger

logger = get_logger(__name__)


class WebSearchProvider(ABC):
    """Abstract provider for web search. Returns list of results with title, link, snippet."""

    @abstractmethod
    def search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Search the web and return results.

        Args:
            query: Search query string.
            num_results: Maximum number of results to return.

        Returns:
            List of dicts with keys title, link, snippet (or equivalent).
        """
        pass


class SerperSearchProvider(WebSearchProvider):
    """Web search via Serper API (https://serper.dev) - Google search JSON API."""

    def __init__(self, api_key: str, timeout: int = 15):
        self.api_key = api_key
        self.timeout = timeout
        self._base_url = "https://google.serper.dev/search"

    def search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        if not query or not query.strip():
            return []
        data = json.dumps({"q": query.strip(), "num": min(num_results, 20)}).encode("utf-8")
        req = urllib.request.Request(
            self._base_url,
            data=data,
            headers={
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            logger.warning(f"Serper API HTTP error: {e.code} {e.reason}")
            return []
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Serper API request failed: {e}")
            return []
        organic = body.get("organic") or []
        results = []
        for i, item in enumerate(organic):
            if i >= num_results:
                break
            results.append({
                "title": item.get("title") or "",
                "link": item.get("link") or "",
                "snippet": item.get("snippet") or "",
            })
        return results


def get_web_search_provider(settings: Any) -> Optional[WebSearchProvider]:
    """
    Return a WebSearchProvider from settings, or None if disabled.

    Uses enable_stage2_web_search and web_search_provider ("serper").
    """
    if not getattr(settings, "enable_stage2_web_search", False):
        return None
    provider = getattr(settings, "web_search_provider", "serper") or "serper"
    api_key = getattr(settings, "web_search_api_key", None) or getattr(settings, "serper_api_key", None)
    if not api_key:
        logger.warning("Stage 2 web search enabled but web_search_api_key (or serper_api_key) not set")
        return None
    if provider == "serper":
        return SerperSearchProvider(
            api_key=api_key,
            timeout=getattr(settings, "web_search_timeout", 15),
        )
    logger.warning(f"Unknown web_search_provider: {provider}")
    return None
