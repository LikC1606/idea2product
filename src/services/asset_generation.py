"""Asset generation step: generate images (hero, placeholder) and write to generated/static/images/."""

from pathlib import Path
from typing import Optional, Dict, Any, List

from src.utils.logger import get_logger
from src.services.image_generation_service import (
    get_image_provider,
    ImageGenerationProvider,
    GenericHTTPImageProvider,
)
from src.core.data_models import ImageSpec

logger = get_logger(__name__)


def _default_image_specs(requirements_title: str, plan_notes: str = "") -> List[ImageSpec]:
    """Build default image specs when plan has no image_specs."""
    title = requirements_title or "App"
    return [
        ImageSpec(
            id="hero",
            prompt=f"Modern, professional hero image for a web application: {title}. Clean layout, subtle gradient or abstract background, no text.",
            suggested_path="static/images/hero.png",
            role="hero",
        ),
        ImageSpec(
            id="placeholder",
            prompt="Neutral placeholder image for web content, soft gray or light pattern, minimal and professional.",
            suggested_path="static/images/placeholder.png",
            role="placeholder",
        ),
    ]


def run_asset_generation(context: Any, settings: Any) -> None:
    """
    Generate images from image_specs (or defaults) and write to context.project_path/generated/static/images/.
    Sets context.generated_image_paths (id -> path string under generated, e.g. static/images/hero.png).

    No-op if enable_image_generation is False or get_image_provider returns None.
    """
    if not getattr(settings, "enable_image_generation", False):
        return
    provider = get_image_provider(settings)
    # Optional: override with plan's external_model_spec (Stage 2 discovered API)
    plan = getattr(context, "engineering_plan", None)
    if plan and getattr(plan, "external_model_specs", None) and provider is not None:
        for spec in plan.external_model_specs:
            if getattr(spec, "capability_type", "") == "image_generation" and getattr(spec, "base_url_hint", None):
                try:
                    provider = GenericHTTPImageProvider(
                        base_url=spec.base_url_hint,
                        api_key=getattr(settings, "image_generation_api_key", None),
                        response_image_path=getattr(spec, "response_image_path", None)
                        or getattr(settings, "image_generation_response_image_path", None),
                        timeout=getattr(settings, "image_generation_timeout", 120),
                    )
                    logger.info("Using plan external_model_spec for image_generation: %s", getattr(spec, "provider_name", ""))
                except Exception as e:
                    logger.debug("Could not use external_model_spec for image: %s", e)
                break
    if provider is None:
        return
    project_path = getattr(context, "project_path", None)
    if not project_path:
        logger.warning("Asset generation skipped: no project_path in context")
        return
    generated_root = Path(project_path) / "generated"
    images_dir = generated_root / "static" / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    specs: List[ImageSpec] = []
    if plan and getattr(plan, "image_specs", None):
        specs = list(plan.image_specs)
    if not specs:
        title = getattr(context.requirements, "title", "") if getattr(context, "requirements", None) else ""
        notes = getattr(plan, "architecture_notes", "") if plan else ""
        specs = _default_image_specs(title, notes)

    generated: Dict[str, str] = {}
    for spec in specs:
        try:
            images = provider.generate(spec.prompt, n=1)
            if not images:
                logger.warning(f"Image spec '{spec.id}': no image returned")
                continue
            # suggested_path like "static/images/hero.png" -> filename "hero.png"
            filename = Path(spec.suggested_path).name
            out_path = images_dir / filename
            out_path.write_bytes(images[0])
            # Store path relative to generated root for use in templates
            rel_path = f"static/images/{filename}"
            generated[spec.id] = rel_path
            logger.info(f"Generated image: {rel_path}")
        except Exception as e:
            logger.warning(f"Image generation failed for spec '{spec.id}': {e}")
    if generated:
        context.generated_image_paths = generated
