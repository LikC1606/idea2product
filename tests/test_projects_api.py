"""Web API tests for projects, chat, status, files, preview-url.

Uses Flask test client. No real LLM calls; chat reply is mocked where needed.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.web.app import app


@pytest.fixture
def client():
    return app.test_client()


@pytest.fixture
def temp_settings():
    """Provide a Settings-like object with a temp directory for isolation."""
    temp_dir = tempfile.mkdtemp(prefix="idea2product_test_")
    projects_dir = Path(temp_dir) / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    mock = MagicMock()
    mock.projects_dir = projects_dir
    mock.data_dir = Path(temp_dir)
    return mock


@pytest.fixture
def app_with_temp_settings(temp_settings):
    """Patch Settings and clear task service cache so handlers use temp dir."""
    with patch("src.web.api.projects.Settings", return_value=temp_settings):
        # Clear cached task service so next request gets TaskService(temp_settings)
        import src.web.api.projects as projects_module
        if hasattr(projects_module._get_task_service, "_instance"):
            del projects_module._get_task_service._instance
        yield
    # Restore cache clear so other tests don't see stale ref
    if hasattr(projects_module._get_task_service, "_instance"):
        del projects_module._get_task_service._instance


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.get_json()
    assert data.get("status") == "healthy"


def test_create_project_start_chat(client, temp_settings, app_with_temp_settings):
    r = client.post(
        "/api/projects",
        json={"start_chat": True},
        content_type="application/json",
    )
    assert r.status_code == 201
    data = r.get_json()
    assert "project_id" in data
    assert data.get("status") == "idle"
    assert data["project_id"].startswith("proj_")


def test_create_project_requirement_required(client, app_with_temp_settings):
    r = client.post("/api/projects", json={}, content_type="application/json")
    assert r.status_code == 400
    data = r.get_json()
    assert "error" in data


def test_status_after_start_chat(client, temp_settings, app_with_temp_settings):
    r = client.post("/api/projects", json={"start_chat": True}, content_type="application/json")
    assert r.status_code == 201
    project_id = r.get_json()["project_id"]

    r2 = client.get(f"/api/projects/{project_id}/status")
    assert r2.status_code == 200
    data = r2.get_json()
    assert data.get("project_id") == project_id
    assert "status" in data
    assert "progress" in data
    assert "current_stage" in data
    assert "error" in data


def test_files_empty_before_generation(client, temp_settings, app_with_temp_settings):
    r = client.post("/api/projects", json={"start_chat": True}, content_type="application/json")
    assert r.status_code == 201
    project_id = r.get_json()["project_id"]

    r2 = client.get(f"/api/projects/{project_id}/files")
    assert r2.status_code == 200
    data = r2.get_json()
    assert "files" in data
    assert data["files"] == []


def test_chat_get_empty(client, temp_settings, app_with_temp_settings):
    r = client.post("/api/projects", json={"start_chat": True}, content_type="application/json")
    assert r.status_code == 201
    project_id = r.get_json()["project_id"]

    r2 = client.get(f"/api/projects/{project_id}/chat")
    assert r2.status_code == 200
    data = r2.get_json()
    assert "messages" in data
    assert data["messages"] == []


def test_chat_post_returns_reply_and_persists(client, temp_settings, app_with_temp_settings):
    r = client.post("/api/projects", json={"start_chat": True}, content_type="application/json")
    assert r.status_code == 201
    project_id = r.get_json()["project_id"]

    with patch("src.web.api.projects.LLMService") as MockLLM, patch(
        "src.web.api.projects.InteractionAgent"
    ) as MockAgent:
        MockLLM.from_settings.return_value = MagicMock()
        mock_agent = MagicMock()
        mock_agent.reply_in_chat.return_value = "Mocked reply text"
        MockAgent.return_value = mock_agent

        r2 = client.post(
            f"/api/projects/{project_id}/chat",
            json={"message": "I want a todo app"},
            content_type="application/json",
        )
    assert r2.status_code == 200
    data = r2.get_json()
    assert data.get("reply") == "Mocked reply text"
    assert data.get("project_id") == project_id

    # Chat history should persist
    r3 = client.get(f"/api/projects/{project_id}/chat")
    assert r3.status_code == 200
    messages = r3.get_json().get("messages", [])
    assert len(messages) == 2
    assert messages[0]["role"] == "user" and messages[0]["content"] == "I want a todo app"
    assert messages[1]["role"] == "assistant" and messages[1]["content"] == "Mocked reply text"


def test_chat_post_message_required(client, temp_settings, app_with_temp_settings):
    r = client.post("/api/projects", json={"start_chat": True}, content_type="application/json")
    assert r.status_code == 201
    project_id = r.get_json()["project_id"]

    r2 = client.post(
        f"/api/projects/{project_id}/chat",
        json={},
        content_type="application/json",
    )
    assert r2.status_code == 400
    assert "error" in r2.get_json()


def test_preview_url_not_running(client, temp_settings, app_with_temp_settings):
    r = client.post("/api/projects", json={"start_chat": True}, content_type="application/json")
    assert r.status_code == 201
    project_id = r.get_json()["project_id"]

    r2 = client.get(f"/api/projects/{project_id}/preview-url")
    assert r2.status_code == 200
    data = r2.get_json()
    assert data.get("running") is False
    assert data.get("preview_url") is None


def test_list_projects(client, temp_settings, app_with_temp_settings):
    r = client.get("/api/projects")
    assert r.status_code == 200
    data = r.get_json()
    assert "projects" in data
    assert isinstance(data["projects"], list)


def test_get_project_404(client, app_with_temp_settings):
    r = client.get("/api/projects/nonexistent_id_12345")
    assert r.status_code == 404


def test_status_404(client, app_with_temp_settings):
    r = client.get("/api/projects/nonexistent_id_12345/status")
    assert r.status_code == 404
