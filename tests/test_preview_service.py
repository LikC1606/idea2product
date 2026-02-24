"""Tests for preview_service: _detect_entry_point, port allocation, get_preview_url when idle."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.web.services.preview_service import (
    PreviewService,
    _find_free_port,
)
from src.web.services.preview_service import PreviewService as PS  # for _detect_entry_point


@pytest.fixture
def temp_projects_dir():
    d = tempfile.mkdtemp(prefix="preview_test_")
    yield Path(d)


@pytest.fixture
def preview_service(temp_projects_dir):
    settings = MagicMock()
    settings.projects_dir = temp_projects_dir
    return PreviewService(settings)


def test_detect_entry_point_prefers_app_py(temp_projects_dir):
    gen_dir = temp_projects_dir / "proj1" / "generated"
    gen_dir.mkdir(parents=True)
    (gen_dir / "main.py").write_text("x = 1")
    (gen_dir / "app.py").write_text("from flask import Flask")
    entry = PS._detect_entry_point(gen_dir)
    assert entry == "app.py"


def test_detect_entry_point_falls_back_to_main(temp_projects_dir):
    gen_dir = temp_projects_dir / "proj2" / "generated"
    gen_dir.mkdir(parents=True)
    (gen_dir / "main.py").write_text("from flask import Flask")
    entry = PS._detect_entry_point(gen_dir)
    assert entry == "main.py"


def test_detect_entry_point_none_when_empty(temp_projects_dir):
    gen_dir = temp_projects_dir / "proj3" / "generated"
    gen_dir.mkdir(parents=True)
    entry = PS._detect_entry_point(gen_dir)
    assert entry is None


def test_detect_entry_point_glob_flask_file(temp_projects_dir):
    gen_dir = temp_projects_dir / "proj4" / "generated"
    gen_dir.mkdir(parents=True)
    (gen_dir / "server.py").write_text("from flask import Flask\napp = Flask(__name__)\napp.run()")
    entry = PS._detect_entry_point(gen_dir)
    assert entry == "server.py"


def test_find_free_port_returns_valid_port():
    port = _find_free_port(18000, 18100)
    assert 18000 <= port < 18100


def test_get_preview_url_returns_none_when_no_preview(preview_service):
    assert preview_service.get_preview_url("nonexistent") is None


def test_stop_preview_idempotent(preview_service):
    preview_service.stop_preview("nonexistent")
    preview_service.stop_preview("nonexistent")
