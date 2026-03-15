"""Execution context for managing state across agents."""

from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
import uuid

from .data_models import (
    Requirements,
    Task,
    Algorithm,
    EngineeringPlan,
    CodeRepository,
    TestResult,
    ValidatedProject,
    ValidationStatus,
)


class ExecutionContext(BaseModel):
    """
    Shared execution context passed through all stages.

    This class maintains all intermediate results and state as the system
    progresses through the 4 stages of development.
    """

    # Project identification
    project_id: str = Field(default_factory=lambda: f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Original user input
    user_requirement: str = Field(..., description="Original user requirement string")

    # Optional: product type and user-selected model (override registry routing)
    product_type: Optional[str] = Field(None, description="Output artifact type: web, pdf, video, audio, app")
    model_id: Optional[str] = Field(None, description="User-selected model id; overrides stage/product_type routing when set")

    # Stage 1: Requirements
    requirements: Optional[Requirements] = None

    # Stage 2: Planning
    tasks: Optional[List[Task]] = None
    algorithms: Optional[Dict[str, Algorithm]] = None
    engineering_plan: Optional[EngineeringPlan] = None

    # Stage 3: Code Generation
    code_repository: Optional[CodeRepository] = None
    # Optional write-back from Orchestrator after prefetch (for observability / future single-context calls)
    memory_context: Optional[str] = None
    mining_by_task: Optional[Dict[str, str]] = None
    # Optional write-back from AssetGeneration: id -> path string under generated/static/images/
    generated_image_paths: Optional[Dict[str, str]] = None

    # Stage 4: Validation
    test_results: Optional[TestResult] = None
    validation_status: ValidationStatus = ValidationStatus.NOT_STARTED
    fix_attempts: int = 0

    # Final output
    validated_project: Optional[ValidatedProject] = None

    # Metadata
    current_stage: int = Field(default=1, ge=1, le=4)
    project_path: Optional[Path] = None
    error_log: List[str] = Field(default_factory=list)
    run_id: str = Field(default_factory=lambda: f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}")
    attempt: int = 1
    input_fingerprint: Optional[str] = None
    execution_signature: Optional[str] = None
    resume_from_stage: Optional[int] = None
    stage_state: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def update_stage(self, stage: int) -> None:
        """
        Update the current stage.

        Args:
            stage: New stage number (1-4)
        """
        self.current_stage = stage
        self.updated_at = datetime.now()

    def add_error(self, error: str) -> None:
        """
        Add an error to the log.

        Args:
            error: Error message
        """
        self.error_log.append(f"[{datetime.now().isoformat()}] {error}")
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert context to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionContext":
        """
        Create context from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            ExecutionContext instance
        """
        return cls.model_validate(data)

    def get_stage_name(self) -> str:
        """
        Get the name of the current stage.

        Returns:
            Stage name
        """
        stage_names = {
            1: "Requirements",
            2: "Planning",
            3: "Code Generation",
            4: "Validation",
        }
        return stage_names.get(self.current_stage, "Unknown")

    def is_stage_complete(self, stage: int) -> bool:
        """
        Check if a stage has been completed.

        Args:
            stage: Stage number to check

        Returns:
            True if stage is complete
        """
        if stage == 1:
            return self.requirements is not None
        elif stage == 2:
            return self.engineering_plan is not None
        elif stage == 3:
            return self.code_repository is not None
        elif stage == 4:
            return self.validated_project is not None
        return False

    def get_progress_summary(self) -> str:
        """
        Get a summary of progress through stages.

        Returns:
            Human-readable progress summary
        """
        stages = []
        for i in range(1, 5):
            status = "[OK]" if self.is_stage_complete(i) else "[ ]"
            current = " (current)" if i == self.current_stage else ""
            stages.append(f"{status} Stage {i}: {self.get_stage_name()}{current}")
        return "\n".join(stages)
