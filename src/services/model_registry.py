"""Model Registry - Discovers and queries available LLM models."""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ModelEntry(BaseModel):
    """A registered LLM model with its capabilities and routing metadata."""

    id: str = Field(..., description="Model identifier (e.g. gpt-4o)")
    provider: str = Field(default="openai", description="Provider name")
    base_url: Optional[str] = Field(None, description="Override base URL for this model")
    capabilities: List[str] = Field(default_factory=list, description="Model capabilities: text, json, vision, code, long_context")
    roles: List[str] = Field(default_factory=list, description="Roles: primary, fallback, vision")
    cost_tier: str = Field(default="high", description="Cost tier: low, medium, high")
    max_tokens: int = Field(default=4096, description="Max output tokens")


class StageRoute(BaseModel):
    """Routing rule for a pipeline stage."""

    preferred_role: str = Field(default="primary")
    required_capabilities: List[str] = Field(default_factory=list)


class ModelRegistry:
    """
    Registry of available LLM models.

    Loads model definitions from a JSON file and provides query methods
    for discovering models by role, capability, or stage routing rules.
    """

    def __init__(self, models: List[ModelEntry] = None, stage_routing: Dict[str, StageRoute] = None):
        self.models = models or []
        self.stage_routing = stage_routing or {}

    @classmethod
    def load(cls, path: Path) -> "ModelRegistry":
        """Load registry from a JSON file. Returns empty registry if file missing."""
        if not path.exists():
            logger.info(f"Model registry not found at {path}, using defaults")
            return cls()

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            models = [ModelEntry(**m) for m in data.get("models", [])]
            routing_raw = data.get("stage_routing", {})
            stage_routing = {k: StageRoute(**v) for k, v in routing_raw.items()}

            logger.info(f"Loaded {len(models)} models from registry ({path})")
            return cls(models=models, stage_routing=stage_routing)
        except Exception as e:
            logger.warning(f"Failed to load model registry from {path}: {e}")
            return cls()

    def get_by_role(self, role: str) -> Optional[ModelEntry]:
        """Return the first model matching the given role."""
        for m in self.models:
            if role in m.roles:
                return m
        return None

    def get_by_capability(self, capability: str) -> List[ModelEntry]:
        """Return all models that have the given capability."""
        return [m for m in self.models if capability in m.capabilities]

    def get_by_id(self, model_id: str) -> Optional[ModelEntry]:
        """Return a model by its exact id."""
        for m in self.models:
            if m.id == model_id:
                return m
        return None

    def get_stage_route(self, stage: int, requires_vision: bool = False) -> Optional[StageRoute]:
        """Get the routing rule for a pipeline stage."""
        key = f"{stage}_vision" if requires_vision else str(stage)
        return self.stage_routing.get(key)

    def is_empty(self) -> bool:
        return len(self.models) == 0
