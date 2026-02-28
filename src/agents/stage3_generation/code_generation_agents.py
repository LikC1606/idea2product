"""Stage 3 Code Generation Agents - Using LangChain Agent."""

import json
import re
import shutil
from pathlib import Path
from typing import List, Dict, Optional

from langchain_core.messages import HumanMessage
from langchain.agents import create_agent

from src.core.data_models import (
    Requirements,
    EngineeringPlan,
    CodeRepository,
    CodeFile,
    DirectoryStructure,
    CodeSkeleton,
)
from src.core.context import ExecutionContext
from src.services.llm_service import LLMService
from src.utils.logger import get_logger
from src.utils.skeleton_builder import build_skeleton_from_pyi_stubs
from src.agents.stage3_generation.tools import (
    get_tools,
    set_project_path,
    set_project_id,
)

logger = get_logger(__name__)

# 框架模板路径
FRAMEWORK_TEMPLATE_PATH = (
    Path(__file__).parent.parent.parent.parent / "templates" / "flask_base"
)


class CodeGenerationAgent:
    """Stage 3 Agent: Generates code based on engineering plan using LangChain Agent."""

    def __init__(self, llm_service: LLMService, settings=None):
        self.llm_service = llm_service
        self.settings = settings

    def execute(
        self,
        context: ExecutionContext,
        mining_by_task: Optional[Dict[str, str]] = None,
        memory_context: Optional[str] = None,
    ) -> CodeRepository:
        """Generate code using LangChain Agent.
        mining_by_task: Pre-fetched mining context from CodeMiningAgent (task_id -> context_str).
        memory_context: Pre-fetched cross-project snippets from CodeMemoryAgent.pre_execute.
        """
        requirements = context.requirements
        plan = context.engineering_plan
        project_path = context.project_path / "generated"

        logger.info(f"Generating code for {len(plan.tasks)} tasks")

        # 获取pyi_stubs和api_specs
        pyi_stubs = getattr(plan, "pyi_stubs", {}) or {}
        api_specs = getattr(plan, "api_specs", {}) or {}

        # Build CodeSkeleton from pyi_stubs (Interface-First); fallback to interface_specs when pyi_stubs empty
        skeleton = build_skeleton_from_pyi_stubs(
            pyi_stubs=pyi_stubs,
            file_structure=plan.file_structure,
            entry_point="app.py",
            interface_specs=getattr(plan, "interface_specs", None),
        )
        logger.info(
            f"Skeleton: {len(skeleton.interfaces)} interfaces, {len(skeleton.dependency_graph.nodes)} nodes"
        )

        # Step 1: 加载框架模板
        logger.info("Loading framework template...")
        files = self._load_framework_template(project_path)

        # 初始化工具（可选启用 code memory 检索）
        set_project_path(project_path)
        set_project_id(getattr(context, "project_id", None))
        code_memory = None
        if self.settings and getattr(self.settings, "enable_code_memory", False):
            from src.services.code_memory_service import CodeMemoryService

            code_memory = CodeMemoryService(self.settings.code_memory_db_path)
        cross_project = (
            getattr(self.settings, "enable_cross_project_memory", False)
            if self.settings
            else False
        )
        tools = get_tools(
            project_path,
            code_memory_service=code_memory,
            project_id=context.project_id,
            cross_project_memory=cross_project,
        )

        # 构建上下文（只传文件列表）
        context_md = self._build_context_md(files)

        # Build BDD constraints from engineering plan (test-driven)
        bdd_constraints = ""
        bdd_cases = getattr(plan, "bdd_test_cases", []) or []
        if bdd_cases:
            bdd_constraints = "\n## BDD Test Cases (your code MUST satisfy these)\n"
            for bc in bdd_cases[:10]:
                bdd_constraints += f"- **{bc.feature}**: Given {bc.given}, When {bc.when}, Then {bc.then}\n"
            bdd_constraints += (
                "\nEnsure your implementation passes all the above test scenarios.\n"
            )

        # Step 2: 按任务顺序处理
        mining_by_task = mining_by_task or {}
        memory_context = memory_context or ""

        for task in plan.tasks:
            logger.info(f"Processing task {task.id}: {task.name}")
            mining_context = mining_by_task.get(task.id, "")

            files = self._process_task_with_tools(
                task=task,
                files=files,
                requirements=requirements,
                plan=plan,
                context_md=context_md,
                tools=tools,
                project_path=project_path,
                pyi_stubs=pyi_stubs,
                api_specs=api_specs,
                skeleton=skeleton,
                mining_context=mining_context,
                memory_context=memory_context,
                bdd_constraints=bdd_constraints,
                code_memory=code_memory,
                project_id=context.project_id,
            )

            # Incremental symbol table update after each task
            if code_memory:
                self._update_symbol_table(code_memory, project_path, context.project_id)

            # Incremental snippet save: enables search_similar_snippet for subsequent tasks
            if code_memory:
                self._incremental_save_snippets(
                    code_memory, project_path, context.project_id, files
                )

            # 更新上下文
            context_md = self._build_context_md(files)

        # 构建最终产物
        directories = list(
            set(
                str(Path(f.path).parent)
                for f in files
                if Path(f.path).parent != Path(".")
            )
        )

        structure = DirectoryStructure(
            root="generated",
            directories=directories,
            entry_point=self._find_entry_point(files),
        )

        dependencies = self._extract_dependencies(plan, files)

        # Consistency check: ensure all frontend_routes are registered in app/__init__.py
        files = self._ensure_frontend_routes(files, plan)

        logger.info(f"Generated {len(files)} files")
        return CodeRepository(
            skeleton=skeleton,
            files=files,
            structure=structure,
            dependencies=dependencies,
            readme_content=self._generate_readme(requirements),
        )

    def _load_framework_template(self, target_path: Path) -> List[CodeFile]:
        """加载框架模板文件到目标目录"""
        files = []

        if not FRAMEWORK_TEMPLATE_PATH.exists():
            logger.warning(f"Framework template not found: {FRAMEWORK_TEMPLATE_PATH}")
            return files

        # 复制框架文件到目标目录
        shutil.copytree(FRAMEWORK_TEMPLATE_PATH, target_path, dirs_exist_ok=True)

        # 读取所有框架文件
        for file_path in FRAMEWORK_TEMPLATE_PATH.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(FRAMEWORK_TEMPLATE_PATH)
                dest_path = str(rel_path)

                try:
                    content = file_path.read_text(encoding="utf-8")
                    files.append(
                        CodeFile(
                            path=dest_path,
                            content=content,
                            language=self._get_language(dest_path),
                            purpose=f"Framework file: {dest_path}",
                            dependencies=[],
                        )
                    )
                except Exception as e:
                    logger.warning(f"Failed to read framework file {file_path}: {e}")

        logger.info(f"Loaded {len(files)} framework files")
        return files

    def _process_task_with_tools(
        self,
        task,
        files: List[CodeFile],
        requirements: Requirements,
        plan: EngineeringPlan,
        context_md: str,
        tools,
        project_path: Path,
        max_iterations: int = 100,
        pyi_stubs: Dict = None,
        api_specs: Dict = None,
        skeleton: CodeSkeleton = None,
        mining_context: str = "",
        memory_context: str = "",
        bdd_constraints: str = "",
        code_memory=None,
        project_id: Optional[str] = None,
    ) -> List[CodeFile]:
        """使用 LangChain Agent，让 LLM 自己选择看哪些文件"""

        # 读取框架规范
        framework_spec = ""
        spec_path = FRAMEWORK_TEMPLATE_PATH / "SPEC.md"
        if spec_path.exists():
            try:
                framework_spec = spec_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                pass

        # 构建 pyi_stubs 信息（任务级过滤：只传相关文件）
        task_relevant_paths = self._get_task_relevant_files(task, plan)
        filtered_pyi = pyi_stubs or {}
        if task_relevant_paths:
            normalized_relevant = {p.replace("\\", "/") for p in task_relevant_paths}
            filtered_pyi = {
                k: v
                for k, v in (pyi_stubs or {}).items()
                if k.replace("\\", "/") in normalized_relevant
                or any(pr in k or k in pr for pr in normalized_relevant)
            }
        if not filtered_pyi:
            filtered_pyi = pyi_stubs or {}

        pyi_info = ""
        if filtered_pyi:
            pyi_info = "\n## Type Definitions (.pyi stubs)\n"
            for path, stub in filtered_pyi.items():
                pyi_info += f"\n### {path}\n```\n{stub}\n```\n"

        # Interface specs from Stage 2 (complements pyi_stubs; describes exports/imports)
        interface_specs = getattr(plan, "interface_specs", []) or []
        filtered_interface_specs = interface_specs
        if task_relevant_paths:
            norm_rel = {p.replace("\\", "/").replace(".py", "").rstrip("/") for p in task_relevant_paths}
            filtered_interface_specs = [
                s for s in interface_specs
                if s.file_path.replace("\\", "/").replace(".py", "").rstrip("/") in norm_rel
                or any(nr in s.file_path or s.file_path in nr for nr in norm_rel)
            ]
        if not filtered_interface_specs:
            filtered_interface_specs = interface_specs

        interface_specs_info = ""
        if filtered_interface_specs:
            interface_specs_info = "\n## Interface Specs (exports/imports - align with pyi_stubs)\n"
            for spec in filtered_interface_specs:
                interface_specs_info += f"\n### {spec.file_path}\n"
                interface_specs_info += f"Purpose: {spec.purpose}\n"
                if spec.layer:
                    interface_specs_info += f"Layer: {spec.layer}\n"
                if spec.exports:
                    interface_specs_info += "Exports:\n"
                    for e in spec.exports:
                        if hasattr(e, "name"):
                            interface_specs_info += f"  - {getattr(e, 'type', '?')}: {e.name}\n"
                        else:
                            interface_specs_info += f"  - {e}\n"
                if spec.imports:
                    interface_specs_info += f"Imports: {', '.join(spec.imports[:10])}\n"

        # Build structured skeleton constraint (Interface-First), task-filtered
        skeleton_info = ""
        if skeleton:
            try:
                interfaces_to_use = skeleton.interfaces
                if task_relevant_paths:
                    norm_rel = {
                        p.replace("\\", "/").replace(".py", "").rstrip("/")
                        for p in task_relevant_paths
                    }
                    mod_as_path = lambda m: m.replace(".", "/")
                    interfaces_to_use = [
                        i
                        for i in skeleton.interfaces
                        if mod_as_path(i.module_name) in norm_rel
                        or any(
                            nr in mod_as_path(i.module_name)
                            or mod_as_path(i.module_name) in nr
                            for nr in norm_rel
                        )
                    ]
                if not interfaces_to_use:
                    interfaces_to_use = skeleton.interfaces

                skel_dict = {
                    "interfaces": [
                        {
                            "module_name": i.module_name,
                            "functions": [
                                {
                                    "name": f.get("name"),
                                    "params": f.get("params", []),
                                    "return_type": f.get("return_type"),
                                }
                                for f in i.functions
                            ],
                            "classes": [
                                {"name": c.get("name"), "bases": c.get("bases", [])}
                                for c in i.classes
                            ],
                        }
                        for i in interfaces_to_use
                    ],
                    "dependency_graph": {
                        "nodes": skeleton.dependency_graph.nodes,
                        "edges": skeleton.dependency_graph.edges,
                        "entry_point": skeleton.dependency_graph.entry_point,
                    },
                }
                skeleton_info = "\n## Interface-First Skeleton (MUST follow these constraints)\n```json\n"
                skeleton_info += json.dumps(skel_dict, indent=2, ensure_ascii=False)[
                    :3000
                ]
                skeleton_info += "\n```\nYour implementation MUST respect these interfaces and dependencies.\n"
            except Exception as e:
                logger.warning(f"Could not serialize skeleton: {e}")

        # Proactive module signatures (dependencies already on disk)
        proactive_sigs = self._get_proactive_signatures(
            task, plan, skeleton, project_path, code_memory, project_id
        )

        # 构建 api_specs 信息
        api_info = ""
        if api_specs and api_specs.get("endpoints"):
            api_info = "\n## API Endpoints (how frontend connects to backend)\n"
            for ep in api_specs.get("endpoints", []):
                method = ep.get("method", "?") or "?"
                path = ep.get("path", "?") or "?"
                desc = ep.get("description", "") or ""
                request_fields = ep.get("request")
                response_fields = ep.get("response")
                session_info = ep.get("session_info")

                api_info += f"- {method} {path}: {desc}\n"
                if request_fields:
                    api_info += f"  Request: {request_fields}\n"
                if response_fields:
                    api_info += f"  Response: {response_fields}\n"
                if session_info and isinstance(session_info, dict):
                    sets = session_info.get("sets")
                    sdesc = session_info.get("description", "")
                    if sets and sdesc:
                        api_info += f"  Session: {sets} - {sdesc}\n"

            if api_specs.get("frontend_routes"):
                api_info += "\nFrontend Routes:\n"
                for path, info in api_specs.get("frontend_routes", {}).items():
                    template = (
                        info.get("template", "") if isinstance(info, dict) else info
                    )
                    description = (
                        info.get("description", "") if isinstance(info, dict) else ""
                    )
                    api_info += (
                        f"- {path} -> render_template('{template}'): {description}\n"
                    )

            ui_guidelines = api_specs.get("ui_guidelines")
            if ui_guidelines and isinstance(ui_guidelines, dict):
                api_info += "\nUI Guidelines (MUST follow):\n"
                for k, v in ui_guidelines.items():
                    if v:
                        api_info += f"- {k}: {v}\n"

        # UI Design Spec from Stage 2 - implement exactly per spec
        ui_design_spec = api_specs.get("ui_design_spec") if api_specs else None
        ui_design_spec_context = ""
        if ui_design_spec and isinstance(ui_design_spec, dict):
            parts = [
                "\n## UI Design Spec (MUST implement exactly - designed in Stage 2)\n"
            ]
            if ui_design_spec.get("content_max_width"):
                parts.append(
                    f"- content_max_width: {ui_design_spec['content_max_width']}"
                )
            if ui_design_spec.get("layout_structure"):
                parts.append(
                    f"- layout_structure: {ui_design_spec['layout_structure']}"
                )
            if ui_design_spec.get("layout_rules"):
                parts.append(f"- layout_rules: {ui_design_spec['layout_rules']}")
            page_layouts = ui_design_spec.get("page_layouts") or {}
            if page_layouts:
                parts.append("\nPage layouts (implement per route):")
                for route_path, layout in page_layouts.items():
                    if isinstance(layout, dict):
                        parts.append(f"\n  {route_path}:")
                        sections = layout.get("sections") or []
                        for s in sections:
                            sid = s.get("id", "")
                            desc = s.get("description", "")
                            parts.append(f"    - {sid}: {desc}")
                        es = layout.get("empty_state")
                        if es and isinstance(es, dict):
                            msg = es.get("message", "")
                            cta = es.get("cta", "")
                            show = es.get("show_when", "")
                            parts.append(
                                f'    empty_state: message="{msg}" cta="{cta}" show_when="{show}"'
                            )
                        ls = layout.get("loading_state")
                        if ls and isinstance(ls, dict):
                            t = ls.get("type", "")
                            d = ls.get("description", "")
                            parts.append(f"    loading_state: type={t} - {d}")
            product_rules = ui_design_spec.get("product_grade_rules")
            if product_rules and isinstance(product_rules, list):
                parts.append("\nproduct_grade_rules:")
                for r in product_rules:
                    parts.append(f"  - {r}")
            ui_design_spec_context = "\n".join(parts)

        # Frontend UI section: implement per ui_design_spec if present, else generic rules
        page_layouts = (
            (ui_design_spec or {}).get("page_layouts")
            if isinstance(ui_design_spec, dict)
            else None
        )
        if page_layouts and isinstance(page_layouts, dict) and len(page_layouts) > 0:
            frontend_ui_section = """1. IMPLEMENT the UI exactly as specified in "UI Design Spec" above - it was designed in Stage 2.
2. Follow page_layouts.sections for page structure; empty_state and loading_state for those components.
3. Use content_max_width and layout_rules for layout; product_grade_rules for interaction.
4. Generated frontend MUST include: <link rel="stylesheet" href="/static/css/base.css"> before any custom CSS.
5. Extend base.css in static/css/style.css only - do NOT override base design tokens unless ui_guidelines specify."""
        else:
            frontend_ui_section = """1. Use CSS variables for colors (--primary, --surface, --text) for consistency
2. Forms: proper spacing, focus states, clear error feedback
3. Lists/cards: adequate padding, hover states, responsive grid
4. Buttons: distinct primary/secondary, disabled state
5. Avoid inline styles; use a dedicated static/css/style.css or per-page <style>
6. Follow ui_guidelines from api_specs if provided (theme, colors, layout)
7. Generated frontend MUST include: <link rel="stylesheet" href="/static/css/base.css"> before any custom CSS
8. Extend base.css in static/css/style.css only - do NOT override base design tokens unless ui_guidelines specify"""

        # Algorithm / implementation guidance from Stage 2
        algorithm_context = ""
        algorithms = getattr(plan, "algorithms", {}) or {}
        algorithm = algorithms.get(task.id) if isinstance(task.id, str) else None
        if algorithm:
            algorithm_context = (
                "\n## Algorithm / Implementation Guidance (for this task)\n"
            )
            algorithm_context += f"{algorithm.implementation_approach or ''}\n"
            if getattr(algorithm, "hf_models", None) and getattr(
                algorithm, "hf_usage_notes", None
            ):
                algorithm_context += f"\nHF Model usage: {algorithm.hf_usage_notes}\n"
            libs = getattr(algorithm, "libraries", []) or []
            if libs:
                algorithm_context += f"Libraries: {', '.join(libs)}\n"

        # Auth implementation checklist (when api_specs has auth endpoints)
        auth_checklist_section = ""
        _endpoints = (api_specs or {}).get("endpoints") or []
        _has_auth = any(
            "auth" in str(ep.get("path", "")).lower() for ep in _endpoints
        )
        if _has_auth:
            auth_checklist_section = """
## 【CRITICAL】Auth 实现检查清单 (app has login/register)
1. app/__init__.py 必须：from app.routes.auth import auth_bp 并 app.register_blueprint(auth_bp, url_prefix='/api/auth')
2. 必须添加页面路由：@app.route('/login') 渲染 login.html，@app.route('/register') 渲染 register.html
3. login.html 必须包含指向 /register 的链接（如「没有账号？去注册」）
4. register.html 必须包含指向 /login 的链接（如「已有账号？去登录」）
5. 未登录用户访问主应用路由时，应重定向到 /login
6. 所有新建的 API blueprint 均需在 app/__init__.py 中完成注册（auth_bp, xxx_bp 等）
"""

        # 构建 system prompt
        system_prompt = f"""You are a Flask development expert. Your job is to complete the given task by reading files, modifying them, and creating new ones.

## Framework Spec (read this first to understand the project structure)
{framework_spec[:2000] if framework_spec else "N/A"}
{pyi_info}
{interface_specs_info}
{skeleton_info}
{proactive_sigs}
{api_info}
{ui_design_spec_context}
{mining_context}
{memory_context}
{bdd_constraints}
{algorithm_context}

## CRITICAL Naming Conventions (NEVER violate)
- Package name: ALWAYS use "app" (NOT myapp, application, or any variant)
- All imports: from app import db | from app.models.xxx import Model
- app.py entry: from app import create_app (NOT from application or myapp)

## Task to Complete
Name: {task.name}
Description: {task.description}

## 【CRITICAL】前端代码必须严格遵循 api_specs
前端发送数据时，必须严格按照 api_specs 中定义的 request 字段和类型生成代码：

1. **字段名必须完全一致**：
   - api_specs 定义了 `author_id: "int"`，前端就必须发送 `author_id`
   - 不能省略任何必填字段！

2. **字段类型必须完全一致**：
   - `"bool"` → JavaScript `true`/`false`（不是字符串 "true"/"false"）
   - `"int"` → JavaScript 数字（如 `parseInt(value)` 或 `Number(value)`）
   - `"array"` 或 `["str"]` → JavaScript 数组（如 `["tag1", "tag2"]`）

3. **【强制】关联 ID（如 author_id）必须从 session 获取**：
   - 如果 api_specs 的 request 中需要 author_id，后端从 session 获取
   - 前端不需要传递 author_id，后端自己从 session['user_id'] 读取
   - 例如：创建博客时，后端用 session.get('user_id') 获取当前用户ID

4. 数据格式：所有 API 用 JSON，禁止用 FormData

## 【CRITICAL】Session 认证实现
如果 api_specs 中的 endpoint 有 session_info 说明，必须按要求实现：

1. **后端设置 session**：登录成功后设置 session['user_id'] = user.id（或其他 session_info 指定的变量）

2. **后端获取当前用户**：提供 /api/auth/me 端点，从 session 获取用户ID并返回用户信息

3. **确保 app/__init__.py 设置了 secret_key**：app.secret_key = 'your-secret-key'
{auth_checklist_section}
## API Endpoints
{api_info}

## Code Quality Requirements
1. Error handling: Use try/except for file I/O, JSON parsing, and external API calls; return appropriate HTTP status on failure
2. Type hints: Add type hints to all function parameters and return values
3. Docstrings: Add docstrings to public functions and classes (one-line for simple, multi-line for complex)
4. Input validation: Validate request JSON keys and types before use; return 400 with clear message on invalid input
5. Avoid: bare except, print() for debugging, hardcoded magic strings

## Frontend UI Requirements
{frontend_ui_section}

## Important Requirements
1. You MUST use tools to explore the project - start by listing files to see what's there
   - Before implementing, call search_similar_snippet(task-relevant keywords) to find reusable patterns (e.g. "flask crud api", "sqlalchemy model")
   - When calling other modules, ALWAYS use get_module_signatures(module_name) first to get interface signatures
   - After creating or modifying a .py file, call validate_syntax(file_path) to verify. If it reports an error, fix the code before proceeding.
2. Database initialization rule:
   - CRITICAL: db = SQLAlchemy() MUST be defined ONLY in app/__init__.py
   - All model files (app/models/*.py) MUST import db from app: from app import db
   - Do NOT create new SQLAlchemy() instances in model files!
   - **IMPORTANT**: 使用 SQLite 兼容的类型：
     - 禁止使用 db.ARRAY (SQLite 不支持)
     - 数组字段用 db.String 存储（如用逗号分隔： "tag1,tag2,tag3"）
     - 或者用 JSON 字符串存储
3. When creating new route files (e.g., app/routes/xxx.py), you MUST also modify app/__init__.py:
   - Add import: from app.routes.xxx import xxx_bp
   - Add registration: app.register_blueprint(xxx_bp, url_prefix='/api')
   - Use: from config import get_config (NOT 'config.get_config' string!)
   - CRITICAL: Inside the Blueprint, use RELATIVE paths only! Example: @blogs_bp.route('/') NOT @blogs_bp.route('/api/blogs')
   - If url_prefix='/api/blogs', then routes inside should be @bp.route('/') NOT @bp.route('/api/blogs')
4. CRITICAL: You MUST add ALL frontend routes in app/__init__.py for EACH template:
   - For each template (e.g., blog.html, blog_list.html, blog_detail.html), add a route that renders it
   - Example: @app.route('/blogs/<int:id>') def blog_detail(): return render_template('blog_detail.html')
   - MUST match the frontend_routes specified above!
   - IMPORTANT: Frontend routes ONLY render templates, do NOT pass data! All data should be fetched via JavaScript API calls in the template
5. CRITICAL: index.html links MUST match api_specs.frontend_routes exactly:
   - If frontend_routes has /blogs, index.html links MUST be /blogs and /api/blogs (NOT /notes or /api/notes)
   - Page title and description MUST match requirements.title (e.g. "Blog App" not "Notes App" if building a blog)
6. Generate ACTUAL working HTML with forms, buttons, and API calls - not placeholder text!
7. **【强制】在修改任何文件之前，必须先阅读文件内容**：
   - 先用 list_files() 查看所有文件
   - 再用 read_file() 读取目标文件的内容
   - 了解现有代码结构后再修改，不能直接覆盖！
   - 特别注意 app/__init__.py 等入口文件的结构
9. CRITICAL: Do NOT worry about whether packages are installed in the current environment.
   Do NOT output messages like "please run pip install" or "dependencies not installed".
   Just write the code with the correct imports. Dependencies will be installed separately.
   Your ONLY job is to write correct Python/HTML/CSS/JS code files using the tools.

## When Task is Complete
Reply with "TASK_COMPLETE" when you have finished the task."""

        try:
            logger.info(f"  Agent processing task {task.id}...")

            llm = self.llm_service.create_langchain_llm(temperature=0, max_tokens=8000)

            # 创建 Agent
            agent = create_agent(
                model=llm,
                tools=tools,
                system_prompt=system_prompt,
            )

            # 用户消息
            frontend_routes_hint = ""
            if api_specs and api_specs.get("frontend_routes"):
                routes = list(api_specs["frontend_routes"].keys())[:5]
                frontend_routes_hint = f"\nApp title: {requirements.title}. Frontend routes: {routes}. When editing index.html, links MUST use these paths (e.g. first non-root route for main nav)."
                # Single-page hint for simple CRUD apps
                title_lower = (requirements.title or "").lower()
                is_simple = len(routes) <= 1 or any(
                    kw in title_lower for kw in ("todo", "task list", "notes", "简单")
                )
                if is_simple:
                    frontend_routes_hint += " SINGLE-PAGE: index.html should contain the full UI (add form + list + delete/mark-done buttons). Use fetch() to call API. No separate /new or /edit pages needed."

            # Build task-relevant files list and key file excerpts
            task_relevant_files = self._get_task_relevant_files(task, plan)
            task_files_hint = ""
            if task_relevant_files:
                task_files_hint = f"\nFiles relevant to this task (read these first): {', '.join(task_relevant_files[:10])}"
                # Include excerpts for up to 2 key .py files
                excerpts = []
                for rel_path in task_relevant_files[:3]:
                    if not rel_path.endswith(".py"):
                        continue
                    fp = project_path / rel_path
                    if fp.exists():
                        try:
                            content = fp.read_text(encoding="utf-8")
                            preview = "\n".join(content.splitlines()[:80])
                            excerpts.append(
                                f"\n--- {rel_path} (current, first ~80 lines) ---\n{preview}"
                            )
                        except Exception as ex:
                            logger.debug("Could not read file for excerpt: %s", ex)
                if excerpts:
                    task_files_hint += (
                        "\n\nKey file previews:" + "".join(excerpts)[:2500]
                    )

            user_message = f"""Current project structure:
{context_md[:1000] if context_md else "No files yet"}
{frontend_routes_hint}
{task_files_hint}

Start by listing files to see the current state, then complete the task: {task.description}

Remember to use tools (list_files, read_file, write_file, modify_file, validate_syntax) to interact with the project."""

            # 运行 Agent
            result = agent.invoke(
                {"messages": [HumanMessage(content=user_message)]},
                {"recursion_limit": max_iterations},
            )

            # 获取最终消息
            if result and "messages" in result:
                final_msg = result["messages"][-1]
                preview = (getattr(final_msg, "content", None) or "")[:200]
                logger.info(f"  Task {task.id} output: {preview}")

            # Post-task syntax validation and retry (max 1 retry)
            syntax_errors = self._validate_all_python_syntax(project_path)
            retry_count = 0
            while syntax_errors and retry_count < 1:
                err_summary = "\n".join(
                    f"- {fp}: {err}" for fp, err in syntax_errors[:5]
                )
                fix_msg = f"""Fix the following Python syntax errors. Use read_file, modify_file, and validate_syntax to fix each file.

{err_summary}

Fix one file at a time, then call validate_syntax to verify."""
                logger.info(
                    f"  Task {task.id}: {len(syntax_errors)} syntax errors, attempting fix..."
                )
                try:
                    agent.invoke(
                        {"messages": [HumanMessage(content=fix_msg)]},
                        {"recursion_limit": 20},
                    )
                except Exception as fix_e:
                    logger.warning(f"  Syntax fix attempt failed: {fix_e}")
                syntax_errors = self._validate_all_python_syntax(project_path)
                retry_count += 1

            logger.info(f"  Task {task.id} completed")

        except Exception as e:
            logger.warning(
                f"  Agent error on task {task.id} ({task.name}): {e}", exc_info=True
            )

        # 更新 files 列表
        files = self._scan_generated_files(project_path)
        return files

    def _scan_generated_files(self, project_path: Path) -> List[CodeFile]:
        """扫描生成的文件，更新文件列表"""
        files = []
        text_extensions = [".py", ".html", ".txt", ".md", ".json", ".env"]

        for f in project_path.rglob("*"):
            if (
                f.is_file()
                and f.suffix in text_extensions
                and "__pycache__" not in str(f)
            ):
                try:
                    content = f.read_text(encoding="utf-8")
                    rel_path = str(f.relative_to(project_path))
                    files.append(
                        CodeFile(
                            path=rel_path,
                            content=content,
                            language=self._get_language(rel_path),
                            purpose=f"Generated file: {rel_path}",
                            dependencies=[],
                        )
                    )
                except Exception as e:
                    logger.warning(f"  Failed to read {f}: {e}")

        logger.info(f"  Scanned {len(files)} files from project")
        return files

    def _incremental_save_snippets(
        self,
        code_memory,
        project_path: Path,
        project_id: str,
        files: List[CodeFile],
    ) -> None:
        """Save snippets from generated .py files after each task for search_similar_snippet."""
        pid = project_id or "current"
        for cf in files:
            if cf.language != "python" or not (cf.path or "").endswith(".py"):
                continue
            try:
                code_memory.add_snippets_from_file(
                    content=(cf.content or ""),
                    file_path=cf.path,
                    project_id=pid,
                    purpose=(cf.purpose or cf.path)[:200],
                )
            except Exception as ex:
                logger.debug("Incremental snippet save failed for %s: %s", cf.path, ex)

    def _update_symbol_table(
        self, code_memory, project_path: Path, project_id: str
    ) -> None:
        """Parse generated .py files and update the symbol table incrementally."""
        import ast as _ast
        from src.core.data_models import SymbolTableEntry

        for py_file in project_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                source = py_file.read_text(encoding="utf-8")
                tree = _ast.parse(source)
                module_name = (
                    str(py_file.relative_to(project_path))
                    .replace("/", ".")
                    .replace("\\", ".")
                    .removesuffix(".py")
                )
                for node in _ast.iter_child_nodes(tree):
                    if isinstance(node, _ast.FunctionDef):
                        args = ", ".join(a.arg for a in node.args.args)
                        ret = ""
                        if node.returns:
                            ret = f" -> {_ast.unparse(node.returns)}"
                        code_memory.add_symbol(
                            SymbolTableEntry(
                                symbol_name=node.name,
                                symbol_type="function",
                                module=module_name,
                                signature=f"def {node.name}({args}){ret}",
                                docstring=_ast.get_docstring(node) or "",
                                line_number=node.lineno,
                            ),
                            project_id=project_id or "current",
                        )
                    elif isinstance(node, _ast.ClassDef):
                        code_memory.add_symbol(
                            SymbolTableEntry(
                                symbol_name=node.name,
                                symbol_type="class",
                                module=module_name,
                                signature=f"class {node.name}",
                                docstring=_ast.get_docstring(node) or "",
                                line_number=node.lineno,
                            ),
                            project_id=project_id or "current",
                        )
            except Exception as ex:
                logger.debug("Could not process symbol for code memory: %s", ex)
                continue

    def _validate_all_python_syntax(self, project_path: Path) -> List[tuple]:
        """Validate syntax of all .py files. Returns [(file_path, error_msg), ...]."""
        import ast as _ast

        errors = []
        for py_file in project_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                rel = str(py_file.relative_to(project_path))
                source = py_file.read_text(encoding="utf-8")
                _ast.parse(source)
            except SyntaxError as e:
                errors.append((rel, f"Line {e.lineno}: {e.msg}"))
            except Exception as ex:
                logger.debug("Could not validate syntax for %s: %s", py_file, ex)
                continue
        return errors

    def _get_task_relevant_files(self, task, plan: EngineeringPlan) -> List[str]:
        """Get list of file paths relevant to this task."""
        paths = set()
        paths.update(getattr(task, "files_to_add", []) or [])
        paths.update(getattr(task, "files_to_modify", []) or [])
        for spec in getattr(plan, "file_structure", []) or []:
            related = getattr(spec, "related_tasks", []) or []
            if task.id in related:
                paths.add(getattr(spec, "path", "") or "")
        return [p for p in sorted(paths) if p]

    def _get_proactive_signatures(
        self,
        task,
        plan: EngineeringPlan,
        skeleton: Optional[CodeSkeleton],
        project_path: Path,
        code_memory,
        project_id: Optional[str],
    ) -> str:
        """Pre-inject signatures of dependency modules that already exist on disk."""
        import ast as _ast

        task_paths = set(
            p.replace("\\", "/") for p in self._get_task_relevant_files(task, plan)
        )
        if not task_paths or not skeleton:
            return ""

        dep_graph = getattr(skeleton, "dependency_graph", None)
        if not dep_graph or not getattr(dep_graph, "edges", []):
            return ""

        dep_modules = set()
        for e in dep_graph.edges:
            from_path = (e.get("from") or "").replace("\\", "/")
            to_path = (e.get("to") or "").replace("\\", "/")
            if from_path in task_paths and to_path:
                dep_modules.add(to_path)

        if not dep_modules:
            return ""

        lines = [
            "\n## Pre-loaded Module Signatures (dependencies already implemented)\n"
        ]
        for dep_path in sorted(dep_modules):
            p = dep_path.replace("\\", "/")
            if not p.endswith(".py"):
                p = p + ".py"
            full_path = project_path / p
            if not full_path.exists():
                continue
            module_name = (
                dep_path.replace("/", ".").replace("\\", ".").removesuffix(".py")
            )
            sigs = []
            if code_memory and project_id:
                try:
                    symbols = code_memory.get_symbols_by_module(module_name, project_id)
                    sigs = [
                        s.signature or s.symbol_name
                        for s in symbols
                        if s.signature or s.symbol_name
                    ]
                except Exception as ex:
                    logger.debug("Could not get symbols for %s: %s", module_name, ex)
            if not sigs:
                try:
                    source = full_path.read_text(encoding="utf-8")
                    tree = _ast.parse(source)
                    for node in _ast.iter_child_nodes(tree):
                        if isinstance(node, _ast.FunctionDef):
                            args = ", ".join(a.arg for a in node.args.args)
                            ret = (
                                f" -> {_ast.unparse(node.returns)}"
                                if node.returns
                                else ""
                            )
                            sigs.append(f"def {node.name}({args}){ret}")
                        elif isinstance(node, _ast.ClassDef):
                            bases = (
                                ", ".join(_ast.unparse(b) for b in node.bases)
                                if node.bases
                                else ""
                            )
                            sigs.append(f"class {node.name}({bases})")
                except Exception as ex:
                    logger.debug("Could not parse %s for signatures: %s", full_path, ex)
                    continue
            if sigs:
                lines.append(f"### {module_name}")
                for s in sigs[:15]:
                    lines.append(f"  {s}")
                lines.append("")
        return "\n".join(lines)[:2000] if len(lines) > 1 else ""

    def _build_context_md(self, files: List[CodeFile]) -> str:
        """构建上下文 - 只传文件列表"""
        lines = ["# Current Project State", ""]
        lines.append("## Project File Structure (use list_files to see all)")
        for f in files:
            lines.append(f"- {f.path}")
        lines.append("")
        return "\n".join(lines)

    def _get_language(self, path: str) -> str:
        """Determine language from file extension."""
        ext = Path(path).suffix.lower()
        lang_map = {
            ".py": "python",
            ".html": "html",
            ".css": "css",
            ".js": "javascript",
            ".json": "json",
            ".txt": "text",
            ".md": "markdown",
        }
        return lang_map.get(ext, "text")

    def _find_entry_point(self, files: List[CodeFile]) -> str:
        """Find the main entry point file."""
        for f in files:
            if f.path == "app.py":
                return f.path
            if f.path.endswith("app.py"):
                return f.path
        return files[0].path if files else "app.py"

    def _extract_dependencies(
        self, plan: EngineeringPlan, files: List[CodeFile]
    ) -> List[str]:
        """Extract Python dependencies from the plan. Always include flask_base deps."""
        deps = set(plan.dependencies or [])
        deps.add("flask")
        # flask_base template uses these; ensure they're in requirements.txt
        deps.update(["flask-sqlalchemy", "flask-cors", "python-dotenv"])
        return list(deps)

    def _ensure_frontend_routes(
        self, files: List[CodeFile], plan: EngineeringPlan
    ) -> List[CodeFile]:
        """Ensure app/__init__.py has routes for all api_specs.frontend_routes."""
        api_specs = getattr(plan, "api_specs", {}) or {}
        frontend_routes = api_specs.get("frontend_routes") or {}
        if not frontend_routes:
            return files

        init_content = None
        init_idx = None
        for i, f in enumerate(files):
            if f.path.replace("\\", "/") in ("app/__init__.py", "app\\__init__.py"):
                init_content = (f.content or "")
                init_idx = i
                break
        if init_content is None or init_idx is None:
            return files

        # Check which routes are missing
        routes_to_add = []
        for path, info in frontend_routes.items():
            if path == "/":
                continue
            if not isinstance(info, dict):
                template = "index.html"
            else:
                template = info.get("template", "index.html")
            # Check if route exists (match @app.route(path) with flexible quoting)
            escaped = re.escape(path)
            pattern = rf"@app\.route\s*\(\s*['\"]{escaped}['\"]"
            if not re.search(pattern, init_content):
                routes_to_add.append((path, template))

        if not routes_to_add:
            return files

        # Generate route code to insert before "with app.app_context()"
        insert_lines = []
        for path, template in routes_to_add:
            fn_name = re.sub(r"[^a-zA-Z0-9_]", "_", path.strip("/")) or "page"
            insert_lines.append(f"    @app.route('{path}')")
            insert_lines.append(f"    def {fn_name}():")
            insert_lines.append(f"        return render_template('{template}')")
            insert_lines.append("")

        insert_block = "\n".join(insert_lines)
        marker = "with app.app_context():"
        if marker in init_content:
            init_content = init_content.replace(
                marker,
                insert_block + "    " + marker,
                1,
            )
        else:
            init_content = init_content.rstrip() + "\n\n    " + insert_block

        new_files = list(files)
        new_files[init_idx] = CodeFile(
            path=files[init_idx].path,
            content=init_content,
            language=files[init_idx].language,
            purpose=files[init_idx].purpose,
            dependencies=files[init_idx].dependencies,
        )
        logger.info(
            f"Added {len(routes_to_add)} missing frontend routes to app/__init__.py"
        )
        return new_files

    def _generate_readme(self, requirements: Requirements) -> str:
        """Generate README content."""
        return f"""# {requirements.title}

{requirements.description}

## Setup
```bash
pip install -r requirements.txt
python app.py
```

## Features
""" + "\n".join(
            f"- {f.name}: {f.description}" for f in requirements.features
        )


