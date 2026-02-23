"""Stage 2 Planning Agents."""

from typing import Dict, Any, List, Tuple
# Import directly from module to avoid circular import
from src.core.data_models import (
    Requirements, Task, Algorithm, FileSpec, TaskType, TaskComplexity,
    InterfaceSpec, ExportSpec
)
from src.services.llm_service import LLMService
from src.utils.logger import get_logger

logger = get_logger(__name__)


class FlowSimulationAgent:
    """Stage 2 Agent 0: Simulates user operation flow before planning."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def execute(self, requirements: Requirements) -> str:
        """Simulate user operation flow and describe the complete user journey."""
        prompt = f"""
你是一个用户体验设计师。在开始技术规划之前，请先想象并描述用户使用这个应用的完整流程。

Requirements:
Title: {requirements.title}
Description: {requirements.description}
Features: {", ".join(f.name for f in requirements.features)}

请按以下格式描述用户操作流程：

## 用户操作流程模拟

1. 首页 (URL: /)
   - 用户打开网页看到什么？
   - 有哪些按钮/链接？
   - 点击后会跳转到哪里？

2. 创建页面 (URL: /xxx/new)
   - 表单有哪些字段？
   - 点击提交后会发生什么？
   - 成功/失败后跳转到哪里？

3. 列表页面 (URL: /xxx)
   - 显示什么数据？
   - 每条数据有什么操作按钮？
   - 点击后会怎样？

4. 详情页面 (URL: /xxx/<id>)
   - 显示什么信息？
   - 有哪些交互操作？
   - 操作结果是什么？

5. 其他页面和交互...

请详细描述每个页面的内容、交互方式和预期结果。
这个描述将帮助后续的任务分解和方案规划。

