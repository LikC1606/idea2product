"""Tests for TaskService: create_chat_project, enqueue_generation with mocked pipeline."""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.web.services.chat_service import append_message
from src.web.services.task_service import TaskService


@pytest.fixture
def temp_settings():
    temp_dir = tempfile.mkdtemp(prefix="task_svc_test_")
    projects_dir = Path(temp_dir) / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    mock = MagicMock()
    mock.projects_dir = projects_dir
    mock.data_dir = Path(temp_dir)
    return mock


@pytest.fixture
def task_service(temp_settings):
    return TaskService(temp_settings)


def test_create_chat_project_returns_id_and_creates_dirs(task_service, temp_settings):
    project_id = task_service.create_chat_project()
    assert project_id.startswith("proj_")
    assert len(project_id.split("_")) >= 3

    project_dir = temp_settings.projects_dir / project_id
    assert project_dir.exists()
    assert (project_dir / "artifacts").exists()
    assert (project_dir / "generated").exists()
    assert (project_dir / "logs").exists()

    status = task_service.get_status(project_id)
    assert status is not None
    assert status["project_id"] == project_id
    assert status["status"] == "idle"


def test_enqueue_generation_runs_and_completes_with_mocked_pipeline(
    task_service, temp_settings
):
    project_id = task_service.create_chat_project()
    append_message(temp_settings, project_id, "user", "Build a todo app")
    append_message(temp_settings, project_id, "assistant", "OK, generating.")

    mock_result = MagicMock()
    mock_result.repository = MagicMock()
    mock_result.repository.files = []
    mock_result.test_results = None

    def fake_thread(*args, **kwargs):
        target = kwargs.get("target") or (args[0] if args else None)
        targs = kwargs.get("args", ())
        mock_t = MagicMock()
        def start():
            if target:
                target(*targs)
        mock_t.start.side_effect = start
        return mock_t

    with patch(
        "src.core.orchestrator.Orchestrator"
    ) as MockOrch:
        MockOrch.return_value.run_from_stage_2.return_value = mock_result
        with patch(
            "src.web.services.chat_service.get_messages",
            return_value=[
                {"role": "user", "content": "Build a todo app"},
                {"role": "assistant", "content": "OK"},
            ],
        ):
            with patch(
                "src.services.llm_service.LLMService"
            ) as MockLLM:
                with patch(
                    "src.agents.stage1_requirements.interaction_agent.InteractionAgent"
                ) as MockAgent:
                    mock_agent = MagicMock()
                    from src.core.data_models import Requirements
                    mock_agent.conversation_to_requirements.return_value = Requirements(
                        title="Todo",
                        description="Todo app",
                        features=[],
                        constraints=[],
                        target_users=None,
                        data_requirements=None,
                    )
                    MockAgent.return_value = mock_agent
                    MockLLM.from_settings.return_value = MagicMock()

                    with patch.object(
                        task_service, "_try_start_preview"
                    ):
                        with patch(
                            "src.web.services.task_service.threading.Thread",
                            side_effect=fake_thread,
                        ):
                            task_service.enqueue_generation(project_id)

    status = task_service.get_status(project_id)
    assert status["status"] == "completed"
    assert status["progress"] == 100
    MockOrch.return_value.run_from_stage_2.assert_called_once()
    call_args = MockOrch.return_value.run_from_stage_2.call_args
    assert call_args[0][0] == project_id
    assert call_args[0][1].title == "Todo"


def test_enqueue_generation_does_nothing_when_no_messages(task_service, temp_settings):
    project_id = task_service.create_chat_project()
    # No chat messages

    with patch(
        "src.core.orchestrator.Orchestrator"
    ) as MockOrch:
        with patch(
            "src.web.services.chat_service.get_messages",
            return_value=[],
        ):
            def fake_thread(*a, **k):
                target = k.get("target") or (a[0] if a else None)
                targs = k.get("args", ())
                mock_t = MagicMock()
                def start():
                    if target:
                        target(*targs)
                mock_t.start.side_effect = start
                return mock_t

            with patch(
                "src.web.services.task_service.threading.Thread",
                side_effect=fake_thread,
            ):
                task_service.enqueue_generation(project_id)

    MockOrch.return_value.run_from_stage_2.assert_not_called()
    status = task_service.get_status(project_id)
    assert status["status"] == "idle"


def test_enqueue_generation_exception_calls_fail(task_service, temp_settings):
    """When pipeline raises, _fail is called and status becomes 'failed'."""
    project_id = task_service.create_chat_project()
    append_message(temp_settings, project_id, "user", "Build a todo app")
    append_message(temp_settings, project_id, "assistant", "OK, generating.")

    def fake_thread(*args, **kwargs):
        target = kwargs.get("target") or (args[0] if args else None)
        targs = kwargs.get("args", ())
        mock_t = MagicMock()
        def start():
            if target:
                target(*targs)
        mock_t.start.side_effect = start
        return mock_t

    with patch("src.web.services.task_service.threading.Thread", side_effect=fake_thread):
        with patch(
            "src.web.services.chat_service.get_messages",
            return_value=[
                {"role": "user", "content": "Build a todo app"},
                {"role": "assistant", "content": "OK"},
            ],
        ):
            with patch("src.services.llm_service.LLMService") as MockLLM:
                MockLLM.from_settings.return_value = MagicMock()
                with patch(
                    "src.core.orchestrator.Orchestrator"
                ) as MockOrch:
                    MockOrch.return_value.run_from_stage_2.side_effect = RuntimeError("Pipeline failed")
                    with patch(
                        "src.agents.stage1_requirements.interaction_agent.InteractionAgent"
                    ) as MockAgent:
                        from src.core.data_models import Requirements
                        mock_agent = MagicMock()
                        mock_agent.conversation_to_requirements.return_value = Requirements(
                            title="Todo", description="Todo app", features=[],
                            constraints=[], target_users=None, data_requirements=None,
                        )
                        MockAgent.return_value = mock_agent
                    task_service.enqueue_generation(project_id)

    status = task_service.get_status(project_id)
    assert status["status"] == "failed"
    assert status.get("error") == "Pipeline failed"


def test_get_file_nonexistent_returns_none(task_service, temp_settings):
    """get_file for non-existent path returns None."""
    project_id = task_service.create_chat_project()
    result = task_service.get_file(project_id, "nonexistent.py")
    assert result is None


def test_get_file_unicode_error_returns_none_or_content(task_service, temp_settings):
    """get_file for file with encoding issues uses errors=replace or returns None."""
    project_id = task_service.create_chat_project()
    gen_dir = temp_settings.projects_dir / project_id / "generated"
    gen_dir.mkdir(parents=True, exist_ok=True)
    # Create file with invalid UTF-8 (latin-1 bytes that aren't valid utf-8)
    bad_file = gen_dir / "bad.py"
    bad_file.write_bytes(b"x = '\xff\xfe'")
    result = task_service.get_file(project_id, "bad.py")
    assert result is not None
    assert "path" in result
    assert "content" in result
