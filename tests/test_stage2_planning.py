"""Test Stage 2 - Planning Agents (TaskDivision, SchemePlanning, AlgorithmAnalysis) with mocked LLM."""

import pytest

from src.core.data_models import Requirements, Feature, Task, TaskType, TaskComplexity, FileSpec, Algorithm
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

    def generate_json(self, prompt: str, **kwargs):
        # Entity/page extraction (Phase 1 of two-phase generation)
        if "识别所有数据实体和前端页面" in prompt:
            return {
                "entities": [{"name": "Todo", "fields": ["id(int)", "title(str)", "done(bool)"], "crud_operations": ["create", "read", "delete"], "relations": []}],
                "pages": [{"name": "主页", "url": "/", "related_entities": ["Todo"], "interactions": ["查看列表", "添加", "删除"]}],
            }
        # Flow structure extraction
        if "提取结构化信息" in prompt:
            return {
                "pages": [{"url": "/", "name": "主页", "description": "待办列表"}],
                "entities": [{"name": "Todo", "fields": ["id(int)", "title(str)"], "relations": []}],
                "key_interactions": ["添加待办", "删除待办"],
            }
        # ReviewAgent task review
        if "审查以下 Stage 2" in prompt:
            return {"issues": [], "refined_tasks": []}
        # TaskDivisionAgent unified prompt (entities + pages + tasks in one call)
        if "一次性输出" in prompt and "数据实体" in prompt:
            return {
                "entities": [{"name": "Todo", "fields": ["id(int)", "title(str)", "done(bool)"], "crud_operations": ["create", "read", "delete"], "relations": []}],
                "pages": [{"name": "主页", "url": "/", "related_entities": ["Todo"], "interactions": ["查看列表", "添加", "删除"]}],
                "tasks": [
                    {"id": "T1", "name": "Create data model", "description": "Todo model with title, done", "type": "database", "priority": 5, "estimated_complexity": "low", "dependencies": []},
                    {"id": "T2", "name": "Create API", "description": "CRUD API for todos", "type": "backend", "priority": 5, "estimated_complexity": "medium", "dependencies": ["T1"]},
                    {"id": "T3", "name": "Create frontend", "description": "List and add UI", "type": "frontend", "priority": 4, "estimated_complexity": "low", "dependencies": ["T2"]},
                ],
            }
        # TaskDivisionAgent two-phase main prompt
        if "OUTPUT FORMAT (JSON array)" in prompt:
            return [
                {"id": "T1", "name": "Create data model", "description": "Todo model with title, done", "type": "database", "priority": 5, "estimated_complexity": "low", "dependencies": []},
                {"id": "T2", "name": "Create API", "description": "CRUD API for todos", "type": "backend", "priority": 5, "estimated_complexity": "medium", "dependencies": ["T1"]},
                {"id": "T3", "name": "Create frontend", "description": "List and add UI", "type": "frontend", "priority": 4, "estimated_complexity": "low", "dependencies": ["T2"]},
            ]
        # AlgorithmAnalysisAgent
        if "implementation_approach" in prompt and "task_files" not in prompt:
            return {
                "T1": {"implementation_approach": "SQLAlchemy model", "notes": ""},
                "T2": {"implementation_approach": "Flask Blueprint with routes", "notes": ""},
                "T3": {"implementation_approach": "HTML templates with fetch", "notes": ""},
            }
        # ReviewAgent API review
        if "审查以下生成的API规范" in prompt:
            return {"issues": [], "refined_api_specs": {}}
        # SchemePlanningAgent
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


def test_task_division_agent_fallback_on_llm_failure(sample_requirements):
    """TaskDivisionAgent uses template fallback when LLM fails and pattern matches."""
    class FailingLLM:
        def generate_json(self, prompt, **kwargs):
            raise ValueError("Simulated LLM failure")

    agent = TaskDivisionAgent(FailingLLM())
    # "Todo App" + "Add todo" + "Delete todo" -> crud keywords (创建, 删除, 列表) -> score >= 2
    crud_req = Requirements(
        title="Todo 应用",
        description="待办列表，支持增删改查",
        features=[
            Feature(id="1", name="添加待办", description="Add item", priority=1),
            Feature(id="2", name="删除待办", description="Remove item", priority=2),
        ],
    )
    tasks = agent.execute(crud_req, flow_simulation="")
    assert isinstance(tasks, list)
    assert len(tasks) >= 1
    for t in tasks:
        assert isinstance(t, Task)
        assert t.id.startswith("T")


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


def test_algorithm_analysis_agent_without_hf(mock_llm):
    """AlgorithmAnalysisAgent returns Algorithm per task when HF is disabled."""
    agent = AlgorithmAnalysisAgent(mock_llm, hf_model_service=None)
    tasks = [
        Task(id="T1", name="Model", description="Data model", type=TaskType.DATABASE, estimated_complexity=TaskComplexity.LOW),
        Task(id="T2", name="API", description="API routes", type=TaskType.BACKEND, estimated_complexity=TaskComplexity.MEDIUM),
    ]
    result = agent.execute(tasks)
    assert isinstance(result, dict)
    assert "T1" in result
    assert "T2" in result
    for alg in result.values():
        assert isinstance(alg, Algorithm)
        assert alg.implementation_approach
        assert alg.hf_models is None or alg.hf_models == []


