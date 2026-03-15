"""Lightweight plan completeness checks before Stage 3.

Validates that EngineeringPlan has minimal structure for code generation
(entry point, pyi coverage). Used by Orchestrator after Stage 2; failures
produce warnings only and do not block Stage 3.
"""

from typing import List, Tuple

from src.core.data_models import EngineeringPlan


_ENTRY_POINTS = ("app.py", "main.py", "server.py", "run.py", "manage.py")


def validate_plan_completeness(plan: EngineeringPlan) -> Tuple[bool, List[str]]:
    """Run light checks on the engineering plan. Does not modify plan.

    Returns:
        (all_passed, list of warning messages)
    """
    warnings: List[str] = []
    if not plan.file_structure:
        warnings.append("Plan has no file_structure entries; Stage 3 may produce minimal output.")
        return False, warnings

    paths = [f.path.replace("\\", "/").strip("/") for f in plan.file_structure]
    # Entry point: top-level app.py / main.py etc.
    has_entry = any(
        p == name or p.endswith("/" + name)
        for p in paths
        for name in _ENTRY_POINTS
    )
    if not has_entry:
        warnings.append(
            "Plan file_structure has no entry point (app.py, main.py, server.py, run.py, or manage.py); "
            "generated app may not be runnable."
        )

    # If we have app/ modules, pyi_stubs or interface_specs should not be empty (optional but recommended)
    has_app_modules = any(p.startswith("app/") or p == "app" for p in paths)
    if has_app_modules and not plan.pyi_stubs and not plan.interface_specs:
        warnings.append(
            "Plan has app/ modules but no pyi_stubs or interface_specs; "
            "CodeGen may fall back to minimal stubs."
        )

    all_passed = len(warnings) == 0
    return all_passed, warnings
