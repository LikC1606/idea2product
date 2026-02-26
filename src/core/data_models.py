"""Data models for the Idea2Product system."""

from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class TaskType(str, Enum):
    """Type of task."""

    FRONTEND = "frontend"
    BACKEND = "backend"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    DATABASE = "database"


class TaskComplexity(str, Enum):
    """Complexity level of a task."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ValidationStatus(str, Enum):
    """Status of code validation."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    FIXED = "fixed"


class ErrorType(str, Enum):
    """Type of error encountered during testing."""

    SYNTAX = "syntax"
    RUNTIME = "runtime"
    LOGIC = "logic"
    DEPENDENCY = "dependency"
    TIMEOUT = "timeout"
    IMPORT = "import"


# ============================================================================
# Stage 1: Requirements Models
# ============================================================================


class Feature(BaseModel):
    """A feature requirement."""

    id: str = Field(..., description="Unique feature identifier")
    name: str = Field(..., description="Feature name")
    description: str = Field(..., description="Detailed description")
    priority: int = Field(default=1, ge=1, le=5, description="Priority (1-5)")
    user_story: Optional[str] = Field(None, description="User story format")


class Requirements(BaseModel):
    """Structured user requirements."""

    title: str = Field(..., description="Application title")
    description: str = Field(..., description="High-level description")
    features: List[Feature] = Field(..., description="List of features")
    constraints: List[str] = Field(default_factory=list, description="Technical constraints")
    target_users: Optional[str] = Field(None, description="Target user description")
    data_requirements: Optional[str] = Field(None, description="Data storage needs")
    user_clarifications: Dict[str, str] = Field(
        default_factory=dict, description="User answers to clarification questions"
    )
    created_at: datetime = Field(default_factory=datetime.now)


# ============================================================================
# Stage 2: Planning Models
# ============================================================================


class Task(BaseModel):
    """An atomic task in the development plan."""

    id: str = Field(..., description="Unique task identifier (e.g., T1, T2)")
    name: str = Field(..., description="Task name")
    description: str = Field(..., description="Detailed task description")
    type: TaskType = Field(..., description="Task type")
    dependencies: List[str] = Field(default_factory=list, description="List of task IDs this depends on")
    priority: int = Field(default=1, ge=1, le=5, description="Priority (1-5)")
    estimated_complexity: TaskComplexity = Field(..., description="Complexity estimate")
    # 新增：文件修改信息
    files_to_add: List[str] = Field(default_factory=list, description="Files to create")
    files_to_modify: List[str] = Field(default_factory=list, description="Files to modify")


class Algorithm(BaseModel):
    """Algorithm/implementation approach for a task."""

    task_id: str = Field(..., description="Associated task ID")
    algorithm_type: str = Field(..., description="Type of algorithm/pattern")
    implementation_approach: str = Field(..., description="How to implement")
    libraries: List[str] = Field(default_factory=list, description="Required libraries")
    data_structures: List[str] = Field(default_factory=list, description="Data structures needed")
    notes: Optional[str] = Field(None, description="Additional implementation notes")


class FileSpec(BaseModel):
    """Specification for a file to be generated."""

    path: str = Field(..., description="Relative file path")
    purpose: str = Field(..., description="Purpose of this file")
    dependencies: List[str] = Field(default_factory=list, description="Files this depends on")
    layer: Optional[str] = Field(default=None, description="Layer: base (database/models), business (controllers/services), assembly (routes/__init__)")
    related_tasks: List[str] = Field(default_factory=list, description="Related task IDs")


class ExportSpec(BaseModel):
    """Specification for an exported class or function."""

    type: str = Field(..., description="Type: class or function")
    name: str = Field(..., description="Name of the class or function")
    extends: Optional[str] = Field(None, description="Parent class if applicable")
    params: List[str] = Field(default_factory=list, description="Function parameters")
    returns: Optional[str] = Field(None, description="Return type hint")
    docstring: Optional[str] = Field(None, description="Documentation")