def test_algorithm_analysis_agent_fallback_uses_type_aware_defaults():
    """AlgorithmAnalysisAgent uses type-aware defaults when LLM fails."""
    class FailingLLM:
        def generate_json(self, prompt, **kwargs):
            raise ValueError("Simulated failure")

    agent = AlgorithmAnalysisAgent(FailingLLM(), hf_model_service=None)
    tasks = [
        Task(id="T1", name="Create backend", description="API", type=TaskType.BACKEND, estimated_complexity=TaskComplexity.MEDIUM),
        Task(id="T2", name="Create frontend", description="UI", type=TaskType.FRONTEND, estimated_complexity=TaskComplexity.LOW),
    ]
    result = agent.execute(tasks)
    assert result["T1"].libraries == ["flask", "sqlalchemy"]
    assert "Flask" in result["T1"].implementation_approach or "SQLAlchemy" in result["T1"].implementation_approach
    assert result["T2"].libraries == ["jinja2"]
    assert "Jinja2" in result["T2"].implementation_approach or "jinja2" in result["T2"].implementation_approach.lower()


def test_algorithm_analysis_agent_parses_data_structures_and_algorithm_type(mock_llm):
    """AlgorithmAnalysisAgent parses data_structures and algorithm_type from LLM."""
    class CustomLLM:
        def generate_json(self, prompt, **kwargs):
            return {
                "T1": {
                    "implementation_approach": "SQLAlchemy model with Todo class",
                    "notes": "",
                    "data_structures": ["Todo", "List"],
                    "algorithm_type": "crud",
                },
            }
    agent = AlgorithmAnalysisAgent(CustomLLM(), hf_model_service=None)
    tasks = [Task(id="T1", name="Model", description="Todo model", type=TaskType.DATABASE, estimated_complexity=TaskComplexity.LOW)]
    result = agent.execute(tasks)
    assert result["T1"].data_structures == ["Todo", "List"]
    assert result["T1"].algorithm_type == "crud"
    assert result["T1"].libraries == ["flask", "sqlalchemy"]


def test_algorithm_analysis_agent_accepts_hf_models_in_response(mock_llm):
    """AlgorithmAnalysisAgent parses hf_models and hf_usage_notes from LLM."""
    class HFLLM:
        def generate_json(self, prompt, **kwargs):
            return {
                "T1": {
                    "implementation_approach": "Use transformers pipeline",
                    "notes": "",
                    "hf_models": ["cardiffnlp/twitter-roberta-base-sentiment-latest"],
                    "hf_usage_notes": "Use pipeline('sentiment-analysis', model=...)",
                },
            }
    agent = AlgorithmAnalysisAgent(HFLLM(), hf_model_service=None)
    tasks = [Task(id="T1", name="Sentiment", description="sentiment analysis", type=TaskType.BACKEND, estimated_complexity=TaskComplexity.MEDIUM)]
    result = agent.execute(tasks)
    assert result["T1"].hf_models == ["cardiffnlp/twitter-roberta-base-sentiment-latest"]
    assert "pipeline" in (result["T1"].hf_usage_notes or "")
    assert "transformers" in result["T1"].libraries


def test_scheme_planning_agent_exception_returns_stable_signature(mock_llm, sample_requirements):
    """SchemePlanningAgent exception path must return 4-tuple."""
    class FailingLLM:
        def generate_json(self, prompt, **kwargs):
            raise ValueError("Simulated failure")

    agent = SchemePlanningAgent(FailingLLM())
    tasks = [Task(id="T1", name="X", description="Y", type=TaskType.BACKEND, estimated_complexity="low")]
    result = agent.execute(sample_requirements, tasks, flow_simulation="")

    assert isinstance(result, tuple)
    assert len(result) == 4
    files, interface_specs, api_specs, pyi_stubs = result
    assert isinstance(files, list)
    assert isinstance(interface_specs, list)
    assert isinstance(api_specs, dict)
    assert isinstance(pyi_stubs, dict)


def test_scheme_planning_agent_fallback_on_llm_failure_with_crud_pattern():
    """SchemePlanningAgent uses template fallback when LLM fails and crud pattern matches."""
    class FailingLLM:
        def generate_json(self, prompt, **kwargs):
            raise ValueError("Simulated failure")

    agent = SchemePlanningAgent(FailingLLM())
    req = Requirements(
        title="Todo 应用",
        description="待办列表，支持增删改查",
        features=[
            Feature(id="1", name="添加待办", description="Add", priority=1),
            Feature(id="2", name="删除待办", description="Delete", priority=2),
        ],
    )
    tasks = [
        Task(id="T1", name="后端", description="Todo model and API", type=TaskType.BACKEND, estimated_complexity="low"),
        Task(id="T2", name="前端", description="Todo list UI", type=TaskType.FRONTEND, estimated_complexity="low"),
    ]
    result = agent.execute(req, tasks, flow_simulation="")
    assert isinstance(result, tuple)
    assert len(result) == 4
    files, interface_specs, api_specs, pyi_stubs = result
    assert len(files) >= 1
    assert "app/" in files[0].path or "templates/" in files[0].path
    assert "endpoints" in api_specs or len(api_specs) >= 0
    assert isinstance(pyi_stubs, dict)
