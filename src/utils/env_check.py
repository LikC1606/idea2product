"""Environment and configuration checks for Idea2Product.

Used at startup (optional) and by GET /api/health (optionally with check_llm=1).
Does not block server start; returns structured results for logging or API response.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)


def run_env_checks(
    settings: Any,
    check_llm: bool = False,
) -> Dict[str, Any]:
    """Run environment and config checks.

    Args:
        settings: Application Settings instance (from config.settings).
        check_llm: If True, perform a lightweight LLM endpoint reachability check (one API call).

    Returns:
        Dict with:
          - ok: bool, True if all critical checks passed
          - checks: dict of check_name -> bool or str (e.g. "skip")
          - warnings: list of warning messages
    """
    checks: Dict[str, Any] = {}
    warnings: List[str] = []

    # API key for primary LLM
    try:
        from config.settings import get_primary_llm_config
        api_key, base_url, model, _ = get_primary_llm_config(settings)
        checks["llm_key_set"] = bool(api_key and api_key.strip())
        if not checks["llm_key_set"]:
            provider = getattr(settings, "primary_llm_provider", "openai")
            warnings.append(f"Primary LLM API key not set (primary_llm_provider={provider}). Set in .env.")
    except Exception as e:
        checks["llm_key_set"] = False
        warnings.append(f"Could not resolve LLM config: {e}")

    # Projects directory exists and is writable
    try:
        projects_dir: Path = getattr(settings, "projects_dir", None) or (getattr(settings, "data_dir", Path("data")) / "projects")
        projects_dir.mkdir(parents=True, exist_ok=True)
        test_file = projects_dir / ".env_check_write_test"
        test_file.touch()
        test_file.unlink()
        checks["projects_dir_writable"] = True
    except OSError as e:
        checks["projects_dir_writable"] = False
        warnings.append(f"Projects dir not writable: {e}")

    # Python version (informational)
    try:
        v = sys.version_info
        checks["python_version"] = f"{v.major}.{v.minor}.{v.micro}"
    except Exception:
        checks["python_version"] = "unknown"

    # Optional: LLM endpoint reachability (can be slow / cost-sensitive)
    if check_llm and getattr(settings, "health_check_llm", False):
        checks["llm_reachable"] = _check_llm_reachable(settings)
        if not checks.get("llm_reachable"):
            warnings.append("LLM endpoint unreachable (network or API key). Check base URL and key.")
    elif check_llm:
        checks["llm_reachable"] = "skip"  # health_check_llm disabled

    ok = checks.get("llm_key_set", False) and checks.get("projects_dir_writable", False)
    if check_llm and checks.get("llm_reachable") is False:
        ok = False

    return {"ok": ok, "checks": checks, "warnings": warnings}


def _check_llm_reachable(settings: Any) -> bool:
    """Perform a minimal LLM API call to verify endpoint is reachable. Returns True on success."""
    try:
        from config.settings import get_primary_llm_config
        from src.services.llm_service import LLMService

        api_key, base_url, model, _ = get_primary_llm_config(settings)
        if not api_key:
            return False
        llm = LLMService(api_key=api_key, base_url=base_url, model=model)
        # Minimal completion to avoid cost; many providers accept a single token request
        llm.generate("Hi", max_tokens=1)
        return True
    except Exception as e:
        logger.debug("LLM reachability check failed: %s", e)
        return False


def run_startup_env_check(settings: Any) -> None:
    """Run env checks at startup and log warnings. Does not raise or block."""
    if not getattr(settings, "enable_startup_env_check", True):
        return
    try:
        result = run_env_checks(settings, check_llm=False)
        for w in result.get("warnings", []):
            logger.warning("[env_check] %s", w)
        if not result.get("ok"):
            logger.warning(
                "[env_check] Some checks failed: %s. See TROUBLESHOOTING.md or .env configuration.",
                result.get("checks", {}),
            )
    except Exception as e:
        logger.debug("Startup env check failed: %s", e)
