"""LLM service for interacting with OpenAI API."""

import time
from typing import Optional, Iterator, Dict, Any, List
from openai import OpenAI, APIError, RateLimitError
from src.utils.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_TIMEOUT = 120


class LLMService:
    """Service for interacting with OpenAI-compatible APIs.

    Supports multi-model routing via ``with_model()`` which returns a
    lightweight copy configured for a different model/base_url.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        vlm_model: str = "gpt-4o",
        max_tokens: int = 8000,
        temperature: float = 0.7,
        max_retries: int = 3,
        base_url: str = "https://api.openai.com/v1",
        timeout: int = _DEFAULT_TIMEOUT,
    ):
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.vlm_model = vlm_model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.max_retries = max_retries
        self.timeout = timeout

    @classmethod
    def from_settings(cls, settings) -> "LLMService":
        """Create LLMService from a Settings instance."""
        return cls(
            api_key=settings.openai_api_key,
            model=getattr(settings, "openai_model", "gpt-4o"),
            vlm_model=getattr(settings, "openai_vlm_model", "gpt-4o"),
            max_tokens=getattr(settings, "max_tokens", 4096),
            temperature=getattr(settings, "temperature", 0.7),
            base_url=getattr(settings, "openai_base_url", "https://api.openai.com/v1"),
            max_retries=getattr(settings, "max_retries", 3),
            timeout=getattr(settings, "llm_timeout_seconds", _DEFAULT_TIMEOUT),
        )

    def with_model(self, model_id: str, base_url: str = None, vlm_model: str = None, max_tokens: int = None, provider: str = None) -> "LLMService":
        """Return a new LLMService configured for a different model.

        Reuses api_key, retries, temperature, timeout from the current instance.
        If base_url is not provided, the current base_url is used (works for
        providers where model routing is purely by model name, e.g. OpenRouter).
        When provider is specified (or auto-detected from base_url), uses the
        appropriate ProviderAdapter to create the OpenAI client.
        """
        target_url = base_url or self.base_url

        if provider or (base_url and base_url != self.base_url):
            from src.services.provider_adapter import get_adapter, detect_provider
            prov = provider or detect_provider(target_url)
            adapter = get_adapter(prov)
            svc = LLMService.__new__(LLMService)
            svc.client = adapter.create_client(self.api_key, target_url, self.timeout)
            svc.api_key = self.api_key
            svc.base_url = target_url
            svc.model = model_id
            svc.vlm_model = vlm_model or self.vlm_model
            svc.max_tokens = max_tokens or self.max_tokens
            svc.temperature = self.temperature
            svc.max_retries = self.max_retries
            svc.timeout = self.timeout
            return svc

        return LLMService(
            api_key=self.api_key,
            model=model_id,
            vlm_model=vlm_model or self.vlm_model,
            max_tokens=max_tokens or self.max_tokens,
            temperature=self.temperature,
            max_retries=self.max_retries,
            base_url=target_url,
            timeout=self.timeout,
        )

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Generate a response from OpenAI.

        Args:
            prompt: User prompt
            system: Optional system prompt
            max_tokens: Override default max_tokens
            temperature: Override default temperature

        Returns:
            Generated text response

        Raises:
            APIError: If API call fails after retries
        """
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature if temperature is not None else self.temperature

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"LLM API call (attempt {attempt + 1}/{self.max_retries})",
                    extra={
                        "model": self.model,
                        "prompt_length": len(prompt),
                        "max_tokens": max_tokens,
                    },
                )

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

                result = response.choices[0].message.content

                logger.debug(
                    "LLM API call successful",
                    extra={
                        "response_length": len(result),
                        "usage": {
                            "prompt_tokens": response.usage.prompt_tokens,
                            "completion_tokens": response.usage.completion_tokens,
                            "total_tokens": response.usage.total_tokens,
                        },
                    },
                )

                return self._strip_code_fences(result)

            except RateLimitError as e:
                logger.warning(f"Rate limit hit, retrying in {2 ** attempt} seconds")
                if attempt < self.max_retries - 1:
                    time.sleep(2**attempt)  # Exponential backoff
                else:
                    raise

            except APIError as e:
                logger.error(f"API error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                else:
                    raise

        raise APIError("Failed to get response from OpenAI after multiple retries")

    def stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Iterator[str]:
        """
        Stream a response from OpenAI with retry on transient failures.

        Yields:
            Chunks of generated text
        """
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature if temperature is not None else self.temperature

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"LLM streaming API call (attempt {attempt + 1}/{self.max_retries})",
                    extra={
                        "model": self.model,
                        "prompt_length": len(prompt),
                        "max_tokens": max_tokens,
                    },
                )

                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=True,
                )

                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        yield chunk.choices[0].delta.content

                logger.debug("LLM streaming completed")
                return

            except RateLimitError:
                logger.warning(f"Stream rate limit hit, retrying in {2 ** attempt}s")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise

            except APIError as e:
                logger.error(f"Streaming API error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                else:
                    raise

    def generate_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        json_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a JSON response from OpenAI.

        Args:
            prompt: User prompt (should request JSON output)
            system: Optional system prompt
            max_tokens: Override default max_tokens
            json_schema: Optional JSON Schema dict for structured output.
                         When provided, uses OpenAI's response_format with
                         json_schema type for guaranteed schema conformance.

        Returns:
            Parsed JSON response as dictionary or list

        Raises:
            ValueError: If response is not valid JSON
            APIError: If API call fails
        """
        import json

        max_tokens = max_tokens or self.max_tokens

        if json_schema is not None:
            return self._generate_json_with_schema(prompt, system, max_tokens, json_schema)

        if system:
            system = system + "\n\nYou must respond with valid JSON only."
        else:
            system = "You must respond with valid JSON only."

        response = self.generate(
            prompt=prompt,
            system=system,
            max_tokens=max_tokens,
            temperature=0.0,
        )

        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()

            return json.loads(json_str)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}\nResponse: {response}")
            raise ValueError(f"Invalid JSON response from OpenAI: {e}")

    def _generate_json_with_schema(
        self,
        prompt: str,
        system: Optional[str],
        max_tokens: int,
        json_schema: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Use OpenAI's structured output (response_format json_schema) for guaranteed conformance."""
        import json

        messages = []
        sys_content = (system or "") + "\n\nYou must respond with valid JSON only."
        messages.append({"role": "system", "content": sys_content.strip()})
        messages.append({"role": "user", "content": prompt})

        schema_name = json_schema.pop("name", "structured_output")

        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0.0,
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": schema_name,
                            "strict": True,
                            "schema": json_schema,
                        },
                    },
                )
                result = response.choices[0].message.content
                return json.loads(result)
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Structured JSON attempt {attempt + 1} failed: {e}, retrying...")
                    import time
                    time.sleep(2 ** attempt)
                else:
                    logger.warning(f"Structured JSON failed after {self.max_retries} attempts: {e}, falling back to unstructured")
                    return self.generate_json(prompt=prompt, system=system, max_tokens=max_tokens, json_schema=None)

    def analyze_image(
        self,
        image_path: str,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Analyze an image using OpenAI's vision model with retry."""
        import base64
        from pathlib import Path

        max_tokens = max_tokens or self.max_tokens

        if image_path.startswith("http"):
            image_content = {"type": "image_url", "image_url": {"url": image_path}}
        else:
            image_file = Path(image_path)
            with open(image_file, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            image_content = {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
            }

        messages = []
        if system:
            messages.append({"role": "system", "content": system})

        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                image_content,
            ],
        })

        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"VLM API call (attempt {attempt + 1}/{self.max_retries})",
                    extra={"model": self.vlm_model, "image_path": image_path},
                )

                response = self.client.chat.completions.create(
                    model=self.vlm_model,
                    messages=messages,
                    max_tokens=max_tokens,
                )

                result = response.choices[0].message.content
                logger.debug("VLM analysis completed")
                return result

            except RateLimitError:
                logger.warning(f"VLM rate limit hit, retrying in {2 ** attempt}s")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise

            except APIError as e:
                logger.error(f"VLM API error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                else:
                    raise

        raise APIError("Failed to analyze image after multiple retries")

    def create_langchain_llm(self, temperature: float = 0, max_tokens: int = 8000):
        """Create a LangChain ChatOpenAI instance using this service's configuration."""
        from langchain_openai import ChatOpenAI

        base_url = None
        if hasattr(self.client, 'base_url'):
            base_url = str(self.client.base_url)

        return ChatOpenAI(
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=self.client.api_key,
            base_url=base_url,
        )

    def _strip_code_fences(self, text: str) -> str:
        """Strip markdown code fences from response."""
        import re
        lines = text.split('\n')

        # Check if first line is a code fence (```python or ```)
        while lines and re.match(r'^```\w*$', lines[0].strip()):
            lines = lines[1:]

        # Check if last line is a code fence (```)
        while lines and lines[-1].strip() == '```':
            lines = lines[:-1]

        # Also handle case where there's content after the closing fence
        result = '\n'.join(lines)
        # Remove any remaining ``` at the end of the string
        result = re.sub(r'```+$', '', result).strip()

        return result
