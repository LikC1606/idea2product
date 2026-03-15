"""Bug-hunting tests: edge cases and failure modes from TROUBLESHOOTING / PROJECT_AND_ISSUES.

These tests are designed to catch regressions and document expected behavior for:
- Data model validation (Requirements, Feature, Task, CodeRepository)
- TaskService dedupe/backpressure/status semantics
- Skeleton builder with empty or malformed inputs
- Preview service when generated/ missing or no entry point
- Orchestrator context persistence on Stage 3 failure
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from src.core.data_models import (
    CodeFile,
    CodeRepository,
    DirectoryStructure,
    EngineeringPlan,
    Feature,
    Requirements,
    Task,
    TaskType,
    TaskComplexity,
)
from src.core.exceptions import StageExecutionError
from src.core.orchestrator import Orchestrator
from src.utils.skeleton_builder import generate_minimal_pyi_from_interface_specs, build_skeleton_from_pyi_stubs
from src.web.services.chat_service import append_message
from src.web.services.preview_service import PreviewService
from src.web.services.task_service import TaskService


# ---------------------------------------------------------------------------
# Data models: validation and edge cases
# ---------------------------------------------------------------------------


def test_requirements_empty_features_allowed():
    """Requirements with empty features list is valid (minimal stub)."""
    r = Requirements(title="App", description="Desc", features=[])
    assert r.features == []
    assert r.title == "App"


def test_feature_priority_bounds_enforced():
    """Feature priority must be 1-5 (ge=1, le=5)."""
    Feature(id="f1", name="F", description="D", priority=1)
    Feature(id="f2", name="F", description="D", priority=5)
    with pytest.raises(ValidationError):
        Feature(id="f3", name="F", description="D", priority=0)
    with pytest.raises(ValidationError):
        Feature(id="f4", name="F", description="D", priority=6)


def test_feature_id_required():
    """Feature id is required (missing raises ValidationError)."""
    with pytest.raises(ValidationError):
        Feature(name="F", description="D")  # type: ignore[call-arg]


def test_task_dependencies_can_reference_any_string():
    """Task dependencies are just list of strings; no cross-validation (could be missing id)."""
    t = Task(
        id="T1",
        name="Task",
        description="D",
        type=TaskType.BACKEND,
        estimated_complexity=TaskComplexity.LOW,
        dependencies=["T0", "T99"],
    )
    assert t.dependencies == ["T0", "T99"]


def test_code_repository_empty_files_allowed():
    """CodeRepository with empty files list is valid (e.g. failed generation)."""
    structure = DirectoryStructure(root=".", directories=[], entry_point="app.py")
    repo = CodeRepository(files=[], structure=structure)
    assert repo.files == []
    assert repo.structure.entry_point == "app.py"


def test_code_repository_requires_structure_and_files_field():
    """CodeRepository requires structure and files (can be empty list)."""
    with pytest.raises(ValidationError):
        CodeRepository(files=[])  # missing required structure


# ---------------------------------------------------------------------------
# TaskService: dedupe, backpressure, status semantics
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_settings():
    temp_dir = tempfile.mkdtemp(prefix="bug_hunt_task_")
    projects_dir = Path(temp_dir) / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    mock = MagicMock()
    mock.projects_dir = projects_dir
    mock.data_dir = Path(temp_dir)
    return mock


@pytest.fixture
def task_service(temp_settings):
    return TaskService(temp_settings)


def test_enqueue_generation_returns_started_when_acquired(task_service, temp_settings):
    """First enqueue for a project with messages returns 'started'."""
    project_id = task_service.create_chat_project()
    append_message(temp_settings, project_id, "user", "Build a todo app")
    append_message(temp_settings, project_id, "assistant", "OK")

    def fake_thread(*args, **kwargs):
        target = kwargs.get("target") or (args[0] if args else None)
        targs = kwargs.get("args", ())
        mock_t = MagicMock()
        def start():
            if target:
                target(*targs)
        mock_t.start.side_effect = start
        return mock_t

    mock_result = MagicMock()
    mock_result.repository = MagicMock()
    mock_result.repository.files = []
    mock_result.test_results = None

    with patch("src.core.orchestrator.Orchestrator") as MockOrch:
        MockOrch.return_value.run_from_stage_2.return_value = mock_result
    with patch("src.web.services.chat_service.get_messages", return_value=[
        {"role": "user", "content": "Build a todo app"},
        {"role": "assistant", "content": "OK"},
    ]):
        with patch("src.services.llm_service.LLMService"):
            with patch("src.agents.stage1_requirements.interaction_agent.InteractionAgent") as MockAgent:
                from src.core.data_models import Requirements
                MockAgent.return_value.conversation_to_requirements.return_value = Requirements(
                    title="Todo", description="Todo app", features=[], constraints=[], target_users=None, data_requirements=None
                )
            with patch.object(task_service, "_try_start_preview"):
                with patch("src.web.services.task_service.threading.Thread", side_effect=fake_thread):
                    result = task_service.enqueue_generation(project_id)

    assert result == "started"


def test_enqueue_generation_returns_deduped_completed_for_same_fingerprint_after_completion(
    task_service, temp_settings
):
    """After a run is marked completed with a fingerprint, same fingerprint returns 'deduped_completed'."""
    project_id = task_service.create_chat_project()
    append_message(temp_settings, project_id, "user", "Same request")
    append_message(temp_settings, project_id, "assistant", "OK")

    fingerprint = task_service._build_input_fingerprint(project_id=project_id, product_type=None, model_id=None)
    assert fingerprint  # ensure we have a fingerprint to dedupe on

    # Simulate a completed run: set status and last-completed fingerprint so next enqueue is deduped
    with task_service._lock:
        task_service.tasks[project_id]["status"] = "completed"
        task_service._last_completed_fingerprint[project_id] = fingerprint
    task_service._persist_task(project_id)

    with patch("src.web.services.chat_service.get_messages", return_value=[
        {"role": "user", "content": "Same request"},
        {"role": "assistant", "content": "OK"},
    ]):
        result = task_service.enqueue_generation(project_id)

    assert result == "deduped_completed"


def test_enqueue_generation_rejected_backpressure_when_max_workers_zero(task_service, temp_settings):
    """When _max_workers is 0, enqueue returns 'rejected_backpressure'."""
    project_id = task_service.create_chat_project()
    append_message(temp_settings, project_id, "user", "Build app")

    with patch.object(task_service, "_max_workers", 0):
        with patch("src.web.services.chat_service.get_messages", return_value=[{"role": "user", "content": "Build app"}]):
            result = task_service.enqueue_generation(project_id)

    assert result == "rejected_backpressure"


def test_get_status_returns_none_for_unknown_project(task_service):
    """get_status(unknown_id) returns None."""
    assert task_service.get_status("proj_nonexistent_xyz") is None


def test_get_status_returns_idle_for_new_project(task_service, temp_settings):
    """New project has status 'idle'."""
    project_id = task_service.create_chat_project()
    status = task_service.get_status(project_id)
    assert status is not None
    assert status["status"] == "idle"


# ---------------------------------------------------------------------------
# Skeleton builder: empty and malformed inputs
# ---------------------------------------------------------------------------


def test_generate_minimal_pyi_empty_inputs_returns_empty_dict():
    """Empty interface_specs and file_structure returns {}."""
    result = generate_minimal_pyi_from_interface_specs([], [])
    assert result == {}


def test_generate_minimal_pyi_interface_spec_without_py_path_skipped():
    """Interface spec with file_path not ending in .py is skipped."""
    class Spec:
        file_path = "readme.txt"
        exports = []
    result = generate_minimal_pyi_from_interface_specs([Spec], [])
    assert result == {}


def test_build_skeleton_empty_pyi_and_no_fallback_returns_minimal_skeleton():
    """build_skeleton with empty pyi_stubs and no interface_specs/file_structure returns minimal skeleton."""
    result = build_skeleton_from_pyi_stubs(
        pyi_stubs={},
        file_structure=[],
        entry_point="app.py",
        interface_specs=[],
    )
    assert result is not None
    assert result.interfaces == []
    assert result.dependency_graph.entry_point == "app.py"
    # When no stubs: fallback adds default node so graph is valid (skeleton_builder lines 201-206)
    assert result.dependency_graph.nodes == ["app.py"]


# ---------------------------------------------------------------------------
# Preview service: missing generated dir / no entry point
# ---------------------------------------------------------------------------


@pytest.fixture
def preview_temp_dir():
    d = tempfile.mkdtemp(prefix="bug_hunt_preview_")
    yield Path(d)


@pytest.fixture
def preview_svc(preview_temp_dir):
    settings = MagicMock()
    settings.projects_dir = preview_temp_dir
    return PreviewService(settings)


def test_start_preview_when_generated_dir_missing_returns_none(preview_svc, preview_temp_dir):
    """start_preview when project has no generated/ returns None and sets error status."""
    project_id = "proj_no_gen"
    (preview_temp_dir / project_id).mkdir(parents=True)
    # No generated/ subdir

    url = preview_svc.start_preview(project_id)
    assert url is None

    info = preview_svc.get_preview_status(project_id)
    assert info.get("state") == "error"
    assert "generated" in (info.get("preview_error") or "").lower() or "no generated" in (info.get("preview_error") or "").lower()


def test_start_preview_when_no_entry_point_returns_none(preview_svc, preview_temp_dir):
    """start_preview when generated/ exists but has no app.py/main.py returns None."""
    project_id = "proj_no_entry"
    gen_dir = preview_temp_dir / project_id / "generated"
    gen_dir.mkdir(parents=True)
    (gen_dir / "readme.txt").write_text("no app")

    url = preview_svc.start_preview(project_id)
    assert url is None

    info = preview_svc.get_preview_status(project_id)
    assert info.get("state") == "error"
    assert "entry" in (info.get("preview_error") or "").lower() or "app.py" in (info.get("preview_error") or "").lower()


# ---------------------------------------------------------------------------
# Orchestrator: Stage 3 failure persists context
# ---------------------------------------------------------------------------


@pytest.fixture
def orch_temp_settings():
    root = Path(tempfile.mkdtemp(prefix="bug_hunt_orch_"))
    (root / "config" / "prompts").mkdir(parents=True, exist_ok=True)
    (root / "templates").mkdir(parents=True, exist_ok=True)
    (root / "data" / "projects").mkdir(parents=True, exist_ok=True)

    settings = MagicMock()
    settings.project_root = root
    settings.data_dir = root / "data"
    settings.projects_dir = root / "data" / "projects"
    settings.prompts_dir = root / "config" / "prompts"
    settings.templates_dir = root / "templates"
    settings.log_level = "INFO"
    settings.models_registry_path = root / "config" / "models_registry.json"
    settings.openai_api_key = "sk-test"
    settings.use_fast_model_for_light_stages = False
    settings.enable_hf_model_search = False
    settings.use_unified_task_division = True
    settings.skip_task_review_when_count_low = 3
    settings.enable_parallel_task_generation = False
    settings.enable_code_memory = False
    settings.enable_code_mining = False
    settings.enable_visual_verification = False
    settings.enable_bdd_testing = False
    settings.random_seed = None  # avoid MagicMock being used as seed in run()
    return settings, root


def _minimal_requirements():
    return Requirements(title="Test", description="Test", features=[])


def _minimal_plan():
    return EngineeringPlan(
        tasks=[],
        algorithms={},
        file_structure=[],
        architecture_notes="Minimal",
        interface_specs=[],
        pyi_stubs={},
        external_model_specs=[],
    )


def test_stage3_failure_saves_context_with_partial_failure_and_failed_stage(orch_temp_settings):
    """When Stage 3 fails, context.json is saved with partial_failure=True and failed_stage=3."""
    settings, root = orch_temp_settings
    with patch("src.core.orchestrator.LLMService") as MockLLM:
        MockLLM.from_settings.return_value = MagicMock()
        orchestrator = Orchestrator(settings)

    with patch.object(orchestrator, "execute_stage_1", return_value=_minimal_requirements()):
        with patch.object(orchestrator, "execute_stage_2", return_value=_minimal_plan()):
            with patch.object(
                orchestrator, "execute_stage_3", side_effect=RuntimeError("Stage 3 simulated failure")
            ):
                with pytest.raises(StageExecutionError):
                    orchestrator.run("Build a todo app", interactive=False)

    projects_dir = root / "data" / "projects"
    project_dirs = [d for d in projects_dir.iterdir() if d.is_dir()]
    assert len(project_dirs) == 1
    artifacts = project_dirs[0] / "artifacts" / "context.json"
    assert artifacts.exists()

    data = json.loads(artifacts.read_text(encoding="utf-8"))
    assert data.get("partial_failure") is True
    assert data.get("failed_stage") == 3
    assert "error_log" in data
    assert len(data["error_log"]) >= 1
