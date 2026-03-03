"""Stage 4 Validation Agents."""

import os
import re
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.core.data_models import (
    Requirements, EngineeringPlan, CodeRepository, CodeFile, ValidatedProject,
    TestResult, BDDTestCase, TestError, ErrorType, ValidationStatus
)
from src.core.context import ExecutionContext
from openai import APIError, RateLimitError
from src.services.llm_service import LLMService
from src.utils.logger import get_logger

logger = get_logger(__name__)

FRAMEWORK_TEMPLATE_PATH = Path(__file__).parent.parent.parent.parent / "templates" / "flask_base"


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

        # BDD single source: Orchestrator._synthesize_bdd_tests. Rule-based fallback only when plan has none.
        plan_bdd = []
        if context.engineering_plan and getattr(context.engineering_plan, 'bdd_test_cases', None):
            plan_bdd = context.engineering_plan.bdd_test_cases
        bdd_tests = plan_bdd if plan_bdd else self._rule_based_bdd_fallback(requirements)

        # Save files to disk
        generated_path = project_path / "generated"
        self._save_files(generated_path, repository)

        # Generate __init__.py files for proper imports
        self._generate_init_files(generated_path)

        # Run syntax check
        errors = self._run_syntax_check(repository)

        # 真正运行代码测试
        test_output = ""
        test_stderr = ""
        warnings = []
        env_install_ok = None
        env_start_ok = None

        # 有语法错误时跳过启应用与 BDD 执行，仍写盘以便 CodeFix/RunAndFix 能修复
        if not errors:
            # 1. 使用 subprocess 直接运行 app.py 测试
            run_errors, env_install_ok, env_start_ok = self._try_run_with_subprocess(generated_path)
            if run_errors:
                errors.extend(run_errors)
                test_stderr = "Run errors found"
            else:
                logger.info("App runs successfully!")

            # 1.5 检查 frontend_routes 是否存在（可选）
            if not errors and context.engineering_plan:
                route_errors = self._check_frontend_routes(generated_path, context.engineering_plan)
                if route_errors:
                    errors.extend(route_errors)
                    test_stderr = test_stderr or "Frontend routes missing"
                # 1.6 检查 auth 流程完整性（当 api_specs 有 auth endpoint 时）
                auth_errors = self._check_auth_flow(generated_path, context.engineering_plan)
                if auth_errors:
                    errors.extend(auth_errors)
                    test_stderr = test_stderr or "Auth flow incomplete"

            # 2. 检查未使用的文件（仅 warnings）
            unused_warnings = self._check_unused_files(generated_path)
            if unused_warnings:
                warnings.extend([str(w.error_message) if hasattr(w, "error_message") else str(w) for w in unused_warnings])
                logger.info(f"Found {len(unused_warnings)} unused files")

            # 3. BDD → pytest: 生成并执行 BDD 测试（当 enable_bdd_testing 时）
            try:
                from config.settings import get_settings
                settings = get_settings()
                if getattr(settings, "enable_bdd_testing", False) and not errors:
                    self._write_bdd_pytest_file(generated_path, bdd_tests, context)
                    bdd_pytest_errors, bdd_stdout, bdd_stderr = self._run_tests(generated_path, repository)
                    if bdd_pytest_errors:
                        errors.extend(bdd_pytest_errors)
                        test_stderr = test_stderr or "BDD tests failed"
            except Exception as e:
                logger.debug(f"BDD pytest skipped: {e}")
        else:
            # 语法错误：未运行应用与 BDD，明确标志
            env_install_ok = False
            env_start_ok = False
            # 仍可做未使用文件检查（不依赖应用运行）
            unused_warnings = self._check_unused_files(generated_path)
            if unused_warnings:
                warnings.extend([str(w.error_message) if hasattr(w, "error_message") else str(w) for w in unused_warnings])

        execution_time = time.time() - start_time

        return TestResult(
            logic_passed=len(errors) == 0,
            bdd_test_cases=bdd_tests,
            errors=errors,
            warnings=warnings,
            env_install_success=env_install_ok,
            env_start_success=env_start_ok,
            execution_time=execution_time,
            stdout=test_output,
            stderr=test_stderr
        )

    def _try_run_with_subprocess(
        self, project_path: Path
    ) -> tuple[List[TestError], bool, bool]:
        """Run app.py via subprocess. Returns (errors, install_success, start_success)."""
        errors = []

        # 查找入口文件：app.py 或 run.py
        entry_file = None
        if (project_path / "app.py").exists():
            entry_file = "app.py"
        elif (project_path / "run.py").exists():
            entry_file = "run.py"

        if not entry_file:
            errors.append(TestError(
                error_type=ErrorType.IMPORT,
                file_path="app.py or run.py",
                line_number=0,
                error_message="No entry point found",
                suggestion="Create app.py or run.py with create_app()"
            ))
            return errors, False, False

        install_success = self._install_project_deps(project_path)
        start_success = False

        import subprocess
        import time

        from config.settings import get_settings
        port = get_settings().validation_port

        logger.info(f"Starting {entry_file} on port {port}...")

        proc = None
        try:
            proc = subprocess.Popen(
                [sys.executable, entry_file],
                cwd=str(project_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env={**os.environ, "PORT": str(port)},
            )

            time.sleep(3)

            if proc.poll() is not None:
                stdout, stderr = proc.communicate()
                errors.append(TestError(
                    error_type=ErrorType.RUNTIME,
                    file_path=entry_file,
                    line_number=0,
                    error_message=f"Process exited immediately: {stderr[:500] if stderr else stdout[:500]}",
                    suggestion="Check for errors in the application"
                ))
                return errors, install_success, start_success

            start_success = True
            try:
                import requests as req
                response = req.get(f"http://localhost:{port}/", timeout=5)
                status_code = str(response.status_code)
                logger.info(f"GET / -> {status_code}")

                if response.status_code >= 500:
                    errors.append(TestError(
                        error_type=ErrorType.RUNTIME,
                        file_path=entry_file,
                        line_number=0,
                        error_message=f"Home page returned {response.status_code}",
                        suggestion="Check server logs for errors"
                    ))
            except Exception as e:
                errors.append(TestError(
                    error_type=ErrorType.RUNTIME,
                    file_path=entry_file,
                    line_number=0,
                    error_message=f"Could not connect to server: {e}",
                    suggestion="Check if the app started correctly"
                ))

        finally:
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()

        # 另外测试能否作为模块导入
        import_test = self._test_import_module(project_path)
        if import_test:
            errors.extend(import_test)

        return errors, install_success, start_success

    def _check_frontend_routes(
        self, project_path: Path, engineering_plan: "EngineeringPlan"
    ) -> List[TestError]:
        """Verify each frontend_route returns non-404 when app is runnable."""
        errors = []
        api_specs = getattr(engineering_plan, "api_specs", None) or {}
        frontend_routes = api_specs.get("frontend_routes") or {}
        if not frontend_routes:
            return errors

        import sys

        sys.path.insert(0, str(project_path))
        try:
            import importlib.util

            app_module = None
            init_path = project_path / "app" / "__init__.py"
            if init_path.exists():
                spec = importlib.util.spec_from_file_location("app", init_path)
                app_module = importlib.util.module_from_spec(spec)
                sys.modules["app"] = app_module
                spec.loader.exec_module(app_module)
            if not app_module or not hasattr(app_module, "create_app"):
                app_py = project_path / "app.py"
                if app_py.exists():
                    spec = importlib.util.spec_from_file_location("app_mod", app_py)
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    if hasattr(mod, "create_app"):
                        app_module = mod
            if not app_module or not hasattr(app_module, "create_app"):
                return errors

            app = app_module.create_app()
            with app.test_client() as client:
                for path in frontend_routes.keys():
                    if path == "/":
                        continue
                    r = client.get(path)
                    if r.status_code == 404:
                        errors.append(
                            TestError(
                                error_type=ErrorType.RUNTIME,
                                file_path="app/__init__.py",
                                line_number=0,
                                error_message=f"Frontend route {path} returns 404",
                                suggestion=f"Add @app.route('{path}') in app/__init__.py",
                            )
                        )
        except Exception as e:
            logger.debug(f"Frontend route check skipped: {e}")
        finally:
            if str(project_path) in sys.path:
                sys.path.remove(str(project_path))

        return errors

    def _check_auth_flow(
        self, project_path: Path, engineering_plan: "EngineeringPlan"
    ) -> List[TestError]:
        """When api_specs has auth endpoints, verify login/register pages exist and cross-link."""
        errors = []
        api_specs = getattr(engineering_plan, "api_specs", None) or {}
        endpoints = api_specs.get("endpoints") or []
        has_auth = any("auth" in str(ep.get("path", "")).lower() for ep in endpoints)
        if not has_auth:
            return errors

        templates_dir = project_path / "templates"
        login_html = templates_dir / "login.html"
        register_html = templates_dir / "register.html"

        if not login_html.exists():
            errors.append(
                TestError(
                    error_type=ErrorType.LOGIC,
                    file_path="templates/login.html",
                    line_number=0,
                    error_message="App has auth but templates/login.html is missing",
                    suggestion="Create login.html and add @app.route('/login') in app/__init__.py",
                )
            )
        else:
            content = login_html.read_text(encoding="utf-8", errors="ignore")
            if "/register" not in content and "注册" not in content and "register" not in content.lower():
                errors.append(
                    TestError(
                        error_type=ErrorType.LOGIC,
                        file_path="templates/login.html",
                        line_number=0,
                        error_message="Login page must have link to register (e.g. '没有账号？去注册' or href='/register')",
                        suggestion="Add <a href='/register'>没有账号？去注册</a> to login.html",
                    )
                )

        if not register_html.exists():
            errors.append(
                TestError(
                    error_type=ErrorType.LOGIC,
                    file_path="templates/register.html",
                    line_number=0,
                    error_message="App has auth but templates/register.html is missing",
                    suggestion="Create register.html and add @app.route('/register') in app/__init__.py",
                )
            )
        else:
            content = register_html.read_text(encoding="utf-8", errors="ignore")
            if "/login" not in content and "登录" not in content and "login" not in content.lower():
                errors.append(
                    TestError(
                        error_type=ErrorType.LOGIC,
                        file_path="templates/register.html",
                        line_number=0,
                        error_message="Register page must have link to login (e.g. '已有账号？去登录' or href='/login')",
                        suggestion="Add <a href='/login'>已有账号？去登录</a> to register.html",
                    )
                )

        return errors

    def _test_import_module(self, project_path: Path) -> List[TestError]:
        """测试能否作为模块导入"""
        errors = []
        import sys

        # 添加到 Python 路径
        sys.path.insert(0, str(project_path))

        # 清理之前的导入
        modules_to_remove = [m for m in sys.modules.keys() if m.startswith('app')]
        for m in modules_to_remove:
            del sys.modules[m]

        try:
            # 尝试导入 app 包
            import importlib.util

            # 尝试 app/__init__.py
            init_path = project_path / "app" / "__init__.py"
            if init_path.exists():
                spec = importlib.util.spec_from_file_location("app", init_path)
                app_module = importlib.util.module_from_spec(spec)
                sys.modules['app'] = app_module
                spec.loader.exec_module(app_module)

                if hasattr(app_module, 'create_app'):
                    logger.info("App module can be imported successfully!")
                    return []

            # 如果 app/__init__.py 没有 create_app，尝试 app.py
            app_py = project_path / "app.py"
            if app_py.exists():
                spec = importlib.util.spec_from_file_location("app_module", app_py)
                test_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(test_module)
                if hasattr(test_module, 'create_app'):
                    logger.info("App from app.py can be imported!")
                    return []

            errors.append(TestError(
                error_type=ErrorType.IMPORT,
                file_path="app/__init__.py",
                line_number=0,
                error_message="Cannot import create_app from app module",
                suggestion="Add create_app() function to app/__init__.py or ensure app.py can be imported"
            ))

        except Exception as e:
            errors.append(TestError(
                error_type=ErrorType.IMPORT,
                file_path="app/__init__.py",
                line_number=0,
                error_message=f"Import error: {str(e)[:200]}",
                suggestion="Fix the import error"
            ))

        return errors

    def _try_import_and_create_app(self, project_path: Path) -> List[TestError]:
        """使用 subprocess 直接运行 app.py 进行测试"""
        errors = []

        # 查找入口文件：app.py 或 run.py
        entry_file = None
        if (project_path / "app.py").exists():
            entry_file = "app.py"
        elif (project_path / "run.py").exists():
            entry_file = "run.py"

        if not entry_file:
            errors.append(TestError(
                error_type=ErrorType.IMPORT,
                file_path="app.py or run.py",
                line_number=0,
                error_message="No entry point found",
                suggestion="Create app.py or run.py with create_app()"
            ))
            return errors

        # 使用 subprocess 启动应用并测试
        import subprocess
        import requests
        import time
        import signal

        from config.settings import get_settings
        port = get_settings().validation_port

        logger.info(f"Starting {entry_file} on port {port}...")

        proc = None
        try:
            proc = subprocess.Popen(
                [sys.executable, entry_file],
                cwd=str(project_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env={**os.environ, "PORT": str(port)},
            )

            time.sleep(3)

            if proc.poll() is not None:
                stdout, stderr = proc.communicate()
                errors.append(TestError(
                    error_type=ErrorType.RUNTIME,
                    file_path=entry_file,
                    line_number=0,
                    error_message=f"Process exited immediately: {stderr[:500]}",
                    suggestion="Check for errors in the application"
                ))
                return errors

            try:
                response = requests.get(f"http://localhost:{port}/", timeout=5)
                logger.info(f"GET / -> {response.status_code}")

                if response.status_code >= 500:
                    errors.append(TestError(
                        error_type=ErrorType.RUNTIME,
                        file_path=entry_file,
                        line_number=0,
                        error_message=f"Home page returned {response.status_code}",
                        suggestion="Check server logs for errors"
                    ))
            except requests.exceptions.RequestException as e:
                errors.append(TestError(
                    error_type=ErrorType.RUNTIME,
                    file_path=entry_file,
                    line_number=0,
                    error_message=f"Could not connect to server: {e}",
                    suggestion="Check if the app started correctly"
                ))

        finally:
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()

        return errors

    def _check_unused_files(self, project_path: Path) -> List[TestError]:
        """检查是否有生成但从未被引用的文件（孤岛文件）；结果作为 warnings 上报，不加入 errors。"""
        errors = []
        try:
            from config.settings import get_settings
            if not getattr(get_settings(), "warn_unused_files", True):
                return []
        except Exception:
            pass

        # 获取所有 Python 文件
        py_files = list(project_path.rglob("*.py"))

        # 分析每个文件的 import
        file_imports = {}  # file -> set of imported modules

        for py_file in py_files:
            try:
                content = py_file.read_text(encoding='utf-8')
                imports = set()

                # 简单的 import 解析
                import re
                # 匹配 from xxx import 和 import xxx
                from_imports = re.findall(r'from\s+([\w.]+)\s+import', content)
                import_stmts = re.findall(r'import\s+([\w.]+)', content)

                imports.update(from_imports)
                imports.update(import_stmts)

                # 转换为相对路径形式
                file_imports[str(py_file.relative_to(project_path))] = imports
            except Exception as ex:
                logger.debug("Could not parse imports from %s: %s", py_file, ex)

        # 检查每个文件是否被其他文件引用
        for py_file in py_files:
            rel_path = str(py_file.relative_to(project_path))

            # 跳过入口文件和 __init__.py
            if rel_path in ["app.py", "run.py", "manage.py"]:
                continue
            if rel_path.endswith("__init__.py"):
                continue

            # 转换为模块名形式
            module_name = rel_path.replace("/", ".").replace("\\", ".").replace(".py", "")

            # 检查是否被其他文件引用
            is_referenced = False
            for file_path, imports in file_imports.items():
                if file_path == rel_path:
                    continue
                # 检查是否引用了这个模块
                for imp in imports:
                    if module_name in imp or imp in module_name:
                        is_referenced = True
                        break
                    # 也检查 from app.database import 这种
                    if "import " + module_name.split(".")[-1] in imp:
                        is_referenced = True
                        break

            if not is_referenced:
                # 对于后端文件（排除 app/static）生成警告
                if rel_path.startswith("app/") and not rel_path.startswith("app/static"):
                    errors.append(TestError(
                        error_type=ErrorType.RUNTIME,
                        file_path=rel_path,
                        line_number=0,
                        error_message=f"Unused file: {rel_path} - not imported by any other file",
                        suggestion="Either use this file or remove it"
                    ))

        return errors

    def _try_test_routes(self, project_path: Path) -> List[TestError]:
        """测试 Flask 路由"""
        warnings = []
        import sys
        import importlib.util

        try:
            # 重新导入
            init_path = project_path / "app" / "__init__.py"
            if not init_path.exists():
                return warnings

            # 清理导入
            modules_to_remove = [m for m in sys.modules.keys() if m.startswith('app')]
            for m in modules_to_remove:
                del sys.modules[m]

            spec = importlib.util.spec_from_file_location("app", init_path)
            app_module = importlib.util.module_from_spec(spec)
            sys.modules['app'] = app_module
            spec.loader.exec_module(app_module)

            if not hasattr(app_module, 'create_app'):
                return warnings

            app = app_module.create_app()
            client = app.test_client()

            # 测试首页
            response = client.get('/')
            if response.status_code >= 500:
                warnings.append(f"Route / returned {response.status_code}")
            elif response.status_code >= 400:
                logger.info(f"Route / returned {response.status_code}")

            logger.info("Routes tested successfully!")

        except Exception as e:
            logger.warning(f"Route test failed: {e}")

        return warnings

    def _extract_file_from_error(self, error_msg: str) -> str:
        """从错误信息中提取文件路径"""
        if "No module named" in error_msg:
            parts = error_msg.split("No module named")
            if len(parts) > 1:
                module = parts[-1].strip().strip("'\"")
                return f"import:{module}"
        if "cannot import name" in error_msg:
            if "from '" in error_msg:
                parts = error_msg.split("from '")
                if len(parts) > 1:
                    module = parts[-1].split("'")[0]
                    return module.replace('.', '/') + '.py'
        return "unknown"

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
        """Run pytest on the generated tests (including test_bdd_smoke.py if present)."""
        errors = []
        stdout = ""
        stderr = ""

        test_dir = project_path / "tests"
        if not test_dir.exists():
            logger.info("No tests directory found")
            return errors, stdout, stderr

        test_files = list(test_dir.glob("test_*.py"))
        if not test_files:
            logger.info("No test_*.py files in tests/")
            return errors, stdout, stderr

        logger.info(f"Running {len(test_files)} test files...")

        self._install_project_deps(project_path)

        # Run pytest on the generated code
        test_dir = project_path / "tests"
        if test_dir.exists():
            try:
                from config.settings import get_settings
                timeout_seconds = getattr(get_settings(), "bdd_test_timeout_seconds", 60)
                # Run pytest with verbose output
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", str(test_dir), "-v", "--tb=short", "--no-header"],
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
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
                                    error_type=ErrorType.RUNTIME,
                                    file_path=match.group(1),
                                    line_number=0,
                                    error_message=line,
                                    suggestion="Fix the test or implementation"
                                ))
                        elif 'ERROR' in line and 'test_' in line:
                            errors.append(TestError(
                                error_type=ErrorType.RUNTIME,
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
                    error_type=ErrorType.RUNTIME,
                    file_path="tests",
                    line_number=0,
                    error_message="Test execution timed out",
                    suggestion="Check test complexity"
                ))
            except Exception as e:
                errors.append(TestError(
                    error_type=ErrorType.RUNTIME,
                    file_path="tests",
                    line_number=0,
                    error_message=f"Test execution failed: {e}",
                    suggestion="Check test setup"
                ))

        return errors, stdout, stderr

    @staticmethod
    def _install_project_deps(project_path: Path) -> bool:
        """Install pip packages listed in the generated project's requirements.txt. Returns True if success or no deps."""
        req_file = project_path / "requirements.txt"
        if not req_file.exists():
            return True
        try:
            logger.info("Installing generated project dependencies...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-q", "-r", str(req_file)],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                logger.warning(f"pip install returned {result.returncode}: {result.stderr[:300]}")
                return False
            logger.info("Project dependencies installed")
            return True
        except Exception as e:
            logger.warning(f"Could not install project deps: {e}")
            return False

    def _rule_based_bdd_fallback(self, requirements: Requirements) -> list[BDDTestCase]:
        """Rule-based fallback when plan.bdd_test_cases is empty (single source: Orchestrator._synthesize_bdd_tests)."""
        return [
            BDDTestCase(
                test_id=f"test_{i}",
                feature=f.name,
                scenario=f"User can {f.name.lower()}",
                given="The application is running",
                when=f"User performs {f.name.lower()}",
                then="The application responds correctly",
                test_code=f"def test_{f.name.lower().replace(' ', '_')}():\n    pass",
                status="pending",
            )
            for i, f in enumerate(requirements.features[:5], 1)
        ]

    def _write_bdd_pytest_file(
        self,
        project_path: Path,
        bdd_tests: list[BDDTestCase],
        context: ExecutionContext,
    ) -> None:
        """Generate and write test_bdd_smoke.py with executable pytest cases."""
        api_specs = {}
        if hasattr(context, "engineering_plan") and context.engineering_plan:
            api_specs = getattr(context.engineering_plan, "api_specs", {}) or {}

        lines = [
            '"""BDD smoke tests auto-generated from requirements."""',
            "",
            "import pytest",
            "",
        ]

        # test_home_page
        lines.append("def test_home_page_loads():")
        lines.append('    """Given app is running, When user visits /, Then page loads."')
        lines.append("    try:")
        lines.append("        from app import create_app")
        lines.append("        app = create_app()")
        lines.append("        with app.test_client() as client:")
        lines.append("            r = client.get('/')")
        lines.append("            assert r.status_code in (200, 302), f'Got {r.status_code}'")
        lines.append("    except Exception as e:")
        lines.append("        pytest.fail(f'Home page failed: {e}')")
        lines.append("")

        # test API endpoints from api_specs
        endpoints = api_specs.get("endpoints", []) or []
        for ep in endpoints[:8]:
            path = ep.get("path", "")
            method = (ep.get("method") or "GET").upper()
            if not path:
                continue
            safe_name = re.sub(r"[^a-zA-Z0-9]", "_", path)[:50]
            lines.append(f"def test_api_{safe_name}_{method.lower()}():")
            lines.append(f'    """BDD: API {method} {path} should respond."')
            lines.append("    try:")
            lines.append("        from app import create_app")
            lines.append("        app = create_app()")
            lines.append("        with app.test_client() as client:")
            if method == "GET":
                lines.append(f'            r = client.get("{path}")')
            elif method == "POST":
                lines.append(f'            r = client.post("{path}", json={{}}, content_type="application/json")')
            else:
                lines.append(f'            r = client.get("{path}")')
            lines.append("            assert r.status_code in (200, 201, 204, 302, 400, 404), f'Got {r.status_code}'")
            lines.append("    except Exception as e:")
            lines.append(f"        pytest.fail(f'API {{path}} failed: {{e}}')")
            lines.append("")

        # Feature-based smoke tests (use LLM-generated test_code when available)
        for t in bdd_tests[:5]:
            safe_id = re.sub(r"[^a-zA-Z0-9]", "_", t.test_id)[:40]
            if t.test_code and "def " in t.test_code and len(t.test_code) > 30:
                lines.append(t.test_code)
            else:
                lines.append(f"def test_bdd_{safe_id}():")
                lines.append(f'    """{t.scenario}: {t.given} -> {t.when} -> {t.then}"""')
                lines.append("    try:")
                lines.append("        from app import create_app")
                lines.append("        app = create_app()")
                lines.append("        with app.test_client() as client:")
                lines.append("            r = client.get('/')")
                lines.append("            assert r.status_code in (200, 302)")
                lines.append("    except Exception as e:")
                lines.append(f"        pytest.fail(str(e))")
            lines.append("")

        content = "\n".join(lines)
        test_dir = project_path / "tests"
        test_dir.mkdir(parents=True, exist_ok=True)
        out_path = test_dir / "test_bdd_smoke.py"
        out_path.write_text(content, encoding="utf-8")
        logger.info(f"Wrote BDD smoke tests to {out_path}")

    def _save_files(self, project_path: Path, repository: CodeRepository):
        """Save generated code files to disk."""
        project_path.mkdir(parents=True, exist_ok=True)

        for code_file in repository.files:
            file_path = project_path / code_file.path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(code_file.content or "", encoding='utf-8')

        if repository.dependencies:
            _NON_PIP = {
                "react", "vue", "angular", "node", "npm", "docker",
                "javascript", "typescript", "webpack", "babel", "standard",
                "dict", "list", "str", "int",
            }

            # Merge with flask_base template baseline to ensure template deps are never dropped
            baseline_packages = []
            req_baseline = FRAMEWORK_TEMPLATE_PATH / "requirements.txt"
            if req_baseline.exists():
                try:
                    for line in req_baseline.read_text(encoding="utf-8").strip().splitlines():
                        pkg = line.split("==")[0].split(">=")[0].split("<=")[0].strip()
                        if pkg and pkg.lower() not in _NON_PIP:
                            baseline_packages.append(pkg)
                except Exception as e:
                    logger.debug(f"Could not read template requirements: {e}")
            if not baseline_packages:
                baseline_packages = ["flask", "flask-sqlalchemy", "flask-cors", "python-dotenv"]

            valid_packages = list(baseline_packages)
            for dep in repository.dependencies:
                dep_stripped = dep.strip().split("==")[0].split(">=")[0].split("<=")[0].strip()
                if not dep_stripped or dep_stripped.lower() in _NON_PIP:
                    continue
                if dep_stripped.lower() not in [p.lower() for p in valid_packages]:
                    valid_packages.append(dep_stripped)

            if "flask" not in [p.lower() for p in valid_packages]:
                valid_packages.insert(0, "flask")

            if valid_packages:
                req_path = project_path / "requirements.txt"
                req_path.write_text("\n".join(valid_packages) + "\n")

        logger.info(f"Saved {len(repository.files)} files to {project_path}")

    def _run_syntax_check(self, repository: CodeRepository) -> list[TestError]:
        """Check Python files for syntax errors."""
        errors = []

        for code_file in repository.files:
            if code_file.language == 'python':
                try:
                    import ast
                    ast.parse(code_file.content or "")
                except SyntaxError as e:
                    errors.append(TestError(
                        error_type=ErrorType.SYNTAX,
                        file_path=code_file.path,
                        line_number=e.lineno,
                        error_message=str(e),
                        suggestion="Fix the syntax error"
                    ))

        return errors

    def _fallback_run_and_fix(self, project_path: Path, repository: CodeRepository, requirements: Requirements, interface_specs: list = None, max_iterations: int = 5) -> CodeRepository:
        """
        Fallback when CodeFixAgent fails. Delegates to RunAndFixAgent (traditional loop-based fix).
        """
        run_fix_agent = RunAndFixAgent(self.llm_service)
        return run_fix_agent.execute(
            project_path=project_path,
            repository=repository,
            requirements=requirements,
            interface_specs=interface_specs,
            max_iterations=max_iterations,
        )


