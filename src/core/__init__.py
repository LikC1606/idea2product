"""Core infrastructure for the Idea2Product system."""

from .agent_base import AgentBase
from .context import ExecutionContext
from .data_models import (
    Feature,
    Requirements,
    Task,
    Algorithm,
    EngineeringPlan,
    CodeFile,
    CodeRepository,
    TestResult,
    ValidatedProject,
)


# Lazy import to avoid circular import
# orchestrator imports planning_agents which imports data_models
def __getattr__(name):
    if name == "Orchestrator":
        from .orchestrator import Orchestrator
        return Orchestrator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "AgentBase",
    "ExecutionContext",
    "Feature",
    "Requirements",
    "Task",
    "Algorithm",
    "EngineeringPlan",
    "CodeFile",
    "CodeRepository",
    "TestResult",
    "ValidatedProject",
]