class CodeMemoryAgent:
    """Code Memory Agent - stores and retrieves code knowledge.

    Plan: maintains dynamic symbol table (AST + global symbols). CodeGenerationAgent
    incrementally updates symbol table after each task; when generating code that
    calls other modules, it retrieves precise interface signatures via CodeMemoryService
    rather than loading full implementations, avoiding context hallucination.

    pre_execute: Seeds symbol table from skeleton before generation; optionally
    prefetches cross-project snippets as memory_context for CodeGenerationAgent.
    """

    def __init__(self, llm_service: LLMService, settings=None):
        self.llm_service = llm_service
        self.settings = settings

    def pre_execute(self, context: ExecutionContext) -> str:
        """Run before CodeGenerationAgent: seed symbol table from skeleton, optionally
        prefetch cross-project snippets. Returns memory_context string for prompts."""
        memory_context = ""
        if not self.settings or not getattr(self.settings, "enable_code_memory", False):
            logger.debug("CodeMemoryAgent.pre_execute: skipped (enable_code_memory=False)")
            return memory_context

        plan = getattr(context, "engineering_plan", None)
        if not plan:
            return memory_context

        try:
            from src.services.code_memory_service import CodeMemoryService

            svc = CodeMemoryService(self.settings.code_memory_db_path)
            project_id = getattr(context, "project_id", "unknown") or "unknown"

            # 1a. Seed symbol table from skeleton (fallback when pyi_stubs empty)
            pyi_stubs = getattr(plan, "pyi_stubs", {}) or {}
            file_structure = getattr(plan, "file_structure", []) or []
            interface_specs = getattr(plan, "interface_specs", None)
            if pyi_stubs or file_structure or interface_specs:
                skeleton = build_skeleton_from_pyi_stubs(
                    pyi_stubs=pyi_stubs,
                    file_structure=file_structure,
                    entry_point="app.py",
                    interface_specs=interface_specs,
                )
                if skeleton.interfaces or skeleton.dependency_graph.nodes:
                    svc.add_symbols_from_skeleton(skeleton, project_id)

            # 1b. Optional cross-project snippet prefetch
            if getattr(self.settings, "enable_cross_project_memory", False):
                tasks = getattr(plan, "tasks", []) or []
                queries = []
                for t in tasks[:5]:
                    name = getattr(t, "name", "") or ""
                    desc = getattr(t, "description", "") or ""
                    task_type = (
                        getattr(t.type, "value", str(t.type))
                        if hasattr(t, "type")
                        else ""
                    )
                    if task_type in ("backend", "database"):
                        queries.append(f"flask {name} {desc[:40]}")
                    elif task_type == "frontend":
                        queries.append(f"flask jinja2 template {name}")
                    else:
                        queries.append(f"flask {name}")
                seen = set()
                snippets_text = []
                for q in queries[:3]:
                    if q.strip() in seen:
                        continue
                    seen.add(q.strip())
                    try:
                        found = svc.search_snippets(
                            query=q,
                            limit=2,
                            project_id=project_id,
                            cross_project=True,
                        )
                        for s in found:
                            snippets_text.append(
                                f"=== {s.function_name} ===\n{s.code[:600]}\n"
                            )
                    except Exception as ex:
                        logger.debug(f"Prefetch search failed: {ex}")
                if snippets_text:
                    memory_context = (
                        "\n## Cross-Project Reference Snippets (adapt to your project)\n"
                        + "\n".join(snippets_text)[:2500]
                    )
        except Exception as e:
            logger.warning(f"CodeMemoryAgent.pre_execute failed: {e}")
        return memory_context

    def execute(self, context: ExecutionContext, repository: CodeRepository) -> None:
        """Save generated code snippets to memory when ENABLE_CODE_MEMORY is True."""
        if not self.settings or not getattr(self.settings, "enable_code_memory", False):
            logger.info("CodeMemoryAgent: skipped (enable_code_memory=False)")
            return
        try:
            from src.services.code_memory_service import CodeMemoryService

            svc = CodeMemoryService(self.settings.code_memory_db_path)
            project_id = getattr(context, "project_id", "unknown")
            count = 0
            for cf in repository.files:
                if cf.language != "python" or not cf.path.endswith(".py"):
                    continue
                n = svc.add_snippets_from_file(
                    content=(cf.content or ""),
                    file_path=cf.path,
                    project_id=project_id,
                    purpose=cf.purpose[:200] if cf.purpose else cf.path,
                )
                count += n
            logger.info(
                f"CodeMemoryAgent: saved {count} function-level snippets to memory"
            )
        except Exception as e:
            logger.warning(f"CodeMemoryAgent save failed: {e}")


