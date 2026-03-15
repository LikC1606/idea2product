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
    """Patch get_settings and clear task service cache so handlers use temp dir."""
    with patch("src.web.api.projects.get_settings", return_value=temp_settings):
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


def test_create_project_invalid_json(client, app_with_temp_settings):
    """Invalid JSON body returns 400."""
    r = client.post(
        "/api/projects",
        data="{invalid json}",
        content_type="application/json",
    )
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
    r = client.get("/api/projects/proj_nonexistent_12345")
    assert r.status_code == 404


def test_status_404(client, app_with_temp_settings):
    r = client.get("/api/projects/proj_nonexistent_12345/status")
    assert r.status_code == 404


def test_post_chat_llm_exception_returns_fallback(client, temp_settings, app_with_temp_settings):
    """When LLM raises, POST chat returns fallback reply and 200."""
    r = client.post("/api/projects", json={"start_chat": True}, content_type="application/json")
    assert r.status_code == 201
    project_id = r.get_json()["project_id"]

    with patch("src.web.api.projects.LLMService") as MockLLM, patch(
        "src.web.api.projects.InteractionAgent"
    ) as MockAgent:
        MockLLM.from_settings.return_value = MagicMock()
        mock_agent = MagicMock()
        mock_agent.reply_in_chat.side_effect = RuntimeError("LLM API failed")
        MockAgent.return_value = mock_agent

        r2 = client.post(
            f"/api/projects/{project_id}/chat",
            json={"message": "I want a todo app"},
            content_type="application/json",
        )
    assert r2.status_code == 200
    data = r2.get_json()
    assert "reply" in data
    assert "Generate" in data["reply"] or "生成" in data["reply"]


def test_request_entity_too_large(client, app_with_temp_settings):
    """Oversized POST body returns 413."""
    r = client.post(
        "/api/projects",
        data="x" * 70000,
        content_type="application/json",
    )
    assert r.status_code == 413
    data = r.get_json()
    assert "error" in data
    assert "large" in data["error"].lower() or "太大" in data["error"]


def test_get_file_not_found_returns_404(client, temp_settings, app_with_temp_settings):
    """GET file for non-existent path returns 404."""
    r = client.post("/api/projects", json={"start_chat": True}, content_type="application/json")
    assert r.status_code == 201
    project_id = r.get_json()["project_id"]

    r2 = client.get(f"/api/projects/{project_id}/file/nonexistent.py")
    assert r2.status_code == 404
    data = r2.get_json()
    assert "error" in data


def test_chat_stream_invalid_json_returns_400(client, temp_settings, app_with_temp_settings):
    r = client.post("/api/projects", json={"start_chat": True}, content_type="application/json")
    project_id = r.get_json()["project_id"]
    r2 = client.post(
        f"/api/projects/{project_id}/chat/stream",
        data="{invalid json}",
        content_type="application/json",
    )
    assert r2.status_code == 400
    assert "error" in r2.get_json()


def test_chat_idempotent_client_message_id(client, temp_settings, app_with_temp_settings):
    r = client.post("/api/projects", json={"start_chat": True}, content_type="application/json")
    project_id = r.get_json()["project_id"]
    cmid = "cmid-12345"
    with patch("src.web.api.projects.LLMService") as MockLLM, patch(
        "src.web.api.projects.InteractionAgent"
    ) as MockAgent:
        MockLLM.from_settings.return_value = MagicMock()
        mock_agent = MagicMock()
        mock_agent.reply_in_chat_stream.return_value = iter(["stream reply"])
        mock_agent.reply_in_chat.return_value = "fallback reply"
        MockAgent.return_value = mock_agent
        rs = client.post(
            f"/api/projects/{project_id}/chat/stream",
            json={"message": "Hello", "client_message_id": cmid},
            content_type="application/json",
        )
        assert rs.status_code == 200
        r2 = client.post(
            f"/api/projects/{project_id}/chat",
            json={"message": "Hello", "client_message_id": cmid},
            content_type="application/json",
        )
        assert r2.status_code == 200
    chat = client.get(f"/api/projects/{project_id}/chat").get_json()["messages"]
    user_msgs = [m for m in chat if m.get("role") == "user" and m.get("content") == "Hello"]
    assert len(user_msgs) == 1


def test_generate_queued_response_shape(client, temp_settings, app_with_temp_settings):
    r = client.post("/api/projects", json={"start_chat": True}, content_type="application/json")
    project_id = r.get_json()["project_id"]
    with patch("src.web.api.projects.LLMService") as MockLLM, patch(
        "src.web.api.projects.InteractionAgent"
    ) as MockAgent:
        MockLLM.from_settings.return_value = MagicMock()
        mock_agent = MagicMock()
        mock_agent.reply_in_chat.return_value = "ok"
        MockAgent.return_value = mock_agent
        client.post(
            f"/api/projects/{project_id}/chat",
            json={"message": "build app"},
            content_type="application/json",
        )
    import src.web.api.projects as projects_module
    ts = projects_module._get_task_service()
    with patch.object(ts, "enqueue_generation", return_value="started"):
        rg = client.post(
            f"/api/projects/{project_id}/generate",
            json={"product_type": "web", "model_id": "gpt-4o-mini"},
            content_type="application/json",
        )
    assert rg.status_code == 200
    data = rg.get_json()
    assert data["status"] in {"started", "queued_rerun", "deduped_active", "deduped_completed"}
    assert "product_type" in data
    assert "model_id" in data


