"""Configuration management for Idea2Product."""

import os
import sys
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import ValidationError
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenAI API Configuration
    openai_api_key: str
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"
    openai_vlm_model: str = "gpt-4o"
    max_tokens: int = 4096
    temperature: float = 0.7

    # GitHub Configuration (Optional)
    github_token: Optional[str] = None
    github_search_limit: int = 5

    # Hugging Face Configuration (for ML algorithm analysis)
    enable_hf_model_search: bool = True  # Default enabled
    hf_search_limit: int = 5
    hf_token: Optional[str] = None
    hf_check_inference: bool = True  # Check Inference API availability

    # System Configuration
    log_level: str = "INFO"
    project_root: Path = Path(__file__).parent.parent
    data_dir: Path = Path(__file__).parent.parent / "data"

    # LLM Reliability Configuration
    max_retries: int = 3
    llm_timeout_seconds: int = 120

    # Execution Configuration
    sandbox_timeout: int = 30
    use_fast_model_for_light_stages: bool = True
    use_unified_task_division: bool = True
    skip_task_review_when_count_low: int = 3
    enable_parallel_task_generation: bool = False
    max_fix_attempts: int = 2
    random_seed: Optional[int] = None  # If set, seeds random/numpy for reproducibility
    enable_code_memory: bool = True  # Plan: skeleton-first + symbol-aware; set False to reduce API/DB usage
    enable_code_mining: bool = True  # Plan: GitHub retrieval + interface adaptation; set False if no GITHUB_TOKEN
    enable_cross_project_memory: bool = False  # When True, search_similar_snippet may fall back to other projects
    enable_llm_code_adaptation: bool = False  # When True, use LLM to adapt mined code to interface (extra API cost)
    enable_visual_verification: bool = True
    enable_bdd_testing: bool = True

    # Validation port (shared by FullCycleTesting, FrontendTesting, VisualVerification, CodeFix)
    validation_port: int = 5555

    # Review: when True, API specs review always runs (SchemePlanningAgent)
    always_review_api_specs: bool = True

    def __init__(self, **kwargs):
        # 临时清除可能存在的环境变量，确保从.env读取；初始化后恢复，避免副作用
        env_backup = {}
        keys_to_temp_clear = ['OPENAI_API_KEY', 'OPENAI_BASE_URL', 'OPENAI_MODEL', 'OPENAI_VLM_MODEL', 'MAX_TOKENS', 'TEMPERATURE']
        for key in keys_to_temp_clear:
            if key in os.environ:
                env_backup[key] = os.environ[key]
                del os.environ[key]
        try:
            super().__init__(**kwargs)
        finally:
            for key, value in env_backup.items():
                os.environ[key] = value

    # Derived paths
    @property
    def models_registry_path(self) -> Path:
        """Path to the model registry JSON file."""
        return self.project_root / "config" / "models_registry.json"

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


def validate_settings(settings: Settings) -> None:
    """
    Validate critical settings. Raises SystemExit with clear message on failure.
    """
    if not (settings.openai_api_key or "").strip():
        print("Error: OPENAI_API_KEY is required. Set it in .env or environment.", file=sys.stderr)
        print("  Example: OPENAI_API_KEY=sk-...", file=sys.stderr)
        sys.exit(1)
    if not settings.prompts_dir.exists():
        print(f"Error: Prompts directory not found: {settings.prompts_dir}", file=sys.stderr)
        sys.exit(1)
    if not settings.templates_dir.exists():
        print(f"Error: Templates directory not found: {settings.templates_dir}", file=sys.stderr)
        sys.exit(1)
    try:
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        test_file = settings.data_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
    except OSError as e:
        print(f"Error: Cannot write to data directory {settings.data_dir}: {e}", file=sys.stderr)
        sys.exit(1)


def get_settings() -> Settings:
    """Get cached settings instance."""
    return _get_settings_cached()


@lru_cache()
def _get_settings_cached() -> Settings:
    """Internal cached settings instance."""
    try:
        settings = Settings()
    except ValidationError as e:
        print("Error: Invalid configuration:", file=sys.stderr)
        for err in e.errors():
            loc = ".".join(str(x) for x in err.get("loc", []))
            msg = err.get("msg", "")
            print(f"  - {loc}: {msg}", file=sys.stderr)
        print("\nCheck .env and environment variables.", file=sys.stderr)
        sys.exit(1)
    settings.ensure_directories()
    validate_settings(settings)
    return settings