Respond in Chinese with detailed descriptions.
"""

        try:
            result = self.llm_service.generate(prompt)
            logger.info("Flow simulation completed")
            return result
        except Exception as e:
            logger.error(f"Flow simulation failed: {e}")
            return ""


class TaskDivisionAgent:
    """Stage 2 Agent 1: Divides requirements into atomic tasks."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def execute(self, requirements: Requirements, flow_simulation: str = "") -> List[Task]:
        """Divide requirements into atomic tasks."""
        flow_section = f"\n\n## 用户操作流程参考\n{flow_simulation}\n" if flow_simulation else ""

        prompt = f"""
根据以下需求，拆分成若干任务。

Requirements:
Title: {requirements.title}
Description: {requirements.description}
Features: {", ".join(f.name for f in requirements.features)}
{flow_section}

OUTPUT FORMAT (JSON array):
每个任务必须包含：
1. name: 任务名称（简洁）
2. description: 用自然语言描述这个任务要实现什么功能

任务拆分要求：
1. 每个任务要能独立完成，不过于复杂
2. 所有任务的总和要能完整实现所有功能，不能有遗漏
3. 任务按依赖排序：先底层（数据库）、后中层（API）、前上层（前端）
4. 前端页面拆分原则：每个单独的HTML页面（如首页、列表页、详情页、创建页）应该是一个独立的任务
5. **同一个实体的CRUD操作必须放在同一个任务中，不要拆分成多个任务**
   - 例如：博客的增删改查应该是一个任务"创建博客API接口"，而不是拆成"创建博客"、"删除博客"、"编辑博客"等多个任务
   - 图片上传如果和博客创建相关，应该集成在一起，而不是单独拆分成"实现图片上传功能"

Example:
[
    {{
        "id": "T1",
        "name": "创建博客数据模型",
        "description": "创建博客的数据模型，包括标题、内容、图片、创建时间等字段，保存到数据库。",
        "type": "database",
        "priority": 5,
        "estimated_complexity": "low"
    }},
    {{
        "id": "T2",
        "name": "创建博客API接口",
        "description": "创建博客的完整后端API接口，包含：获取博客列表、获取单篇博客、创建博客（含图片上传）、更新博客、删除博客。图片上传应该集成在创建/更新API中。",
        "type": "backend",
        "priority": 5,
        "estimated_complexity": "medium"
    }},
    {{
        "id": "T3",
        "name": "创建首页",
        "description": "创建首页HTML页面，显示欢迎信息和导航链接。",
        "type": "frontend",
        "priority": 4,
        "estimated_complexity": "low"
    }},
    {{
        "id": "T4",
        "name": "创建博客列表页",
        "description": "创建博客列表HTML页面，展示所有博客的标题、摘要、图片，点击可查看详情。",
        "type": "frontend",
        "priority": 4,
        "estimated_complexity": "low"
    }},
    {{
        "id": "T5",
        "name": "创建博客详情页",
        "description": "创建单篇博客详情HTML页面，显示完整内容和图片。",
        "type": "frontend",
        "priority": 4,
        "estimated_complexity": "low"
    }},
    {{
        "id": "T6",
        "name": "创建新建博客页面",
        "description": "创建新建博客的HTML表单页面，包含标题、内容输入框和图片上传。",
        "type": "frontend",
        "priority": 4,
        "estimated_complexity": "low"
    }},
    {{
        "id": "T7",
        "name": "创建编辑博客页面",
        "description": "创建编辑博客的HTML表单页面，预填充现有内容。",
        "type": "frontend",
        "priority": 4,
        "estimated_complexity": "low"
    }}
]

Respond with valid JSON array only.
"""

        try:
            result = self.llm_service.generate_json(prompt)
            tasks = []
            for t in result:
                complexity = t.get("complexity", "medium")
                if complexity not in [c.value for c in TaskComplexity]:
                    complexity = "medium"

                detailed_desc = t.get("description", "")

                # 处理 api_specs（新的统一 API 格式）
                api_specs = t.get("api_specs", {})
                if api_specs.get("endpoints"):
                    detailed_desc += "\n\nAPI Specification (ALL TASKS MUST USE SAME API):\n"
                    for api in api_specs["endpoints"]:
                        detailed_desc += f"- {api.get('method', '?')} {api.get('path', '?')}"
                        if api.get('request'):
                            detailed_desc += f" (request: {api.get('request')})"
                        detailed_desc += f" -> {api.get('response', '?')}\n"

                # 处理 implementation_specs（旧格式，保持兼容）
                impl_specs = t.get("implementation_specs", {})

                # 添加 API 端点信息
                if impl_specs.get("api_endpoints"):
                    apis = impl_specs["api_endpoints"]
                    detailed_desc += "\n\nAPI Endpoints:\n"
                    for api in apis:
                        detailed_desc += f"- {api.get('method', '?')} {api.get('path', '?')}"
                        if api.get('request'):
                            detailed_desc += f" (request: {api.get('request')})"
                        detailed_desc += f" -> {api.get('response', '?')}\n"

                # 添加函数信息
                if impl_specs.get("functions"):
                    detailed_desc += "\nFunctions to implement:\n"
                    for func in impl_specs["functions"]:
                        detailed_desc += f"- {func}\n"

                # 添加类信息
                if impl_specs.get("classes"):
                    detailed_desc += "\nClasses to define:\n"
                    for cls in impl_specs["classes"]:
                        if isinstance(cls, dict):
                            detailed_desc += f"- class {cls.get('name', '?')}: {cls.get('attributes', [])}\n"
                        else:
                            detailed_desc += f"- {cls}\n"

                # 处理 type，确保在枚举中
                task_type_str = t.get("type", "frontend")
                try:
                    task_type = TaskType(task_type_str)
                except ValueError:
                    # 如果 type 不在枚举中，尝试映射
                    if "front" in task_type_str.lower():
                        task_type = TaskType.FRONTEND
                    elif "back" in task_type_str.lower() or "api" in task_type_str.lower():
                        task_type = TaskType.BACKEND
                    elif "data" in task_type_str.lower() or "model" in task_type_str.lower():
                        task_type = TaskType.DATABASE
                    elif "test" in task_type_str.lower():
                        task_type = TaskType.TESTING
                    elif "deploy" in task_type_str.lower():
                        task_type = TaskType.DEPLOYMENT
                    else:
                        task_type = TaskType.FRONTEND  # 默认

                tasks.append(Task(
                    id=t["id"],
                    name=t["name"],
                    description=detailed_desc,
                    type=task_type,
                    dependencies=t.get("dependencies", []),
                    priority=t.get("priority", 3),
                    estimated_complexity=TaskComplexity(complexity),
                    files_to_add=t.get("files_to_add", []),
                    files_to_modify=t.get("files_to_modify", [])
                ))
            return tasks
        except Exception as e:
            logger.error(f"LLM task division failed: {e}")
            raise


