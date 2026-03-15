"""Adapters for normalizing and validating pipeline stage outputs.

Centralizes fallback logic and format normalization so Orchestrator
does not depend on raw agent output structure.
"""

from typing import Dict, List, Any, Optional

from src.core.data_models import (
    EngineeringPlan,
    Requirements,
    FileSpec,
    BDDTestCase,
    ExternalModelSpec,
    ProductType,
)
from src.utils.skeleton_builder import generate_minimal_pyi_from_interface_specs
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _minimal_file_structure() -> List[FileSpec]:
    """Fallback file structure when Stage 2 outputs are incomplete."""
    return [
        FileSpec(path="app.py", purpose="Application entry point", dependencies=[]),
        FileSpec(path="app/__init__.py", purpose="Flask app factory and route wiring", dependencies=[]),
        FileSpec(path="templates/index.html", purpose="Main UI template", dependencies=["app/__init__.py"]),
        FileSpec(path="requirements.txt", purpose="Runtime dependencies", dependencies=[]),
    ]


def engineering_plan_from_stage2(
    *,
    tasks: List[Any],
    algorithms: Dict[str, Any],
    file_structure: List[Any],
    interface_specs: List[Any],
    api_specs: Dict[str, Any],
    pyi_stubs: Dict[str, str],
    requirements: Requirements,
    bdd_test_cases: Optional[List[BDDTestCase]] = None,
    external_model_specs: Optional[List[ExternalModelSpec]] = None,
    default_file_structure_fn=None,
) -> EngineeringPlan:
    """
    Normalize and validate Stage 2 outputs into EngineeringPlan.

    Applies fallbacks: when pyi_stubs is empty but interface_specs exist,
    generates minimal pyi stubs. When file_structure is empty, uses default.
    """
    if requirements is None:
        raise ValueError("engineering_plan_from_stage2 requires non-None requirements")
    if tasks is not None and not isinstance(tasks, list):
        raise TypeError("tasks must be a list")
    if algorithms is not None and not isinstance(algorithms, dict):
        raise TypeError("algorithms must be a dict")

    effective_file_structure = list(file_structure or [])
    if not effective_file_structure and default_file_structure_fn:
        try:
            effective_file_structure = default_file_structure_fn(tasks or [])
        except Exception as ex:
            logger.warning("engineering_plan_from_stage2: default_file_structure_fn failed: %s", ex)
        if effective_file_structure:
            logger.info("engineering_plan_from_stage2: used default file_structure")
    if not effective_file_structure:
        effective_file_structure = _minimal_file_structure()
        logger.info("engineering_plan_from_stage2: used minimal fallback file_structure")

    effective_pyi_stubs = dict(pyi_stubs or {})
    if not effective_pyi_stubs and (interface_specs or effective_file_structure):
        effective_pyi_stubs = generate_minimal_pyi_from_interface_specs(
            interface_specs or [],
            effective_file_structure or [],
        )
        if effective_pyi_stubs:
            logger.info(
                "engineering_plan_from_stage2: generated %d minimal pyi_stubs from interface_specs/file_structure",
                len(effective_pyi_stubs),
            )

    dependencies: set = {"flask"}
    for alg in (algorithms or {}).values():
        for lib in getattr(alg, "libraries", []) or []:
            if not lib:
                continue
            lib_normalized = lib.strip()
            if lib_normalized.lower() in {"dict", "list", "str", "int", "standard"}:
                continue
            dependencies.add(lib_normalized)

    ui_guidelines = None
    if isinstance(api_specs, dict):
        maybe_ui = api_specs.get("ui_guidelines")
        if isinstance(maybe_ui, dict):
            ui_guidelines = maybe_ui

    product_type = getattr(requirements, "product_type", None)
    if product_type is None:
        product_type = ProductType.WEB

    return EngineeringPlan(
        tasks=tasks,
        algorithms=algorithms,
        file_structure=effective_file_structure,
        interface_specs=interface_specs or [],
        dependencies=sorted(dependencies),
        architecture_notes=f"Web application: {requirements.title}",
        api_specs=api_specs or {},
        pyi_stubs=effective_pyi_stubs,
        bdd_test_cases=bdd_test_cases or [],
        external_model_specs=external_model_specs or [],
        ui_guidelines=ui_guidelines,
        product_type=product_type,
    )
