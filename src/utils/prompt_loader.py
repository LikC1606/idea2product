"""Prompt template loading utilities."""

from pathlib import Path
from string import Template
from typing import Dict, Optional
from .file_utils import read_file


class PromptLoader:
    """Loads and manages agent prompt templates.

    Templates use ``$variable`` syntax (via string.Template) so that JSON
    braces ``{...}`` in the prompt body don't need escaping.
    """

    def __init__(self, prompts_dir: Path):
        self.prompts_dir = Path(prompts_dir)
        self._cache: Dict[str, str] = {}

    def load(self, template_name: str) -> str:
        """Load a raw prompt template by name (without extension)."""
        if template_name in self._cache:
            return self._cache[template_name]

        template_path = self.prompts_dir / f"{template_name}.txt"
        if not template_path.exists():
            raise FileNotFoundError(
                f"Prompt template not found: {template_path}\n"
                f"Please create a template file at {template_path}"
            )

        content = read_file(template_path)
        self._cache[template_name] = content
        return content

    def format(self, template_name: str, **kwargs) -> str:
        """Load and substitute ``$variable`` placeholders using string.Template.

        This is safe for templates that contain JSON ``{...}`` because
        string.Template only interprets ``$var`` / ``${var}`` syntax.
        """
        raw = self.load(template_name)
        return Template(raw).safe_substitute(**kwargs)

    def clear_cache(self) -> None:
        """Clear the template cache."""
        self._cache.clear()
