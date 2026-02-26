"""Stage 2 Planning Agents."""

from pathlib import Path
from typing import Dict, Any, List, Tuple
from src.core.data_models import (
    Requirements, Task, Algorithm, FileSpec, TaskType, TaskComplexity,
    InterfaceSpec, ExportSpec
)
from src.services.llm_service import LLMService
from src.agents.stage2_planning.task_templates import detect_pattern, format_template_hint
from src.utils.logger import get_logger
from src.utils.prompt_loader import PromptLoader
from src.core.response_schemas import (
    TaskReviewResponse, ApiReviewResponse, AlgorithmEntry, validate_response,
)

logger = get_logger(__name__)

_PROMPTS_DIR = Path(__file__).parent.parent.parent.parent / "config" / "prompts"
_prompt_loader = PromptLoader(_PROMPTS_DIR)


class FlowSimulationAgent:
    """Stage 2 Agent 0: Simulates user operation flow before planning."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def execute(self, requirements: Requirements) -> str:
        """Simulate user operation flow and describe the complete user journey."""
        prompt = _prompt_loader.format(
            "flow_simulation",
            title=requirements.title,
            description=requirements.description,
            features=", ".join(f.name for f in requirements.features),
        )

        try:
            result = self.llm_service.generate(prompt)
            logger.info("Flow simulation completed")
            return result
        except Exception as e:
            logger.warning(f"Flow simulation failed, using placeholder: {e}")
            features_list = "\n".join(f"- {f.name}" for f in requirements.features)
            return (
                f"## 用户操作流程（自动生成占位）\n\n"
                f"应用: {requirements.title}\n"
                f"功能列表:\n{features_list}\n\n"
                f"（流程模拟失败，后续任务分解将仅基于需求文本。）"
            )


class ReviewAgent:
    """Stage 2 Agent: Reviews and refines task division and API specs."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def review_tasks(self, initial_tasks: List[Dict], requirements: Requirements) -> Dict:
        """Review task division for completeness and consistency."""
        features_str = "\n".join([
            f"- {f.name}: {f.description}" for f in requirements.features
        ])

        prompt = _prompt_loader.format(
            "review_tasks",
            title=requirements.title,
            description=requirements.description,
            features_str=features_str,
            initial_tasks=initial_tasks,
        )
        try:
            result = self.llm_service.generate_json(prompt)
            validated = validate_response(result, TaskReviewResponse)
            return validated.model_dump()
        except Exception as e:
            logger.warning(f"Task review failed, returning original tasks: {e}")
            return {"issues": [], "refined_tasks": initial_tasks}

    def review_api_specs(
        self,
        initial_api_specs: Dict,
        tasks: List[Task],
        requirements: Requirements
    ) -> Dict:
        """Review API specs for consistency with tasks and requirements."""
        tasks_str = "\n".join([
            f"- {t.id}: {t.name} - {t.description[:200]}..."
            for t in tasks
        ])

        prompt = _prompt_loader.format(
            "review_api_specs",
            title=requirements.title,
            features=", ".join(f.name for f in requirements.features),
            tasks_str=tasks_str,
            initial_api_specs=initial_api_specs,
        )
        try:
            result = self.llm_service.generate_json(prompt)
            validated = validate_response(result, ApiReviewResponse)
            return validated.model_dump()
        except Exception as e:
            logger.warning(f"API review failed, returning original specs: {e}")
            return {"issues": [], "refined_api_specs": initial_api_specs}


