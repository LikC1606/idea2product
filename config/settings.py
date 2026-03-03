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
    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"
    openai_vlm_model: str = "gpt-4o"
    max_tokens: int = 4096
    temperature: float = 0.7

    # Primary LLM provider: openai | anthropic | google (at least one key for primary required)
    primary_llm_provider: str = "openai"

    # Anthropic (Claude) – OpenAI-compatible endpoint e.g. OpenRouter; set ANTHROPIC_API_KEY
    anthropic_api_key: Optional[str] = None
    anthropic_base_url: str = "https://openrouter.ai/api/v1"
    anthropic_model: str = "anthropic/claude-3-5-sonnet-20241022"

    # Google (Gemini) – OpenAI-compatible endpoint e.g. OpenRouter; set GOOGLE_API_KEY
    google_api_key: Optional[str] = None
    google_base_url: Optional[str] = None  # default OpenRouter below in get_primary_llm_config
    google_model: str = "google/gemini-1.5-pro"

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
    # When True, 500 API responses may include error details; when False, return generic message only
    expose_error_details: bool = False
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
    force_task_review_when_count_high: int = 10
    force_task_review_dep_depth: int = 2
    skip_flow_extraction: bool = False
    use_fast_model_for_task_review: bool = True
    fast_model_for_review: str = "gpt-4o-mini"
    enable_parallel_task_generation: bool = False
    max_fix_attempts: int = 2
    random_seed: Optional[int] = None  # If set, seeds random/numpy for reproducibility
    enable_code_memory: bool = True  # Plan: skeleton-first + symbol-aware; set False to reduce API/DB usage
    enable_code_mining: bool = True  # Plan: GitHub retrieval + interface adaptation; set False if no GITHUB_TOKEN

    # Code Memory Agent
    code_memory_prefetch_max_queries: int = 3
    code_memory_context_max_chars: int = 2500

    # Code Mining Agent
    code_mining_parallel_workers: int = 3
    code_mining_max_context_chars: int = 800
    code_mining_deduplicate_queries: bool = True

    # Stage 3 prefetch: when True, run CodeMemoryAgent.pre_execute and CodeMiningAgent.execute in parallel
    enable_parallel_stage3_prefetch: bool = True

    # Code Generation (Stage 3)
    use_fast_model_for_simple_code_tasks: bool = True
    fast_model_for_code_gen: str = "gpt-4o-mini"
    skip_mining_for_simple_tasks: bool = False
    max_system_prompt_chars: int = 16000
    use_fast_model_for_syntax_fix: bool = True
    code_gen_syntax_fix_retries: int = 1
    # Stage 3 correctness checks (syntax/import sanity)
    enable_stage3_syntax_check: bool = True
    enable_stage3_import_sanity_check: bool = False
    enable_cross_project_memory: bool = False  # When True, search_similar_snippet may fall back to other projects
    enable_llm_code_adaptation: bool = False  # When True, use LLM to adapt mined code to interface (extra API cost)
    enable_visual_verification: bool = True
    enable_bdd_testing: bool = True
    # When True, report unused backend files (under app/) as warnings in FullCycleTesting
    warn_unused_files: bool = True
    # Timeout in seconds for BDD pytest run in FullCycleTesting
    bdd_test_timeout_seconds: int = 60

    # FineTuning Agent: max chars for LLM context in _fix_test_error / _fix_visual_issues
    fine_tuning_max_context_chars: int = 12000
    # When True, _fix_syntax_error uses fast model (e.g. fast_model_for_code_gen)
    use_fast_model_for_fine_tuning_syntax: bool = True

    # Validation port (shared by FullCycleTesting, FrontendTesting, VisualVerification, CodeFix)
    validation_port: int = 5555

    # Image generation (optional: hero images, placeholders for frontend)
    enable_image_generation: bool = False
    image_generation_provider: str = "openai"  # openai | generic_http
    image_generation_openai_model: str = "dall-e-3"
    image_generation_base_url: Optional[str] = None  # for generic_http or override for openai
    image_generation_api_key: Optional[str] = None  # for generic_http; openai reuses openai_api_key
    image_generation_extra_headers: Optional[str] = None  # JSON string for generic_http
    image_generation_prompt_key: str = "prompt"
    image_generation_response_image_path: Optional[str] = None  # e.g. "data[0].url"
    image_generation_timeout: int = 120

    # Video generation (optional: tutorials, demos)
    enable_video_generation: bool = False
    video_generation_provider: str = "generic_http"  # generic_http | custom
    video_generation_base_url: Optional[str] = None
    video_generation_api_key: Optional[str] = None
    video_generation_extra_headers: Optional[str] = None  # JSON string for generic_http
    video_generation_timeout: int = 300

    # PPT generation (optional: slide decks)
    enable_ppt_generation: bool = False
    ppt_generation_provider: str = "generic_http"
    ppt_generation_base_url: Optional[str] = None
    ppt_generation_api_key: Optional[str] = None
    ppt_generation_extra_headers: Optional[str] = None
    ppt_generation_timeout: int = 300

    # LaTeX/PDF generation (optional: exportable documents)
    enable_latex_generation: bool = False
    latex_generation_provider: str = "generic_http"
    latex_generation_base_url: Optional[str] = None
    latex_generation_api_key: Optional[str] = None
    latex_generation_extra_headers: Optional[str] = None
    latex_generation_timeout: int = 300

    # Audio generation (optional: TTS / music)
    enable_audio_generation: bool = False
    audio_generation_provider: str = "generic_http"
    audio_generation_base_url: Optional[str] = None
    audio_generation_api_key: Optional[str] = None
    audio_generation_extra_headers: Optional[str] = None
    audio_generation_timeout: int = 120

    # Review: when True, API specs review always runs (SchemePlanningAgent)
    always_review_api_specs: bool = True
    # When > 0, skip API review when endpoint count <= N and no auth
    skip_api_review_when_simple: int = 0
    use_fast_model_for_api_review: bool = True
    skip_flow_in_scheme_planning: bool = False

    # Algorithm Analysis: 0=always run HF; >0 skip HF when task count <= N and no ML tasks
    skip_hf_for_simple_tasks: int = 0
    # When True, do not inject flow_simulation into algorithm_analysis prompt
    skip_flow_in_algorithm: bool = False
    # When True, HfModelService caches search_and_fetch_docs results (LRU)
    enable_hf_cache: bool = False

    # Stage 2 web search (for ModelIntegrationPlanningAgent: discover external APIs/models)
    enable_stage2_web_search: bool = False
    web_search_provider: str = "serper"  # serper | (bing/tavily later)
    web_search_api_key: Optional[str] = None  # Serper: SERPER_API_KEY or web_search_api_key
    web_search_num_results: int = 5
    web_search_timeout: int = 15
    # When True, use LLM to help infer external capabilities (video_generation, ppt_generation, etc.) in Stage 2
    enable_stage2_llm_capability_infer: bool = False

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


