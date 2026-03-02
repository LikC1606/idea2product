"""Stage 2 Planning Agents."""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from src.core.data_models import (
    Requirements, Task, Algorithm, FileSpec, TaskType, TaskComplexity,
    InterfaceSpec, ExportSpec
)
from src.services.llm_service import LLMService
from src.agents.stage2_planning.task_templates import detect_pattern, format_template_hint
from src.utils.logger import get_logger
from src.utils.prompt_loader import PromptLoader
from pydantic import ValidationError
from src.core.response_schemas import (
    TaskReviewResponse, ApiReviewResponse, AlgorithmEntry, validate_response,
)

logger = get_logger(__name__)

_PROMPTS_DIR = Path(__file__).parent.parent.parent.parent / "config" / "prompts"
_prompt_loader = PromptLoader(_PROMPTS_DIR)

# Keywords that suggest ML/NLP/CV tasks; value is HF pipeline_tag for search
_ML_TASK_KEYWORDS: Dict[str, str] = {
    "nlp": "text-classification",
    "自然语言": "text-classification",
    "文本": "text-classification",
    "情感": "sentiment-analysis",
    "sentiment": "sentiment-analysis",
    "分类": "text-classification",
    "classification": "text-classification",
    "embedding": "feature-extraction",
    "图像": "image-classification",
    "image": "image-classification",
    "transformer": "text-classification",
    "bert": "text-classification",
    "summarize": "summarization",
    "摘要": "summarization",
    "问答": "question-answering",
    "question answering": "question-answering",
    "ner": "token-classification",
    "命名实体": "token-classification",
    "翻译": "translation",
    "translation": "translation",
}