class InterfaceSpec(BaseModel):
    """Detailed interface specification for a file."""

    module_name: str = Field(..., description="Module name, e.g., app.models.problem")
    file_path: str = Field(..., description="Relative file path, e.g., app/models/problem.py")
    purpose: str = Field(..., description="Purpose of this module")
    layer: Optional[str] = Field(default=None, description="Layer: base, business, or assembly")
    exports: List[ExportSpec] = Field(default_factory=list, description="Classes and functions to export")
    imports: List[str] = Field(default_factory=list, description="Required import statements")
    database_access: str = Field(default="none", description="Database layer: sqlalchemy, sqlite3, or none")
    related_files: List[str] = Field(default_factory=list, description="Related module paths")
    usage_in_code: List[str] = Field(default_factory=list, description="How other files use this module")


class EngineeringPlan(BaseModel):
    """Complete engineering plan for code generation."""

    tasks: List[Task] = Field(..., description="All tasks")
    algorithms: Dict[str, Algorithm] = Field(..., description="Algorithm per task")
    file_structure: List[FileSpec] = Field(..., description="Files to generate")
    interface_specs: List[InterfaceSpec] = Field(default_factory=list, description="Detailed interface specifications for each module")
    dependencies: List[str] = Field(default_factory=list, description="Python packages needed")
    architecture_notes: str = Field(..., description="Overall architecture description")
    api_specs: Dict[str, Any] = Field(default_factory=dict, description="API specifications for frontend-backend connection")
    pyi_stubs: Dict[str, str] = Field(default_factory=dict, description="Python .pyi stub files with type definitions")
    bdd_test_cases: List["BDDTestCase"] = Field(default_factory=list, description="BDD test cases synthesized from requirements (test-driven)")
    created_at: datetime = Field(default_factory=datetime.now)


# ============================================================================
# Stage 3: Code Generation Models
# ============================================================================


class InterfaceDefinition(BaseModel):
    """Interface definition (.pyi style) for a module."""

    module_name: str = Field(..., description="Module name")
    functions: List[Dict[str, Any]] = Field(default_factory=list, description="Function signatures")
    classes: List[Dict[str, Any]] = Field(default_factory=list, description="Class definitions")
    imports: List[str] = Field(default_factory=list, description="Import statements")
    type_hints: str = Field(..., description="Type hints content")


class SymbolTableEntry(BaseModel):
    """Entry in the global symbol table."""

    symbol_name: str = Field(..., description="Name of the symbol")
    symbol_type: str = Field(..., description="Type (function, class, variable)")
    module: str = Field(..., description="Module containing the symbol")
    signature: Optional[str] = Field(None, description="Function/method signature")
    docstring: Optional[str] = Field(None, description="Documentation string")
    line_number: int = Field(..., description="Line number in source")


class DependencyGraph(BaseModel):
    """File dependency graph for the project."""

    nodes: List[str] = Field(..., description="File paths")
    edges: List[Dict[str, str]] = Field(..., description="Dependencies (from -> to)")
    entry_point: str = Field(..., description="Main entry point file")


class CodeSkeleton(BaseModel):
    """Global skeleton with interfaces and dependency graph (Interface-First)."""

    interfaces: List[InterfaceDefinition] = Field(..., description="All interface definitions")
    dependency_graph: DependencyGraph = Field(..., description="File dependency graph")
    symbol_table: List[SymbolTableEntry] = Field(default_factory=list, description="Global symbol table")
    created_at: datetime = Field(default_factory=datetime.now)


class CodeFile(BaseModel):
    """A generated code file."""

    path: str = Field(..., description="Relative file path")
    content: str = Field(..., description="File content")
    language: str = Field(..., description="Programming language")
    purpose: str = Field(..., description="Purpose of this file")
    dependencies: List[str] = Field(default_factory=list, description="File dependencies")
    interface_id: Optional[str] = Field(None, description="Associated interface definition")
    generated_at: datetime = Field(default_factory=datetime.now)


class DirectoryStructure(BaseModel):
    """Directory structure of generated project."""

    root: str = Field(..., description="Root directory name")
    directories: List[str] = Field(..., description="All directories")
    entry_point: str = Field(..., description="Main entry point file")


class CodeRepository(BaseModel):
    """Complete generated code repository."""

    skeleton: Optional[CodeSkeleton] = Field(None, description="Code skeleton (Interface-First)")
    files: List[CodeFile] = Field(..., description="All generated files")
    structure: DirectoryStructure = Field(..., description="Directory structure")
    dependencies: List[str] = Field(default_factory=list, description="Package dependencies")
    readme_content: Optional[str] = Field(None, description="README content")
    created_at: datetime = Field(default_factory=datetime.now)


