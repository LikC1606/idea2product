"""Reliability tests for TaskService fingerprint dedupe and metrics."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.web.services.chat_service import append_message
from src.web.services.task_service import TaskService


def _fake_thread_factory():
    def fake_thread(*args, **kwargs):
        target = kwargs.get("target") or (args[0] if args else None)
        targs = kwargs.get("args", ())
        mock_t = MagicMock()

        def start():
            if target:
                target(*targs)

        mock_t.start.side_effect = start
        return mock_t

    return fake_thread


def _make_settings():
    root = Path(tempfile.mkdtemp(prefix="task_svc_rel_test_"))
    projects_dir = root / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    settings = MagicMock()
    settings.projects_dir = projects_dir
    settings.data_dir = root
    settings.task_generation_retry_on_transient = True
    return settings


def test_skip_duplicate_when_same_fingerprint_already_completed():
    settings = _make_settings()
    svc = TaskService(settings)
    pid = svc.create_chat_project()
    append_message(settings, pid, "user", "build todo app")
    append_message(settings, pid, "assistant", "ok")

    with patch("src.web.services.task_service.threading.Thread", side_effect=_fake_thread_factory()):
        with patch("src.web.services.chat_service.get_messages", return_value=[{"role": "user", "content": "build todo app"}]):
            with patch("src.services.llm_service.LLMService") as MockLLM, patch(
                "src.agents.stage1_requirements.interaction_agent.InteractionAgent"
            ) as MockAgent, patch("src.core.orchestrator.Orchestrator") as MockOrch:
                from src.core.data_models import Requirements

                MockLLM.from_settings.return_value = MagicMock()
                mock_agent = MagicMock()
                mock_agent.conversation_to_requirements.return_value = Requirements(
                    title="Todo", description="Todo app", features=[], constraints=[]
                )
                MockAgent.return_value = mock_agent
                mock_result = MagicMock()
                mock_result.repository = MagicMock()
                mock_result.repository.files = []
                mock_result.test_results = None
                MockOrch.return_value.run_from_stage_2.return_value = mock_result

                with patch.object(svc, "_try_start_preview"):
                    svc.enqueue_generation(pid)
                assert MockOrch.return_value.run_from_stage_2.call_count == 1

                # Same input -> deduped at enqueue time
                with patch.object(svc, "_try_start_preview"):
                    svc.enqueue_generation(pid)
                assert MockOrch.return_value.run_from_stage_2.call_count == 1


def test_reliability_metrics_transient_retry_success():
    settings = _make_settings()
    svc = TaskService(settings)
    pid = svc.create_chat_project()
    append_message(settings, pid, "user", "build todo app")
    append_message(settings, pid, "assistant", "ok")

    with patch("src.web.services.task_service.threading.Thread", side_effect=_fake_thread_factory()):
        with patch(
            "src.web.services.chat_service.get_messages",
            return_value=[{"role": "user", "content": "build todo app"}],
        ):
            with patch("src.services.llm_service.LLMService") as MockLLM, patch(
                "src.agents.stage1_requirements.interaction_agent.InteractionAgent"
            ) as MockAgent, patch("src.core.orchestrator.Orchestrator") as MockOrch:
                from src.core.data_models import Requirements
                from src.core.exceptions import TransientLLMError, PermanentLLMError

                MockLLM.from_settings.return_value = MagicMock()
                mock_agent = MagicMock()
                mock_agent.conversation_to_requirements.return_value = Requirements(
                    title="Todo", description="Todo app", features=[], constraints=[]
                )
                MockAgent.return_value = mock_agent
                mock_result = MagicMock()
                mock_result.repository = MagicMock()
                mock_result.repository.files = []
                mock_result.test_results = None
                MockOrch.return_value.run_from_stage_2.side_effect = [
                    TransientLLMError("timeout"),
                    mock_result,
                ]

                with patch.object(svc, "_try_start_preview"):
                    svc.enqueue_generation(pid)
                metrics = svc.get_reliability_metrics()
                assert metrics["transient_retry_attempts"] >= 1
                assert metrics["transient_retry_successes"] >= 1


def test_no_retry_on_permanent_error():
    settings = _make_settings()
    svc = TaskService(settings)
    pid = svc.create_chat_project()
    append_message(settings, pid, "user", "build todo app")
    append_message(settings, pid, "assistant", "ok")

    with patch("src.web.services.task_service.threading.Thread", side_effect=_fake_thread_factory()):
        with patch("src.web.services.chat_service.get_messages", return_value=[{"role": "user", "content": "build todo app"}]):
            with patch("src.services.llm_service.LLMService") as MockLLM, patch(
                "src.agents.stage1_requirements.interaction_agent.InteractionAgent"
            ) as MockAgent, patch("src.core.orchestrator.Orchestrator") as MockOrch:
                from src.core.data_models import Requirements
                from src.core.exceptions import PermanentLLMError

                MockLLM.from_settings.return_value = MagicMock()
                mock_agent = MagicMock()
                mock_agent.conversation_to_requirements.return_value = Requirements(
                    title="Todo", description="Todo app", features=[], constraints=[]
                )
                MockAgent.return_value = mock_agent
                MockOrch.return_value.run_from_stage_2.side_effect = PermanentLLMError("bad request")
                with patch.object(svc, "_try_start_preview"):
                    svc.enqueue_generation(pid)
                assert MockOrch.return_value.run_from_stage_2.call_count == 1


def test_backpressure_rejects_when_workers_exhausted():
    settings = _make_settings()
    settings.task_max_workers = 1
    svc = TaskService(settings)
    pid = svc.create_chat_project()
    append_message(settings, pid, "user", "build todo app")
    append_message(settings, pid, "assistant", "ok")
    svc._active_workers = 1

    with patch("src.web.services.task_service.threading.Thread", side_effect=_fake_thread_factory()):
        result = svc.enqueue_generation(pid)
    assert result == "rejected_backpressure"
    metrics = svc.get_reliability_metrics()
    assert metrics["queue_rejects"] >= 1


def test_cancelled_generation_becomes_cancelled_status():
    settings = _make_settings()
    svc = TaskService(settings)
    pid = svc.create_chat_project()
    append_message(settings, pid, "user", "build todo app")
    append_message(settings, pid, "assistant", "ok")
    with patch("src.web.services.task_service.threading.Thread", side_effect=_fake_thread_factory()):
        with patch("src.web.services.chat_service.get_messages", return_value=[{"role": "user", "content": "build todo app"}]):
            with patch("src.services.llm_service.LLMService") as MockLLM, patch(
                "src.agents.stage1_requirements.interaction_agent.InteractionAgent"
            ) as MockAgent, patch("src.core.orchestrator.Orchestrator") as MockOrch:
                from src.core.data_models import Requirements

                MockLLM.from_settings.return_value = MagicMock()
                mock_agent = MagicMock()
                mock_agent.conversation_to_requirements.return_value = Requirements(
                    title="Todo", description="Todo app", features=[], constraints=[]
                )
                MockAgent.return_value = mock_agent

                def _cancel_then_progress(*args, **kwargs):
                    progress_cb = kwargs.get("progress_callback")
                    svc.cancel_generation(pid)
                    progress_cb(30, "Stage 2: Planning")
                    return MagicMock()

                MockOrch.return_value.run_from_stage_2.side_effect = _cancel_then_progress
                with patch.object(svc, "_try_start_preview"):
                    svc.enqueue_generation(pid)

    status = svc.get_status(pid)
    assert status["status"] == "cancelled"


def test_enqueue_returns_queued_rerun_when_project_lock_busy():
    settings = _make_settings()
    svc = TaskService(settings)
    pid = svc.create_chat_project()
    append_message(settings, pid, "user", "build todo app")
    append_message(settings, pid, "assistant", "ok")

    proj_lock = svc._get_project_lock(pid)
    assert proj_lock.acquire(blocking=False) is True
    try:
        result = svc.enqueue_generation(pid)
    finally:
        proj_lock.release()

    assert result == "queued_rerun"
    assert svc._pending_regenerate.get(pid) is True


def test_enqueue_returns_deduped_active_when_same_fingerprint_running():
    settings = _make_settings()
    svc = TaskService(settings)
    pid = svc.create_chat_project()
    append_message(settings, pid, "user", "build todo app")
    append_message(settings, pid, "assistant", "ok")

    fp = svc._build_input_fingerprint(project_id=pid, product_type=None, model_id=None)
    proj_lock = svc._get_project_lock(pid)
    assert proj_lock.acquire(blocking=False) is True
    try:
        with svc._lock:
            svc._active_fingerprints[pid] = fp
        result = svc.enqueue_generation(pid)
    finally:
        proj_lock.release()

    assert result == "deduped_active"
