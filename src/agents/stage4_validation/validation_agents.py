"""Stage 4 Validation Agents."""

import subprocess
import time
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from src.core.data_models import (
    Requirements, EngineeringPlan, CodeRepository, ValidatedProject,
    TestResult, BDDTestCase, TestError, ErrorType, ValidationStatus
)
from src.core.context import ExecutionContext
from src.services.llm_service import LLMService
from src.utils.logger import get_logger

logger = get_logger(__name__)


class FullCycleTestingAgent:
    """Stage 4 Agent 1: Full-cycle testing with BDD."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def execute(self, context: ExecutionContext) -> TestResult:
        """Run full-cycle tests on the generated code."""
        repository = context.code_repository
        requirements = context.requirements

        start_time = time.time()

        logger.info("Running full-cycle tests")

        # Generate BDD test cases
        bdd_tests = self._generate_bdd_tests(requirements)

        # Save files to disk
        self._save_files(context.project_path / "generated", repository)

        # Run syntax check
        errors = self._run_syntax_check(repository)

        # Try to run the application
        warnings = []
        try:
            can_run, msg = self._check_can_run(repository)
            if not can_run:
                warnings.append(msg)
        except Exception as e:
            warnings.append(f"Could not verify run: {e}")

        execution_time = time.time() - start_time

        return TestResult(
            logic_passed=len(errors) == 0,
            bdd_test_cases=bdd_tests,
            errors=errors,
            warnings=warnings,
            execution_time=execution_time,
            stdout="",
            stderr=""
        )

    def _generate_bdd_tests(self, requirements: Requirements) -> list[BDDTestCase]:
        """Generate BDD test cases from requirements."""
        tests = []

        for i, feature in enumerate(requirements.features[:5], 1):
            tests.append(BDDTestCase(
                test_id=f"test_{i}",
                feature=feature.name,
                scenario=f"User can {feature.name.lower()}",
                given=f"User is on the application page",
                when=f"User performs {feature.name.lower()}",
                then=f"The application should respond correctly",
                test_code=f"def test_{feature.name.lower().replace(' ', '_')}():\n    # TODO: Implement test for {feature.name}",
                status="pending"
            ))

        return tests

    def _save_files(self, project_path: Path, repository: CodeRepository):
        """Save generated code files to disk."""
        project_path.mkdir(parents=True, exist_ok=True)

        for code_file in repository.files:
            file_path = project_path / code_file.path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(code_file.content, encoding='utf-8')

        # Save requirements.txt
        if repository.dependencies:
            req_path = project_path / "requirements.txt"
            req_content = "\n".join(repository.dependencies)
            req_path.write_text(req_content)

        logger.info(f"Saved {len(repository.files)} files to {project_path}")

    def _run_syntax_check(self, repository: CodeRepository) -> list[TestError]:
        """Check Python files for syntax errors."""
        errors = []

        for code_file in repository.files:
            if code_file.language == 'python':
                try:
                    import ast
                    ast.parse(code_file.content)
                except SyntaxError as e:
                    errors.append(TestError(
                        error_type=ErrorType.SYNTAX,
                        file_path=code_file.path,
                        line_number=e.lineno,
                        error_message=str(e),
                        suggestion="Fix the syntax error"
                    ))

        return errors

    def _check_can_run(self, repository: CodeRepository) -> tuple[bool, str]:
        """Check if the application can run."""
        # Find app.py or main file
        app_file = None
        for f in repository.files:
            if f.path == 'app.py' or f.path.endswith('/app.py'):
                app_file = f
                break

        if not app_file:
            return False, "No app.py found"

        # Check for Flask import
        if 'flask' not in app_file.content.lower():
            return False, "No Flask import found"

        return True, "Application appears runnable"


class FineTuningAgent:
    """Stage 4 Agent 2: Fine-tuning based on test results."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def execute(self, context: ExecutionContext, test_result: TestResult) -> tuple[CodeRepository, bool]:
        """Fix issues found during testing."""
        if test_result.logic_passed and not test_result.warnings:
            logger.info("No fixes needed - tests passed")
            return context.code_repository, False

        logger.info(f"Attempting to fix {len(test_result.errors)} errors")

        # For MVP, we don't actually fix - we just return the original code
        # In a full implementation, this would use LLM to fix the errors
        return context.code_repository, False


class VisualVerificationAgent:
    """Stage 4 Agent 3: Visual verification using VLM."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def execute(self, context: ExecutionContext) -> Any:
        """Verify visual rendering of the application."""
        # For MVP, visual verification is skipped
        # In a full implementation, this would:
        # 1. Start the application
        # 2. Take a screenshot
        # 3. Use VLM to analyze the screenshot
        logger.info("Visual verification skipped for MVP")
        return None


def create_validated_project(
    repository: CodeRepository,
    test_result: TestResult,
    requirements: Requirements
) -> ValidatedProject:
    """Create the final validated project."""

    is_deployable = (
        test_result.logic_passed and
        len(test_result.errors) == 0
    )

    deployment_instructions = f"""To run the application:

1. Navigate to the generated directory:
   cd {repository.structure.root}

2. Install dependencies:
   pip install -r requirements.txt

3. Run the application:
   python {repository.structure.entry_point}

4. Open http://localhost:5000 in your browser
"""

    return ValidatedProject(
        repository=repository,
        test_results=test_result,
        is_deployable=is_deployable,
        deployment_instructions=deployment_instructions,
        fix_attempts=0,
        validated_at=datetime.now()
    )
