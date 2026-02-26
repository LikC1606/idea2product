"""Pydantic models for validating LLM JSON responses across agents."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class ReviewIssue(BaseModel):
    task_id: Optional[str] = None
    endpoint: Optional[str] = None
    issue_type: str = ""
    description: str = ""
    suggestion: str = ""


class RefinedTask(BaseModel):
    id: str
    name: str
    description: str = ""
    type: str = "frontend"
    priority: int = Field(default=3, ge=1, le=5)
    estimated_complexity: str = "medium"
    dependencies: List[str] = Field(default_factory=list)

    @field_validator("estimated_complexity")
    @classmethod
    def _validate_complexity(cls, v: str) -> str:
        allowed = {"low", "medium", "high"}
        return v if v in allowed else "medium"


class TaskReviewResponse(BaseModel):
    issues: List[ReviewIssue] = Field(default_factory=list)
    refined_tasks: List[RefinedTask] = Field(default_factory=list)


class ApiReviewResponse(BaseModel):
    issues: List[ReviewIssue] = Field(default_factory=list)
    refined_api_specs: Dict = Field(default_factory=dict)


class AlgorithmEntry(BaseModel):
    implementation_approach: str = "Standard implementation"
    notes: Optional[str] = None


class RequirementAnalysis(BaseModel):
    needs_clarification: bool = True
    questions: List[Dict] = Field(default_factory=list)
    improvements: List[Dict] = Field(default_factory=list)


class ExtractedRequirements(BaseModel):
    title: str = "Generated Application"
    description: str = ""
    features: List[Dict] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    target_users: Optional[str] = None
    data_requirements: Optional[str] = None


def validate_response(data: dict, model_class: type[BaseModel]) -> BaseModel:
    """Validate a dict against a Pydantic model, returning a model instance.

    Raises ``pydantic.ValidationError`` on schema mismatch.
    """
    return model_class.model_validate(data)
