"""Stage 4 Validation Agents."""

import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from src.core.data_models import (
    Requirements, EngineeringPlan, CodeRepository, CodeFile, ValidatedProject,
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
        project_path = context.project_path

        start_time = time.time()

        logger.info("Running full-cycle tests")

        # Generate BDD test cases
        bdd_tests = self._generate_bdd_tests(requirements)

        # Save files to disk
        generated_path = project_path / "generated"
        self._save_files(generated_path, repository)

        # Generate __init__.py files for proper imports
        self._generate_init_files(generated_path)

        # Run syntax check
        errors = self._run_syntax_check(repository)

        # Try to run the tests
        test_output = ""
        test_stderr = ""
        warnings = []

        if len(errors) == 0:
            try:
                test_results, test_output, test_stderr = self._run_tests(generated_path, repository)
                if test_results:
                    errors.extend(test_results)
            except Exception as e:
                warnings.append(f"Test execution failed: {e}")
                test_output = str(e)
        else:
            warnings.append("Skipping test execution due to syntax errors")

        # Check if app can run
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
            stdout=test_output,
            stderr=test_stderr
        )

    def _generate_init_files(self, project_path: Path):
        """Generate __init__.py files for all Python packages."""
        init_files = set()

        for py_file in project_path.rglob("*.py"):
            parent = py_file.parent
            if parent != project_path:
                init_file = parent / "__init__.py"
                if not init_file.exists():
                    init_file.write_text(f'"""Package: {parent.name}"""\n')
                    init_files.add(str(init_file))

        if init_files:
            logger.info(f"Generated {len(init_files)} __init__.py files")

    def _run_tests(self, project_path: Path, repository: CodeRepository) -> tuple[List[TestError], str, str]:
        """Run pytest on the generated tests."""
        errors = []
        stdout = ""
        stderr = ""

        # Find test files
        test_files = [f for f in repository.files if f.path.startswith('tests/') and f.language == 'python']

        if not test_files:
            logger.info("No test files found")
            return errors, stdout, stderr

        logger.info(f"Running {len(test_files)} test files...")

        # Create a virtual environment or use existing one
        # First, install dependencies
        req_file = project_path / "requirements.txt"
        if req_file.exists():
            logger.info("Installing dependencies...")
            try:
                # Install requirements (only actual pip packages, filter out non-pip items)
                req_content = req_file.read_text()
                # Filter to only actual pip packages
                valid_packages = ['flask', 'sqlalchemy', 'werkzeug', 'Pillow', 'openai']
                packages_to_install = []
                for line in req_content.strip().split('\n'):
                    pkg = line.strip()
                    if pkg and not pkg.startswith('#'):
                        # Only install known working packages
                        for valid in valid_packages:
                            if valid.lower() in pkg.lower():
                                packages_to_install.append(valid)
                                break

                if packages_to_install:
                    install_result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-q"] + packages_to_install,
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    if install_result.returncode != 0:
                        logger.warning(f"Failed to install some dependencies: {install_result.stderr}")
            except Exception as e:
                logger.warning(f"Could not install dependencies: {e}")

        # Run pytest on the generated code
        test_dir = project_path / "tests"
        if test_dir.exists():
            try:
                # Run pytest with verbose output
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", str(test_dir), "-v", "--tb=short", "--no-header"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=str(project_path)
                )
                stdout = result.stdout
                stderr = result.stderr
                logger.info(f"Pytest exit code: {result.returncode}")

                # Parse pytest output for errors
                if result.returncode != 0:
                    # Parse failure output
                    error_lines = stderr.split('\n') if stderr else stdout.split('\n')
                    current_file = None

                    for line in error_lines:
                        if 'FAILED' in line:
                            # Extract test name
                            match = re.search(r'FAILED (\S+)', line)
                            if match:
                                errors.append(TestError(
                                    error_type=ErrorType.TEST_FAILED,
                                    file_path=match.group(1),
                                    line_number=0,
                                    error_message=line,
                                    suggestion="Fix the test or implementation"
                                ))
                        elif 'ERROR' in line and 'test_' in line:
                            errors.append(TestError(
                                error_type=ErrorType.TEST_ERROR,
                                file_path="tests",
                                line_number=0,
                                error_message=line,
                                suggestion="Check test setup"
                            ))
                        elif 'ModuleNotFoundError' in line:
                            # Extract module name
                            match = re.search(r"ModuleNotFoundError: No module named '(\S+)'", line)
                            if match:
                                errors.append(TestError(
                                    error_type=ErrorType.IMPORT,
                                    file_path="",
                                    line_number=0,
                                    error_message=f"Missing module: {match.group(1)}",
                                    suggestion=f"Install {match.group(1)} or fix imports"
                                ))

                # If tests passed, log success
                if result.returncode == 0:
                    logger.info("All tests passed!")

            except subprocess.TimeoutExpired:
                errors.append(TestError(
                    error_type=ErrorType.TEST_ERROR,
                    file_path="tests",
                    line_number=0,
                    error_message="Test execution timed out",
                    suggestion="Check test complexity"
                ))
            except Exception as e:
                errors.append(TestError(
                    error_type=ErrorType.TEST_ERROR,
                    file_path="tests",
                    line_number=0,
                    error_message=f"Test execution failed: {e}",
                    suggestion="Check test setup"
                ))

        return errors, stdout, stderr

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

        # Save requirements.txt - filter to actual pip packages
        if repository.dependencies:
            # Filter out non-pip items (like React, Docker, etc.)
            valid_packages = []
            for dep in repository.dependencies:
                dep_lower = dep.lower()
                # Known valid Python packages
                if any(pkg in dep_lower for pkg in ['flask', 'sqlalchemy', 'werkzeug', 'pillow',
                    'openai', 'requests', 'python-dotenv', 'gunicorn', 'pytest', 'pyyaml',
                    'jinja', 'markupsafe', 'click', 'itsdangerous', 'jmespath']):
                    if dep not in valid_packages:
                        valid_packages.append(dep)

            # Always include flask as base
            if 'flask' not in valid_packages:
                valid_packages.insert(0, 'flask')

            if valid_packages:
                req_path = project_path / "requirements.txt"
                req_content = "\n".join(valid_packages)
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
        # Find app.py, main.py or any entry point
        app_file = None
        for f in repository.files:
            if f.path == 'app.py' or f.path.endswith('/app.py') or f.path.endswith('/main.py'):
                app_file = f
                break

        if not app_file:
            return False, "No app.py or main.py found"

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

        logger.info(f"Attempting to fix {len(test_result.errors)} errors and {len(test_result.warnings)} warnings")

        repository = context.code_repository
        fixed = False

        # Try to fix errors
        for error in test_result.errors:
            if error.error_type == ErrorType.SYNTAX:
                # Try to fix syntax errors
                repository = self._fix_syntax_error(repository, error)
                fixed = True
            elif error.error_type == ErrorType.IMPORT:
                # Try to fix import errors
                repository = self._fix_import_error(repository, error)
                fixed = True
            elif error.error_type in [ErrorType.TEST_FAILED, ErrorType.TEST_ERROR]:
                # Try to fix test failures
                repository = self._fix_test_error(repository, error)
                fixed = True

        # Also fix warnings
        for warning in test_result.warnings:
            if "No app.py found" in warning or "No main.py found" in warning:
                repository = self._fix_missing_entry_point(repository)
                fixed = True

        if fixed:
            logger.info("Applied fixes to code")

        return repository, fixed

    def _fix_syntax_error(self, repository: CodeRepository, error: TestError) -> CodeRepository:
        """Fix syntax errors in code."""
        for i, f in enumerate(repository.files):
            if f.path == error.file_path:
                logger.info(f"Fixing syntax error in {f.path}")
                # Use LLM to fix the syntax error
                prompt = f"""Fix the syntax error in this Python file:

File: {f.path}
Error at line {error.line_number}: {error.error_message}

Original code:
{f.content}

Return the corrected code only, no explanations.
"""
                try:
                    fixed_code = self.llm_service.generate(prompt, max_tokens=2000)
                    # Verify it parses
                    import ast
                    ast.parse(fixed_code)
                    repository.files[i] = CodeFile(
                        path=f.path,
                        content=fixed_code,
                        language=f.language,
                        purpose=f.purpose,
                        dependencies=f.dependencies
                    )
                    logger.info(f"Fixed syntax error in {f.path}")
                except Exception as e:
                    logger.warning(f"Could not fix syntax error: {e}")
                break

        return repository

    def _fix_import_error(self, repository: CodeRepository, error: TestError) -> CodeRepository:
        """Fix import errors by generating missing modules."""
        # Extract missing module from error message
        # e.g., "Missing module: app.config" -> generate config.py
        if "Missing module:" in error.error_message:
            module_name = error.error_message.split("Missing module:")[-1].strip()
            logger.info(f"Attempting to fix missing module: {module_name}")

            # Generate stub for missing module
            module_path = module_name.replace('.', '/') + '.py'

            # Check if we can generate a simple stub
            if 'config' in module_name.lower():
                stub_content = '''"""Configuration module."""

class Config:
    SECRET_KEY = 'dev-secret-key'
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
'''
                # Add to repository
                repository.files.append(CodeFile(
                    path=module_path,
                    content=stub_content,
                    language='python',
                    purpose='Auto-generated config',
                    dependencies=[]
                ))
                logger.info(f"Generated stub for {module_path}")

        return repository

    def _fix_test_error(self, repository: CodeRepository, error: TestError) -> CodeRepository:
        """Fix test errors by updating tests or implementations."""
        # For now, just mark the test as xfail or skip
        # A full implementation would use LLM to understand and fix the issue
        logger.info(f"Test error in {error.file_path}: {error.error_message}")
        return repository

    def _fix_missing_entry_point(self, repository: CodeRepository) -> CodeRepository:
        """Fix missing entry point issue."""
        # Check if we have app/main.py
        main_file = None
        for f in repository.files:
            if f.path.endswith('/main.py'):
                main_file = f
                break

        if not main_file:
            # Generate a simple entry point
            entry_content = '''"""Application entry point."""
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({'message': 'Application running'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
'''
            repository.files.append(CodeFile(
                path='app/main.py',
                content=entry_content,
                language='python',
                purpose='Application entry point',
                dependencies=[]
            ))
            logger.info("Generated app/main.py as entry point")

        return repository


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
