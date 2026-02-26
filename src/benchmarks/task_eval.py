"""Task division quality evaluation metrics.

Provides standalone functions to assess the quality of task division output
without requiring LLM calls — purely structural/coverage analysis.
"""

from typing import Dict, List, Any
from src.core.data_models import Task, Requirements


def evaluate_task_division(tasks: List[Task], requirements: Requirements) -> Dict[str, Any]:
    """Evaluate task division quality across multiple dimensions.

    Returns a dict with:
        - task_count: number of tasks
        - feature_coverage: ratio of features mentioned in at least one task description
        - has_backend_tasks: whether backend tasks exist
        - has_frontend_tasks: whether frontend tasks exist
        - dependency_validity: whether dependencies form a valid DAG (no cycles, no dangling refs)
        - orphan_tasks: tasks with no dependents and no dependencies (potential isolation)
        - issues: list of human-readable issue strings
    """
    metrics: Dict[str, Any] = {
        "task_count": len(tasks),
        "feature_coverage": 0.0,
        "has_backend_tasks": False,
        "has_frontend_tasks": False,
        "dependency_validity": True,
        "orphan_tasks": [],
        "issues": [],
    }

    if not tasks:
        metrics["issues"].append("No tasks generated")
        metrics["dependency_validity"] = False
        return metrics

    task_ids = {t.id for t in tasks}
    task_types = {t.type.value for t in tasks}
    all_descriptions = " ".join(t.description.lower() + " " + t.name.lower() for t in tasks)

    metrics["has_backend_tasks"] = "backend" in task_types
    metrics["has_frontend_tasks"] = "frontend" in task_types

    # Feature coverage: check if each feature name appears in any task description
    covered = 0
    for f in requirements.features:
        feature_terms = f.name.lower().split()
        if any(term in all_descriptions for term in feature_terms if len(term) > 2):
            covered += 1
    metrics["feature_coverage"] = covered / len(requirements.features) if requirements.features else 1.0

    if metrics["feature_coverage"] < 1.0:
        uncovered = []
        for f in requirements.features:
            feature_terms = f.name.lower().split()
            if not any(term in all_descriptions for term in feature_terms if len(term) > 2):
                uncovered.append(f.name)
        metrics["issues"].append(f"Uncovered features: {uncovered}")

    # Dependency validity: check for dangling references and cycles
    for t in tasks:
        for dep in t.dependencies:
            if dep not in task_ids:
                metrics["dependency_validity"] = False
                metrics["issues"].append(f"Task {t.id} depends on non-existent task {dep}")

    if _has_cycle(tasks):
        metrics["dependency_validity"] = False
        metrics["issues"].append("Dependency graph contains a cycle")

    # Orphan detection
    all_deps = set()
    for t in tasks:
        all_deps.update(t.dependencies)
    depended_on = all_deps & task_ids
    for t in tasks:
        if not t.dependencies and t.id not in depended_on and len(tasks) > 1:
            metrics["orphan_tasks"].append(t.id)

    if not metrics["has_backend_tasks"]:
        metrics["issues"].append("No backend tasks found")
    if not metrics["has_frontend_tasks"]:
        metrics["issues"].append("No frontend tasks found")

    return metrics


def _has_cycle(tasks: List[Task]) -> bool:
    """Detect cycles in the task dependency graph using DFS."""
    graph: Dict[str, List[str]] = {t.id: list(t.dependencies) for t in tasks}
    visited: set = set()
    rec_stack: set = set()

    def dfs(node: str) -> bool:
        visited.add(node)
        rec_stack.add(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True
        rec_stack.discard(node)
        return False

    for t in tasks:
        if t.id not in visited:
            if dfs(t.id):
                return True
    return False
