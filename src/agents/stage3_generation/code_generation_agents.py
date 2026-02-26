"""Stage 3 Code Generation Agents - Using LangChain Agent."""

import json
import re
import shutil
from pathlib import Path
from typing import List, Dict

from langchain_core.messages import HumanMessage
from langchain.agents import create_agent

from src.core.data_models import (
    Requirements, EngineeringPlan, CodeRepository, CodeFile,
    DirectoryStructure, CodeSkeleton
)
from src.core.context import ExecutionContext
from src.services.llm_service import LLMService
from src.utils.logger import get_logger
from src.utils.skeleton_builder import build_skeleton_from_pyi_stubs
from src.agents.stage3_generation.tools import get_tools, set_project_path

logger = get_logger(__name__)

# 框架模板路径
FRAMEWORK_TEMPLATE_PATH = Path(__file__).parent.parent.parent.parent / "templates" / "flask_base"


class CodeGenerationAgent:
    """Stage 3 Agent: Generates code based on engineering plan using LangChain Agent."""

    def __init__(self, llm_service: LLMService, settings=None):
        self.llm_service = llm_service
        self.settings = settings

    def execute(self, context: ExecutionContext) -> CodeRepository:
        """Generate code using LangChain Agent."""
        requirements = context.requirements
        plan = context.engineering_plan
        project_path = context.project_path / "generated"

        logger.info(f"Generating code for {len(plan.tasks)} tasks")

        # 获取pyi_stubs和api_specs
        pyi_stubs = getattr(plan, 'pyi_stubs', {}) or {}
        api_specs = getattr(plan, 'api_specs', {}) or {}

        # Build CodeSkeleton from pyi_stubs (Interface-First)
        skeleton = build_skeleton_from_pyi_stubs(
            pyi_stubs=pyi_stubs,
            file_structure=plan.file_structure,
            entry_point="app.py",
        )
        logger.info(f"Skeleton: {len(skeleton.interfaces)} interfaces, {len(skeleton.dependency_graph.nodes)} nodes")

        # Step 1: 加载框架模板
        logger.info("Loading framework template...")
        files = self._load_framework_template(project_path)

        # 初始化工具（可选启用 code memory 检索）
        set_project_path(project_path)
        code_memory = None
        if self.settings and getattr(self.settings, "enable_code_memory", False):
            from src.services.code_memory_service import CodeMemoryService
            code_memory = CodeMemoryService(self.settings.code_memory_db_path)
        tools = get_tools(project_path, code_memory_service=code_memory)

        # 构建上下文（只传文件列表）
        context_md = self._build_context_md(files)

        # Build BDD constraints from engineering plan (test-driven)
        bdd_constraints = ""
        bdd_cases = getattr(plan, 'bdd_test_cases', []) or []
        if bdd_cases:
            bdd_constraints = "\n## BDD Test Cases (your code MUST satisfy these)\n"
            for bc in bdd_cases[:10]:
                bdd_constraints += f"- **{bc.feature}**: Given {bc.given}, When {bc.when}, Then {bc.then}\n"
            bdd_constraints += "\nEnsure your implementation passes all the above test scenarios.\n"

        # Step 2: 按任务顺序处理
        for task in plan.tasks:
            logger.info(f"Processing task {task.id}: {task.name}")
            mining_context = ""
            if self.settings and getattr(self.settings, "enable_code_mining", False):
                mining_context = self._get_mining_context(task, skeleton=skeleton)

            files = self._process_task_with_tools(
                task=task,
                files=files,
                requirements=requirements,
                context_md=context_md,
                tools=tools,
                project_path=project_path,
                pyi_stubs=pyi_stubs,
                api_specs=api_specs,
                skeleton=skeleton,
                mining_context=mining_context,
                bdd_constraints=bdd_constraints,
            )

            # Incremental symbol table update after each task
            if code_memory:
                self._update_symbol_table(code_memory, project_path, context.project_id)

            # 更新上下文
            context_md = self._build_context_md(files)

        # 构建最终产物
        directories = list(set(
            str(Path(f.path).parent) for f in files
            if Path(f.path).parent != Path(".")
        ))

        structure = DirectoryStructure(
            root="generated",
            directories=directories,
            entry_point=self._find_entry_point(files)
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
            readme_content=self._generate_readme(requirements)
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
                    content = file_path.read_text(encoding='utf-8')
                    files.append(CodeFile(
                        path=dest_path,
                        content=content,
                        language=self._get_language(dest_path),
                        purpose=f"Framework file: {dest_path}",
                        dependencies=[]
                    ))
                except Exception as e:
                    logger.warning(f"Failed to read framework file {file_path}: {e}")

        logger.info(f"Loaded {len(files)} framework files")
        return files

    def _get_mining_context(self, task, skeleton: "CodeSkeleton" = None) -> str:
        """Fetch external code examples for backend/database tasks with interface adaptation."""
        from src.services.code_mining_service import CodeMiningService
        task_type = getattr(task.type, "value", str(task.type)) if hasattr(task, "type") else ""
        if task_type not in ("backend", "database"):
            return ""

        # Build real interface_spec from skeleton for this task
        interface_spec = {"functions": [], "classes": []}
        if skeleton:
            task_files = getattr(task, "related_files", []) or []
            task_name_lower = task.name.lower().replace(" ", "_")
            for iface in skeleton.interfaces:
                mod_lower = iface.module_name.lower()
                is_related = any(tf in mod_lower for tf in task_files) or task_name_lower in mod_lower
                if is_related or not task_files:
                    for fn in iface.functions:
                        interface_spec["functions"].append({
                            "name": fn.get("name"),
                            "params": fn.get("params", []),
                            "return_type": fn.get("return_type", "Any"),
                        })
                    for cls in iface.classes:
                        interface_spec["classes"].append({
                            "name": cls.get("name"),
                            "bases": cls.get("bases", []),
                        })

        query = f"flask {task.name} {getattr(task, 'description', '')[:50]}"
        try:
            svc = CodeMiningService(
                github_token=getattr(self.settings, "github_token", None),
                search_limit=getattr(self.settings, "github_search_limit", 3),
            )
            results = svc.search_and_adapt(query, interface_spec)
            if not results:
                return ""
            out = "\n## External Code References (adapt to your project)\n"
            for r in results[:2]:
                repo = r.get("repo") or {}
                if repo.get("url"):
                    out += f"- {repo.get('full_name', '')}: {repo.get('url', '')}\n"
                adapted = r.get("adapted_code")
                if adapted:
                    out += f"  Adapted snippet:\n```python\n{adapted[:600]}\n```\n"

            # Add interface constraint context so LLM knows what to implement
            if interface_spec["functions"] or interface_spec["classes"]:
                out += "\nRequired interfaces for this task:\n"
                for fn in interface_spec["functions"][:5]:
                    out += f"  - def {fn['name']}({', '.join(fn.get('params', []))}) -> {fn.get('return_type', 'Any')}\n"
                for cls in interface_spec["classes"][:3]:
                    out += f"  - class {cls['name']}\n"

            return out[:800] if out else ""
        except Exception as e:
            logger.debug(f"Code mining skipped: {e}")
            return ""

    def _process_task_with_tools(self, task, files: List[CodeFile], requirements: Requirements,
                                context_md: str, tools, project_path: Path,
                                max_iterations: int = 100,
                                pyi_stubs: Dict = None,
                                api_specs: Dict = None,
                                skeleton: CodeSkeleton = None,
                                mining_context: str = "",
                                bdd_constraints: str = "") -> List[CodeFile]:
        """使用 LangChain Agent，让 LLM 自己选择看哪些文件"""

        # 读取框架规范
        framework_spec = ""
        spec_path = FRAMEWORK_TEMPLATE_PATH / "SPEC.md"
        if spec_path.exists():
            try:
                framework_spec = spec_path.read_text(encoding='utf-8')
            except:
                pass

        # 构建 pyi_stubs 信息
        pyi_info = ""
        if pyi_stubs:
            pyi_info = "\n## Type Definitions (.pyi stubs)\n"
            for path, stub in pyi_stubs.items():
                pyi_info += f"\n### {path}\n```\n{stub}\n```\n"

        # Build structured skeleton constraint (Interface-First)
        skeleton_info = ""
        if skeleton:
            try:
                skel_dict = {
                    "interfaces": [
                        {
                            "module_name": i.module_name,
                            "functions": [{"name": f.get("name"), "params": f.get("params", []), "return_type": f.get("return_type")}
                                         for f in i.functions],
                            "classes": [{"name": c.get("name"), "bases": c.get("bases", [])} for c in i.classes],
                        }
                        for i in skeleton.interfaces
                    ],
                    "dependency_graph": {
                        "nodes": skeleton.dependency_graph.nodes,
                        "edges": skeleton.dependency_graph.edges,
                        "entry_point": skeleton.dependency_graph.entry_point,
                    },
                }
                skeleton_info = "\n## Interface-First Skeleton (MUST follow these constraints)\n```json\n"
                skeleton_info += json.dumps(skel_dict, indent=2, ensure_ascii=False)[:3000]
                skeleton_info += "\n```\nYour implementation MUST respect these interfaces and dependencies.\n"
            except Exception as e:
                logger.warning(f"Could not serialize skeleton: {e}")

        # 构建 api_specs 信息
        api_info = ""
        if api_specs and api_specs.get("endpoints"):
            api_info = "\n## API Endpoints (how frontend connects to backend)\n"
            for ep in api_specs.get("endpoints", []):
                method = ep.get('method', '?') or '?'
                path = ep.get('path', '?') or '?'
                desc = ep.get('description', '') or ''
                request_fields = ep.get('request')
                response_fields = ep.get('response')
                session_info = ep.get('session_info')

                api_info += f"- {method} {path}: {desc}\n"
                if request_fields:
                    api_info += f"  Request: {request_fields}\n"
                if response_fields:
                    api_info += f"  Response: {response_fields}\n"
                if session_info and isinstance(session_info, dict):
                    sets = session_info.get('sets')
                    sdesc = session_info.get('description', '')
                    if sets and sdesc:
                        api_info += f"  Session: {sets} - {sdesc}\n"

            if api_specs.get("frontend_routes"):
                api_info += "\nFrontend Routes:\n"
                for path, info in api_specs.get("frontend_routes", {}).items():
                    template = info.get("template", "") if isinstance(info, dict) else info
                    description = info.get("description", "") if isinstance(info, dict) else ""
                    api_info += f"- {path} -> render_template('{template}'): {description}\n"

        # 构建 system prompt
        system_prompt = f"""You are a Flask development expert. Your job is to complete the given task by reading files, modifying them, and creating new ones.

## Framework Spec (read this first to understand the project structure)
{framework_spec[:2000] if framework_spec else "N/A"}
{pyi_info}
{skeleton_info}
{api_info}
{mining_context}
{bdd_constraints}

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

## API Endpoints
{api_info}

## Important Requirements
1. You MUST use tools to explore the project - start by listing files to see what's there
   - When you need to call functions from another module, use get_module_signatures(module_name) first to discover the available interfaces
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
8. CRITICAL: Do NOT worry about whether packages are installed in the current environment.
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
            user_message = f"""Current project structure:
{context_md[:1000] if context_md else "No files yet"}
{frontend_routes_hint}

Start by listing files to see the current state, then complete the task: {task.description}

Remember to use tools (list_files, read_file, write_file, modify_file) to interact with the project."""

            # 运行 Agent
            result = agent.invoke(
                {"messages": [HumanMessage(content=user_message)]},
                {"recursion_limit": max_iterations}
            )

            # 获取最终消息
            if result and "messages" in result:
                final_msg = result["messages"][-1]
                logger.info(f"  Task {task.id} output: {final_msg.content[:200]}")

            logger.info(f"  Task {task.id} completed")

        except Exception as e:
            logger.warning(f"  Agent error on task {task.id} ({task.name}): {e}", exc_info=True)

        # 更新 files 列表
        files = self._scan_generated_files(project_path)
        return files

    def _scan_generated_files(self, project_path: Path) -> List[CodeFile]:
        """扫描生成的文件，更新文件列表"""
        files = []
        text_extensions = ['.py', '.html', '.txt', '.md', '.json', '.env']

        for f in project_path.rglob("*"):
            if f.is_file() and f.suffix in text_extensions and '__pycache__' not in str(f):
                try:
                    content = f.read_text(encoding='utf-8')
                    rel_path = str(f.relative_to(project_path))
                    files.append(CodeFile(
                        path=rel_path,
                        content=content,
                        language=self._get_language(rel_path),
                        purpose=f"Generated file: {rel_path}",
                        dependencies=[]
                    ))
                except Exception as e:
                    logger.warning(f"  Failed to read {f}: {e}")

        logger.info(f"  Scanned {len(files)} files from project")
        return files

    def _update_symbol_table(self, code_memory, project_path: Path, project_id: str) -> None:
        """Parse generated .py files and update the symbol table incrementally."""
        import ast as _ast
        from src.core.data_models import SymbolTableEntry

        for py_file in project_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                source = py_file.read_text(encoding="utf-8")
                tree = _ast.parse(source)
                module_name = str(py_file.relative_to(project_path)).replace("/", ".").replace("\\", ".").removesuffix(".py")
                for node in _ast.iter_child_nodes(tree):
                    if isinstance(node, _ast.FunctionDef):
                        args = ", ".join(a.arg for a in node.args.args)
                        ret = ""
                        if node.returns:
                            ret = f" -> {_ast.unparse(node.returns)}"
                        code_memory.add_symbol(SymbolTableEntry(
                            symbol_name=node.name,
                            symbol_type="function",
                            module=module_name,
                            signature=f"def {node.name}({args}){ret}",
                            docstring=_ast.get_docstring(node) or "",
                            line_number=node.lineno,
                        ), project_id=project_id or "current")
                    elif isinstance(node, _ast.ClassDef):
                        code_memory.add_symbol(SymbolTableEntry(
                            symbol_name=node.name,
                            symbol_type="class",
                            module=module_name,
                            signature=f"class {node.name}",
                            docstring=_ast.get_docstring(node) or "",
                            line_number=node.lineno,
                        ), project_id=project_id or "current")
            except Exception:
                continue

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
            '.py': 'python',
            '.html': 'html',
            '.css': 'css',
            '.js': 'javascript',
            '.json': 'json',
            '.txt': 'text',
            '.md': 'markdown'
        }
        return lang_map.get(ext, 'text')

    def _find_entry_point(self, files: List[CodeFile]) -> str:
        """Find the main entry point file."""
        for f in files:
            if f.path == 'app.py':
                return f.path
            if f.path.endswith('app.py'):
                return f.path
        return files[0].path if files else "app.py"

    def _extract_dependencies(self, plan: EngineeringPlan, files: List[CodeFile]) -> List[str]:
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
                init_content = f.content
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
        logger.info(f"Added {len(routes_to_add)} missing frontend routes to app/__init__.py")
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
""" + "\n".join(f"- {f.name}: {f.description}" for f in requirements.features)


class CodeMemoryAgent:
    """Code Memory Agent - stores and retrieves code knowledge."""

    def __init__(self, llm_service: LLMService, settings=None):
        self.llm_service = llm_service
        self.settings = settings

    def execute(self, context: ExecutionContext, repository: CodeRepository) -> None:
        """Save generated code snippets to memory when ENABLE_CODE_MEMORY is True."""
        if not self.settings or not getattr(self.settings, "enable_code_memory", False):
            logger.info("CodeMemoryAgent: skipped (enable_code_memory=False)")
            return
        try:
            from src.services.code_memory_service import CodeMemoryService
            from src.core.data_models import CodeSnippet

            svc = CodeMemoryService(self.settings.code_memory_db_path)
            project_id = getattr(context, "project_id", "unknown")
            count = 0
            for cf in repository.files:
                if cf.language != "python" or not cf.path.endswith(".py"):
                    continue
                name = Path(cf.path).stem
                snip = CodeSnippet(
                    id=f"{project_id}_{cf.path.replace('/', '_')}",
                    function_name=name,
                    description=cf.purpose[:200] if cf.purpose else cf.path,
                    code=cf.content[:4000],
                    language="python",
                    tags=[project_id, name, "generated"],
                    usage_count=0,
                    project_id=project_id,
                )
                svc.add_snippet(snip)
                count += 1
            logger.info(f"CodeMemoryAgent: saved {count} snippets to memory")
        except Exception as e:
            logger.warning(f"CodeMemoryAgent save failed: {e}")


class CodeMiningAgent:
    """Status/logging wrapper for code mining.

    The actual mining logic lives in ``CodeGenerationAgent._get_mining_context``
    which calls ``CodeMiningService.search_and_adapt`` per-task.  This agent is
    invoked by the orchestrator solely to report mining status in the pipeline
    logs; it does **not** call the LLM or perform any mining itself.
    """

    def __init__(self, llm_service: LLMService, settings=None):
        self.llm_service = llm_service
        self.settings = settings

    def execute(self, context: ExecutionContext) -> dict:
        """Log mining status. Actual work happens in CodeGenerationAgent."""
        if self.settings and getattr(self.settings, "enable_code_mining", False):
            logger.info("CodeMiningAgent: mining ran per-task during code generation")
        else:
            logger.debug("CodeMiningAgent: skipped (enable_code_mining=False)")
        return {}