def get_primary_llm_config(settings: Settings) -> tuple:
    """
    Return (api_key, base_url, model) for the primary LLM provider.
    Used by LLMService.from_settings to build the client.
    """
    provider = (getattr(settings, "primary_llm_provider", None) or "openai").strip().lower()
    if provider == "openai":
        key = (settings.openai_api_key or "").strip()
        base = getattr(settings, "openai_base_url", "https://api.openai.com/v1") or "https://api.openai.com/v1"
        model = getattr(settings, "openai_model", "gpt-4o") or "gpt-4o"
        vlm = getattr(settings, "openai_vlm_model", None) or model
        return (key, base, model, vlm)
    if provider == "anthropic":
        key = (getattr(settings, "anthropic_api_key", None) or "").strip()
        base = getattr(settings, "anthropic_base_url", "https://openrouter.ai/api/v1") or "https://openrouter.ai/api/v1"
        model = getattr(settings, "anthropic_model", "anthropic/claude-3-5-sonnet-20241022") or "anthropic/claude-3-5-sonnet-20241022"
        return (key, base, model, model)
    if provider == "google":
        key = (getattr(settings, "google_api_key", None) or "").strip()
        base = getattr(settings, "google_base_url", None) or "https://openrouter.ai/api/v1"
        model = getattr(settings, "google_model", "google/gemini-1.5-pro") or "google/gemini-1.5-pro"
        return (key, base, model, model)
    # fallback to openai
    key = (settings.openai_api_key or "").strip()
    base = getattr(settings, "openai_base_url", "https://api.openai.com/v1") or "https://api.openai.com/v1"
    model = getattr(settings, "openai_model", "gpt-4o") or "gpt-4o"
    vlm = getattr(settings, "openai_vlm_model", None) or model
    return (key, base, model, vlm)


def _primary_llm_key_name(settings: Settings) -> str:
    """Return env var name for the primary provider's API key (for error messages)."""
    provider = (getattr(settings, "primary_llm_provider", None) or "openai").strip().lower()
    return {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "google": "GOOGLE_API_KEY"}.get(
        provider, "OPENAI_API_KEY"
    )


def validate_settings(settings: Settings, require_llm_key: bool = True) -> None:
    """
    Validate critical settings. Raises SystemExit with clear message on failure.
    When require_llm_key is False, skips the primary API key check (for interactive key prompt flow).
    """
    if require_llm_key:
        api_key, _, _, _ = get_primary_llm_config(settings)
        if not api_key:
            var_name = _primary_llm_key_name(settings)
            primary = getattr(settings, "primary_llm_provider", "openai")
            print(f"Error: {var_name} is required (primary_llm_provider={primary}). Set it in .env or environment.", file=sys.stderr)
            print(f"  Example: {var_name}=sk-...", file=sys.stderr)
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
    """Get cached settings instance (full validation including primary LLM key)."""
    return _get_settings_cached()


def load_settings_lenient() -> Settings:
    """
    Load settings and validate directories/paths only; do not require primary LLM key.
    Use for interactive flow when we may prompt for API key before continuing.
    """
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
    validate_settings(settings, require_llm_key=False)
    return settings


def clear_settings_cache() -> None:
    """Clear the cached settings so next get_settings() reloads from env (e.g. after setting API key)."""
    _get_settings_cached.cache_clear()


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