def _build_mining_context_for_task(
    task,
    skeleton: CodeSkeleton,
    plan: EngineeringPlan,
    settings,
    llm_service: Optional[LLMService] = None,
) -> str:
    """Fetch external code examples for a task with interface adaptation.
    Returns formatted markdown string for prompt injection."""
    from src.services.code_mining_service import CodeMiningService

    task_type = (
        getattr(task.type, "value", str(task.type)) if hasattr(task, "type") else ""
    )

    # Build interface_spec from skeleton
    interface_spec = {"functions": [], "classes": []}
    task_relevant_paths = set()
    for spec in getattr(plan, "file_structure", []) or []:
        if task.id in (getattr(spec, "related_tasks", []) or []):
            task_relevant_paths.add(getattr(spec, "path", "") or "")
    task_relevant_paths.update(getattr(task, "files_to_add", []) or [])
    task_relevant_paths.update(getattr(task, "files_to_modify", []) or [])
    task_name_lower = task.name.lower().replace(" ", "_")
    norm_rel = {p.replace("\\", "/").replace(".py", "").rstrip("/") for p in task_relevant_paths if p}

    for iface in skeleton.interfaces:
        mod_path = iface.module_name.replace(".", "/")
        is_related = (
            mod_path in norm_rel
            or any(nr in mod_path or mod_path in nr for nr in norm_rel)
            or task_name_lower in iface.module_name.lower()
            or not norm_rel
        )
        if not is_related:
            continue
        for fn in iface.functions:
            interface_spec["functions"].append(
                {
                    "name": fn.get("name"),
                    "params": fn.get("params", []),
                    "return_type": fn.get("return_type", "Any"),
                }
            )
        for cls in iface.classes:
            interface_spec["classes"].append(
                {"name": cls.get("name"), "bases": cls.get("bases", [])}
            )

    algorithms = (plan.algorithms or {}).get(task.id) if plan else None
    algo_extras = []
    if algorithms:
        libs = getattr(algorithms, "libraries", []) or []
        ds = getattr(algorithms, "data_structures", []) or []
        algo_extras = [str(x) for x in (libs[:2] + ds[:2]) if x]
    extra = " " + " ".join(algo_extras) if algo_extras else ""

    if task_type == "frontend":
        query = f"flask jinja2 template {task.name} {getattr(task, 'description', '')[:40]}{extra}"
        language = "html"
        interface_spec = {"templates": [], "components": []}
    elif task_type in ("backend", "database"):
        query = f"flask {task.name} {getattr(task, 'description', '')[:50]}{extra}"
        language = "python"
    else:
        return ""

    try:
        cache_path = None
        if settings:
            data_dir = getattr(settings, "data_dir", None)
            if data_dir:
                cache_path = Path(data_dir) / "code_mining_cache.json"
        svc = CodeMiningService(
            github_token=getattr(settings, "github_token", None),
            search_limit=getattr(settings, "github_search_limit", 3),
            cache_path=cache_path,
        )
        use_llm = (
            getattr(settings, "enable_llm_code_adaptation", False) if settings else False
        )
        results = svc.search_and_adapt(
            query,
            interface_spec,
            language=language,
            llm_service=llm_service if use_llm else None,
            use_llm_adaptation=use_llm,
        )
        if not results:
            return ""
        out = "\n## External Code References (adapt to your project)\n"
        code_lang = "html" if task_type == "frontend" else "python"
        for r in results[:2]:
            repo = r.get("repo") or {}
            if repo.get("url") or repo.get("html_url"):
                out += f"- {repo.get('full_name', '')}: {repo.get('url') or repo.get('html_url', '')}\n"
            adapted = r.get("adapted_code")
            if adapted:
                out += f"  Reference snippet:\n```{code_lang}\n{adapted[:600]}\n```\n"

        if interface_spec.get("functions") or interface_spec.get("classes"):
            out += "\nRequired interfaces for this task:\n"
            for fn in interface_spec.get("functions", [])[:5]:
                out += f"  - def {fn['name']}({', '.join(fn.get('params', []))}) -> {fn.get('return_type', 'Any')}\n"
            for cls in interface_spec.get("classes", [])[:3]:
                out += f"  - class {cls['name']}\n"

        return out[:800] if out else ""
    except Exception as e:
        logger.debug(f"Code mining for task {task.id} skipped: {e}")
        return ""


