"""Tests for orchestrator checkpoint/resume behavior."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from config.settings import Settings
from src.core.data_models import (
    Requirements,
    EngineeringPlan,
    Task,
    TaskType,
    TaskComplexity,
    FileSpec,
    CodeRepository,
    CodeFile,
    DirectoryStructure,
)
from src.core.exceptions import StageExecutionError
from src.core.orchestrator import Orchestrator


@pytest.fixture
def temp_settings():
    root = Path(tempfile.mkdtemp(prefix="idea2product_orch_recovery_"))
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
    settings.models_registry_path = root / "config" / "models_registry.json"
    settings.log_level = "INFO"
    settings.openai_api_key = "sk-test"
    settings.openai_base_url = "https://api.openai.com/v1"
    settings.openai_model = "gpt-4o-mini"
    settings.openai_vlm_model = "gpt-4o-mini"
    settings.primary_llm_provider = "openai"
    settings.use_fast_model_for_light_stages = False
    settings.enable_hf_model_search = False
    return settings


def _req():
    return Requirements(title="Todo", description="Todo app", features=[], constraints=[])


def _plan():
    return EngineeringPlan(
        tasks=[
            Task(
                id="T1",
                name="Setup",
                description="Setup app",
                type=TaskType.BACKEND,
                estimated_complexity=TaskComplexity.LOW,
            )
        ],
        algorithms={},
        file_structure=[FileSpec(path="app/main.py", purpose="entry")],
        architecture_notes="minimal",
    )


def _repo():
    return CodeRepository(
        files=[
            CodeFile(
                path="app/main.py",
                content="print('ok')",
                language="python",
                purpose="entry",
            )
        ],
        structure=DirectoryStructure(root="generated", directories=["app"], entry_point="app/main.py"),
    )


def test_run_from_stage2_resume_skips_stage2_after_previous_success(temp_settings):
    orchestrator = Orchestrator(temp_settings)
    req = _req()
    pid = "proj_resume_test_001"

    # First run: Stage 2 succeeds, Stage 3 fails.
    with patch.object(orchestrator, "execute_stage_2", return_value=_plan()) as m2, patch.object(
        orchestrator, "execute_stage_3", side_effect=RuntimeError("stage3 fail")
    ):
        with pytest.raises(StageExecutionError):
            orchestrator.run_from_stage_2(pid, req)
    assert m2.call_count == 1

    # Second run with same requirements: should reuse Stage 2 checkpoint.
    with patch.object(orchestrator, "execute_stage_2", side_effect=AssertionError("should not rerun stage2")) as m2_again, patch.object(
        orchestrator, "execute_stage_3", return_value=_repo()
    ), patch.object(orchestrator, "execute_stage_4", return_value=MagicMock()):
        orchestrator.run_from_stage_2(pid, req)
    assert m2_again.call_count == 0


def test_resume_invalidated_when_model_id_changes(temp_settings):
    orchestrator = Orchestrator(temp_settings)
    req = _req()
    pid = "proj_resume_test_002"

    with patch.object(orchestrator, "execute_stage_2", return_value=_plan()) as m2, patch.object(
        orchestrator, "execute_stage_3", side_effect=RuntimeError("stage3 fail")
    ):
        with pytest.raises(StageExecutionError):
            orchestrator.run_from_stage_2(pid, req, model_id="gpt-4o-mini")
    assert m2.call_count == 1

    with patch.object(orchestrator, "execute_stage_2", return_value=_plan()) as m2_again, patch.object(
        orchestrator, "execute_stage_3", return_value=_repo()
    ), patch.object(orchestrator, "execute_stage_4", return_value=MagicMock()):
        orchestrator.run_from_stage_2(pid, req, model_id="gpt-4o")
    assert m2_again.call_count == 1


def test_resume_invalidated_when_product_type_changes(temp_settings):
    orchestrator = Orchestrator(temp_settings)
    req = _req()
    pid = "proj_resume_test_003"

    with patch.object(orchestrator, "execute_stage_2", return_value=_plan()) as m2, patch.object(
        orchestrator, "execute_stage_3", side_effect=RuntimeError("stage3 fail")
    ):
        with pytest.raises(StageExecutionError):
            orchestrator.run_from_stage_2(pid, req, product_type="web")
    assert m2.call_count == 1

    with patch.object(orchestrator, "execute_stage_2", return_value=_plan()) as m2_again, patch.object(
        orchestrator, "execute_stage_3", return_value=_repo()
    ), patch.object(orchestrator, "execute_stage_4", return_value=MagicMock()):
        orchestrator.run_from_stage_2(pid, req, product_type="app")
    assert m2_again.call_count == 1
