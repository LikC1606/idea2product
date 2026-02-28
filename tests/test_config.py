"""Tests for config/settings and validate_settings."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from config.settings import Settings, validate_settings


@pytest.fixture
def valid_project_root():
    """Create a temp dir with prompts and templates subdirs."""
    root = Path(tempfile.mkdtemp(prefix="idea2product_config_test_"))
    (root / "config" / "prompts").mkdir(parents=True, exist_ok=True)
    (root / "templates").mkdir(parents=True, exist_ok=True)
    (root / "data").mkdir(parents=True, exist_ok=True)
    yield root


def test_validate_settings_empty_api_key(valid_project_root):
    """validate_settings exits when OPENAI_API_KEY is empty."""
    settings = MagicMock()
    settings.openai_api_key = ""
    settings.prompts_dir = valid_project_root / "config" / "prompts"
    settings.templates_dir = valid_project_root / "templates"
    settings.data_dir = valid_project_root / "data"

    with pytest.raises(SystemExit):
        validate_settings(settings)


def test_validate_settings_whitespace_api_key(valid_project_root):
    """validate_settings exits when OPENAI_API_KEY is whitespace-only."""
    settings = MagicMock()
    settings.openai_api_key = "   "
    settings.prompts_dir = valid_project_root / "config" / "prompts"
    settings.templates_dir = valid_project_root / "templates"
    settings.data_dir = valid_project_root / "data"

    with pytest.raises(SystemExit):
        validate_settings(settings)


def test_validate_settings_missing_prompts_dir(valid_project_root):
    """validate_settings exits when prompts_dir does not exist."""
    settings = MagicMock()
    settings.openai_api_key = "sk-test"
    settings.prompts_dir = valid_project_root / "nonexistent_prompts"
    settings.templates_dir = valid_project_root / "templates"
    settings.data_dir = valid_project_root / "data"

    with pytest.raises(SystemExit):
        validate_settings(settings)


def test_validate_settings_missing_templates_dir(valid_project_root):
    """validate_settings exits when templates_dir does not exist."""
    settings = MagicMock()
    settings.openai_api_key = "sk-test"
    settings.prompts_dir = valid_project_root / "config" / "prompts"
    settings.templates_dir = valid_project_root / "nonexistent_templates"
    settings.data_dir = valid_project_root / "data"

    with pytest.raises(SystemExit):
        validate_settings(settings)


def test_validate_settings_non_writable_data_dir(valid_project_root):
    """validate_settings exits when data_dir is not writable."""
    settings = MagicMock()
    settings.openai_api_key = "sk-test"
    settings.prompts_dir = valid_project_root / "config" / "prompts"
    settings.templates_dir = valid_project_root / "templates"
    settings.data_dir = valid_project_root / "data"

    with patch.object(Path, "mkdir") as mock_mkdir:
        with patch.object(Path, "touch", side_effect=OSError("Permission denied")):
            with pytest.raises(SystemExit):
                validate_settings(settings)


def test_validate_settings_success(valid_project_root):
    """validate_settings passes with valid settings."""
    settings = MagicMock()
    settings.openai_api_key = "sk-test"
    settings.prompts_dir = valid_project_root / "config" / "prompts"
    settings.templates_dir = valid_project_root / "templates"
    settings.data_dir = valid_project_root / "data"

    validate_settings(settings)  # should not raise
