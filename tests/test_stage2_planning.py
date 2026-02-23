"""Test Stage 2 - Planning Agents (TaskDivision, SchemePlanning) with mocked LLM."""

import pytest

from src.core.data_models import Requirements, Feature, Task, TaskType, FileSpec
from src.agents.stage2_planning.planning_agents import (
    TaskDivisionAgent,
    SchemePlanningAgent,
    FlowSimulationAgent,
    AlgorithmAnalysisAgent,
)


class MockLLMService:
    """Mock LLM that returns fixed JSON for planning agents."""

    def generate(self, prompt: str, **kwargs) -> str:
        return "User opens app, sees list, can add/delete items. Flow: / -> /list -> /add."

    def generate_json(self, prompt: str):
        # TaskDivisionAgent expects list of dicts
        if "OUTPUT FORMAT (JSON array)" in prompt or "task_files" not in prompt:
            return [
                {"id": "T1", "name": "Create data model", "description": "Todo model with title, done", "type": "database", "priority": 5, "estimated_complexity": "low"},
                {"id": "T2", "name": "Create API", "description": "CRUD API for todos", "type": "backend", "priority": 5, "estimated_complexity": "medium"},
                {"id": "T3", "name": "Create frontend", "description": "List and add UI", "type": "frontend", "priority": 4, "estimated_complexity": "low"},
            ]
        # AlgorithmAnalysisAgent expects dict keyed by task_id
        if "implementation_approach" in prompt:
            return {
                "T1": {"implementation_approach": "SQLAlchemy model", "notes": ""},
                "T2": {"implementation_approach": "Flask Blueprint with routes", "notes": ""},
                "T3": {"implementation_approach": "HTML templates with fetch", "notes": ""},
            }
        # SchemePlanningAgent expects task_files, api_specs, pyi_stubs
        return {
            "task_files": {
                "T1": [{"path": "app/models/todo.py", "layer": "base", "purpose": "Todo model", "dependencies": []}],
                "T2": [{"path": "app/routes/todos.py", "layer": "business", "purpose": "Todo API", "dependencies": ["app/models/todo.py"]}],
                "T3": [{"path": "templates/index.html", "layer": "assembly", "purpose": "List UI", "dependencies": []}],
            },
            "api_specs": {
                "endpoints": [
                    {"path": "/api/todos", "method": "GET", "description": "List todos"},
                    {"path": "/api/todos", "method": "POST", "description": "Create todo"},
                ],
                "frontend_routes": {"/": {"template": "index.html", "description": "Home"}},
            },
            "pyi_stubs": {
                "app/models/todo.py": "class Todo(db.Model):\n    id: int\n    title: str\n    done: bool\ndef get_todos() -> list: ...",
                "app/routes/todos.py": "todos_bp = Blueprint('todos', __name__)\ndef get_todos() -> list: ...",
            },
        }


@pytest.fixture
def mock_llm():
    return MockLLMService()


@pytest.fixture
def sample_requirements():
    return Requirements(
        title="Todo App",
        description="Simple todo list",
        features=[
            Feature(id="1", name="Add todo", description="Add item", priority=1),
            Feature(id="2", name="Delete todo", description="Remove item", priority=2),
        ],
    )


def test_task_division_agent_output_structure(mock_llm, sample_requirements):
    """TaskDivisionAgent should return List[Task] with valid structure."""
    agent = TaskDivisionAgent(mock_llm)
    tasks = agent.execute(sample_requirements, flow_simulation="")

    assert isinstance(tasks, list)
    assert len(tasks) >= 1
    for t in tasks:
        assert isinstance(t, Task)
        assert t.id
        assert t.name
        assert t.description
        assert t.type in TaskType
        assert t.estimated_complexity


def test_scheme_planning_agent_return_signature(mock_llm, sample_requirements):
    """SchemePlanningAgent must return (files, interface_specs, api_specs, pyi_stubs)."""
    agent = SchemePlanningAgent(mock_llm)
    tasks = [
        Task(id="T1", name="Model", description="Data model", type=TaskType.DATABASE, estimated_complexity="low"),
        Task(id="T2", name="API", description="API routes", type=TaskType.BACKEND, estimated_complexity="medium"),
    ]
    result = agent.execute(sample_requirements, tasks, flow_simulation="")

    assert isinstance(result, tuple)
    assert len(result) == 4
    files, interface_specs, api_specs, pyi_stubs = result
    assert isinstance(files, list)
    assert isinstance(interface_specs, list)
    assert isinstance(api_specs, dict)
    assert isinstance(pyi_stubs, dict)
    if files:
        assert isinstance(files[0], FileSpec)
        assert files[0].path


def test_scheme_planning_agent_exception_returns_stable_signature(mock_llm, sample_requirements):
    """SchemePlanningAgent exception path must return 4-tuple."""
    class FailingLLM:
        def generate_json(self, prompt):
            raise ValueError("Simulated failure")

    agent = SchemePlanningAgent(FailingLLM())
    tasks = [Task(id="T1", name="X", description="Y", type=TaskType.BACKEND, estimated_complexity="low")]
    result = agent.execute(sample_requirements, tasks, flow_simulation="")

    assert isinstance(result, tuple)
    assert len(result) == 4
    files, interface_specs, api_specs, pyi_stubs = result
    assert files == []
    assert interface_specs == []
    assert api_specs == {}
    assert pyi_stubs == {}