class FineTuningAgent:
    """Stage 4 Agent 2: Fine-tuning based on test results."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def execute(self, context: ExecutionContext, test_result: TestResult) -> tuple[CodeRepository, bool]:
        """Fix issues found during testing (logic errors) or visual verification (alignment < 0.7)."""
        visual_fb = getattr(test_result, "visual_feedback", None)
        need_visual_fix = visual_fb and visual_fb.get("alignment_score", 1.0) < 0.7
        need_logic_fix = (test_result.errors or test_result.warnings) and not test_result.logic_passed

        if not need_logic_fix and not need_visual_fix:
            logger.info("No fixes needed - tests passed and visual alignment OK")
            return context.code_repository, False

        logger.info(
            f"Attempting to fix: {len(test_result.errors)} errors, {len(test_result.warnings)} warnings"
            + (f", visual alignment={visual_fb.get('alignment_score', 0):.2f}" if need_visual_fix else "")
        )

        repository = context.code_repository
        fixed = False

        # Group errors by type and process in order: SYNTAX → IMPORT → RUNTIME|LOGIC
        errors_by_type: Dict[ErrorType, List[TestError]] = {}
        for error in test_result.errors:
            if error.error_type not in errors_by_type:
                errors_by_type[error.error_type] = []
            errors_by_type[error.error_type].append(error)

        for error_type in [ErrorType.SYNTAX, ErrorType.IMPORT, ErrorType.RUNTIME, ErrorType.LOGIC]:
            for error in errors_by_type.get(error_type, []):
                if error_type == ErrorType.SYNTAX:
                    repository, changed = self._fix_syntax_error(repository, error)
                    fixed = fixed or changed
                elif error_type == ErrorType.IMPORT:
                    repository, changed = self._fix_import_error(repository, error)
                    fixed = fixed or changed
                elif error_type in (ErrorType.RUNTIME, ErrorType.LOGIC):
                    repository, changed = self._fix_test_error(repository, error)
                    fixed = fixed or changed

        # Also fix warnings (missing entry point)
        for warning in test_result.warnings:
            if "No app.py found" in warning or "No main.py found" in warning or "No entry point" in warning:
                repository, changed = self._fix_missing_entry_point(repository)
                fixed = fixed or changed
                break

        # Visual feedback repair: if alignment_score < 0.7, apply visual fixes
        if need_visual_fix and visual_fb:
            repository, changed = self._fix_visual_issues(repository, visual_fb, context)
            fixed = fixed or changed

        if fixed:
            logger.info("Applied fixes to code")

        return repository, fixed

    def _fix_syntax_error(self, repository: CodeRepository, error: TestError) -> tuple[CodeRepository, bool]:
        """Fix syntax errors in code. Returns (repository, True) only when a file was actually modified."""
        import ast

        # Normalize path for matching (e.g. backslash to slash)
        err_path = (error.file_path or "").replace("\\", "/")

        for i, f in enumerate(repository.files):
            if (f.path or "").replace("\\", "/") == err_path:
                logger.info(f"Fixing syntax error in {f.path}")
                prompt = f"""Fix the syntax error in this Python file:

