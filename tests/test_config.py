"""Tests for config/settings and validate_settings."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from config.settings import (
    Settings,
    validate_settings,
    get_primary_llm_config,
    _primary_llm_key_name,
)


def _mock_settings(valid_project_root, **kwargs):
    """Build a minimal mock for validate_settings (dirs + optional keys)."""
    s = MagicMock()
    s.prompts_dir = valid_project_root / "config" / "prompts"
    s.templates_dir = valid_project_root / "templates"
    s.data_dir = valid_project_root / "data"
    s.openai_api_key = kwargs.get("openai_api_key", None)
    s.anthropic_api_key = kwargs.get("anthropic_api_key", None)
    s.google_api_key = kwargs.get("google_api_key", None)
    s.primary_llm_provider = kwargs.get("primary_llm_provider", "openai")
    return s


@pytest.fixture
def valid_project_root():
    """Create a temp dir with prompts and templates subdirs."""
    root = Path(tempfile.mkdtemp(prefix="idea2product_config_test_"))
    (root / "config" / "prompts").mkdir(parents=True, exist_ok=True)
    (root / "templates").mkdir(parents=True, exist_ok=True)
    (root / "data").mkdir(parents=True, exist_ok=True)
    yield root


def test_validate_settings_empty_api_key(valid_project_root):
    """validate_settings exits when primary (openai) API key is empty."""
    settings = _mock_settings(
        valid_project_root,
        primary_llm_provider="openai",
        openai_api_key="",
    )

    with pytest.raises(SystemExit):
        validate_settings(settings)


def test_validate_settings_whitespace_api_key(valid_project_root):
    """validate_settings exits when primary (openai) API key is whitespace-only."""
    settings = _mock_settings(
        valid_project_root,
        primary_llm_provider="openai",
        openai_api_key="   ",
    )

    with pytest.raises(SystemExit):
        validate_settings(settings)


def test_validate_settings_missing_prompts_dir(valid_project_root):
    """validate_settings exits when prompts_dir does not exist."""
    settings = _mock_settings(
        valid_project_root,
        primary_llm_provider="openai",
        openai_api_key="sk-test",
    )
    settings.prompts_dir = valid_project_root / "nonexistent_prompts"

    with pytest.raises(SystemExit):
        validate_settings(settings)


def test_validate_settings_missing_templates_dir(valid_project_root):
    """validate_settings exits when templates_dir does not exist."""
    settings = _mock_settings(
        valid_project_root,
        primary_llm_provider="openai",
        openai_api_key="sk-test",
    )
    settings.templates_dir = valid_project_root / "nonexistent_templates"

    with pytest.raises(SystemExit):
        validate_settings(settings)


def test_validate_settings_non_writable_data_dir(valid_project_root):
    """validate_settings exits when data_dir is not writable."""
    settings = _mock_settings(
        valid_project_root,
        primary_llm_provider="openai",
        openai_api_key="sk-test",
    )

    with patch.object(Path, "mkdir") as mock_mkdir:
        with patch.object(Path, "touch", side_effect=OSError("Permission denied")):
            with pytest.raises(SystemExit):
                validate_settings(settings)


def test_validate_settings_success(valid_project_root):
    """validate_settings passes with valid settings (primary=openai)."""
    settings = _mock_settings(
        valid_project_root,
        primary_llm_provider="openai",
        openai_api_key="sk-test",
    )

    validate_settings(settings)  # should not raise


def test_validate_settings_primary_anthropic_with_key(valid_project_root):
    """validate_settings passes when primary=anthropic and anthropic_api_key is set."""
    settings = _mock_settings(
        valid_project_root,
        primary_llm_provider="anthropic",
        anthropic_api_key="sk-ant-test",
    )

    validate_settings(settings)  # should not raise


def test_validate_settings_primary_anthropic_missing_key(valid_project_root):
    """validate_settings exits when primary=anthropic and anthropic_api_key is empty."""
    settings = _mock_settings(
        valid_project_root,
        primary_llm_provider="anthropic",
        anthropic_api_key="",
    )

    with pytest.raises(SystemExit):
        validate_settings(settings)


def test_validate_settings_primary_google_with_key(valid_project_root):
    """validate_settings passes when primary=google and google_api_key is set."""
    settings = _mock_settings(
        valid_project_root,
        primary_llm_provider="google",
        google_api_key="test-google-key",
    )

    validate_settings(settings)  # should not raise


def test_validate_settings_primary_google_missing_key(valid_project_root):
    """validate_settings exits when primary=google and google_api_key is empty."""
    settings = _mock_settings(
        valid_project_root,
        primary_llm_provider="google",
        google_api_key="",
    )

    with pytest.raises(SystemExit):
        validate_settings(settings)


def test_validate_settings_require_llm_key_false(valid_project_root):
    """validate_settings(require_llm_key=False) does not exit when primary key is missing."""
    settings = _mock_settings(
        valid_project_root,
        primary_llm_provider="openai",
        openai_api_key="",
    )

    validate_settings(settings, require_llm_key=False)  # should not raise


def test_get_primary_llm_config_openai(valid_project_root):
    """get_primary_llm_config returns openai key and defaults when primary=openai."""
    settings = _mock_settings(
        valid_project_root,
        primary_llm_provider="openai",
        openai_api_key="sk-abc",
    )
    key, base, model, vlm = get_primary_llm_config(settings)
    assert key == "sk-abc"
    assert base  # base_url string
    assert model
    assert vlm


def test_get_primary_llm_config_anthropic(valid_project_root):
    """get_primary_llm_config returns anthropic key when primary=anthropic."""
    settings = _mock_settings(
        valid_project_root,
        primary_llm_provider="anthropic",
        anthropic_api_key="sk-ant-xyz",
    )
    key, base, model, vlm = get_primary_llm_config(settings)
    assert key == "sk-ant-xyz"
    assert base
    assert model


def test_primary_llm_key_name():
    """_primary_llm_key_name returns correct env var names."""
    for provider, var in [("openai", "OPENAI_API_KEY"), ("anthropic", "ANTHROPIC_API_KEY"), ("google", "GOOGLE_API_KEY")]:
        s = MagicMock()
        s.primary_llm_provider = provider
        assert _primary_llm_key_name(s) == var