class CodeSnippet(BaseModel):
    """A reusable code snippet from code memory."""

    id: str = Field(..., description="Unique snippet ID")
    function_name: str = Field(..., description="Function/class name")
    description: str = Field(..., description="What this code does")
    code: str = Field(..., description="The code itself")
    language: str = Field(..., description="Programming language")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    usage_count: int = Field(default=0, description="Times reused")
    project_id: str = Field(..., description="Source project")
    created_at: datetime = Field(default_factory=datetime.now)


# ============================================================================
# Stage 4: Validation Models (Full-cycle Testing with BDD + Visual Verification)
# ============================================================================


class BDDTestCase(BaseModel):
    """BDD (Behavior-Driven Development) test case."""

    test_id: str = Field(..., description="Unique test identifier")
    feature: str = Field(..., description="Feature being tested")
    scenario: str = Field(..., description="Test scenario description")
    given: str = Field(..., description="Given precondition")
    when: str = Field(..., description="When action")
    then: str = Field(..., description="Then expected outcome")
    test_code: str = Field(..., description="Generated test code")
    status: str = Field(default="pending", description="Test status (pending/passed/failed)")


class VisualVerificationResult(BaseModel):
    """Results from visual verification using VLM."""

    screenshot_path: str = Field(..., description="Path to screenshot")
    requirement_text: str = Field(..., description="Original requirement")
    alignment_score: float = Field(..., ge=0.0, le=1.0, description="Visual-semantic alignment score")
    layout_feedback: str = Field(..., description="Layout analysis feedback")
    missing_elements: List[str] = Field(default_factory=list, description="Missing UI elements")
    issues: List[str] = Field(default_factory=list, description="Visual issues found")
    passed: bool = Field(..., description="Whether visual verification passed")


class TestError(BaseModel):
    """An error encountered during testing."""

    error_type: ErrorType = Field(..., description="Type of error")
    file_path: Optional[str] = Field(None, description="File where error occurred")
    line_number: Optional[int] = Field(None, description="Line number")
    error_message: str = Field(..., description="Error message")
    stack_trace: Optional[str] = Field(None, description="Stack trace")
    suggestion: Optional[str] = Field(None, description="Suggested fix")


class TestResult(BaseModel):
    """Results from full-cycle testing (logic + visual)."""

    __test__ = False  # Pytest: do not collect as test class

    # Logic testing
    logic_passed: bool = Field(..., description="Whether logic tests passed")
    bdd_test_cases: List[BDDTestCase] = Field(default_factory=list, description="BDD test cases")
    errors: List[TestError] = Field(default_factory=list, description="Errors encountered")
    warnings: List[str] = Field(default_factory=list, description="Warnings")

    # Visual verification
    visual_verification: Optional[VisualVerificationResult] = Field(None, description="Visual verification results")
    visual_feedback: Optional[Dict[str, Any]] = Field(None, description="Structured visual feedback for repair loop (alignment_score, missing_elements, issues)")

    # Overall
    execution_time: float = Field(..., description="Execution time in seconds")
    stdout: Optional[str] = Field(None, description="Standard output")
    stderr: Optional[str] = Field(None, description="Standard error")
    timestamp: datetime = Field(default_factory=datetime.now)

    @property
    def passed(self) -> bool:
        """Overall pass status (logic AND visual)."""
        visual_ok = True if self.visual_verification is None else self.visual_verification.passed
        return self.logic_passed and visual_ok


class ValidatedProject(BaseModel):
    """Final validated and deployable project."""

    repository: CodeRepository = Field(..., description="Code repository")
    test_results: TestResult = Field(..., description="Final test results")
    is_deployable: bool = Field(..., description="Ready for deployment")
    deployment_instructions: str = Field(..., description="How to run/deploy")
    fix_attempts: int = Field(default=0, description="Number of fix iterations")
    validated_at: datetime = Field(default_factory=datetime.now)


# ============================================================================
# Utility Models
# ============================================================================


class ProjectMetadata(BaseModel):
    """Metadata for a generated project."""

    project_id: str = Field(..., description="Unique project identifier")
    title: str = Field(..., description="Project title")
    description: str = Field(..., description="Project description")
    status: str = Field(..., description="Current status")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    stage: int = Field(default=1, ge=1, le=4, description="Current stage (1-4)")
    project_path: str = Field(..., description="Path to project directory")