class FlowSimulationAgent:
    """Stage 2 Agent 0: Simulates user operation flow before planning."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def _structured_fallback(self, requirements: Requirements) -> str:
        """Return structured pages/entities placeholder when LLM fails. TaskDivision uses directly."""
        sections = ["## 用户操作流程（自动生成占位）", f"\n应用: {requirements.title}\n"]
        # Pages: one per feature + home
        sections.append("## 页面列表")
        sections.append("- /: 首页 - 应用入口")
        for f in requirements.features[:8]:
            path = "/" + f.name.lower().replace(" ", "_")
            sections.append(f"- {path}: {f.name} - {f.description[:80]}")
        # Entities: infer from feature names (common patterns)
        sections.append("\n## 数据实体")
        seen = set()
        for f in requirements.features[:6]:
            name = "".join(w.capitalize() for w in f.name.split()[:2]) or "Item"
            if name not in seen:
                seen.add(name)
                sections.append(f"- {name}(id, name, created_at) [关联: ]")
        sections.append("\n## 关键交互")
        for f in requirements.features[:5]:
            sections.append(f"- 用户执行 {f.name}")
        return "\n".join(sections)

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
            logger.warning(f"Flow simulation failed, using structured placeholder: {e}")
            return self._structured_fallback(requirements)


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
            if not isinstance(result, dict):
                return {"issues": [], "refined_tasks": initial_tasks}
            validated = validate_response(result, TaskReviewResponse)
            return validated.model_dump()
        except ValidationError as e:
            logger.warning(f"Task review schema mismatch: {e.errors()}, returning original tasks")
            return {"issues": [], "refined_tasks": initial_tasks}
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
            if not isinstance(result, dict):
                return {"issues": [], "refined_api_specs": initial_api_specs}
            validated = validate_response(result, ApiReviewResponse)
            return validated.model_dump()
        except ValidationError as e:
            logger.warning(f"API review schema mismatch: {e.errors()}, returning original specs")
            return {"issues": [], "refined_api_specs": initial_api_specs}
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
            if not isinstance(result, dict):
                return f"## 用户操作流程参考\n{flow_simulation}"
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
            if not isinstance(result, dict):
                return ""
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
        """Divide requirements into atomic tasks. Uses unified prompt when enabled to reduce LLM calls."""
        from config.settings import get_settings
        settings = get_settings()
        use_unified = getattr(settings, "use_unified_task_division", True)

        if use_unified:
            return self._execute_unified(requirements, flow_simulation, settings)
        return self._execute_two_phase(requirements, flow_simulation, settings)

    def _execute_unified(
        self, requirements: Requirements, flow_simulation: str, settings
    ) -> List[Task]:
        """Single LLM call: entities + pages + tasks."""
        flow_section = ""
        if flow_simulation:
            flow_section = "\n\n" + self._extract_structured_flow(flow_simulation) + "\n"

        combined_text = f"{requirements.title} {requirements.description} {' '.join(f.name for f in requirements.features)}"
        pattern = detect_pattern(combined_text)
        template_hint = format_template_hint(pattern) if pattern else ""

        prompt = _prompt_loader.format(
            "task_division_unified",
            title=requirements.title,
            description=requirements.description,
            features=", ".join(f.name for f in requirements.features),
            flow_section=flow_section,
            template_hint=template_hint,
        )
        try:
            result = self.llm_service.generate_json(prompt)
            if not isinstance(result, dict):
                return []
            tasks_raw = result.get("tasks", [])
            tasks = self._parse_tasks(tasks_raw)
            skip_review = getattr(settings, "skip_task_review_when_count_low", 0)
            if skip_review > 0 and len(tasks) <= skip_review:
                logger.info(f"Skipping task review (count={len(tasks)} <= {skip_review})")
                return tasks
            return self._run_review(tasks, requirements, settings)
        except Exception as e:
            logger.warning(f"Unified task division failed, falling back to two-phase: {e}")
            return self._execute_two_phase(requirements, flow_simulation, settings)

    def _execute_two_phase(
        self, requirements: Requirements, flow_simulation: str, settings
    ) -> List[Task]:
        """Legacy two-phase: extract entities/pages, then task division."""
        entity_page_section = self._extract_entities_and_pages(requirements)
        if flow_simulation:
            flow_section = "\n\n" + self._extract_structured_flow(flow_simulation) + "\n"
        else:
            flow_section = ""
        if entity_page_section:
            flow_section = f"\n\n{entity_page_section}\n{flow_section}"

        combined_text = f"{requirements.title} {requirements.description} {' '.join(f.name for f in requirements.features)}"
        pattern = detect_pattern(combined_text)
        template_hint = format_template_hint(pattern) if pattern else ""

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
            if not isinstance(result, list):
                result = list(result.values()) if isinstance(result, dict) else []
            tasks = self._parse_tasks(result)
            return self._run_review(tasks, requirements, settings)
        except Exception as e:
            logger.warning(f"Task division failed: {e}")
            return []

    def _parse_tasks(self, result: List) -> List[Task]:
        """Parse raw task dicts into Task objects."""
        tasks = []
        for t in result:
            if not isinstance(t, dict):
                continue
            complexity = t.get("estimated_complexity", t.get("complexity", "medium"))
            if complexity not in [c.value for c in TaskComplexity]:
                complexity = "medium"

            detailed_desc = t.get("description", "")

            api_specs = t.get("api_specs", {})
            if api_specs.get("endpoints"):
                detailed_desc += "\n\nAPI Specification (ALL TASKS MUST USE SAME API):\n"
                for api in api_specs["endpoints"]:
                    detailed_desc += f"- {api.get('method', '?')} {api.get('path', '?')}"
                    if api.get('request'):
                        detailed_desc += f" (request: {api.get('request')})"
                    detailed_desc += f" -> {api.get('response', '?')}\n"

            impl_specs = t.get("implementation_specs", {})
            if impl_specs.get("api_endpoints"):
                apis = impl_specs["api_endpoints"]
                detailed_desc += "\n\nAPI Endpoints:\n"
                for api in apis:
                    detailed_desc += f"- {api.get('method', '?')} {api.get('path', '?')}"
                    if api.get('request'):
                        detailed_desc += f" (request: {api.get('request')})"
                    detailed_desc += f" -> {api.get('response', '?')}\n"

            if impl_specs.get("functions"):
                detailed_desc += "\nFunctions to implement:\n"
                for func in impl_specs["functions"]:
                    detailed_desc += f"- {func}\n"

            if impl_specs.get("classes"):
                detailed_desc += "\nClasses to define:\n"
                for cls in impl_specs["classes"]:
                    if isinstance(cls, dict):
                        detailed_desc += f"- class {cls.get('name', '?')}: {cls.get('attributes', [])}\n"
                    else:
                        detailed_desc += f"- {cls}\n"

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

    def _run_review(self, tasks: List[Task], requirements: Requirements, settings) -> List[Task]:
        """Run task division review and apply refinements if needed."""
        logger.info("Running task division review...")
        review_agent = ReviewAgent(self.llm_service)
        initial_tasks_dict = [
            {"id": t.id, "name": t.name, "description": t.description, "type": t.type.value,
             "priority": t.priority, "estimated_complexity": t.estimated_complexity.value,
             "dependencies": t.dependencies}
            for t in tasks
        ]
        review_result = review_agent.review_tasks(initial_tasks_dict, requirements)
        if review_result.get("issues") and review_result["issues"]:
            logger.info(f"Found {len(review_result['issues'])} issues, applying refinements...")
            refined_tasks = review_result.get("refined_tasks", [])
            if refined_tasks:
                tasks = self._parse_tasks(refined_tasks)
        return tasks


def _is_ml_task(task: Task) -> bool:
    """Check if task description suggests ML/NLP/CV usage."""
    text = (f"{task.name} {task.description}").lower()
    return any(kw in text for kw in _ML_TASK_KEYWORDS)


def _get_pipeline_tag(task: Task) -> Optional[str]:
    """Get Hugging Face pipeline_tag for task, or None."""
    text = (f"{task.name} {task.description}").lower()
    for kw, tag in _ML_TASK_KEYWORDS.items():
        if kw in text:
            return tag
    return None


class AlgorithmAnalysisAgent:
    """Stage 2 Agent 2: Analyzes algorithms for each task."""

    def __init__(
        self,
        llm_service: LLMService,
        hf_model_service: Optional[Any] = None,
        hf_search_limit: int = 5,
        hf_check_inference: bool = True,
    ):
        self.llm_service = llm_service
        self.hf_model_service = hf_model_service
        self.hf_search_limit = hf_search_limit
        self.hf_check_inference = hf_check_inference

    def _detect_ml_task(self, task: Task) -> Optional[Dict[str, Any]]:
        """
        Use LLM to detect if task requires ML/NLP/CV and extract keywords.
        Returns dict with is_ml, pipeline_tag, keywords, or None if not ML task.
        """
        prompt = f"""Analyze if this task requires Machine Learning/NLP/CV.

