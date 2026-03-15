"""Model Selector - Chooses the best model for each pipeline stage and task."""

from typing import Optional
from src.services.model_registry import ModelRegistry, ModelEntry
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ModelSelector:
    """
    Selects models for each pipeline stage based on registry routing rules.

    When the registry is empty or no match is found, falls back to the
    default models from Settings (openai_model / openai_vlm_model).
    """

    def __init__(self, registry: ModelRegistry, default_model: str = "gpt-4o", default_vlm_model: str = "gpt-4o"):
        self.registry = registry
        self.default_model = default_model
        self.default_vlm_model = default_vlm_model

    def select(
        self,
        stage: int,
        task_type: Optional[str] = None,
        requires_vision: bool = False,
        prefer_fast: bool = False,
        product_type: Optional[str] = None,
    ) -> ModelEntry:
        """
        Select a model for a given pipeline stage.

        Args:
            stage: Pipeline stage number (1-4)
            task_type: Optional task type hint (e.g. 'frontend', 'backend')
            requires_vision: Whether vision/VLM capability is needed
            prefer_fast: Prefer fallback/fast model when not requiring vision
            product_type: Optional product type (web, pdf, video, audio, app) for type-specific routing

        Returns:
            ModelEntry for the selected model
        """
        if self.registry.is_empty():
            return self._default_entry(requires_vision)

        if prefer_fast and not requires_vision:
            fast = self.registry.get_by_role("fallback")
            if fast:
                logger.debug(f"Stage {stage}: using fast model {fast.id}")
                return fast

        route = self.registry.get_stage_route(
            stage, requires_vision=requires_vision, product_type=product_type
        )
        if route is None:
            return self._default_entry(requires_vision)

        # Try to find a model matching the preferred role
        candidate = self.registry.get_by_role(route.preferred_role)
        if candidate and self._has_required_capabilities(candidate, route.required_capabilities):
            logger.debug(f"Stage {stage} (vision={requires_vision}): selected {candidate.id} via role '{route.preferred_role}'")
            return candidate

        # Fallback: find any model with required capabilities
        if route.required_capabilities:
            for m in self.registry.models:
                if self._has_required_capabilities(m, route.required_capabilities):
                    logger.debug(
                        "Stage %s: selected %s via all-capabilities fallback %s",
                        stage,
                        m.id,
                        route.required_capabilities,
                    )
                    return m

        # Ultimate fallback
        logger.debug(f"Stage {stage}: no matching model, using default")
        return self._default_entry(requires_vision)

    def select_by_id(self, model_id: str) -> ModelEntry:
        """Select a specific model by id, falling back to default if not found."""
        entry = self.registry.get_by_id(model_id)
        if entry:
            return entry
        return self._default_entry(False)

    def _has_required_capabilities(self, model: ModelEntry, required: list) -> bool:
        if not required:
            return True
        return all(cap in model.capabilities for cap in required)

    def _default_entry(self, requires_vision: bool = False) -> ModelEntry:
        """Build a ModelEntry from the default settings values."""
        model_id = self.default_vlm_model if requires_vision else self.default_model
        return ModelEntry(
            id=model_id,
            provider="openai",
            capabilities=["text", "json", "code", "long_context"] + (["vision"] if requires_vision else []),
            roles=["primary"] + (["vision"] if requires_vision else []),
            cost_tier="high",
            max_tokens=8000,
        )
