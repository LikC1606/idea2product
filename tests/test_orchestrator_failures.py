"""Tests for orchestrator failure handling and context persistence."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from config.settings import Settings
from src.core.data_models import Requirements
from src.core.exceptions import StageExecutionError
from src.core.orchestrator import Orchestrator


@pytest.fixture
def temp_settings():
    """Create settings with temp directories."""
    root = Path(tempfile.mkdtemp(prefix="idea2product_orch_test_"))
    (root / "config" / "prompts").mkdir(parents=True, exist_ok=True)
    (root / "templates").mkdir(parents=True, exist_ok=True)
    (root / "data" / "projects").mkdir(parents=True, exist_ok=True)
    (root / "config").mkdir(parents=True, exist_ok=True)

    settings = MagicMock(spec=Settings)
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
    return settings, root


def _make_minimal_requirements():
    return Requirements(
        title="Test",
        description="Test",
        features=[],
    )


def test_stage2_failure_saves_context(temp_settings):
    """When Stage 2 fails, context.json is saved with partial_failure and failed_stage."""
    settings, root = temp_settings
    orchestrator = Orchestrator(settings)

    with patch.object(orchestrator, "execute_stage_1", return_value=_make_minimal_requirements()):
        with patch.object(orchestrator, "execute_stage_2", side_effect=RuntimeError("Stage 2 simulated failure")):
            with pytest.raises(StageExecutionError):
                orchestrator.run("Build a todo app", interactive=False)

    projects_dir = root / "data" / "projects"
    project_dirs = [d for d in projects_dir.iterdir() if d.is_dir()]
    assert len(project_dirs) == 1
    artifacts = project_dirs[0] / "artifacts" / "context.json"
    assert artifacts.exists()

    import json
    data = json.loads(artifacts.read_text(encoding="utf-8"))
    assert data.get("partial_failure") is True
    assert data.get("failed_stage") == 2
    assert "error_log" in data
    assert len(data["error_log"]) >= 1
    assert "Stage 2" in data["error_log"][0] or "simulated failure" in data["error_log"][0]


def test_stage1_failure_saves_context(temp_settings):
    """When Stage 1 fails, context.json is saved with error_log."""
    settings, root = temp_settings
    orchestrator = Orchestrator(settings)

    with patch.object(
        orchestrator, "execute_stage_1", side_effect=RuntimeError("Stage 1 simulated failure")
    ):
        with pytest.raises(StageExecutionError):
            orchestrator.run("Build a todo app", interactive=False)

    projects_dir = root / "data" / "projects"
    project_dirs = [d for d in projects_dir.iterdir() if d.is_dir()]
    assert len(project_dirs) == 1
    artifacts = project_dirs[0] / "artifacts" / "context.json"
    assert artifacts.exists()

    import json
    data = json.loads(artifacts.read_text(encoding="utf-8"))
    assert "error_log" in data
    assert len(data["error_log"]) >= 1


def _make_minimal_engineering_plan():
    from src.core.data_models import (
        EngineeringPlan,
        Task,
        TaskType,
        TaskComplexity,
        Algorithm,
        FileSpec,
    )
    return EngineeringPlan(
        tasks=[Task(id="T1", name="Setup", description="Setup app", type=TaskType.BACKEND, estimated_complexity=TaskComplexity.LOW)],
        algorithms={},
        file_structure=[FileSpec(path="app/main.py", purpose="Entry")],
        architecture_notes="Minimal",
    )


def _make_minimal_code_repository():
    from src.core.data_models import CodeRepository, CodeFile, DirectoryStructure
    return CodeRepository(
        files=[CodeFile(path="app/main.py", content="print('hi')", language="python", purpose="Entry")],
        structure=DirectoryStructure(root="app", directories=["app"], entry_point="app/main.py"),
    )


def test_stage3_failure_saves_context(temp_settings):
    """When Stage 3 fails, context.json is saved with partial_failure and failed_stage."""
    settings, root = temp_settings
    orchestrator = Orchestrator(settings)

    with patch.object(orchestrator, "execute_stage_1", return_value=_make_minimal_requirements()):
        with patch.object(orchestrator, "execute_stage_2", return_value=_make_minimal_engineering_plan()):
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

    import json
    data = json.loads(artifacts.read_text(encoding="utf-8"))
    assert data.get("partial_failure") is True
    assert data.get("failed_stage") == 3
    assert "error_log" in data


def test_stage4_failure_saves_context(temp_settings):
    """When Stage 4 fails, context.json is saved with partial_failure and failed_stage."""
    settings, root = temp_settings
    orchestrator = Orchestrator(settings)

    with patch.object(orchestrator, "execute_stage_1", return_value=_make_minimal_requirements()):
        with patch.object(orchestrator, "execute_stage_2", return_value=_make_minimal_engineering_plan()):
            with patch.object(orchestrator, "execute_stage_3", return_value=_make_minimal_code_repository()):
                with patch.object(
                    orchestrator, "execute_stage_4", side_effect=RuntimeError("Stage 4 simulated failure")
                ):
                    with pytest.raises(StageExecutionError):
                        orchestrator.run("Build a todo app", interactive=False)

    projects_dir = root / "data" / "projects"
    project_dirs = [d for d in projects_dir.iterdir() if d.is_dir()]
    assert len(project_dirs) == 1
    artifacts = project_dirs[0] / "artifacts" / "context.json"
    assert artifacts.exists()

    import json
    data = json.loads(artifacts.read_text(encoding="utf-8"))
    assert data.get("partial_failure") is True
    assert data.get("failed_stage") == 4
    assert "error_log" in data