class TaskDivisionAgent:
    """Stage 2 Agent 1: Divides requirements into atomic tasks."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def _extract_structured_flow(self, flow_simulation: str) -> str:
        """Extract structured pages and entities from raw flow simulation text."""
        if not flow_simulation or len(flow_simulation.strip()) < 20:
            return ""

        prompt = _prompt_loader.format(
            "extract_structured_flow",
            flow_simulation=flow_simulation,
        )
        try:
            result = self.llm_service.generate_json(prompt)
            sections = []

            pages = result.get("pages", [])
            if pages:
                sections.append("## 页面列表")
                for p in pages:
                    sections.append(f"- {p.get('url', '?')}: {p.get('name', '?')} - {p.get('description', '')}")

            entities = result.get("entities", [])
            if entities:
                sections.append("\n## 数据实体")
                for e in entities:
                    fields = ", ".join(e.get("fields", []))
                    relations = ", ".join(e.get("relations", []))
                    line = f"- {e.get('name', '?')}({fields})"
                    if relations:
                        line += f" [关联: {relations}]"
                    sections.append(line)

            interactions = result.get("key_interactions", [])
            if interactions:
                sections.append("\n## 关键交互")
                for i in interactions:
                    sections.append(f"- {i}")

            return "\n".join(sections)
        except Exception as e:
            logger.warning(f"Flow structure extraction failed, using raw text: {e}")
            return f"## 用户操作流程参考\n{flow_simulation}"

    def _extract_entities_and_pages(self, requirements: Requirements) -> str:
        """Phase 1: Extract structured entities and pages directly from requirements."""
        prompt = _prompt_loader.format(
            "extract_entities_and_pages",
            title=requirements.title,
            description=requirements.description,
            features=", ".join(f.name for f in requirements.features),
        )
        try:
            result = self.llm_service.generate_json(prompt)
            sections = []

            entities = result.get("entities", [])
            if entities:
                sections.append("## 需求分析 - 数据实体")
                for e in entities:
                    fields = ", ".join(e.get("fields", []))
                    crud = ", ".join(e.get("crud_operations", []))
                    relations = ", ".join(e.get("relations", []))
                    line = f"- {e.get('name', '?')}({fields}) [CRUD: {crud}]"
                    if relations:
                        line += f" [关联: {relations}]"
                    sections.append(line)

            pages = result.get("pages", [])
            if pages:
                sections.append("\n## 需求分析 - 前端页面")
                for p in pages:
                    related = ", ".join(p.get("related_entities", []))
                    interactions = ", ".join(p.get("interactions", []))
                    sections.append(f"- {p.get('url', '?')}: {p.get('name', '?')} (实体: {related}, 交互: {interactions})")

            return "\n".join(sections) if sections else ""
        except Exception as e:
            logger.warning(f"Entity/page extraction failed: {e}")
            return ""

    def execute(self, requirements: Requirements, flow_simulation: str = "") -> List[Task]:
        """Divide requirements into atomic tasks using two-phase generation."""
        # Phase 1: extract structured entities & pages from requirements
        entity_page_section = self._extract_entities_and_pages(requirements)

        # Phase 1b: also structure flow_simulation if available
        if flow_simulation:
            flow_section = "\n\n" + self._extract_structured_flow(flow_simulation) + "\n"
        else:
            flow_section = ""

        if entity_page_section:
            flow_section = f"\n\n{entity_page_section}\n{flow_section}"

        # Template hint: detect common pattern and inject structural guidance
        combined_text = f"{requirements.title} {requirements.description} {' '.join(f.name for f in requirements.features)}"
        pattern = detect_pattern(combined_text)
        template_hint = ""
        if pattern:
            template_hint = format_template_hint(pattern)
            logger.info(f"Detected app pattern: {pattern}, injecting template hint")

        prompt = _prompt_loader.format(
            "task_division",
            title=requirements.title,
            description=requirements.description,
            features=", ".join(f.name for f in requirements.features),
            flow_section=flow_section,
            template_hint=template_hint,
        )

        try:
            result = self.llm_service.generate_json(prompt)
            tasks = []
            for t in result:
                complexity = t.get("estimated_complexity", t.get("complexity", "medium"))
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

                priority = t.get("priority", 3)

                tasks.append(Task(
                    id=t["id"],
                    name=t["name"],
                    description=detailed_desc,
                    type=task_type,
                    dependencies=t.get("dependencies", []),
                    priority=priority,
                    estimated_complexity=TaskComplexity(complexity),
                    files_to_add=t.get("files_to_add", []),
                    files_to_modify=t.get("files_to_modify", [])
                ))

            # ===== Stage 2 反思审查机制 =====
            # 首次生成完成后，进行审查
            logger.info("Running task division review...")
            review_agent = ReviewAgent(self.llm_service)

            initial_tasks_dict = [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "type": t.type.value,
                    "priority": t.priority,
                    "estimated_complexity": t.estimated_complexity.value,
                    "dependencies": t.dependencies,
                }
                for t in tasks
            ]

            review_result = review_agent.review_tasks(initial_tasks_dict, requirements)

            # 如果审查发现问题，使用修正后的任务列表
            if review_result.get("issues") and review_result["issues"]:
                logger.info(f"Found {len(review_result['issues'])} issues, applying refinements...")
                refined_tasks = review_result.get("refined_tasks", [])

                # 重新解析修正后的任务
                if refined_tasks:
                    tasks = []
                    for t in refined_tasks:
                        complexity = t.get("estimated_complexity", "medium")
                        if complexity not in [c.value for c in TaskComplexity]:
                            complexity = "medium"

                        detailed_desc = t.get("description", "")

                        task_type_str = t.get("type", "frontend")
                        try:
                            task_type = TaskType(task_type_str)
                        except ValueError:
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
                                task_type = TaskType.FRONTEND

                        priority = t.get("priority", 3)

                        tasks.append(Task(
                            id=t["id"],
                            name=t["name"],
                            description=detailed_desc,
                            type=task_type,
                            dependencies=t.get("dependencies", []),
                            priority=priority,
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
        prompt = _prompt_loader.format(
            "algorithm_analysis",
            tasks_summary=", ".join(f"{t.id}: {t.name}" for t in tasks),
        )

        try:
            result = self.llm_service.generate_json(prompt)
            algorithms = {}
            for task_id, alg_data in result.items():
                entry = validate_response(alg_data, AlgorithmEntry)
                algorithms[task_id] = Algorithm(
                    task_id=task_id,
                    algorithm_type="standard",
                    implementation_approach=entry.implementation_approach,
                    libraries=[],
                    data_structures=[],
                    notes=entry.notes,
                )
            return algorithms
        except Exception as e:
            logger.warning(f"Algorithm analysis failed, using defaults: {e}")
            return {
                t.id: Algorithm(
                    task_id=t.id,
                    algorithm_type="standard",
                    implementation_approach=f"Standard implementation for {t.name}",
                    libraries=[],
                    data_structures=[],
                )
                for t in tasks
            }


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

        prompt = _prompt_loader.format(
            "scheme_planning",
            title=requirements.title,
            description=requirements.description,
            features=", ".join(f.name for f in requirements.features),
            flow_section=flow_section,
            task_descriptions=task_descriptions,
        )

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

            # ===== Stage 2 反思审查机制 - API规范审查 =====
            logger.info("Running API specs review...")
            review_agent = ReviewAgent(self.llm_service)

            api_review_result = review_agent.review_api_specs(
                initial_api_specs=api_specs,
                tasks=tasks,
                requirements=requirements
            )

            # 如果审查发现问题，使用修正后的API规范
            if api_review_result.get("issues") and api_review_result["issues"]:
                logger.info(f"Found {len(api_review_result['issues'])} API issues, applying refinements...")
                refined_api_specs = api_review_result.get("refined_api_specs", {})
                if refined_api_specs:
                    api_specs = refined_api_specs

            return files, interface_specs, api_specs, pyi_stubs

        except Exception as e:
            # 保证返回值签名稳定，让上游可以做空计划处理或显式报错
            logger.warning(f"LLM scheme planning failed, returning empty plan: {e}")
            return [], [], {}, {}