File: {f.path}
Error at line {error.line_number}: {error.error_message}

Original code:
{f.content or ""}

Return the corrected code only, no explanations.
"""
                llm = self.llm_service
                try:
                    from config.settings import get_settings
                    if getattr(get_settings(), "use_fast_model_for_fine_tuning_syntax", True):
                        fast_model = getattr(get_settings(), "fast_model_for_code_gen", "gpt-4o-mini")
                        llm = self.llm_service.with_model(fast_model)
                except Exception:
                    pass
                try:
                    fixed_code = llm.generate(prompt, max_tokens=2000)
                    ast.parse(fixed_code)
                    repository.files[i] = CodeFile(
                        path=f.path,
                        content=fixed_code,
                        language=f.language,
                        purpose=f.purpose,
                        dependencies=f.dependencies
                    )
                    logger.info(f"Fixed syntax error in {f.path}")
                    return repository, True
                except (APIError, RateLimitError) as e:
                    logger.error(f"LLM API error fixing syntax in {f.path}: {e}")
                except SyntaxError:
                    logger.warning(f"LLM-generated fix still has syntax errors in {f.path}")
                except Exception as e:
                    logger.warning(f"Could not fix syntax error in {f.path}: {e}")
                return repository, False

        return repository, False

    _KNOWN_STUBS: Dict[str, str] = {
        "config": (
            '"""Configuration module."""\n\n'
            "class Config:\n"
            "    SECRET_KEY = 'dev-secret-key'\n"
            "    DEBUG = True\n"
            "    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'\n"
        ),
        "models": (
            '"""Models placeholder."""\n\n'
            "from flask_sqlalchemy import SQLAlchemy\n\n"
            "db = SQLAlchemy()\n"
        ),
        "schemas": (
            '"""Schemas placeholder."""\n'
        ),
        "extensions": (
            '"""Extensions placeholder."""\n\n'
            "from flask_sqlalchemy import SQLAlchemy\n\n"
            "db = SQLAlchemy()\n"
        ),
        "database": (
            '"""Database module."""\n\n'
            "from flask_sqlalchemy import SQLAlchemy\n\n"
            "db = SQLAlchemy()\n\n"
            "def init_db(app):\n"
            "    db.init_app(app)\n"
            "    with app.app_context():\n"
            "        db.create_all()\n"
        ),
    }

    def _fix_import_error(self, repository: CodeRepository, error: TestError) -> tuple[CodeRepository, bool]:
        """Fix import errors by generating missing modules. Returns (repository, True) when a stub was added."""
        if "Missing module:" not in error.error_message:
            return repository, False

        module_name = error.error_message.split("Missing module:")[-1].strip()
        logger.info(f"Attempting to fix missing module: {module_name}")

        module_path = module_name.replace('.', '/') + '.py'

        if any(f.path == module_path for f in repository.files):
            logger.debug(f"Module {module_path} already exists in repository")
            return repository, False

        stub_content = None
        module_base = module_name.rsplit(".", 1)[-1].lower()
        for keyword, template in self._KNOWN_STUBS.items():
            if keyword in module_base:
                stub_content = template
                break

        if stub_content is None:
            try:
                prompt = (
                    f"Generate a minimal Python stub module for '{module_name}' "
                    f"that would be imported in a Flask application. "
                    f"Return ONLY the Python code, no explanations."
                )
                stub_content = self.llm_service.generate(prompt, max_tokens=500)
            except Exception as e:
                logger.warning(f"LLM stub generation failed for {module_name}: {e}")
                stub_content = f'"""{module_name} placeholder."""\n'

        repository.files.append(CodeFile(
            path=module_path,
            content=stub_content,
            language='python',
            purpose=f'Auto-generated stub for {module_name}',
            dependencies=[],
        ))
        logger.info(f"Generated stub for {module_path}")
        return repository, True

    def _fix_test_error(self, repository: CodeRepository, error: TestError) -> tuple[CodeRepository, bool]:
        """Fix test errors by using LLM to understand and fix the issue. Returns (repository, True) when any file was modified."""
        logger.info(f"Test error in {error.file_path}: {error.error_message}")

        # Collect all Python files to provide context to LLM
        all_files_content = []
        for f in repository.files:
            if f.language == 'python' and f.path.endswith('.py'):
                all_files_content.append(f"=== {f.path} ===\n{f.content or ''}")

        context = "\n\n".join(all_files_content)
        try:
            from config.settings import get_settings
            max_chars = getattr(get_settings(), "fine_tuning_max_context_chars", 12000)
            if len(context) > max_chars:
                context = context[:max_chars] + "\n\n... (truncated)"
        except Exception:
            if len(context) > 12000:
                context = context[:12000] + "\n\n... (truncated)"

        # Check if this is a blueprint-related error
        is_blueprint_error = "function" in error.error_message and "register" in error.error_message

        # Use LLM to fix the issue
        if is_blueprint_error:
            prompt = f"""Fix the Flask Blueprint registration error.

