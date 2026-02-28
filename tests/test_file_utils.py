"""Tests for file_utils including read_file_safe and error handling."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.core.exceptions import ArtifactIOError
from src.utils.file_utils import (
    ensure_dir,
    read_file,
    read_file_safe,
    read_json_safe,
    write_file,
)


def test_read_file_safe_missing_file():
    """read_file_safe returns default when file does not exist."""
    result = read_file_safe(Path("/nonexistent/path/file.txt"))
    assert result is None

    result = read_file_safe(Path("/nonexistent/path/file.txt"), default="fallback")
    assert result == "fallback"


def test_read_file_safe_existing_file(tmp_path):
    """read_file_safe returns content when file exists."""
    f = tmp_path / "test.txt"
    f.write_text("hello world", encoding="utf-8")
    assert read_file_safe(f) == "hello world"


def test_read_file_safe_encoding_errors(tmp_path):
    """read_file_safe uses errors=replace for bad encoding."""
    f = tmp_path / "bad.txt"
    f.write_bytes(b"\xff\xfe")
    result = read_file_safe(f, default="failed")
    assert result is not None
    assert result != "failed"


def test_read_file_raises_on_missing():
    """read_file raises FileNotFoundError when file does not exist."""
    with pytest.raises(FileNotFoundError):
        read_file(Path("/nonexistent/file.txt"))


def test_read_file_raises_artifact_io_on_permission(tmp_path):
    """read_file raises ArtifactIOError on permission error."""
    f = tmp_path / "test.txt"
    f.write_text("content")
    with patch.object(Path, "read_text", side_effect=PermissionError("denied")):
        with pytest.raises(ArtifactIOError):
            read_file(f)


def test_write_file_raises_artifact_io_on_permission(tmp_path):
    """write_file raises ArtifactIOError on permission error."""
    f = tmp_path / "test.txt"
    with patch.object(Path, "write_text", side_effect=PermissionError("denied")):
        with pytest.raises(ArtifactIOError):
            write_file(f, "content")


def test_ensure_dir_raises_artifact_io_on_permission():
    """ensure_dir raises ArtifactIOError on permission error."""
    with patch.object(Path, "mkdir", side_effect=PermissionError("denied")):
        with pytest.raises(ArtifactIOError):
            ensure_dir(Path("/nonexistent/foo"))


def test_read_json_safe_missing():
    """read_json_safe returns default when file missing."""
    assert read_json_safe(Path("/nonexistent/file.json")) is None
    assert read_json_safe(Path("/nonexistent/file.json"), default={}) == {}