class AlgorithmAnalysisAgent:
    """Stage 2 Agent 2: Analyzes algorithms for each task."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def execute(self, tasks: List[Task]) -> Dict[str, Algorithm]:
        """Analyze algorithms for each task."""
        prompt = f"""
For each task, provide a brief implementation approach.
Return a JSON object with task ID as key:
{{
    "T1": {{
        "implementation_approach": "Brief description of how to implement this task",
        "notes": "Any important notes"
    }}
}}

Tasks: {", ".join(f"{t.id}: {t.name}" for t in tasks)}

Respond with valid JSON only. Keep it simple - just 1-2 sentences per task.
"""

        try:
            result = self.llm_service.generate_json(prompt)
            algorithms = {}
            for task_id, alg in result.items():
                algorithms[task_id] = Algorithm(
                    task_id=task_id,
                    algorithm_type="standard",
                    implementation_approach=alg.get("implementation_approach", "Standard implementation"),
                    libraries=[],
                    data_structures=[],
                    notes=alg.get("notes")
                )
            return algorithms
        except Exception as e:
            logger.error(f"LLM algorithm analysis failed: {e}")
            raise


class SchemePlanningAgent:
    """Stage 2 Agent 3: Creates file structure. Interface specs generated in Stage 3."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def execute(
        self,
        requirements: Requirements,
        tasks: List[Task],
        flow_simulation: str = "",
    ) -> Tuple[List[FileSpec], List[InterfaceSpec], Dict, Dict]:
        """Create file structure - files grouped by task."""
        # 构建每个任务的详细描述
        task_descriptions = ""
        for t in tasks:
            task_descriptions += f"""
Task {t.id}: {t.name} ({t.type})
  Goal: {t.description}
  Complexity: {t.estimated_complexity}
  Priority: {t.priority}
  Dependencies: {t.dependencies or "none"}
"""

        flow_section = f"\n\n## 用户操作流程参考\n{flow_simulation}\n" if flow_simulation else ""

        prompt = f"""
Generate detailed file specification for this Flask web app.

CRITICAL: 你在这里的pyi_stubs和api_specs描述将决定Stage 3代码生成的结果。请务必写完整、写详细。

Application: {requirements.title}
Description: {requirements.description}
Features: {", ".join(f.name for f in requirements.features)}
{flow_section}

{task_descriptions}

YOUR JOB:
1. For each task, determine what files need to be created
2. For each Python file, generate its .pyi stub file content (type definitions) - 越详细越好，包括所有函数签名、参数类型、返回值类型
3. Assign each file to ONE task only (no duplicates)
4. Consider dependencies between tasks when ordering
5. api_specs must be extremely detailed: 每个endpoint的完整路径、请求参数、响应格式
6. frontend_routes must list EVERY single page route and its corresponding template file
7. CRITICAL: task_files must include ALL files defined in pyi_stubs, including base files like app/__init__.py, app/database.py that need to be created or modified

File assignment guidelines:
- Frontend task: templates/*.html, static/*
- Backend task: app/routes.py or app/*_routes.py
- Database task: app/database.py, app/models/*.py
- Entry files (app/__init__.py, app.py): put in the task that depends on them
- CRITICAL: If pyi_stubs defines app/database.py or app/__init__.py, you MUST add them to task_files and assign to an appropriate task

Output format (JSON):
{{
    "task_files": {{
        "T1": [{{"path": "...", "layer": "...", "purpose": "..."}}],
        "T2": [...]
    }},
    "task_goals": {{
        "T1": "明确的目标描述",
        "T2": "明确的目标描述"
    }},
    "api_specs": {{
        "description": "前后端连接方式描述",
        "endpoints": [
            {{"path": "/api/notes", "method": "GET", "description": "获取笔记列表", "response": "[{{id, content, created_at}}]"}},
            {{"path": "/api/notes", "method": "POST", "description": "创建笔记", "request": "{{title, content}}", "response": "{{id, title, content, created_at}}"}}
        ],
        "frontend_routes": {{
            "/": {{"template": "index.html", "description": "主页显示笔记列表"}},
            "/notes": {{"template": "notes.html", "description": "笔记列表页"}},
            "/notes/new": {{"template": "note_new.html", "description": "新建笔记页"}}
        }}
    }},
    "pyi_stubs": {{
        "app/models/note.py": "class Note(db.Model):\\n    __tablename__ = 'notes'\\n    id: int\\n    title: str\\n    content: str\\n    created_at: datetime\\n    def to_dict(self) -> dict: ...",
        "app/routes/notes.py": "notes_bp = Blueprint('notes', __name__)\\ndef get_notes() -> list[Note]: ...\\ndef create_note(title: str, content: str) -> Note: ...",
        "app/__init__.py": "def create_app(config_name=None) -> Flask: ..."
    }}
}}

IMPORTANT:
- Each file should appear exactly ONCE
- Include all necessary files (templates, static, routes, models, app factory, entry point)
- task_goals should describe what this task should achieve
- pyi_stubs: 为每个Python文件生成类型存根（.pyi格式），让Stage 3知道每个文件的接口 - 必须详细
- api_specs: 描述前后端如何连接，前端调用哪个URL，后端返回什么格式 - 必须完整
- frontend_routes: 列出所有前端页面路由 - 不能遗漏

Return ONLY valid JSON.
"""

        try:
            result = self.llm_service.generate_json(prompt)

            # 解析 task_files
            files: list[FileSpec] = []
            task_files_dict = result.get("task_files", {}) or {}

            for task_id, task_file_list in task_files_dict.items():
                if not isinstance(task_file_list, list):
                    continue
                for f in task_file_list:
                    if not isinstance(f, dict):
                        continue
                    path = (f.get("path") or "").strip()
                    if not path:
                        continue
                    files.append(
                        FileSpec(
                            path=path,
                            purpose=f.get("purpose", "") or "",
                            dependencies=f.get("dependencies", []) or [],
                            layer=f.get("layer"),
                            related_tasks=[task_id],
                        )
                    )

            # 简化 interface_specs - 从 task_files 推断
            interface_specs: list[InterfaceSpec] = []
            for f in files:
                if f.path.endswith(".py") and not f.path.startswith("tests/"):
                    # 推断简单的 interface spec
                    spec = InterfaceSpec(
                        module_name=f.path.replace("/", ".").replace(".py", ""),
                        file_path=f.path,
                        purpose=f.purpose,
                        layer=f.layer,
                        exports=[],
                        imports=[],
                        database_access="none",
                        related_files=[],
                    )
                    interface_specs.append(spec)

            # 解析 api_specs / pyi_stubs，保证至少返回空 dict
            api_specs: Dict = result.get("api_specs") or {}
            pyi_stubs: Dict = result.get("pyi_stubs") or {}

            return files, interface_specs, api_specs, pyi_stubs

        except Exception as e:
            # 保证返回值签名稳定，让上游可以做空计划处理或显式报错
            logger.warning(f"LLM scheme planning failed, returning empty plan: {e}")
            return [], [], {}, {}
