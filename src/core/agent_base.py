"""Base class for all agents in the system."""

from abc import ABC, abstractmethod
from typing import Any, Optional
from pathlib import Path

from src.services.llm_service import LLMService
from src.utils.logger import get_logger
from src.utils.prompt_loader import PromptLoader


class AgentBase(ABC):
    """
    Abstract base class for all agents.

    All agents in the system inherit from this class and implement
    the execute() method to perform their specific task.
    """

    def __init__(
        self,
        llm_service: LLMService,
        prompt_loader: PromptLoader,
        agent_name: str,
    ):
        """
        Initialize the agent.

        Args:
            llm_service: LLM service for API calls
            prompt_loader: Prompt template loader
            agent_name: Name of this agent (for prompt loading)
        """
        self.llm_service = llm_service
        self.prompt_loader = prompt_loader
        self.agent_name = agent_name
        self.logger = get_logger(f"agent.{agent_name}")

    @abstractmethod
    def execute(self, input_data: Any) -> Any:
        """
        Execute the agent's task.

        This method must be implemented by all concrete agent classes.

        Args:
            input_data: Input data for the agent (type varies by agent)

        Returns:
            Output data from the agent (type varies by agent)

        Raises:
            Any exception that occurs during execution
        """
        pass

    def load_prompt_template(self) -> str:
        """
        Load the prompt template for this agent.

        Returns:
            Prompt template content

        Raises:
            FileNotFoundError: If template doesn't exist
        """
        try:
            return self.prompt_loader.load(self.agent_name)
        except FileNotFoundError as e:
            self.logger.error(f"Prompt template not found: {e}")
            raise

    def format_prompt(self, **kwargs) -> str:
        """
        Load and format the prompt template with variables.

        Args:
            **kwargs: Variables to substitute in template

        Returns:
            Formatted prompt

        Raises:
            FileNotFoundError: If template doesn't exist
            KeyError: If required variable is missing
        """
        try:
            return self.prompt_loader.format(self.agent_name, **kwargs)
        except FileNotFoundError as e:
            self.logger.error(f"Prompt template not found: {e}")
            raise
        except KeyError as e:
            self.logger.error(f"Missing template variable: {e}")
            raise

    def log_start(self) -> None:
        """Log the start of agent execution."""
        self.logger.info(f"[{self.agent_name}] Starting execution")

    def log_complete(self) -> None:
        """Log the completion of agent execution."""
        self.logger.info(f"[{self.agent_name}] Execution complete")

    def log_error(self, error: Exception) -> None:
        """
        Log an error during execution.

        Args:
            error: The exception that occurred
        """
        self.logger.error(f"[{self.agent_name}] Error: {error}", exc_info=True)

    def call_llm(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Make an LLM API call.

        Args:
            prompt: User prompt
            system: Optional system prompt
            max_tokens: Override default max_tokens
            temperature: Override default temperature

        Returns:
            LLM response
        """
        self.logger.debug(f"Calling LLM with prompt length: {len(prompt)}")
        response = self.llm_service.generate(
            prompt=prompt,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        self.logger.debug(f"LLM response length: {len(response)}")
        return response

    def call_llm_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> dict:
        """
        Make an LLM API call expecting JSON response.

        Args:
            prompt: User prompt
            system: Optional system prompt
            max_tokens: Override default max_tokens

        Returns:
            Parsed JSON response
        """
        self.logger.debug(f"Calling LLM for JSON with prompt length: {len(prompt)}")
        response = self.llm_service.generate_json(
            prompt=prompt,
            system=system,
            max_tokens=max_tokens,
        )
        self.logger.debug(f"LLM JSON response keys: {list(response.keys())}")
        return response
