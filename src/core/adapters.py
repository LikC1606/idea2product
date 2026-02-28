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
)
from src.utils.skeleton_builder import generate_minimal_pyi_from_interface_specs
from src.utils.logger import get_logger

logger = get_logger(__name__)


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
    default_file_structure_fn=None,
) -> EngineeringPlan:
    """
    Normalize and validate Stage 2 outputs into EngineeringPlan.

    Applies fallbacks: when pyi_stubs is empty but interface_specs exist,
    generates minimal pyi stubs. When file_structure is empty, uses default.
    """
    effective_file_structure = list(file_structure or [])
    if not effective_file_structure and default_file_structure_fn and tasks:
        effective_file_structure = default_file_structure_fn(tasks)
        logger.info("engineering_plan_from_stage2: used default file_structure")

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
    )