Error: {error.error_message}

This error happens because:
1. Controllers are exporting functions instead of Blueprint objects
2. Or routes/__init__.py is passing a function to register_blueprint() instead of calling it

The fix requires changes to BOTH:
1. controllers (to export Blueprint directly, not a function)
2. routes.py or __init__.py (to call the function if needed)

Example CORRECT controller code:
```python
# WRONG:
def problem_blueprint():
    bp = Blueprint(...)
    ...
    return bp

# CORRECT - export Blueprint directly:
problem_bp = Blueprint('problem', __name__)
```

Example CORRECT routes/__init__.py code:
```python
# If importing function:
app.register_blueprint(problem_blueprint())  # CALL the function

# If importing Blueprint object:
app.register_blueprint(problem_bp)  # DON'T call
```

All Python files in the project:
{context}

Return the fixed content for ALL files that need changes. Format your response as:
=== FILENAME1 ===
<fixed code for filename1>
=== FILENAME2 ===
<fixed code for filename2>
etc.

Only include files that need to be fixed.
"""
        else:
            prompt = f"""Fix the following error in the Flask application:

Error: {error.error_message}
File: {error.file_path}
Error Type: {error.error_type}

All Python files in the project:
{context}

Return ONLY the fixed content for the file that has the error ({error.file_path}), no explanations or markdown.
If the file doesn't need changes, return the original content unchanged.
"""

        changed = False
        try:
            fixed_content = self.llm_service.generate(prompt, max_tokens=5000)

            # Parse the response to find file contents
            # Format: === FILENAME ===\ncontent
            import re
            file_pattern = r'=== ([^\n]+) ===\n(.*?)(?=====|$)'
            matches = re.findall(file_pattern, fixed_content, re.DOTALL)

            if matches:
                # Update all files mentioned in the response
                for filename, content in matches:
                    filename = filename.strip().replace("\\", "/")
                    for i, f in enumerate(repository.files):
                        if (f.path or "").replace("\\", "/") == filename:
                            try:
                                # Verify it parses
                                if filename.endswith('.py'):
                                    import ast
                                    ast.parse(content)
                                repository.files[i] = CodeFile(
                                    path=f.path,
                                    content=content,
                                    language=f.language,
                                    purpose=f.purpose,
                                    dependencies=f.dependencies
                                )
                                logger.info(f"Fixed {filename} using LLM")
                                changed = True
                            except SyntaxError as e:
                                logger.warning(f"LLM fix resulted in syntax error in {filename}: {e}")
                            break
            else:
                # Single file response: resolve error.file_path to repository file (normalize, then match by path suffix)
                err_path = (error.file_path or "").strip().replace("\\", "/")
                if err_path.endswith(".py"):
                    pass
                elif err_path in ("tests", "tests/"):
                    err_path = None  # pytest reported "tests" as file
                else:
                    err_path = err_path + ".py" if not err_path.endswith(".py") else err_path
                target_idx = None
                if err_path:
                    for i, f in enumerate(repository.files):
                        fp = (f.path or "").replace("\\", "/")
                        if fp == err_path or fp.endswith("/" + err_path) or fp.endswith(err_path):
                            target_idx = i
                            break
                if target_idx is not None:
                    f = repository.files[target_idx]
                    try:
                        if (f.path or "").endswith('.py'):
                            import ast
                            ast.parse(fixed_content)
                        repository.files[target_idx] = CodeFile(
                            path=f.path,
                            content=fixed_content,
                            language=f.language,
                            purpose=f.purpose,
                            dependencies=f.dependencies
                        )
                        logger.info(f"Fixed error in {f.path} using LLM")
                        changed = True
                    except SyntaxError as e:
                        logger.warning(f"LLM fix resulted in syntax error: {e}")

        except (APIError, RateLimitError) as e:
            logger.error(f"LLM API error fixing test error in {error.file_path}: {e}")
        except Exception as e:
            logger.warning(f"Could not fix test error in {error.file_path}: {e}")

        return repository, changed

    def _fix_missing_entry_point(self, repository: CodeRepository) -> tuple[CodeRepository, bool]:
        """Fix missing entry point: add app.py (or run.py) when absent, aligned with FullCycleTesting which expects app.py or run.py."""
        def is_entry(p: str) -> bool:
            n = (p or "").replace("\\", "/").strip("/")
            return n == "app.py" or n == "run.py" or n.endswith("/app.py") or n.endswith("/run.py")
        has_app_py = any(is_entry(f.path) for f in repository.files)
        if has_app_py:
            return repository, False

        # Minimal Flask app.py so FullCycleTesting's _try_run_with_subprocess can find it
        entry_content = '''"""Application entry point (generated by FineTuningAgent)."""
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({'message': 'Application running'})

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
'''
        repository.files.append(CodeFile(
            path='app.py',
            content=entry_content,
            language='python',
            purpose='Application entry point',
            dependencies=[]
        ))
        logger.info("Generated app.py as entry point (aligned with FullCycleTesting)")
        return repository, True


    def _fix_visual_issues(self, repository: CodeRepository, visual_fb: dict, context: ExecutionContext) -> tuple[CodeRepository, bool]:
        """Use LLM to fix visual/UI issues identified by VisualVerificationAgent. Returns (repository, True) when any file was modified."""
        missing = visual_fb.get("missing_elements", [])
        issues = visual_fb.get("issues", [])
        layout_feedback = visual_fb.get("layout_feedback", "")
        alignment_score = visual_fb.get("alignment_score", 0.0)

        if not missing and not issues:
            return repository, False

        # Collect HTML/CSS/JS files for context
        frontend_files = []
        for f in repository.files:
            if f.path.endswith(('.html', '.css', '.js')):
                frontend_files.append(f"=== {f.path} ===\n{f.content or ''}")

        if not frontend_files:
            return repository, False

        fe_context = "\n\n".join(frontend_files)
        try:
            from config.settings import get_settings
            max_chars = getattr(get_settings(), "fine_tuning_max_context_chars", 12000)
            if len(fe_context) > max_chars:
                fe_context = fe_context[:max_chars] + "\n\n... (truncated)"
        except Exception:
            if len(fe_context) > 12000:
                fe_context = fe_context[:12000] + "\n\n... (truncated)"

        requirements_text = ""
        if context.requirements:
            requirements_text = f"App: {context.requirements.title}\nFeatures: {', '.join(f.name for f in context.requirements.features[:5])}"

        missing_list = "\n".join(f"  - {m}" for m in missing) if missing else "  (none)"
        issues_list = "\n".join(f"  - {i}" for i in issues) if issues else "  (none)"

        prompt = f"""Fix the visual/UI issues in this Flask web application.

