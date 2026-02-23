"""Test Stage 4 - Validation Agents (_run_syntax_check, _generate_bdd_tests, etc.)."""

import tempfile
from pathlib import Path

import pytest

from src.core.data_models import (
    Requirements, Feature, CodeRepository, CodeFile, DirectoryStructure,
    TestResult, BDDTestCase,
)
from src.core.context import ExecutionContext
from src.agents.stage4_validation.validation_agents import FullCycleTestingAgent


class MockLLMService:
    def generate(self, prompt, **kwargs):
        return "fixed code"


@pytest.fixture
def mock_llm():
    return MockLLMService()


@pytest.fixture
def sample_repository():
    return CodeRepository(
        files=[
            CodeFile(path="app.py", content="from flask import Flask\napp = Flask(__name__)\n@app.route('/')\ndef index(): return 'ok'", language="python", purpose="Entry"),
            CodeFile(path="app/__init__.py", content="def create_app():\n    from flask import Flask\n    return Flask(__name__)", language="python", purpose="Factory"),
            CodeFile(path="bad.py", content="def broken(\n    pass", language="python", purpose="Invalid"),
        ],
        structure=DirectoryStructure(root="generated", directories=["app"], entry_point="app.py"),
        dependencies=["flask"],
    )


def test_run_syntax_check_detects_errors(mock_llm, sample_repository):
    """_run_syntax_check finds syntax errors."""
    agent = FullCycleTestingAgent(mock_llm)
    errors = agent._run_syntax_check(sample_repository)
    assert len(errors) >= 1
    assert any("bad.py" in str(e.file_path) for e in errors)


def test_run_syntax_check_passes_valid_code(mock_llm):
    """_run_syntax_check passes valid Python."""
    repo = CodeRepository(
        files=[CodeFile(path="good.py", content="x = 1", language="python", purpose="")],
        structure=DirectoryStructure(root="r", directories=[], entry_point="good.py"),
        dependencies=[],
    )
    agent = FullCycleTestingAgent(mock_llm)
    errors = agent._run_syntax_check(repo)
    assert len(errors) == 0


def test_generate_bdd_tests_structure(mock_llm):
    """_generate_bdd_tests returns BDDTestCase list with required fields."""
    agent = FullCycleTestingAgent(mock_llm)
    req = Requirements(
        title="Todo",
        description="App",
        features=[
            Feature(id="1", name="Add todo", description="Add", priority=1),
            Feature(id="2", name="Delete todo", description="Del", priority=2),
        ],
    )
    tests = agent._generate_bdd_tests(req)
    assert isinstance(tests, list)
    assert len(tests) >= 1
    for t in tests:
        assert isinstance(t, BDDTestCase)
        assert t.test_id
        assert t.feature
        assert t.scenario
        assert t.given
        assert t.when
        assert t.then
        assert t.test_code


def test_write_bdd_pytest_file(mock_llm):
    """_write_bdd_pytest_file produces runnable pytest file."""
    agent = FullCycleTestingAgent(mock_llm)
    req = Requirements(title="Todo", description="App", features=[Feature(id="1", name="Add", description="Add", priority=1)])
    bdd_tests = agent._generate_bdd_tests(req)
    ctx = ExecutionContext(user_requirement="Todo app")
    ctx.engineering_plan = None

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)
        agent._write_bdd_pytest_file(path, bdd_tests, ctx)
        test_file = path / "tests" / "test_bdd_smoke.py"
        assert test_file.exists()
        content = test_file.read_text()
        assert "def test_home_page_loads" in content
        assert "def test_bdd_" in content or "create_app" in content
