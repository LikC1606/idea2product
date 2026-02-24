"""Tests for Stage 1 - InteractionAgent (reply_in_chat, conversation_to_requirements, merge_requirements)."""

import pytest

from src.core.data_models import Requirements, Feature
from src.agents.stage1_requirements.interaction_agent import InteractionAgent


class MockLLMService:
    def __init__(self, generate_return=None, generate_json_return=None):
        self.generate_return = generate_return or "Mocked reply"
        self.generate_json_return = generate_json_return or {
            "title": "Test App",
            "description": "A test application",
            "features": [
                {"id": "f1", "name": "Feature 1", "description": "First feature", "priority": 1},
            ],
            "constraints": [],
            "target_users": "Users",
            "data_requirements": "None",
        }

    def generate(self, prompt: str, **kwargs) -> str:
        return self.generate_return

    def generate_json(self, prompt: str):
        return self.generate_json_return


@pytest.fixture
def mock_llm():
    return MockLLMService()


@pytest.fixture
def agent(mock_llm):
    return InteractionAgent(mock_llm)


def test_reply_in_chat_empty_messages(agent):
    reply = agent.reply_in_chat([])
    assert isinstance(reply, str)
    assert len(reply) > 0
    assert "描述" in reply or "应用" in reply or "功能" in reply


def test_reply_in_chat_returns_llm_reply(agent, mock_llm):
    mock_llm.generate_return = "I'll help you build that."
    reply = agent.reply_in_chat([
        {"role": "user", "content": "I want a todo app"},
    ])
    assert reply == "I'll help you build that."


def test_reply_in_chat_fallback_on_exception(agent, mock_llm):
    def raise_err(*a, **k):
        raise RuntimeError("API error")
    mock_llm.generate = raise_err
    reply = agent.reply_in_chat([{"role": "user", "content": "Hi"}])
    assert isinstance(reply, str)
    assert "已收到" in reply or "后台" in reply


def test_conversation_to_requirements_returns_requirements(agent, mock_llm):
    mock_llm.generate_json_return = {
        "title": "Todo App",
        "description": "A simple todo list",
        "features": [
            {"id": "f1", "name": "Add task", "description": "Add a task", "priority": 1},
            {"id": "f2", "name": "Delete task", "description": "Delete a task", "priority": 2},
        ],
        "constraints": ["Flask"],
        "target_users": "Everyone",
        "data_requirements": "In-memory list",
    }
    messages = [
        {"role": "user", "content": "Build a todo app"},
        {"role": "assistant", "content": "Sure."},
    ]
    req = agent.conversation_to_requirements(messages)
    assert isinstance(req, Requirements)
    assert req.title == "Todo App"
    assert req.description == "A simple todo list"
    assert len(req.features) == 2
    assert req.features[0].name == "Add task"
    assert req.constraints == ["Flask"]


def test_conversation_to_requirements_fallback_on_exception(agent, mock_llm):
    def raise_err(*a, **k):
        raise RuntimeError("JSON error")
    mock_llm.generate_json = raise_err
    messages = [{"role": "user", "content": "Weather app"}]
    req = agent.conversation_to_requirements(messages)
    assert isinstance(req, Requirements)
    assert req.title == "Generated Application" or "weather" in req.description.lower() or len(req.features) >= 1


def test_merge_requirements_returns_updated_requirements(agent, mock_llm):
    existing = Requirements(
        title="Todo App",
        description="Todo list",
        features=[
            Feature(id="f1", name="Add", description="Add task", priority=1),
        ],
        constraints=[],
        target_users=None,
        data_requirements=None,
    )
    mock_llm.generate_json_return = {
        "title": "Todo App",
        "description": "Todo list with due dates",
        "features": [
            {"id": "f1", "name": "Add", "description": "Add task", "priority": 1},
            {"id": "f2", "name": "Due date", "description": "Set due date", "priority": 2},
        ],
        "constraints": [],
        "target_users": None,
        "data_requirements": None,
    }
    merged = agent.merge_requirements(existing, "Add due dates for each task")
    assert isinstance(merged, Requirements)
    assert merged.title == "Todo App"
    assert len(merged.features) == 2
    assert merged.description == "Todo list with due dates"


def test_merge_requirements_returns_existing_on_exception(agent, mock_llm):
    existing = Requirements(
        title="My App",
        description="Desc",
        features=[],
        constraints=[],
        target_users=None,
        data_requirements=None,
    )
    def raise_err(*a, **k):
        raise RuntimeError("Merge failed")
    mock_llm.generate_json = raise_err
    merged = agent.merge_requirements(existing, "Add feature X")
    assert merged is existing
    assert merged.title == "My App"