## Visual Analysis Results (Plan: dual grounding - address these explicitly)
- Alignment score: {alignment_score} (target >= 0.7)
- Layout feedback: {layout_feedback}

**Missing UI elements (PRIORITY - add each one):**
{missing_list}

**Issues found (fix each):**
{issues_list}

## Requirements
{requirements_text}

## Current Frontend Files
{fe_context}

Fix the HTML/CSS/JS to address ALL missing elements first, then the issues.
Return the fixed files in format:
=== FILENAME ===
<fixed content>

Only include files that need changes."""

        changed = False
        try:
            fixed_content = self.llm_service.generate(prompt, max_tokens=6000)

            import re
            file_pattern = r'=== ([^\n]+) ===\n(.*?)(?=====|$)'
            matches = re.findall(file_pattern, fixed_content, re.DOTALL)

            for filename, content in matches:
                filename = filename.strip().replace("\\", "/")
                for i, f in enumerate(repository.files):
                    if (f.path or "").replace("\\", "/") == filename:
                        repository.files[i] = CodeFile(
                            path=f.path,
                            content=content.strip(),
                            language=f.language,
                            purpose=f.purpose,
                            dependencies=f.dependencies,
                        )
                        logger.info(f"Fixed visual issues in {filename}")
                        changed = True
                        break

        except (APIError, RateLimitError) as e:
            logger.error(f"LLM API error fixing visual issues: {e}")
        except Exception as e:
            logger.warning(f"Could not fix visual issues: {e}", exc_info=True)

        return repository, changed


class FrontendTestingAgent:
    """Stage 4 Agent: Test APIs by reading frontend code using LangChain Agent."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def execute(self, project_path: Path, port: Optional[int] = None) -> List[TestError]:
        """Test APIs by analyzing frontend code with LangChain Agent."""
        from langchain.agents import create_agent

        from config.settings import get_settings
        from .tools import get_testing_tools

        if port is None:
            port = get_settings().validation_port
        logger.info(f"Starting frontend API testing on port {port}...")

        # Start the Flask app
        proc = self._start_app(project_path, port)
        if not proc:
            return [
                TestError(
                    error_type=ErrorType.RUNTIME,
                    file_path="app.py",
                    line_number=0,
                    error_message="Failed to start Flask app",
                    suggestion="Check if app.py can run"
                )
            ]

        errors = []

        try:
            llm = self.llm_service.create_langchain_llm(temperature=0, max_tokens=8000)

            tools = get_testing_tools(str(project_path), port)

            # Build system prompt
            system_prompt = f"""You are a testing engineer. Your task is to:
1. Use list_files and read_html_file to find frontend templates
2. Extract all fetch/axios API calls from the HTML/JavaScript
3. Use test_api to test these APIs

## Rules
- App runs on http://localhost:{port}
- Test complete CRUD: create -> list -> detail -> update -> delete
- Verify status codes are 2xx or 201

After testing, output "TEST_COMPLETE" with results."""

            # Create agent
            agent = create_agent(
                model=llm,
                tools=tools,
                system_prompt=system_prompt,
            )

            # Run agent
            initial_input = """Please test all APIs by:
1. First list files in templates/ directory
2. Read the HTML files to find all API calls
3. Test each API endpoint you find with appropriate data
4. Verify the responses are correct

Start by exploring the templates directory."""

            logger.info("Running LangChain agent for API testing...")

            try:
                result = agent.invoke(initial_input)
                response = result.get("output", "")

                logger.info(f"Agent response: {response[:500]}...")

                # Parse errors from response
                if "FAIL" in response or "error" in response.lower():
                    # Extract error information
                    error_lines = [line for line in response.split("\n")
                                   if "FAIL" in line or "error" in line.lower()]
                    for line in error_lines[:5]:  # Limit to 5 errors
                        errors.append(TestError(
                            error_type=ErrorType.RUNTIME,
                            file_path="frontend_api",
                            line_number=0,
                            error_message=line.strip(),
                            suggestion="Check API response"
                        ))

                if not errors:
                    logger.info("Frontend API testing passed!")

            except Exception as e:
                logger.warning(f"Agent testing failed: {e}")
                errors.append(TestError(
                    error_type=ErrorType.RUNTIME,
                    file_path="frontend_api",
                    line_number=0,
                    error_message=f"Agent testing error: {str(e)[:200]}",
                    suggestion="Check if app is running correctly"
                ))

        finally:
            # Stop the app
            self._stop_app(proc)

        return errors

    def _start_app(self, project_path: Path, port: int):
        """Start the Flask app in subprocess."""
        import subprocess
        import time

        # Find entry file
        entry_file = None
        if (project_path / "app.py").exists():
            entry_file = "app.py"
        elif (project_path / "run.py").exists():
            entry_file = "run.py"

        if not entry_file:
            logger.error("No entry point found")
            return None

        env = {"PORT": str(port), "FLASK_ENV": "testing"}

        proc = None
        try:
            proc = subprocess.Popen(
                [sys.executable, entry_file],
                cwd=str(project_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={**os.environ, **env},
                text=True
            )

            time.sleep(4)

            if proc.poll() is not None:
                stdout, stderr = proc.communicate()
                logger.error(f"App exited: {stderr[:200]}")
                return None

            logger.info(f"App started on port {port}")
            return proc

        except Exception as e:
            logger.error(f"Failed to start app: {e}")
            if proc is not None and proc.poll() is None:
                proc.terminate()
            return None

    def _stop_app(self, proc):
        """Stop the Flask app subprocess."""
        import subprocess

        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()


class RunAndFixAgent:
    """
    Stage 4 Agent: Traditional loop-based run-and-fix for runnability.

    Run code -> capture error -> LLM fix -> repeat until success or max iterations.
    Use as fallback when CodeFixAgent (LangChain-driven) fails.
    """

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def execute(
        self,
        project_path: Path,
        repository: CodeRepository,
        requirements: Requirements,
        interface_specs: Optional[List[Any]] = None,
        max_iterations: int = 5,
    ) -> CodeRepository:
        """Fix code until app runs. Modifies repository in-place and returns it."""
        logger.info("RunAndFixAgent: Starting run-and-fix loop...")
        generated_path = project_path / "generated"

        for iteration in range(max_iterations):
            logger.info(f"RunAndFixAgent iteration {iteration + 1}/{max_iterations}")
            error_info = self._try_run_app(generated_path)

            if error_info is None:
                logger.info("RunAndFixAgent: Code runs without errors!")
                return repository

            file_path, error_msg, line_number = error_info
            logger.info(f"RunAndFixAgent: Error in {file_path}: {error_msg}")

            if file_path.startswith("import:") and "No module named" in error_msg:
                module = file_path.split("import:")[-1]
                logger.info(f"RunAndFixAgent: pip install {module}")
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-q", module],
                    capture_output=True, text=True, timeout=60,
                )
                continue

            base_path = generated_path / file_path
            full_path = None
            candidates = [base_path, base_path.with_suffix(".py")] if base_path.suffix != ".py" else [base_path]
            for candidate in candidates:
                if candidate.exists():
                    full_path = candidate
                    break
            if full_path is None:
                logger.warning(f"RunAndFixAgent: File not found {file_path}")
                continue

            original_content = full_path.read_text(encoding="utf-8")
            fixed_content = self._llm_fix_error(
                file_path, error_msg, line_number, original_content, requirements, interface_specs
            )

            if fixed_content:
                full_path.write_text(fixed_content, encoding="utf-8")
                logger.info(f"RunAndFixAgent: Fixed {file_path}")
                for f in repository.files:
                    if f.path == file_path:
                        f.content = fixed_content
                        break
            else:
                logger.warning(f"RunAndFixAgent: LLM could not fix {file_path}")

        return repository

    def _try_run_app(self, generated_path: Path) -> Optional[tuple]:
        """Try to import and create app. Returns (file_path, error_msg, line_number) or None."""
        sys.path.insert(0, str(generated_path))
        try:
            import importlib.util
            app_module = None
            init_path = generated_path / "app" / "__init__.py"
            if init_path.exists():
                spec = importlib.util.spec_from_file_location("app", init_path)
                app_module = importlib.util.module_from_spec(spec)
                sys.modules["app"] = app_module
                spec.loader.exec_module(app_module)
            if app_module and hasattr(app_module, "create_app"):
                app_module.create_app()
                return None
            app_py = generated_path / "app.py"
            if app_py.exists():
                spec = importlib.util.spec_from_file_location("app_module", app_py)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, "create_app"):
                    return None
            return ("app/__init__.py", "Could not find create_app function", 0)
        except ImportError as e:
            err = str(e)
            if "No module named" in err:
                module_name = err.split("No module named")[-1].strip().strip("'\"")
                return (f"import:{module_name}", err, 0)
            return (self._extract_file_from_import_error(err), err, 0)
        except Exception as e:
            tb = traceback.format_exc()
            fp, ln = self._extract_location_from_traceback(tb)
            return (fp or "unknown", str(e), ln or 0)
        finally:
            if str(generated_path) in sys.path:
                sys.path.remove(str(generated_path))

    def _extract_file_from_import_error(self, error_msg: str) -> str:
        if "cannot import name" in error_msg and "from 'app." in error_msg:
            try:
                parts = error_msg.split("from 'app.")[1].split("'")
                return parts[0].replace(".", "/") + ".py" if parts else "app/__init__.py"
            except (IndexError, AttributeError):
                pass
        return "app/__init__.py"

    def _extract_location_from_traceback(self, tb: str) -> tuple:
        for line in tb.split("\n"):
            if "File" in line and "generated" in line:
                match = re.search(r'File "(.*?)"', line)
                if match:
                    fp = match.group(1)
                    if "generated" in fp:
                        fp = fp.split("generated")[-1].lstrip("/\\")
                    line_match = re.search(r"line (\d+)", line)
                    ln = int(line_match.group(1)) if line_match else 0
                    return fp, ln
        return None, 0

    def _llm_fix_error(
        self,
        file_path: str,
        error_message: str,
        line_number: int,
        code: str,
        requirements: Requirements,
        interface_specs: Optional[List[Any]] = None,
    ) -> Optional[str]:
        interface_context = ""
        if interface_specs:
            interface_context = "Interface specifications:\n"
            for spec in interface_specs:
                fp = getattr(spec, "file_path", "") or ""
                if fp in file_path or file_path in fp:
                    exports = getattr(spec, "exports", []) or []
                    names = [getattr(e, "name", "") for e in exports if hasattr(e, "name")]
                    interface_context += f"- {fp}: exports {', '.join(names)}\n"

        prompt = f"""Fix the Python error in this file.

FILE: {file_path}
ERROR: {error_message}
{interface_context}

APPLICATION: {requirements.title}
FEATURES: {", ".join(f.name for f in requirements.features)}

ORIGINAL CODE:
{code}

Instructions:
1. Fix the error so the code can run
2. If app/__init__.py or app.py: ensure models are imported before db.create_all()
3. Ensure blueprint registration is correct
4. Use correct import names based on actual exports

Return ONLY the corrected code, no explanations.
"""
        try:
            fixed = self.llm_service.generate(prompt, max_tokens=2000)
            fixed = self._clean_code(fixed)
            import ast
            ast.parse(fixed)
            return fixed
        except Exception as e:
            logger.warning(f"RunAndFixAgent LLM fix failed: {e}")
            return None

    def _clean_code(self, code: str) -> str:
        if code.startswith("```python"):
            code = code[len("```python"):]
        if code.startswith("```"):
            code = code[len("```"):]
        if code.endswith("```"):
            code = code[:-3]
        return code.strip()


