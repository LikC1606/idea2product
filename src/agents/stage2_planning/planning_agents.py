"""Stage 2 Planning Agents."""

from typing import Dict, Any, List
from src.core.data_models import Requirements, EngineeringPlan, Task, Algorithm, FileSpec, TaskType, TaskComplexity
from src.core.context import ExecutionContext
from src.services.llm_service import LLMService
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TaskDivisionAgent:
    """Stage 2 Agent 1: Divides requirements into atomic tasks."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def execute(self, requirements: Requirements) -> List[Task]:
        """Divide requirements into tasks."""
        prompt = f"""
Based on the following requirements, divide them into atomic tasks.
Return a JSON array of tasks with this structure:
[
    {{
        "id": "T1",
        "name": "Task name",
        "description": "What this task does",
        "type": "frontend|backend|testing|deployment|database",
        "dependencies": ["T0 or empty"],
        "priority": 1-5,
        "complexity": "low|medium|high"
    }}
]

Requirements:
Title: {requirements.title}
Description: {requirements.description}
Features: {", ".join(f.name for f in requirements.features)}

Respond with valid JSON array only.
"""

        try:
            result = self.llm_service.generate_json(prompt)
            tasks = []
            for t in result:
                complexity = t.get("complexity", "medium")
                if complexity not in [c.value for c in TaskComplexity]:
                    complexity = "medium"
                tasks.append(Task(
                    id=t["id"],
                    name=t["name"],
                    description=t["description"],
                    type=TaskType(t.get("type", "frontend")),
                    dependencies=t.get("dependencies", []),
                    priority=t.get("priority", 3),
                    estimated_complexity=TaskComplexity(complexity)
                ))
            return tasks
        except Exception as e:
            logger.warning(f"LLM task division failed: {e}")
            return _fallback_tasks(requirements)


class AlgorithmAnalysisAgent:
    """Stage 2 Agent 2: Analyzes algorithms for each task."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def execute(self, tasks: List[Task]) -> Dict[str, Algorithm]:
        """Analyze algorithms for each task."""
        prompt = f"""
For each task, provide the algorithm/implementation approach.
Return a JSON object with task ID as key:
{{
    "T1": {{
        "algorithm_type": "CRUD|Algorithm pattern type",
        "implementation_approach": "How to implement",
        "libraries": ["list of libraries"],
        "data_structures": ["list of data structures"],
        "notes": "additional notes"
    }}
}}

Tasks: {", ".join(f"{t.id}: {t.name}" for t in tasks)}

Respond with valid JSON only.
"""

        try:
            result = self.llm_service.generate_json(prompt)
            algorithms = {}
            for task_id, alg in result.items():
                algorithms[task_id] = Algorithm(
                    task_id=task_id,
                    algorithm_type=alg.get("algorithm_type", "standard"),
                    implementation_approach=alg.get("implementation_approach", "Standard implementation"),
                    libraries=alg.get("libraries", []),
                    data_structures=alg.get("data_structures", []),
                    notes=alg.get("notes")
                )
            return algorithms
        except Exception as e:
            logger.warning(f"LLM algorithm analysis failed: {e}")
            return _fallback_algorithms(tasks)


class SchemePlanningAgent:
    """Stage 2 Agent 3: Creates file structure and dependencies."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def execute(self, requirements: Requirements, tasks: List[Task]) -> List[FileSpec]:
        """Create file structure specification."""
        prompt = f"""
Create a file structure for the application.
Return a JSON array of files:
[
    {{
        "path": "relative/path/to/file.py",
        "purpose": "What this file does",
        "dependencies": ["other files it imports"],
        "related_tasks": ["T1"]
    }}
]

Requirements: {requirements.title}
Tasks: {", ".join(t.name for t in tasks)}

Respond with valid JSON array only.
"""

        try:
            result = self.llm_service.generate_json(prompt)
            files = []
            for f in result:
                files.append(FileSpec(
                    path=f["path"],
                    purpose=f.get("purpose", ""),
                    dependencies=f.get("dependencies", []),
                    related_tasks=f.get("related_tasks", [])
                ))
            return files
        except Exception as e:
            logger.warning(f"LLM scheme planning failed: {e}")
            return _fallback_files(requirements)


# Fallback methods
def _fallback_tasks(requirements: Requirements) -> List[Task]:
    """Create basic tasks from requirements."""
    tasks = []

    # Always add frontend task
    tasks.append(Task(
        id="T1",
        name="Frontend Development",
        description="Create the user interface",
        type=TaskType.FRONTEND,
        dependencies=[],
        priority=1,
        estimated_complexity=TaskComplexity.MEDIUM
    ))

    # Add backend if complex
    if len(requirements.features) > 3:
        tasks.append(Task(
            id="T2",
            name="Backend Development",
            description="Create API endpoints and logic",
            type=TaskType.BACKEND,
            dependencies=["T1"],
            priority=2,
            estimated_complexity=TaskComplexity.MEDIUM
        ))

    # Always add testing
    tasks.append(Task(
        id="T3",
        name="Testing",
        description="Write tests for the application",
        type=TaskType.TESTING,
        dependencies=["T1"],
        priority=3,
        estimated_complexity=TaskComplexity.LOW
    ))

    return tasks


def _fallback_algorithms(tasks: List[Task]) -> Dict[str, Algorithm]:
    """Create basic algorithms."""
    algorithms = {}
    for task in tasks:
        algorithms[task.id] = Algorithm(
            task_id=task.id,
            algorithm_type="standard",
            implementation_approach="Standard implementation for this task type",
            libraries=["flask", "requests"],
            data_structures=["dict", "list"],
            notes="Basic implementation"
        )
    return algorithms


def _fallback_files(requirements: Requirements) -> List[FileSpec]:
    """Create basic file structure."""
    files = [
        FileSpec(
            path="app.py",
            purpose="Main application entry point",
            dependencies=[],
            related_tasks=["T1", "T2"]
        ),
        FileSpec(
            path="templates/index.html",
            purpose="Main HTML template",
            dependencies=[],
            related_tasks=["T1"]
        ),
        FileSpec(
            path="static/style.css",
            purpose="Stylesheet",
            dependencies=[],
            related_tasks=["T1"]
        ),
    ]

    if len(requirements.features) > 3:
        files.append(FileSpec(
            path="routes.py",
            purpose="API routes",
            dependencies=["app.py"],
            related_tasks=["T2"]
        ))

    return files
