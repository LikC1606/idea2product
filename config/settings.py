"""Configuration management for Idea2Product."""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenAI API Configuration
    openai_api_key: str
    openai_model: str = "gpt-4o"
    openai_vlm_model: str = "gpt-4o"
    max_tokens: int = 4096
    temperature: float = 0.7

    # GitHub Configuration (Optional)
    github_token: Optional[str] = None
    github_search_limit: int = 5

    # System Configuration
    log_level: str = "INFO"
    project_root: Path = Path(__file__).parent.parent
    data_dir: Path = Path(__file__).parent.parent / "data"

    # Execution Configuration
    sandbox_timeout: int = 30
    max_fix_attempts: int = 2
    enable_code_mining: bool = True
    enable_visual_verification: bool = True
    enable_bdd_testing: bool = True

    # Derived paths
    @property
    def prompts_dir(self) -> Path:
        """Directory containing agent prompt templates."""
        return self.project_root / "config" / "prompts"

    @property
    def templates_dir(self) -> Path:
        """Directory containing code generation templates."""
        return self.project_root / "templates"

    @property
    def projects_dir(self) -> Path:
        """Directory for generated projects."""
        return self.data_dir / "projects"

    @property
    def code_memory_db_path(self) -> Path:
        """Path to the code memory SQLite database."""
        return self.data_dir / "code_memory.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    settings.ensure_directories()
    return settings
