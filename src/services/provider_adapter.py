"""Provider Adapter - Abstracts differences between LLM API providers.

Currently supports:
  - OpenAI (and any OpenAI-compatible endpoint)
  - OpenRouter (via base_url detection)
  - Azure OpenAI (via base_url detection)

All providers are accessed through the OpenAI Python SDK; the adapter
handles provider-specific header or parameter differences.
"""

from typing import Optional, Dict, Any
from openai import OpenAI
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ProviderAdapter:
    """Base adapter for LLM providers. Uses standard OpenAI client."""

    provider_name: str = "openai"

    def create_client(self, api_key: str, base_url: str, timeout: int = 120) -> OpenAI:
        return OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

    def prepare_kwargs(self, model: str, **kwargs) -> Dict[str, Any]:
        """Modify API call kwargs if the provider needs special handling."""
        kwargs["model"] = model
        return kwargs


class OpenRouterAdapter(ProviderAdapter):
    """Adapter for OpenRouter (openrouter.ai).

    OpenRouter uses the same OpenAI-compatible API but requires the model
    to be specified as provider/model (e.g. 'openai/gpt-4o').
    It also accepts an optional HTTP-Referer header for attribution.
    """

    provider_name: str = "openrouter"

    def create_client(self, api_key: str, base_url: str, timeout: int = 120) -> OpenAI:
        return OpenAI(
            api_key=api_key,
            base_url=base_url or "https://openrouter.ai/api/v1",
            timeout=timeout,
            default_headers={"HTTP-Referer": "https://github.com/idea2product"},
        )


class AzureAdapter(ProviderAdapter):
    """Adapter for Azure OpenAI Service.

    Azure uses a deployment-based URL pattern and api-version query param.
    The OpenAI SDK's AzureOpenAI client handles this natively, but we
    keep the adapter thin: if the base_url looks like Azure, we use
    AzureOpenAI instead.
    """

    provider_name: str = "azure"

    def create_client(self, api_key: str, base_url: str, timeout: int = 120) -> OpenAI:
        try:
            from openai import AzureOpenAI
            return AzureOpenAI(
                api_key=api_key,
                azure_endpoint=base_url,
                api_version="2024-02-01",
                timeout=timeout,
            )
        except ImportError:
            logger.warning("AzureOpenAI not available, falling back to standard OpenAI client")
            return OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)


_ADAPTERS = {
    "openai": ProviderAdapter,
    "openrouter": OpenRouterAdapter,
    "azure": AzureAdapter,
}


def get_adapter(provider: str = "openai") -> ProviderAdapter:
    """Get the adapter for a given provider name."""
    cls = _ADAPTERS.get(provider.lower(), ProviderAdapter)
    return cls()


def detect_provider(base_url: str) -> str:
    """Auto-detect provider from base_url."""
    url_lower = (base_url or "").lower()
    if "openrouter.ai" in url_lower:
        return "openrouter"
    if "azure" in url_lower or "cognitiveservices" in url_lower:
        return "azure"
    return "openai"