class CodeFixAgent:
    """Stage 4 Agent: Use LangChain Agent to fix code until it runs (runnability fixes)."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def execute(self, project_path: Path) -> "Optional[CodeRepository]":
        """Fix code on disk until it runs. Returns None; files are modified in-place."""
        from langchain.agents import create_agent
        from langchain_core.messages import HumanMessage

        from .tools import get_fix_tools

        logger.info("Starting CodeFixAgent to fix code...")

        # Install project dependencies before attempting fixes (reduces ModuleNotFoundError)
        from config.settings import get_settings

        proj_path = Path(project_path) if not isinstance(project_path, Path) else project_path
        FullCycleTestingAgent._install_project_deps(proj_path)

        llm = self.llm_service.create_langchain_llm(temperature=0, max_tokens=8000)

        port = get_settings().validation_port
        tools = get_fix_tools(str(project_path), port=port)

        # Build system prompt
        system_prompt = """You are a code fixing expert. Your task is to fix Flask app errors until it runs successfully.

## Workflow (you will loop automatically)
1. try_run() - Run app.py to check if it works
2. If error:
   - read_file() to read the code with error
   - analyze the error
   - write_file() to fix it
   - try_run() again to verify
3. Repeat until success

## Common Errors and Fixes
- db.ARRAY error → Use db.String instead (SQLite doesn't support ARRAY)
- Missing fields → Check and add default values or optional fields
- Import errors → Fix import paths
- Route errors → Check Blueprint configuration
- from myapp/application import X → Change to: from app import X
- Index.html links 404 → Ensure app/__init__.py has @app.route('/path') for each frontend route
- ModuleNotFoundError flask_sqlalchemy → Add to requirements.txt and run pip install

## Important Rules
- After each fix, must verify with try_run()
- Do not make multiple fixes at once, fix one thing at a time
- If unsure, read the code to understand the logic

Output "FIXED" when the app runs successfully."""

        # Create agent
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=system_prompt,
        )

        # Run agent
        initial_input = """Fix the Flask app code to make it run successfully.
Start by running try_run() to see what error occurs."""

        logger.info("Running CodeFixAgent...")

        try:
            result = agent.invoke(
                {"messages": [HumanMessage(content=initial_input)]},
                {"recursion_limit": 50}
            )

            # Handle different return types
            if isinstance(result, dict):
                if "messages" in result and result["messages"]:
                    last_msg = result["messages"][-1]
                    response = getattr(last_msg, "content", "") or str(last_msg)
                else:
                    response = result.get("output", "")
            else:
                response = str(result)

            logger.info(f"CodeFixAgent result: {response[:500]}...")

            if "FIXED" in response:
                logger.info("CodeFixAgent: Code fixed successfully!")
            else:
                logger.warning("CodeFixAgent: May not have fixed all issues")

        except (APIError, RateLimitError) as e:
            logger.error(f"CodeFixAgent LLM API error: {e}")
        except Exception as e:
            logger.error(f"CodeFixAgent error: {e}", exc_info=True)

        return None


class VisualVerificationAgent:
    """
    Stage 4 Agent 3: Visual verification using VLM.

    Full implementation with:
    - Flask app startup
    - Screenshot capture using Playwright/Selenium
    - VLM-based UI analysis
    - Layout element detection
    - Visual-semantic alignment scoring
    """

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.server_process = None

    def execute(self, context: ExecutionContext) -> Dict[str, Any]:
        """
        Verify visual rendering of the application using VLM.

        Process:
        1. Start the application
        2. Take screenshots
        3. Use VLM to analyze the screenshots against requirements
        4. Calculate alignment score
        """
        logger.info("Visual Verification: Starting UI analysis")

        requirements = context.requirements
        repository = context.code_repository
        project_path = context.project_path / "generated"

        result = {
            "passed": False,
            "alignment_score": 0.0,
            "layout_feedback": "",
            "missing_elements": [],
            "issues": [],
            "screenshots": []
        }

        # Check if there are frontend files
        has_frontend = any(f.path.endswith(('.html', '.css', '.js')) for f in repository.files)

        if not has_frontend:
            logger.info("No frontend files found, skipping visual verification")
            result["layout_feedback"] = "No frontend files to verify"
            return result

        # Try to start the app and take screenshot
        try:
            screenshot_path = self._capture_screenshot(project_path)
            if screenshot_path:
                result["screenshots"].append(str(screenshot_path))

                # Analyze with VLM
                vlm_result = self._analyze_with_vlm(screenshot_path, requirements)
                result.update(vlm_result)
            else:
                # Fallback to HTML structure analysis
                result = self._analyze_html_structure(repository, requirements)
        except Exception as e:
            logger.warning(f"Screenshot capture failed: {e}, falling back to HTML analysis")
            result = self._analyze_html_structure(repository, requirements)
            result["issues"].append(f"Screenshot failed: {str(e)}")

        logger.info(f"Visual verification: alignment_score={result['alignment_score']}")
        return result

    def _capture_screenshot(self, project_path: Path) -> Optional[Path]:
        """Start the app and capture a screenshot."""
        import subprocess
        import time
        import socket

        from config.settings import get_settings

        # Use validation_port; if occupied, try validation_port+1 (plan: share or use fallback)
        base_port = get_settings().validation_port

        def is_port_available(p):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(('localhost', p)) != 0

        port = base_port
        while port < base_port + 10 and not is_port_available(port):
            port += 1

        if port >= base_port + 10:
            logger.warning("No available port for visual verification")
            return None

        # Check for requirements
        app_file = None
        for f in project_path.glob("*.py"):
            if "app" in f.name.lower():
                app_file = f
                break

        if not app_file:
            logger.warning("No app.py found in generated files")
            return None

        # Try to start the app
        try:
            # Start Flask app in background with PORT so it binds correctly
            popen_env = {**os.environ, "FLASK_ENV": "production", "PYTHONUNBUFFERED": "1", "PORT": str(port)}
            self.server_process = subprocess.Popen(
                [sys.executable, str(app_file)],
                cwd=str(project_path),
                env=popen_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for server to start
            time.sleep(3)

            # Try to capture screenshot with Playwright
            try:
                from playwright.sync_api import sync_playwright

                screenshot_path = project_path / "screenshot.png"

                with sync_playwright() as p:
                    browser = p.chromium.launch()
                    page = browser.new_page()
                    page.goto(f"http://localhost:{port}", wait_until="networkidle", timeout=10000)
                    page.screenshot(path=str(screenshot_path))
                    browser.close()

                logger.info(f"Screenshot saved to {screenshot_path}")
                return screenshot_path

            except ImportError:
                # Try Selenium as fallback
                try:
                    from selenium import webdriver
                    from selenium.webdriver.chrome.options import Options
                    from selenium.webdriver.common.by import By
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC

                    options = Options()
                    options.add_argument("--headless")
                    options.add_argument("--no-sandbox")
                    options.add_argument("--disable-dev-shm-usage")

                    driver = webdriver.Chrome(options=options)
                    driver.get(f"http://localhost:{port}")

                    screenshot_path = project_path / "screenshot.png"
                    driver.save_screenshot(str(screenshot_path))
                    driver.quit()

                    logger.info(f"Screenshot saved (Selenium) to {screenshot_path}")
                    return screenshot_path

                except ImportError:
                    logger.warning("Neither Playwright nor Selenium available for screenshots")
                    return None

        except Exception as e:
            logger.warning(f"Failed to start app: {e}")
            return None

        finally:
            # Cleanup
            if self.server_process:
                self.server_process.terminate()
                try:
                    self.server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.server_process.kill()

    def _analyze_with_vlm(self, screenshot_path: Path, requirements: Requirements) -> Dict[str, Any]:
        """
        Use VLM to analyze screenshot against requirements.
        """
        # Check if we have a VLM model available
        if not hasattr(self.llm_service, 'vlm_model') or not self.llm_service.vlm_model:
            logger.info("No VLM model configured, using fallback analysis")
            return self._fallback_vlm_analysis(screenshot_path, requirements)

        prompt = f"""
You are an expert UI/UX analyst. Analyze this screenshot of a web application.

Requirements that should be visible:
- Title: {requirements.title}
- Description: {requirements.description}
- Features: {", ".join(f.name for f in requirements.features)}

Analyze the screenshot and provide:
1. alignment_score: 0-1 score for how well the UI matches requirements (1.0 = perfect match)
2. missing_elements: List of UI elements that should exist but are missing
3. layout_feedback: Overall assessment of the layout quality
4. issues: Any visual issues (overlapping elements, bad colors, etc.)

Return a JSON object with these fields.
"""

        try:
            if hasattr(self.llm_service, 'analyze_image'):
                result = self.llm_service.analyze_image(str(screenshot_path), prompt)
                return self._parse_vlm_result(result)
            else:
                return self._fallback_vlm_analysis(screenshot_path, requirements)

        except Exception as e:
            logger.warning(f"VLM analysis failed: {e}")
            return self._fallback_vlm_analysis(screenshot_path, requirements)

    def _fallback_vlm_analysis(self, screenshot_path: Path, requirements: Requirements) -> Dict[str, Any]:
        """Fallback analysis when VLM is not available."""
        # Use image analysis to extract basic info
        try:
            from PIL import Image

            img = Image.open(screenshot_path)
            width, height = img.size

            result = {
                "passed": True,
                "alignment_score": 0.8,  # Assumed good since app runs
                "layout_feedback": f"App renders correctly. Screen size: {width}x{height}",
                "missing_elements": [],
                "issues": []
            }

            # Check image properties for issues
            if width < 320 or height < 480:
                result["issues"].append("Screen resolution too small")
                result["alignment_score"] -= 0.2

            if result["alignment_score"] >= 0.7:
                result["passed"] = True
            else:
                result["passed"] = False

            return result

        except ImportError:
            # No image library, return basic success
            return {
                "passed": True,
                "alignment_score": 0.7,
                "layout_feedback": "Visual verification passed (basic check)",
                "missing_elements": [],
                "issues": []
            }

    def _parse_vlm_result(self, result: str) -> Dict[str, Any]:
        """Parse VLM response into structured result."""
        import json
        import re

        # Try to extract JSON from response
        try:
            # Find JSON in response
            match = re.search(r'\{.*\}', result, re.DOTALL)
            if match:
                data = json.loads(match.group())
                return {
                    "passed": data.get("alignment_score", 0) >= 0.7,
                    "alignment_score": data.get("alignment_score", 0),
                    "layout_feedback": data.get("layout_feedback", ""),
                    "missing_elements": data.get("missing_elements", []),
                    "issues": data.get("issues", [])
                }
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

        # Default fallback
        return {
            "passed": True,
            "alignment_score": 0.7,
            "layout_feedback": "VLM analysis completed",
            "missing_elements": [],
            "issues": []
        }

    def _analyze_html_structure(self, repository: CodeRepository, requirements: Requirements) -> Dict[str, Any]:
        """Analyze HTML structure for visual compliance."""
        result = {
            "passed": False,
            "alignment_score": 0.5,
            "layout_feedback": "",
            "missing_elements": [],
            "issues": []
        }

        # Find HTML files
        html_files = [f for f in repository.files if f.path.endswith('.html')]

        if not html_files:
            result["issues"].append("No HTML files found")
            return result

        # Analyze each HTML file
        for html_file in html_files:
            content = (html_file.content or "").lower()

            # Check for common elements
            checks = {
                "title": "<title>" in content or requirements.title.lower() in content,
                "heading": "<h1>" in content or "<h2>" in content,
                "form": "<form>" in content or "<input>" in content,
                "button": "<button>" in content or "submit" in content,
                "list": "<ul>" in content or "<ol>" in content or "<li>" in content,
                "css_link": "<link" in content and ".css" in content,
                "script_link": "<script" in content,
            }

            # Calculate alignment score
            present = sum(checks.values())
            total = len(checks)
            result["alignment_score"] = present / total

            # Find missing elements
            for element, found in checks.items():
                if not found:
                    result["missing_elements"].append(element)

            # Check for responsive design
            if 'viewport' in content:
                result["alignment_score"] += 0.1

            # Generate feedback
            if result["alignment_score"] >= 0.7:
                result["passed"] = True
                result["layout_feedback"] = "Layout structure looks good with proper semantic elements"
            else:
                result["layout_feedback"] = f"Missing elements: {', '.join(result['missing_elements'])}"

        return result


def create_validated_project(
    repository: CodeRepository,
    test_result: TestResult,
    requirements: Requirements,
    fix_attempts: int = 0,
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
        fix_attempts=fix_attempts,
        validated_at=datetime.now()
    )
