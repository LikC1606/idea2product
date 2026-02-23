"""Test Stage 3 - Code Generation (skeleton builder, template loading)."""

import tempfile
from pathlib import Path

import pytest

from src.core.data_models import Requirements, Feature, EngineeringPlan, Task, Algorithm, FileSpec, TaskType, TaskComplexity
from src.core.context import ExecutionContext
from src.utils.skeleton_builder import build_skeleton_from_pyi_stubs
from src.agents.stage3_generation.code_generation_agents import CodeGenerationAgent, FRAMEWORK_TEMPLATE_PATH


def test_skeleton_builder_from_pyi_stubs():
    """build_skeleton_from_pyi_stubs produces valid CodeSkeleton."""
    pyi_stubs = {
        "app/models/todo.py": "class Todo(db.Model):\n    id: int\n    title: str\ndef get_todos() -> list: ...",
        "app/routes/todos.py": "def create_todo(title: str) -> Todo: ...",
    }
    file_structure = [
        FileSpec(path="app/models/todo.py", purpose="Model", dependencies=[]),
        FileSpec(path="app/routes/todos.py", purpose="Routes", dependencies=["app/models/todo.py"]),
    ]
    skeleton = build_skeleton_from_pyi_stubs(pyi_stubs, file_structure, entry_point="app.py")

    assert skeleton is not None
    assert len(skeleton.interfaces) >= 1
    assert len(skeleton.dependency_graph.nodes) >= 1
    assert skeleton.dependency_graph.entry_point == "app.py"
    assert any("Todo" in str(s) for s in skeleton.interfaces)


def test_skeleton_builder_empty_stubs():
    """Empty pyi_stubs returns minimal skeleton."""
    skeleton = build_skeleton_from_pyi_stubs({}, [], entry_point="app.py")
    assert skeleton.dependency_graph.entry_point == "app.py"
    assert skeleton.dependency_graph.nodes


@pytest.fixture
def sample_plan():
    return EngineeringPlan(
        tasks=[
            Task(id="T1", name="Model", description="Todo model", type=TaskType.DATABASE, estimated_complexity=TaskComplexity.LOW),
            Task(id="T2", name="API", description="Routes", type=TaskType.BACKEND, estimated_complexity=TaskComplexity.MEDIUM),
        ],
        algorithms={"T1": Algorithm(task_id="T1", algorithm_type="standard", implementation_approach="SQLAlchemy"), "T2": Algorithm(task_id="T2", algorithm_type="standard", implementation_approach="Flask")},
        file_structure=[
            FileSpec(path="app/models/todo.py", purpose="Model", dependencies=[]),
            FileSpec(path="app/routes/todos.py", purpose="Routes", dependencies=["app/models/todo.py"]),
        ],
        dependencies=["flask"],
        architecture_notes="Todo app",
        api_specs={"endpoints": []},
        pyi_stubs={"app/models/todo.py": "class Todo: ...", "app/routes/todos.py": "def get_todos(): ..."},
    )


def test_code_generation_agent_template_load():
    """CodeGenerationAgent._load_framework_template returns files when template exists."""
    if not FRAMEWORK_TEMPLATE_PATH.exists():
        pytest.skip("Flask template not found")

    class NoOpLLM:
        pass

    agent = CodeGenerationAgent(NoOpLLM(), settings=None)
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "generated"
        target.mkdir()
        files = agent._load_framework_template(target)
        assert isinstance(files, list)
        if files:
            assert any(f.path.endswith(".py") for f in files)