def test_events_not_found_for_missing_project(client, app_with_temp_settings):
    r = client.get("/api/projects/proj_missing_123/events")
    assert r.status_code == 404
    assert "error" in r.get_json()


def test_plan_and_validation_runs_for_existing_project(client, temp_settings, app_with_temp_settings):
    r = client.post("/api/projects", json={"start_chat": True}, content_type="application/json")
    project_id = r.get_json()["project_id"]
    rp = client.get(f"/api/projects/{project_id}/plan")
    assert rp.status_code == 404
    rv = client.get(f"/api/projects/{project_id}/validation-runs")
    assert rv.status_code == 200
    assert rv.get_json().get("runs") == []


def test_overview_for_existing_project(client, temp_settings, app_with_temp_settings):
    r = client.post("/api/projects", json={"start_chat": True}, content_type="application/json")
    project_id = r.get_json()["project_id"]
    ro = client.get(f"/api/projects/{project_id}/overview")
    assert ro.status_code == 200
    data = ro.get_json()
    assert "project" in data
    assert "timeline" in data


def test_clarification_questions_empty_without_assistant_message(client, temp_settings, app_with_temp_settings):
    r = client.post("/api/projects", json={"start_chat": True}, content_type="application/json")
    project_id = r.get_json()["project_id"]
    rc = client.get(f"/api/projects/{project_id}/clarification-questions")
    assert rc.status_code == 200
    assert rc.get_json().get("questions") == []


def test_reliability_metrics_endpoint(client, app_with_temp_settings):
    r = client.get("/api/projects/metrics")
    assert r.status_code == 200
    data = r.get_json()
    assert "stage_failure_rate" in data
    assert "transient_retry_success_rate" in data
    assert "resume_success_rate" in data
    assert "avg_recovery_seconds" in data


def test_cancel_generation_endpoint(client, temp_settings, app_with_temp_settings):
    r = client.post("/api/projects", json={"start_chat": True}, content_type="application/json")
    project_id = r.get_json()["project_id"]
    rc = client.post(f"/api/projects/{project_id}/cancel", content_type="application/json")
    assert rc.status_code == 200
    assert rc.get_json().get("status") == "cancelling"


def test_generate_backpressure_returns_429(client, temp_settings, app_with_temp_settings):
    r = client.post("/api/projects", json={"start_chat": True}, content_type="application/json")
    project_id = r.get_json()["project_id"]
    with patch("src.web.api.projects.chat_service.get_messages", return_value=[{"role": "user", "content": "build app"}]):
        import src.web.api.projects as projects_module
        ts = projects_module._get_task_service()
        with patch.object(ts, "enqueue_generation", return_value="rejected_backpressure"):
            rg = client.post(
                f"/api/projects/{project_id}/generate",
                json={"product_type": "web", "model_id": "gpt-4o-mini"},
                content_type="application/json",
            )
    assert rg.status_code == 429
    data = rg.get_json()
    assert data["status"] == "rejected_backpressure"
    assert "retry_after_seconds" in data


def test_generate_deduped_active_returns_200(client, temp_settings, app_with_temp_settings):
    r = client.post("/api/projects", json={"start_chat": True}, content_type="application/json")
    project_id = r.get_json()["project_id"]
    with patch("src.web.api.projects.chat_service.get_messages", return_value=[{"role": "user", "content": "build app"}]):
        import src.web.api.projects as projects_module
        ts = projects_module._get_task_service()
        with patch.object(ts, "enqueue_generation", return_value="deduped_active"):
            rg = client.post(
                f"/api/projects/{project_id}/generate",
                json={"product_type": "web", "model_id": "gpt-4o-mini"},
                content_type="application/json",
            )
    assert rg.status_code == 200
    data = rg.get_json()
    assert data["status"] == "deduped_active"


def test_generate_queued_rerun_returns_200(client, temp_settings, app_with_temp_settings):
    r = client.post("/api/projects", json={"start_chat": True}, content_type="application/json")
    project_id = r.get_json()["project_id"]
    with patch("src.web.api.projects.chat_service.get_messages", return_value=[{"role": "user", "content": "build app"}]):
        import src.web.api.projects as projects_module
        ts = projects_module._get_task_service()
        with patch.object(ts, "enqueue_generation", return_value="queued_rerun"):
            rg = client.post(
                f"/api/projects/{project_id}/generate",
                json={"product_type": "web", "model_id": "gpt-4o-mini"},
                content_type="application/json",
            )
    assert rg.status_code == 200
    data = rg.get_json()
    assert data["status"] == "queued_rerun"
