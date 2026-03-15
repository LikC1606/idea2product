"""Tests for LLM retry classification and retry budget behavior."""

from types import SimpleNamespace

import pytest

from src.core.exceptions import TransientLLMError, PermanentLLMError
from src.services.llm_service import LLMService


def _ok_response(text: str):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=text))],
        usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1, total_tokens=2),
    )


def test_generate_retries_transient_timeout_then_succeeds():
    svc = LLMService(api_key="sk-test", max_retries=2)
    calls = {"n": 0}

    def _create(**kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise TimeoutError("timeout")
        return _ok_response("ok")

    svc.client.chat.completions.create = _create
    out = svc.generate("hello")
    assert out == "ok"
    assert calls["n"] == 2


def test_generate_retry_budget_exceeded_fails_fast():
    svc = LLMService(api_key="sk-test", max_retries=5)

    def _create(**kwargs):
        raise TimeoutError("timeout")

    svc.client.chat.completions.create = _create
    with pytest.raises(PermanentLLMError):
        svc.generate("hello", retry_budget_seconds=0.01)


def test_generate_marks_non_transient_as_permanent(monkeypatch):
    svc = LLMService(api_key="sk-test", max_retries=1)

    def _create(**kwargs):
        raise TimeoutError("timeout")

    svc.client.chat.completions.create = _create
    monkeypatch.setattr("src.services.llm_service._is_transient_error", lambda e: False)
    with pytest.raises(PermanentLLMError):
        svc.generate("hello")