class CodeMiningAgent:
    """Code Mining Agent - fetches external code from GitHub with interface adaptation.

    Runs before CodeGenerationAgent to pre-fetch mining context per task.
    Returns {task_id: mining_context_str} for CodeGenerationAgent to consume.
    """

    def __init__(self, llm_service: LLMService, settings=None):
        self.llm_service = llm_service
        self.settings = settings

    def execute(self, context: ExecutionContext) -> Dict[str, str]:
        """Pre-fetch mining context for all tasks. Returns {task_id: mining_context_str}."""
        mining_by_task: Dict[str, str] = {}
        if not self.settings or not getattr(self.settings, "enable_code_mining", False):
            logger.debug("CodeMiningAgent: skipped (enable_code_mining=False)")
            return mining_by_task

        plan = getattr(context, "engineering_plan", None)
        if not plan:
            return mining_by_task

        pyi_stubs = getattr(plan, "pyi_stubs", {}) or {}
        file_structure = getattr(plan, "file_structure", []) or []
        interface_specs = getattr(plan, "interface_specs", None)
        if not pyi_stubs and not file_structure:
            return mining_by_task

        skeleton = build_skeleton_from_pyi_stubs(
            pyi_stubs=pyi_stubs,
            file_structure=file_structure,
            entry_point="app.py",
            interface_specs=interface_specs,
        )

        for task in getattr(plan, "tasks", []) or []:
            task_id = getattr(task, "id", None)
            if not task_id:
                continue
            ctx = _build_mining_context_for_task(
                task, skeleton, plan, self.settings, self.llm_service
            )
            if ctx:
                mining_by_task[task_id] = ctx

        logger.info(
            f"CodeMiningAgent: pre-fetched mining context for {len(mining_by_task)} tasks"
        )
        return mining_by_task
