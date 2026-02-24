"""Tests for chat_service: get_messages, append_message with temp directory."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.web.services.chat_service import get_messages, append_message


@pytest.fixture
def temp_projects_dir():
    d = tempfile.mkdtemp(prefix="chat_test_")
    yield Path(d)
    # no cleanup needed for temp dir


@pytest.fixture
def settings_mock(temp_projects_dir):
    m = MagicMock()
    m.projects_dir = temp_projects_dir
    return m


def test_get_messages_empty_when_no_file(settings_mock):
    messages = get_messages(settings_mock, "proj_abc")
    assert messages == []


def test_append_message_creates_file_and_get_messages_returns_content(settings_mock):
    project_id = "proj_xyz"
    append_message(settings_mock, project_id, "user", "Hello")
    messages = get_messages(settings_mock, project_id)
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello"

    append_message(settings_mock, project_id, "assistant", "Hi there")
    messages = get_messages(settings_mock, project_id)
    assert len(messages) == 2
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Hi there"