Task: {task.name}
Description: {task.description}

Respond in JSON format:
{{
    "is_ml_task": true/false,
    "reason": "why it is or is not ML task",
    "pipeline_tag": "huggingface pipeline tag if applicable (e.g., text-classification, text-to-image, object-detection)",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "suggested_models": ["optional model suggestions"]
}}

Only return is_ml_task=true if the task genuinely needs ML models (e.g., sentiment analysis, image generation, object detection, translation, speech recognition, etc).
Tasks like "user login", "CRUD operations", "display data" are NOT ML tasks.
"""
        try:
            result = self.llm_service.generate_json(prompt)
            if result and isinstance(result, dict):
                return result
        except Exception as e:
            logger.debug(f"ML task detection failed for {task.id}: {e}")
        return None

    def _get_hf_info_for_task(self, task: Task) -> Optional[Dict[str, Any]]:
        """Get HuggingFace info for a task using LLM."""
        ml_info = self._detect_ml_task(task)
        if not ml_info or not ml_info.get("is_ml_task"):
            return None

        if not self.hf_model_service:
            return None

        # Get pipeline_tag from LLM response or use keyword matching
        pipeline_tag = ml_info.get("pipeline_tag")
        if not pipeline_tag:
            pipeline_tag = _get_pipeline_tag(task)

        keywords = ml_info.get("keywords", [])
        query = " ".join(keywords) if keywords else f"{task.name} {task.description}"[:200]

        try:
            models = self.hf_model_service.search_and_fetch_docs(
                query=query,
                pipeline_tag=pipeline_tag,
                limit=self.hf_search_limit,
                keywords=keywords,
                check_inference=self.hf_check_inference,
            )
            return {
                "pipeline_tag": pipeline_tag,
                "keywords": keywords,
                "models": models,
                "suggested_models": ml_info.get("suggested_models", []),
            }
        except Exception as e:
            logger.debug(f"HF search for task {task.id} failed: {e}")
            return None

    def execute(
        self,
        tasks: List[Task],
        flow_simulation: str = "",
    ) -> Dict[str, Algorithm]:
        """Analyze algorithms for each task. flow_simulation provides user-flow context for algorithm choice."""
        hf_context_parts: List[str] = []

        flow_section = ""
        if flow_simulation and len(flow_simulation.strip()) > 20:
            flow_section = f"\n## User Operation Flow (consider for algorithm choice)\n{flow_simulation[:1500]}\n"

        # Use LLM to detect ML tasks and search HF
        if self.hf_model_service:
            for t in tasks:
                hf_info = self._get_hf_info_for_task(t)
                if not hf_info or not hf_info.get("models"):
                    continue

                models = hf_info["models"]
                lines = [f"## {t.id} - {t.name} (ML/NLP/CV candidates)"]
                lines.append(f"Pipeline: {hf_info.get('pipeline_tag', 'N/A')}")
                lines.append(f"Keywords: {', '.join(hf_info.get('keywords', []))}")

                for m in models:
                    model_id = m.get("model_id", "")
                    downloads = m.get("downloads", 0)
                    card = (m.get("card_text") or "")[:600]
                    lines.append(f"- **{model_id}** (downloads: {downloads:,})")
                    lines.append(f"  {card[:500]}")

                if hf_info.get("suggested_models"):
                    lines.append(f"\nSuggested by LLM: {', '.join(hf_info['suggested_models'])}")

                hf_context_parts.append("\n".join(lines))

        hf_context = "\n\n".join(hf_context_parts) if hf_context_parts else ""

        prompt = _prompt_loader.format(
            "algorithm_analysis",
            tasks_summary=", ".join(f"{t.id}: {t.name}" for t in tasks),
            flow_section=flow_section,
            hf_context=hf_context,
        )

        try:
            result = self.llm_service.generate_json(prompt)
            if not isinstance(result, dict):
                if isinstance(result, list) and result and isinstance(result[0], dict):
                    result = {f"T{i + 1}": v for i, v in enumerate(result)}
                else:
                    result = {}
            algorithms = {}
            for task_id, alg_data in result.items():
                entry = validate_response(alg_data, AlgorithmEntry)
                hf_models = getattr(entry, "hf_models", None) or []
                hf_usage_notes = getattr(entry, "hf_usage_notes", None)
                libraries: List[str] = []
                if hf_models:
                    libraries = ["transformers", "huggingface_hub"]
                algorithms[task_id] = Algorithm(
                    task_id=task_id,
                    algorithm_type="standard",
                    implementation_approach=entry.implementation_approach or "",
                    libraries=libraries,
                    data_structures=[],
                    notes=entry.notes,
                    hf_models=hf_models if hf_models else None,
                    hf_usage_notes=hf_usage_notes,
                )
            return algorithms
        except ValidationError as e:
            logger.warning(f"Algorithm analysis schema mismatch: {e.errors()}, using defaults")
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
        algorithms: Optional[Dict[str, Algorithm]] = None,
    ) -> Tuple[List[FileSpec], List[InterfaceSpec], Dict, Dict]:
        """Create file structure - files grouped by task. Uses algorithms for libraries and implementation context."""
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

        # Algorithm context: libraries, implementation approach - ensures file_structure aligns with algo needs
        algorithms_section = ""
        if algorithms:
            lines = ["\n## Algorithm Analysis (align file_structure and dependencies with these)\n"]
            for task_id, alg in algorithms.items():
                libs = getattr(alg, "libraries", []) or []
                approach = getattr(alg, "implementation_approach", "") or ""
                hf = getattr(alg, "hf_models", None)
                lib_str = ", ".join(libs) if libs else "standard libs"
                hf_str = f" | HF models: {hf}" if hf else ""
                lines.append(f"- {task_id}: {approach[:120]}... | Libraries: {lib_str}{hf_str}")
            algorithms_section = "\n".join(lines)

        design_mode = getattr(requirements, "design_mode", None)
        if design_mode and design_mode in ("modern", "minimal", "dashboard"):
            design_mode_hint = (
                f"## Design Mode: Use theme=\"{design_mode}\" in ui_guidelines. "
                f"Adjust primary_color and layout_hints for this style.\n\n"
            )
        else:
            design_mode_hint = ""

        prompt = _prompt_loader.format(
            "scheme_planning",
            design_mode_hint=design_mode_hint,
            title=requirements.title,
            description=requirements.description,
            features=", ".join(f.name for f in requirements.features),
            flow_section=flow_section,
            task_descriptions=task_descriptions,
            algorithms_section=algorithms_section,
        )

        try:
            result = self.llm_service.generate_json(prompt)
            if not isinstance(result, dict):
                result = {}
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

            # Merge ui_guidelines into api_specs (default theme: modern if not provided)
            ui_guidelines = result.get("ui_guidelines")
            if ui_guidelines and isinstance(ui_guidelines, dict):
                api_specs["ui_guidelines"] = ui_guidelines
            elif "ui_guidelines" not in api_specs:
                api_specs["ui_guidelines"] = {"theme": "modern"}

            # Merge ui_design_spec into api_specs (Stage 2 plans UI; Stage 3 implements it)
            ui_design_spec = result.get("ui_design_spec")
            if ui_design_spec and isinstance(ui_design_spec, dict):
                api_specs["ui_design_spec"] = ui_design_spec

            # ===== Stage 2 反思审查机制 - API规范审查 =====
            from config.settings import get_settings
            if getattr(get_settings(), "always_review_api_specs", True):
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
