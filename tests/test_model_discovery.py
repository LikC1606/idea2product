"""Tests for model discovery and selection (ModelRegistry, ModelSelector, LLMService.with_model)."""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.services.model_registry import ModelRegistry, ModelEntry, StageRoute
from src.services.model_selector import ModelSelector
from src.services.provider_adapter import detect_provider, get_adapter, ProviderAdapter, OpenRouterAdapter, AzureAdapter


# ---------------------------------------------------------------------------
# ModelRegistry
# ---------------------------------------------------------------------------

def _sample_registry_data():
    return {
        "models": [
            {"id": "gpt-4o", "provider": "openai", "capabilities": ["text", "json", "vision", "code", "long_context"], "roles": ["primary", "vision"], "cost_tier": "high", "max_tokens": 8000},
            {"id": "gpt-4o-mini", "provider": "openai", "capabilities": ["text", "json"], "roles": ["fallback"], "cost_tier": "low", "max_tokens": 4096},
        ],
        "stage_routing": {
            "1": {"preferred_role": "primary", "required_capabilities": ["text"]},
            "2": {"preferred_role": "primary", "required_capabilities": ["json"]},
            "4_vision": {"preferred_role": "vision", "required_capabilities": ["vision"]},
        },
    }


def test_registry_load_from_file(tmp_path):
    p = tmp_path / "registry.json"
    p.write_text(json.dumps(_sample_registry_data()), encoding="utf-8")
    reg = ModelRegistry.load(p)
    assert len(reg.models) == 2
    assert reg.models[0].id == "gpt-4o"
    assert not reg.is_empty()


def test_registry_load_missing_file(tmp_path):
    reg = ModelRegistry.load(tmp_path / "nonexistent.json")
    assert reg.is_empty()


def test_registry_get_by_role():
    data = _sample_registry_data()
    models = [ModelEntry(**m) for m in data["models"]]
    reg = ModelRegistry(models=models)
    assert reg.get_by_role("primary").id == "gpt-4o"
    assert reg.get_by_role("fallback").id == "gpt-4o-mini"
    assert reg.get_by_role("nonexistent") is None


def test_registry_get_by_capability():
    data = _sample_registry_data()
    models = [ModelEntry(**m) for m in data["models"]]
    reg = ModelRegistry(models=models)
    vision_models = reg.get_by_capability("vision")
    assert len(vision_models) == 1
    assert vision_models[0].id == "gpt-4o"


def test_registry_get_by_id():
    data = _sample_registry_data()
    models = [ModelEntry(**m) for m in data["models"]]
    reg = ModelRegistry(models=models)
    assert reg.get_by_id("gpt-4o-mini").cost_tier == "low"
    assert reg.get_by_id("nonexistent") is None


def test_registry_stage_route():
    data = _sample_registry_data()
    routing = {k: StageRoute(**v) for k, v in data["stage_routing"].items()}
    reg = ModelRegistry(stage_routing=routing)
    route = reg.get_stage_route(1)
    assert route.preferred_role == "primary"
    assert reg.get_stage_route(4, requires_vision=True).required_capabilities == ["vision"]
    assert reg.get_stage_route(99) is None


# ---------------------------------------------------------------------------
# ModelSelector
# ---------------------------------------------------------------------------

def _build_selector():
    data = _sample_registry_data()
    models = [ModelEntry(**m) for m in data["models"]]
    routing = {k: StageRoute(**v) for k, v in data["stage_routing"].items()}
    reg = ModelRegistry(models=models, stage_routing=routing)
    return ModelSelector(registry=reg, default_model="gpt-4o", default_vlm_model="gpt-4o")


def test_selector_stage_1_returns_primary():
    sel = _build_selector()
    entry = sel.select(stage=1)
    assert entry.id == "gpt-4o"


def test_selector_stage_4_vision():
    sel = _build_selector()
    entry = sel.select(stage=4, requires_vision=True)
    assert "vision" in entry.capabilities


def test_selector_empty_registry_returns_default():
    sel = ModelSelector(registry=ModelRegistry(), default_model="my-default")
    entry = sel.select(stage=2)
    assert entry.id == "my-default"


def test_selector_select_by_id():
    sel = _build_selector()
    entry = sel.select_by_id("gpt-4o-mini")
    assert entry.id == "gpt-4o-mini"
    entry = sel.select_by_id("nonexistent")
    assert entry.id == "gpt-4o"


# ---------------------------------------------------------------------------
# ProviderAdapter detection
# ---------------------------------------------------------------------------

def test_detect_provider_openai():
    assert detect_provider("https://api.openai.com/v1") == "openai"


def test_detect_provider_openrouter():
    assert detect_provider("https://openrouter.ai/api/v1") == "openrouter"


def test_detect_provider_azure():
    assert detect_provider("https://myinstance.cognitiveservices.azure.com/") == "azure"


def test_get_adapter_types():
    assert isinstance(get_adapter("openai"), ProviderAdapter)
    assert isinstance(get_adapter("openrouter"), OpenRouterAdapter)
    assert isinstance(get_adapter("azure"), AzureAdapter)


# ---------------------------------------------------------------------------
# LLMService.with_model
# ---------------------------------------------------------------------------

def test_with_model_returns_new_instance():
    from src.services.llm_service import LLMService
    svc = LLMService(api_key="test-key", model="gpt-4o", base_url="https://api.openai.com/v1")
    new_svc = svc.with_model("gpt-4o-mini")
    assert new_svc.model == "gpt-4o-mini"
    assert new_svc is not svc
    assert new_svc.api_key == "test-key"
    assert new_svc.base_url == svc.base_url


def test_with_model_different_base_url():
    from src.services.llm_service import LLMService
    svc = LLMService(api_key="test-key", model="gpt-4o", base_url="https://api.openai.com/v1")
    new_svc = svc.with_model("openai/gpt-4o", base_url="https://openrouter.ai/api/v1")
    assert new_svc.model == "openai/gpt-4o"
    assert new_svc.base_url == "https://openrouter.ai/api/v1"
