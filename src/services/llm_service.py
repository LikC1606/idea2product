"""LLM service for interacting with OpenAI API."""

import random
import time
from typing import Optional, Iterator, Dict, Any, List
from openai import (
    OpenAI,
    APIError,
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_TIMEOUT = 120


def _extract_status_code(exc: BaseException) -> Optional[int]:
    """Best-effort HTTP status extraction from OpenAI exceptions."""
    for attr in ("status_code", "status"):
        code = getattr(exc, attr, None)
        if isinstance(code, int):
            return code
    resp = getattr(exc, "response", None)
    code = getattr(resp, "status_code", None)
    return code if isinstance(code, int) else None


def _is_transient_error(exc: BaseException) -> bool:
    """True for timeout/connection/429/5xx style retryable failures."""
    if isinstance(exc, (RateLimitError, APITimeoutError, APIConnectionError, TimeoutError)):
        return True
    if isinstance(exc, APIError):
        status = _extract_status_code(exc)
        return status in (408, 409, 429) or (status is not None and status >= 500)
    return False


def _retry_after_seconds(exc: BaseException) -> Optional[float]:
    """Best-effort Retry-After parsing from response headers."""
    headers = None
    resp = getattr(exc, "response", None)
    headers = getattr(resp, "headers", None) if resp is not None else None
    if not headers:
        return None
    val = headers.get("retry-after") or headers.get("Retry-After")
    if not val:
        return None
    try:
        return max(float(val), 0.0)
    except (TypeError, ValueError):
        return None


def _compute_backoff_seconds(attempt: int, exc: BaseException) -> float:
    """Exponential backoff with jitter and optional Retry-After."""
    hdr = _retry_after_seconds(exc)
    if hdr is not None:
        return min(hdr, 30.0)
    base = min(2**attempt, 30)
    jitter = random.uniform(0.0, 0.35 * base)
    return float(base + jitter)


def _make_llm_service_error(message: str, transient: bool) -> Exception:
    """Import lazily to avoid circular import via src.core.__init__."""
    if transient:
        from src.core.exceptions import TransientLLMError

        return TransientLLMError(message)
    from src.core.exceptions import PermanentLLMError

    return PermanentLLMError(message)


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
        """Create LLMService from a Settings instance (uses primary_llm_provider)."""
        from config.settings import get_primary_llm_config
        api_key, base_url, model, vlm_model = get_primary_llm_config(settings)
        return cls(
            api_key=api_key,
            model=model,
            vlm_model=vlm_model,
            max_tokens=getattr(settings, "max_tokens", 4096),
            temperature=getattr(settings, "temperature", 0.7),
            base_url=base_url,
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
        retry_budget_seconds: Optional[float] = None,
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

        started = time.monotonic()
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

                if not response.choices:
                    raise APIError("Empty choices in OpenAI response")
                result = response.choices[0].message.content
                if result is None:
                    raise APIError("Null content in OpenAI response (e.g. refusal)")

                usage = getattr(response, "usage", None)
                usage_log = {}
                if usage is not None:
                    usage_log = {
                        "prompt_tokens": getattr(usage, "prompt_tokens", None),
                        "completion_tokens": getattr(usage, "completion_tokens", None),
                        "total_tokens": getattr(usage, "total_tokens", None),
                    }
                logger.debug(
                    "LLM API call successful",
                    extra={
                        "response_length": len(result),
                        "usage": usage_log,
                    },
                )

                return self._strip_code_fences(result or "")

            except (RateLimitError, APIError, APITimeoutError, APIConnectionError, TimeoutError) as e:
                transient = _is_transient_error(e)
                last = attempt >= self.max_retries - 1
                if transient and not last:
                    delay = _compute_backoff_seconds(attempt, e)
                    if retry_budget_seconds is not None:
                        elapsed = time.monotonic() - started
                        if elapsed + delay > max(retry_budget_seconds, 0.0):
                            raise _make_llm_service_error(
                                f"LLM retry budget exceeded (budget={retry_budget_seconds}s): {e}",
                                transient=False,
                            ) from e
                    logger.warning("Transient LLM error, retrying in %.2fs: %s", delay, e)
                    time.sleep(delay)
                    continue
                if not transient:
                    logger.error("Non-transient LLM error: %s", e)
                status = _extract_status_code(e)
                raise _make_llm_service_error(
                    f"LLM generate failed (transient={transient}, status={status}): {e}",
                    transient=transient,
                ) from e

        raise _make_llm_service_error(
            "Failed to get response from LLM after multiple retries",
            transient=True,
        )

    def stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        retry_budget_seconds: Optional[float] = None,
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

        emitted_any = False
        started = time.monotonic()
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
                    if chunk.choices and chunk.choices[0].delta.content is not None:
                        emitted_any = True
                        yield chunk.choices[0].delta.content

                logger.debug("LLM streaming completed")
                return

            except (RateLimitError, APIError, APITimeoutError, APIConnectionError, TimeoutError) as e:
                transient = _is_transient_error(e)
                if emitted_any:
                    raise _make_llm_service_error(
                        f"Stream interrupted after partial output: {e}", transient=False
                    ) from e
                if transient and attempt < self.max_retries - 1:
                    delay = _compute_backoff_seconds(attempt, e)
                    if retry_budget_seconds is not None:
                        elapsed = time.monotonic() - started
                        if elapsed + delay > max(retry_budget_seconds, 0.0):
                            raise _make_llm_service_error(
                                f"Stream retry budget exceeded (budget={retry_budget_seconds}s): {e}",
                                transient=False,
                            ) from e
                    logger.warning("Transient stream error, retrying in %.2fs: %s", delay, e)
                    time.sleep(delay)
                    continue
                raise _make_llm_service_error(
                    f"Stream failed (transient={transient}): {e}",
                    transient=transient,
                ) from e

    def stream_messages(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        retry_budget_seconds: Optional[float] = None,
    ) -> Iterator[str]:
        """
        Stream a chat completion from a list of messages (OpenAI format).

        Args:
            messages: List of {"role": "system"|"user"|"assistant", "content": "..."}
            max_tokens: Override default
            temperature: Override default

        Yields:
            Chunks of generated text
        """
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature if temperature is not None else self.temperature

        emitted_any = False
        started = time.monotonic()
        for attempt in range(self.max_retries):
            try:
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=True,
                )
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content is not None:
                        emitted_any = True
                        yield chunk.choices[0].delta.content
                return
            except (RateLimitError, APIError, APITimeoutError, APIConnectionError, TimeoutError) as e:
                transient = _is_transient_error(e)
                if emitted_any:
                    raise _make_llm_service_error(
                        f"Message stream interrupted after partial output: {e}", transient=False
                    ) from e
                if transient and attempt < self.max_retries - 1:
                    delay = _compute_backoff_seconds(attempt, e)
                    if retry_budget_seconds is not None:
                        elapsed = time.monotonic() - started
                        if elapsed + delay > max(retry_budget_seconds, 0.0):
                            raise _make_llm_service_error(
                                f"Message stream retry budget exceeded (budget={retry_budget_seconds}s): {e}",
                                transient=False,
                            ) from e
                    logger.warning("Transient message stream error, retrying in %.2fs: %s", delay, e)
                    time.sleep(delay)
                    continue
                raise _make_llm_service_error(
                    f"Message stream failed (transient={transient}): {e}",
                    transient=transient,
                ) from e

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
                segments = response.split("```json")
                json_str = segments[1].split("```")[0].strip() if len(segments) > 1 else response.strip()
            elif "```" in response:
                segments = response.split("```")
                json_str = segments[1].split("```")[0].strip() if len(segments) > 1 else response.strip()
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

        schema_name = json_schema.get("name", "structured_output")
        schema_for_api = {k: v for k, v in json_schema.items() if k != "name"}

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
                            "schema": schema_for_api,
                        },
                    },
                )
                if not response.choices:
                    raise APIError("Empty choices in OpenAI response")
                result = response.choices[0].message.content
                if result is None:
                    raise APIError("Null content in OpenAI structured output")
                return json.loads(result)
            except Exception as e:
                transient = _is_transient_error(e) if isinstance(
                    e, (RateLimitError, APIError, APITimeoutError, APIConnectionError, TimeoutError)
                ) else False
                if transient and attempt < self.max_retries - 1:
                    delay = _compute_backoff_seconds(attempt, e)
                    logger.warning("Structured JSON transient failure, retrying in %.2fs: %s", delay, e)
                    time.sleep(delay)
                else:
                    logger.warning(
                        "Structured JSON failed after %s attempts: %s, falling back to unstructured",
                        self.max_retries,
                        e,
                    )
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
            if not image_file.exists() or not image_file.is_file():
                raise FileNotFoundError(f"Image file not found: {image_path}")
            try:
                with open(image_file, "rb") as f:
                    image_data = base64.b64encode(f.read()).decode("utf-8")
            except OSError as e:
                raise OSError(f"Failed to read image file {image_path}: {e}") from e
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

                if not response.choices:
                    raise APIError("Empty choices in OpenAI VLM response")
                result = response.choices[0].message.content
                if result is None:
                    raise APIError("Null content in OpenAI VLM response")
                logger.debug("VLM analysis completed")
                return result

            except RateLimitError:
                logger.warning(f"VLM rate limit hit, retrying in {2 ** attempt}s")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise

            except (APIError, APITimeoutError, APIConnectionError, TimeoutError) as e:
                logger.warning(f"VLM API/connection/timeout error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2**attempt)
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
