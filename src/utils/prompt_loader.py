"""Prompt template loading utilities."""

from pathlib import Path
from typing import Dict, Optional
from .file_utils import read_file


class PromptLoader:
    """Loads and manages agent prompt templates."""

    def __init__(self, prompts_dir: Path):
        """
        Initialize the prompt loader.

        Args:
            prompts_dir: Directory containing prompt template files
        """
        self.prompts_dir = Path(prompts_dir)
        self._cache: Dict[str, str] = {}

    def load(self, agent_name: str) -> str:
        """
        Load a prompt template for an agent.

        Args:
            agent_name: Name of the agent (e.g., "interaction_agent")

        Returns:
            Prompt template content

        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        if agent_name in self._cache:
            return self._cache[agent_name]

        template_path = self.prompts_dir / f"{agent_name}.txt"
        if not template_path.exists():
            raise FileNotFoundError(
                f"Prompt template not found: {template_path}\n"
                f"Please create a template file at {template_path}"
            )

        content = read_file(template_path)
        self._cache[agent_name] = content
        return content

    def format(self, agent_name: str, **kwargs) -> str:
        """
        Load and format a prompt template with variables.

        Args:
            agent_name: Name of the agent
            **kwargs: Variables to substitute in the template

        Returns:
            Formatted prompt

        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        template = self.load(agent_name)
        return template.format(**kwargs)

    def clear_cache(self) -> None:
        """Clear the template cache."""
        self._cache.clear()
