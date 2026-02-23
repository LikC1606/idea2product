"""LLM service for interacting with OpenAI API."""

import time
from typing import Optional, Iterator, Dict, Any, List
from openai import OpenAI, APIError, RateLimitError
from src.utils.logger import get_logger

logger = get_logger(__name__)


class LLMService:
    """Service for interacting with OpenAI API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        vlm_model: str = "gpt-4o",
        max_tokens: int = 8000,
        temperature: float = 0.7,
        max_retries: int = 3,
        base_url: str = "https://api.openai.com/v1",
    ):
        """
        Initialize the LLM service.

        Args:
            api_key: OpenAI API key
            model: OpenAI model to use for text generation
            vlm_model: OpenAI model to use for vision tasks
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            max_retries: Maximum number of retry attempts
            base_url: API base URL
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.vlm_model = vlm_model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.max_retries = max_retries

    @classmethod
    def from_settings(cls, settings) -> "LLMService":
        """Create LLMService from a Settings instance (config.settings.Settings or any object with same attributes)."""
        return cls(
            api_key=settings.openai_api_key,
            model=getattr(settings, "openai_model", "gpt-4o"),
            vlm_model=getattr(settings, "openai_vlm_model", "gpt-4o"),
            max_tokens=getattr(settings, "max_tokens", 4096),
            temperature=getattr(settings, "temperature", 0.7),
            base_url=getattr(settings, "openai_base_url", "https://api.openai.com/v1"),
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
        Stream a response from OpenAI.

        Args:
            prompt: User prompt
            system: Optional system prompt
            max_tokens: Override default max_tokens
            temperature: Override default temperature

        Yields:
            Chunks of generated text

        Raises:
            APIError: If API call fails
        """
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature if temperature is not None else self.temperature

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            logger.debug(
                "LLM streaming API call",
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

        except APIError as e:
            logger.error(f"Streaming API error: {e}")
            raise

    def generate_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate a JSON response from OpenAI.

        This method expects the response to be valid JSON.

        Args:
            prompt: User prompt (should request JSON output)
            system: Optional system prompt
            max_tokens: Override default max_tokens

        Returns:
            Parsed JSON response as dictionary

        Raises:
            ValueError: If response is not valid JSON
            APIError: If API call fails
        """
        import json

        # Ensure system prompt requests JSON
        if system:
            system = system + "\n\nYou must respond with valid JSON only."
        else:
            system = "You must respond with valid JSON only."

        response = self.generate(
            prompt=prompt,
            system=system,
            max_tokens=max_tokens,
            temperature=0.0,  # Use temperature 0 for structured output
        )

        try:
            # Try to extract JSON if wrapped in code blocks
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

    def analyze_image(
        self,
        image_path: str,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Analyze an image using OpenAI's vision model (for visual verification).

        Args:
            image_path: Path to image file or image URL
            prompt: Question or instruction about the image
            system: Optional system prompt
            max_tokens: Override default max_tokens

        Returns:
            Analysis result

        Raises:
            APIError: If API call fails
        """
        import base64
        from pathlib import Path

        max_tokens = max_tokens or self.max_tokens

        # Prepare image content
        if image_path.startswith("http"):
            image_content = {"type": "image_url", "image_url": {"url": image_path}}
        else:
            # Read local image file and encode as base64
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

        try:
            logger.debug(
                "VLM API call for image analysis",
                extra={
                    "model": self.vlm_model,
                    "image_path": image_path,
                },
            )

            response = self.client.chat.completions.create(
                model=self.vlm_model,
                messages=messages,
                max_tokens=max_tokens,
            )

            result = response.choices[0].message.content

            logger.debug("VLM analysis completed")
            return result

        except APIError as e:
            logger.error(f"VLM API error: {e}")
            raise

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
