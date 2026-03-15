"""Stage 2 Planning Agents."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from src.core.data_models import (
    Requirements, Task, Algorithm, FileSpec, TaskType, TaskComplexity,
    InterfaceSpec, ExportSpec, ExternalModelSpec,
)
from src.services.llm_service import LLMService
from src.agents.stage2_planning.task_templates import (
    detect_pattern,
    detect_pattern_with_score,
    format_template_hint,
    format_scheme_pattern_hint,
    build_fallback_tasks,
    build_scheme_fallback,
    PATTERN_CONFIDENCE_THRESHOLD,
)
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

# Keywords that suggest non-HF external capabilities (image/video gen, TTS, PPT, LaTeX, etc.)
# for ModelIntegrationPlanningAgent. Keys are capability_type values for ExternalModelSpec.
_EXTERNAL_CAPABILITY_KEYWORDS: Dict[str, List[str]] = {
    "image_generation": [
        "图片生成",
        "image generation",
        "hero",
        "placeholder",
        "generate image",
        "图生",
        "配图",
        "banner",
        "头图",
        "dall",
        "imagen",
        "stable diffusion",
    ],
    "tts": [
        "语音",
        "tts",
        "text to speech",
        "read aloud",
        "朗读",
        "语音合成",
        "audio narration",
    ],
    # Multimodal generation capabilities discovered in Stage 2
    "video_generation": [
        "视频",
        "video",
        "shorts",
        "讲解视频",
        "课程视频",
        "demo 视频",
        "动画",
        "剪辑",
        "text to video",
        "generate video",
    ],
    "ppt_generation": [
        "ppt",
        "幻灯片",
        "slides",
        "演示文稿",
        "deck",
        "slide deck",
        "pitch deck",
    ],
    "latex_generation": [
        "latex",
        "tex",
        "公式",
        "数学排版",
        "论文模版",
        "math document",
        "数学文档",
        "导出为 latex",
    ],
    "audio_tts": [
        "旁白",
        "配音",
        "语音播报",
        "text to speech",
        "tts",
        "audio narration",
        "voice over",
    ],
    "audio_music": [
        "背景音乐",
        "bgm",
        "配乐",
        "music generation",
        "生成音乐",
        "生成音效",
    ],
}


def _infer_external_capabilities(requirements: Requirements, tasks: List[Task]) -> List[Tuple[str, str]]:
    """Infer which external capabilities are needed from requirements and tasks.

    Returns a list of (capability_type, reason_keyword) pairs, where capability_type
    matches keys in _EXTERNAL_CAPABILITY_KEYWORDS (e.g., image_generation, tts,
    video_generation, ppt_generation, latex_generation, audio_tts, audio_music).
    """
    text_parts = [
        requirements.title or "",
        requirements.description or "",
        " ".join(f.name + " " + (f.description or "") for f in requirements.features),
        " ".join(t.name + " " + (t.description or "") for t in tasks),
    ]
    combined = " ".join(text_parts).lower()
    found: List[Tuple[str, str]] = []
    for cap_type, keywords in _EXTERNAL_CAPABILITY_KEYWORDS.items():
        if any(kw in combined for kw in keywords):
            # Brief reason for logging
            reason = next((kw for kw in keywords if kw in combined), cap_type)
            found.append((cap_type, reason))
    return found


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
        """Single LLM call: entities + pages + tasks. Raw flow text injected directly (no extract LLM call)."""
        flow_section = ""
        skip_flow = getattr(settings, "skip_flow_extraction", False)
        if flow_simulation and not skip_flow and len(flow_simulation.strip()) >= 20:
            raw_flow = flow_simulation.strip()[:1500]
            flow_section = f"\n\n## 用户操作流程参考\n{raw_flow}\n"

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
                return self._fallback_tasks(requirements, combined_text)
            tasks_raw = result.get("tasks", [])
            if not tasks_raw:
                return self._fallback_tasks(requirements, combined_text)
            tasks = self._parse_tasks(tasks_raw)
            if not tasks:
                return self._fallback_tasks(requirements, combined_text)
            tasks = self._validate_dag(tasks)
            if not self._should_run_review(tasks, requirements, combined_text, settings):
                return tasks
            return self._run_review(tasks, requirements, settings)
        except Exception as e:
            logger.warning(f"Unified task division failed: {e}")
            return self._fallback_tasks(requirements, combined_text)

    def _execute_two_phase(
        self, requirements: Requirements, flow_simulation: str, settings
    ) -> List[Task]:
        """Legacy two-phase: extract entities/pages, then task division."""
        entity_page_section = self._extract_entities_and_pages(requirements)
        flow_section = ""
        skip_flow = getattr(settings, "skip_flow_extraction", False)
        if flow_simulation and not skip_flow and len(flow_simulation.strip()) >= 20:
            raw_flow = flow_simulation.strip()[:1500]
            flow_section = f"\n\n## 用户操作流程参考\n{raw_flow}\n"
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
            if not result:
                return self._fallback_tasks(requirements, combined_text)
            tasks = self._parse_tasks(result)
            if not tasks:
                return self._fallback_tasks(requirements, combined_text)
            tasks = self._validate_dag(tasks)
            if not self._should_run_review(tasks, requirements, combined_text, settings):
                return tasks
            return self._run_review(tasks, requirements, settings)
        except Exception as e:
            logger.warning(f"Task division failed: {e}")
            return self._fallback_tasks(requirements, combined_text)

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

    def _fallback_tasks(self, requirements: Requirements, combined_text: str) -> List[Task]:
        """Return template-based tasks when LLM fails. Always returns non-empty tasks."""
        pattern, score = detect_pattern_with_score(combined_text)
        if not pattern or score < PATTERN_CONFIDENCE_THRESHOLD:
            logger.warning("No high-confidence pattern for fallback, using minimal generic tasks")
            return self._minimal_fallback_tasks(requirements)
        raw = build_fallback_tasks(pattern, requirements)
        if not raw:
            logger.warning("Pattern fallback returned no tasks, using minimal generic tasks")
            return self._minimal_fallback_tasks(requirements)
        tasks = self._parse_tasks(raw)
        if not tasks:
            return self._minimal_fallback_tasks(requirements)
        tasks = self._validate_dag(tasks)
        logger.info(f"Using fallback tasks for pattern={pattern} (score={score})")
        return tasks

    def _minimal_fallback_tasks(self, requirements: Requirements) -> List[Task]:
        """Guarantee a runnable minimal task set when pattern matching is unavailable."""
        feature_names = ", ".join(f.name for f in requirements.features[:4]) or "core features"
        raw = [
            {
                "id": "T1",
                "name": "Bootstrap backend skeleton",
                "description": f"Create Flask app entry, config, and core routes for {requirements.title}.",
                "type": "backend",
                "priority": 1,
                "estimated_complexity": "medium",
                "dependencies": [],
                "files_to_add": ["app.py", "app/__init__.py", "requirements.txt"],
                "files_to_modify": [],
            },
            {
                "id": "T2",
                "name": "Implement core user flows",
                "description": f"Implement primary user flows covering: {feature_names}.",
                "type": "frontend",
                "priority": 2,
                "estimated_complexity": "medium",
                "dependencies": ["T1"],
                "files_to_add": ["templates/index.html", "static/css/style.css"],
                "files_to_modify": ["app/__init__.py"],
            },
            {
                "id": "T3",
                "name": "Add basic validation tests",
                "description": "Add smoke tests and route checks for core pages and APIs.",
                "type": "testing",
                "priority": 3,
                "estimated_complexity": "low",
                "dependencies": ["T1", "T2"],
                "files_to_add": ["tests/test_smoke.py"],
                "files_to_modify": [],
            },
        ]
        tasks = self._parse_tasks(raw)
        return self._validate_dag(tasks)

    def _validate_dag(self, tasks: List[Task]) -> List[Task]:
        """Validate dependencies: remove invalid refs, detect cycles, return topo-sorted list."""
        task_ids = {t.id for t in tasks}
        # Fix invalid dependency IDs
        fixed: List[Task] = []
        for t in tasks:
            deps = [d for d in (t.dependencies or []) if d in task_ids]
            fixed.append(Task(
                id=t.id, name=t.name, description=t.description, type=t.type,
                dependencies=deps, priority=t.priority, estimated_complexity=t.estimated_complexity,
                files_to_add=t.files_to_add, files_to_modify=t.files_to_modify,
            ))
        # Topological sort (cycle detection via visited set)
        order: List[str] = []
        temp: set = set()
        perm: set = set()

        def visit(nid: str) -> bool:
            if nid in perm:
                return True
            if nid in temp:
                return False  # cycle
            temp.add(nid)
            task = next((x for x in fixed if x.id == nid), None)
            if task:
                for d in task.dependencies:
                    if not visit(d):
                        return False
            temp.discard(nid)
            perm.add(nid)
            order.append(nid)
            return True

        for t in fixed:
            if not visit(t.id):
                logger.warning("Cycle detected in task dependencies, returning original order")
                return fixed
        ordered = [next(x for x in fixed if x.id == i) for i in reversed(order)]
        return ordered

    def _dependency_depth(self, tasks: List[Task]) -> int:
        """Compute max dependency chain depth. Single task = 1, no deps = 1."""
        task_map = {t.id: t for t in tasks}
        cache: Dict[str, int] = {}

        def depth(tid: str) -> int:
            if tid in cache:
                return cache[tid]
            t = task_map.get(tid)
            if not t or not t.dependencies:
                cache[tid] = 1
                return 1
            cache[tid] = 1 + max(depth(d) for d in t.dependencies)
            return cache[tid]

        return max(depth(t.id) for t in tasks) if tasks else 0

    def _should_run_review(
        self, tasks: List[Task], requirements: Requirements, combined_text: str, settings
    ) -> bool:
        """Decide whether to run task review. Skip when count low unless auth/complex."""
        skip_review = getattr(settings, "skip_task_review_when_count_low", 0)
        force_review_threshold = getattr(settings, "force_task_review_when_count_high", 10)
        dep_depth_threshold = getattr(settings, "force_task_review_dep_depth", 2)
        auth_keywords = ["登录", "login", "注册", "register", "用户认证", "auth"]
        text_lower = combined_text.lower()
        has_auth = any(kw in text_lower for kw in auth_keywords)
        dep_depth = self._dependency_depth(tasks)
        count = len(tasks)
        if count > force_review_threshold:
            logger.info(f"Running task review (count={count} > {force_review_threshold})")
            return True
        if has_auth:
            logger.info("Running task review (auth-related requirements)")
            return True
        if dep_depth > dep_depth_threshold:
            logger.info(f"Running task review (dep depth={dep_depth} > {dep_depth_threshold})")
            return True
        if skip_review > 0 and count <= skip_review:
            logger.info(f"Skipping task review (count={count} <= {skip_review})")
            return False
        return True

    def _run_review(self, tasks: List[Task], requirements: Requirements, settings) -> List[Task]:
        """Run task division review and apply refinements if needed."""
        logger.info("Running task division review...")
        llm = self.llm_service
        if getattr(settings, "use_fast_model_for_task_review", False) and hasattr(llm, "with_model"):
            fast_model = getattr(settings, "fast_model_for_review", "gpt-4o-mini")
            llm = llm.with_model(fast_model)
        review_agent = ReviewAgent(llm)
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


def _default_algorithm_for_task(task: Task) -> Algorithm:
    """Type-aware default Algorithm when LLM fails."""
    tt = task.type.value if hasattr(task.type, "value") else str(task.type)
    if tt in ("backend", "database"):
        approach = f"Flask Blueprint with SQLAlchemy models and REST API routes for {task.name}. Use db.Model subclasses, CRUD endpoints."
        libs = ["flask", "sqlalchemy"]
        ds = ["db.Model", "Blueprint"]
        alg_type = "crud"
    elif tt == "frontend":
        approach = f"Jinja2 templates with fetch() for API calls. Render {task.name} with proper form handling and navigation."
        libs = ["jinja2"]
        ds = []
        alg_type = "standard"
    else:
        approach = f"Standard implementation for {task.name}"
        libs = []
        ds = []
        alg_type = "standard"
    return Algorithm(
        task_id=task.id,
        algorithm_type=alg_type,
        implementation_approach=approach,
        libraries=libs,
        data_structures=ds,
        notes=None,
        hf_models=None,
        hf_usage_notes=None,
    )


def _infer_libraries_for_task(task: Task, hf_models: Optional[List[str]]) -> List[str]:
    """Infer libraries from HF models or task type when LLM omits them."""
    if hf_models:
        return ["transformers", "huggingface_hub"]
    tt = task.type.value if hasattr(task.type, "value") else str(task.type)
    if tt in ("backend", "database"):
        return ["flask", "sqlalchemy"]
    if tt == "frontend":
        return ["jinja2"]
    return []


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
        settings: Any = None,
    ) -> Dict[str, Algorithm]:
        """Analyze algorithms for each task. flow_simulation provides user-flow context for algorithm choice."""
        if settings is None:
            try:
                from config.settings import get_settings
                settings = get_settings()
            except Exception:
                settings = type("_Empty", (), {"skip_hf_for_simple_tasks": 0, "skip_flow_in_algorithm": False})()
        skip_hf = getattr(settings, "skip_hf_for_simple_tasks", 0) or 0
        skip_flow = getattr(settings, "skip_flow_in_algorithm", False)
        has_ml = any(_is_ml_task(t) for t in tasks)
        run_hf = self.hf_model_service and (skip_hf <= 0 or (skip_hf > 0 and len(tasks) > skip_hf) or has_ml)

        hf_context_parts: List[str] = []

        flow_section = ""
        if flow_simulation and not skip_flow and len(flow_simulation.strip()) > 20:
            flow_section = f"\n## User Operation Flow (consider for algorithm choice)\n{flow_simulation[:1500]}\n"

        # Use LLM to detect ML tasks and search HF (enhanced: inference check, relevance, diversity)
        if self.hf_model_service and run_hf:
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

        tasks_summary = "; ".join(
            f"{t.id} [{t.type.value}]: {t.name} - {(t.description or '')[:80]}"
            for t in tasks
        )

        prompt = _prompt_loader.format(
            "algorithm_analysis",
            tasks_summary=tasks_summary,
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
                task = next((x for x in tasks if x.id == task_id), None)
                libraries = _infer_libraries_for_task(task, hf_models) if task else (["transformers", "huggingface_hub"] if hf_models else [])
                ds = getattr(entry, "data_structures", None) or []
                alg_type = getattr(entry, "algorithm_type", None) or "standard"
                algorithms[task_id] = Algorithm(
                    task_id=task_id,
                    algorithm_type=alg_type,
                    implementation_approach=entry.implementation_approach or "",
                    libraries=libraries,
                    data_structures=ds if isinstance(ds, list) else [],
                    notes=entry.notes,
                    hf_models=hf_models if hf_models else None,
                    hf_usage_notes=hf_usage_notes,
                )
            return algorithms
        except ValidationError as e:
            logger.warning(f"Algorithm analysis schema mismatch: {e.errors()}, using defaults")
            return {t.id: _default_algorithm_for_task(t) for t in tasks}
        except Exception as e:
            logger.warning(f"Algorithm analysis failed, using defaults: {e}")
            return {t.id: _default_algorithm_for_task(t) for t in tasks}


class SchemePlanningAgent:
    """Stage 2 Agent 3: Creates file structure. Interface specs generated in Stage 3."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def _should_run_api_review(
        self,
        api_specs: Dict,
        tasks: List[Task],
        requirements: Requirements,
        settings: Any,
    ) -> bool:
        """Decide whether to run API specs review."""
        if not getattr(settings, "always_review_api_specs", True):
            return False
        skip_when = getattr(settings, "skip_api_review_when_simple", 0)
        if skip_when <= 0:
            return True
        endpoints = (api_specs or {}).get("endpoints") or []
        ep_count = len(endpoints)
        has_auth = any(
            "auth" in str(ep.get("path", "")).lower()
            for ep in endpoints
        )
        if has_auth:
            return True
        if ep_count <= skip_when:
            logger.info(f"Skipping API review (endpoints={ep_count} <= {skip_when}, no auth)")
            return False
        return True

    def _fallback_scheme(
        self,
        requirements: Requirements,
        tasks: List[Task],
        combined_text: str,
    ) -> Tuple[List[FileSpec], List[InterfaceSpec], Dict, Dict]:
        """Return structured scheme from template when LLM fails."""
        pattern, score = detect_pattern_with_score(combined_text)
        if not pattern or score < PATTERN_CONFIDENCE_THRESHOLD:
            logger.warning("No high-confidence pattern for scheme fallback, returning empty")
            return [], [], {}, {}
        raw = build_scheme_fallback(pattern, requirements, tasks)
        if not raw:
            return [], [], {}, {}
        return self._parse_scheme_result(raw)

    def _parse_scheme_result(self, result: Dict) -> Tuple[List[FileSpec], List[InterfaceSpec], Dict, Dict]:
        """Parse scheme result (from LLM or fallback) into 4-tuple."""
        files: List[FileSpec] = []
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
        interface_specs: List[InterfaceSpec] = []
        for f in files:
            if f.path.endswith(".py") and not f.path.startswith("tests/"):
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
        api_specs: Dict = result.get("api_specs") or {}
        pyi_stubs: Dict = result.get("pyi_stubs") or {}
        # ui_guidelines may be returned either at top-level or nested inside api_specs.
        ui_guidelines = result.get("ui_guidelines")
        if not ui_guidelines and isinstance(api_specs, dict):
            ui_guidelines = api_specs.get("ui_guidelines")
        if ui_guidelines and isinstance(ui_guidelines, dict):
            api_specs["ui_guidelines"] = ui_guidelines
        elif "ui_guidelines" not in api_specs:
            api_specs["ui_guidelines"] = {"theme": "modern"}
        return files, interface_specs, api_specs, pyi_stubs

    def execute(
        self,
        requirements: Requirements,
        tasks: List[Task],
        flow_simulation: str = "",
        algorithms: Optional[Dict[str, Algorithm]] = None,
    ) -> Tuple[List[FileSpec], List[InterfaceSpec], Dict, Dict]:
        """Create file structure - files grouped by task. Uses algorithms for libraries and implementation context."""
        from config.settings import get_settings
        settings = get_settings()
        skip_flow = getattr(settings, "skip_flow_in_scheme_planning", False)
        combined_text = f"{requirements.title} {requirements.description} {' '.join(f.name for f in requirements.features)}"

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

        flow_section = ""
        if flow_simulation and not skip_flow and len(flow_simulation.strip()) > 0:
            flow_section = f"\n\n## 用户操作流程参考\n{flow_simulation}\n"

        pattern_hint = format_scheme_pattern_hint(detect_pattern(combined_text))

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

        # Layout preference hint: allow Stage 2 to bias toward certain layout archetypes.
        layout_prefs = getattr(requirements, "layout_preferences", None) or []
        layout_prefs_set = {str(v).strip() for v in layout_prefs if v}
        editorial_hint = ""
        combined_text_lower = combined_text.lower()
        content_keywords = [
            "report",
            "whitepaper",
            "case study",
            "analysis",
            "article",
            "blog",
            "portfolio",
            "magazine",
            "杂志",
            "报告",
            "案例研究",
            "长文",
            "文档",
        ]
        editorial_pref = "editorial_magazine" in layout_prefs_set
        editorial_by_content = any(kw in combined_text_lower for kw in content_keywords)
        if editorial_pref or editorial_by_content:
            editorial_hint = (
                "## Layout Archetype Hint: editorial_magazine\n"
                "- Some overview/report/knowledge pages in this app are content-heavy and should prefer an\n"
                "  editorial/magazine layout archetype instead of evenly split grids.\n"
                "- When appropriate, set ui_guidelines.global_layout_style = \"editorial_magazine\" and add\n"
                "  entries under ui_guidelines.page_layouts for routes like \"/\", \"/overview\", \"/report\".\n"
                "- For each such page, describe an asymmetric layout with alternating big headlines and\n"
                "  supporting visuals (images/diagrams), strong typographic hierarchy, and generous\n"
                "  whitespace. Avoid uniform card grids.\n"
                "- In page_layouts[route], you MAY include layout_archetype=\"editorial_magazine\",\n"
                "  applicability_score (0–1), and notes explaining why this layout fits that page.\n\n"
            )

        # Hero layout hint: split hero with left text / right preview for landing/entry pages.
        hero_keywords = [
            "landing",
            "homepage",
            "home page",
            "入口页",
            "首页",
            "产品介绍",
            "项目介绍",
            "选择生成方向",
            "hero",
        ]
        hero_pref = "split_hero_left_text_right_preview" in layout_prefs_set
        hero_by_content = any(kw in combined_text_lower for kw in hero_keywords)
        hero_hint = ""
        if hero_pref or hero_by_content:
            hero_hint = (
                "## Hero Layout Hint: split_hero_left_text_right_preview\n"
                "- 当应用存在典型「产品入口页 / Landing / 首页 Hero」场景时（如根路由 `/` 或 `/overview`），"
                "并且需要在首屏左侧展示主标题、副标题、卖点与操作按钮，右侧展示产品界面预览卡片或截图时，"
                "请在 `ui_guidelines.hero_layouts` 中为对应路由写入分屏 Hero 布局 archetype。\n"
                "- 示例（首页 `/`）：\n"
                "  hero_layouts[\"/\"] = {\n"
                "    \"layout_archetype\": \"split_hero_left_text_right_preview\",\n"
                "    \"primary_column\": \"left\",\n"
                "    \"contrast_mode\": \"dark_bg_light_text\",\n"
                "    \"notes\": \"左列为大标题、副标题、2–3 个卖点要点与主/次 CTA 按钮；右列为产品界面预览卡片，略小于左列，形成 3:2 或 5:4 的左右分屏对比。\"\n"
                "  }\n"
                "- 非入口/介绍性质的页面（例如纯表单页、次级设置页等）无需在 hero_layouts 中登记，保持默认布局即可。\n"
                "- 如果首页 hero 需要在渐变背景上叠加细腻噪点纹理以增强质感，可以在对应路由的 ui_design_spec.page_layouts[route].background 中，\n"
                "  使用 `\"type\": \"aurora_parallax_with_noise\"`，并补充 `\"parallax_speed\"`（如 0.5）与 `\"noise_opacity\"`（如 0.04–0.08），\n"
                "  说明该噪点纹理应保持低对比度、不产生明显网格或拼接痕迹，且不得影响标题与正文的可读性。\n\n"
            )

        prompt = _prompt_loader.format(
            "scheme_planning",
            design_mode_hint=design_mode_hint + editorial_hint + hero_hint,
            title=requirements.title,
            description=requirements.description,
            features=", ".join(f.name for f in requirements.features),
            flow_section=flow_section,
            task_descriptions=task_descriptions,
            algorithms_section=algorithms_section,
            pattern_hint=pattern_hint,
        )

        try:
            result = self.llm_service.generate_json(prompt)
            if not isinstance(result, dict):
                result = {}
            files, interface_specs, api_specs, pyi_stubs = self._parse_scheme_result(result)

            # Merge ui_design_spec if LLM provided it
            ui_design_spec = result.get("ui_design_spec")
            if ui_design_spec and isinstance(ui_design_spec, dict):
                api_specs["ui_design_spec"] = ui_design_spec

            # ===== API 规范审查 =====
            if self._should_run_api_review(api_specs, tasks, requirements, settings):
                logger.info("Running API specs review...")
                llm = self.llm_service
                if getattr(settings, "use_fast_model_for_api_review", False) and hasattr(llm, "with_model"):
                    fast_model = getattr(settings, "fast_model_for_review", "gpt-4o-mini")
                    llm = llm.with_model(fast_model)
                review_agent = ReviewAgent(llm)
                api_review_result = review_agent.review_api_specs(
                    initial_api_specs=api_specs,
                    tasks=tasks,
                    requirements=requirements
                )
                if api_review_result.get("issues") and api_review_result["issues"]:
                    logger.info(f"Found {len(api_review_result['issues'])} API issues, applying refinements...")
                    refined_api_specs = api_review_result.get("refined_api_specs", {})
                    if refined_api_specs:
                        api_specs = refined_api_specs

            return files, interface_specs, api_specs, pyi_stubs

        except Exception as e:
            logger.warning(f"LLM scheme planning failed: {e}")
            return self._fallback_scheme(requirements, tasks, combined_text)


class ModelIntegrationPlanningAgent:
    """Stage 2: Infers external capabilities, searches web for API docs, outputs ExternalModelSpec list."""

    def __init__(self, llm_service: LLMService, web_search_provider: Any = None):
        self.llm_service = llm_service
        self.web_search_provider = web_search_provider

    def _llm_infer_capabilities(
        self,
        requirements: Requirements,
        tasks: List[Task],
        settings: Any = None,
    ) -> List[Tuple[str, str]]:
        """Optionally use LLM to infer external capabilities (video, ppt, latex, audio, etc.)."""
        # Guard: feature flag, default off for backwards compatibility
        if settings is not None and not getattr(
            settings, "enable_stage2_llm_capability_infer", False
        ):
            return []

        allowed_caps = ", ".join(sorted(_EXTERNAL_CAPABILITY_KEYWORDS.keys()))
        tasks_summary = "\n".join(
            f"- {t.id}: {t.name} - {(t.description or '')[:120]}"
            for t in tasks[:20]
        )
        prompt = f"""
You are helping design integrations with external APIs (non-LLM) for an app.

App title: {requirements.title}
Description: {(requirements.description or '')[:500]}

Key features:
{chr(10).join(f"- {f.name}: {(f.description or '')[:120]}" for f in requirements.features[:12])}

Current tasks:
{tasks_summary}

From this description, infer which external capabilities are needed from the following set:
{allowed_caps}

Only include capabilities that clearly add value (e.g., image/video generation, TTS, PPT export, LaTeX export, audio).

Respond in JSON array format, for example:
[
  {{"capability_type": "video_generation", "reason": "User wants tutorial videos for each feature"}},
  {{"capability_type": "ppt_generation", "reason": "User needs downloadable slide decks"}}
]

Do not include capabilities that are not clearly implied by the requirements.
"""
        import json

        try:
            result = self.llm_service.generate_json(prompt)
        except Exception as e:
            logger.debug("LLM capability inference failed: %s", e)
            return []
        if not result:
            return []
        if isinstance(result, dict):
            # tolerate dict with capabilities list
            items = result.get("capabilities") or []
        else:
            items = result
        inferred: List[Tuple[str, str]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            cap = str(item.get("capability_type", "")).strip()
            reason = str(item.get("reason", "")).strip()
            if not cap or cap not in _EXTERNAL_CAPABILITY_KEYWORDS:
                continue
            inferred.append((cap, reason or cap))
        return inferred

    def execute(
        self,
        requirements: Requirements,
        tasks: List[Task],
        flow_simulation: str = "",
        settings: Any = None,
    ) -> List[ExternalModelSpec]:
        if not self.web_search_provider:
            return []
        # 1) Keyword-based capabilities
        capabilities = _infer_external_capabilities(requirements, tasks)
        # 2) Optional LLM-based capability inference for richer multimodal detection
        llm_caps: List[Tuple[str, str]] = []
        try:
            llm_caps = self._llm_infer_capabilities(requirements, tasks, settings=settings)
        except Exception as e:
            logger.debug("LLM-based capability inference skipped due to error: %s", e)

        merged: Dict[str, str] = {}
        for cap, reason in capabilities + llm_caps:
            if cap not in merged:
                merged[cap] = reason
        capabilities_merged: List[Tuple[str, str]] = [(c, r) for c, r in merged.items()]

        if not capabilities_merged:
            return []
        num_results = 5
        if settings:
            num_results = getattr(settings, "web_search_num_results", 5) or 5
        search_results_by_cap: Dict[str, str] = {}
        for cap_type, reason in capabilities_merged:
            natural_name = cap_type.replace("_", " ")
            # Use slightly richer queries to bias towards 2025/2026 docs and API references
            queries = [
                f"{natural_name} API documentation 2026",
                f"{natural_name} REST API reference",
            ]
            if reason:
                queries.append(f"{natural_name} {reason} API 2026")
            snippets = []
            for q in queries[:3]:
                results = self.web_search_provider.search(q, num_results=num_results)
                for r in results:
                    snippets.append(f"- {r.get('title', '')}: {r.get('link', '')}\n  {r.get('snippet', '')}")
            search_results_by_cap[cap_type] = "\n\n".join(snippets) if snippets else "No results."
        capabilities_list = ", ".join(f"{c[0]} ({c[1]})" for c in capabilities_merged)
        search_results = "\n---\n".join(
            f"## {cap}\n{search_results_by_cap.get(cap, '')}" for cap, _ in capabilities_merged
        )
        prompt = _prompt_loader.format(
            "model_integration_planning",
            title=requirements.title or "App",
            description=(requirements.description or "")[:800],
            capabilities_list=capabilities_list,
            search_results=search_results[:6000],
        )
        try:
            schema = {
                "name": "external_model_specs",
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "capability_type": {"type": "string"},
                        "provider_name": {"type": "string"},
                        "docs_url": {"type": "string"},
                        "api_docs_summary": {"type": "string"},
                        "base_url_hint": {"type": "string"},
                        "auth_type": {"type": "string"},
                        "request_body_example": {"type": "string"},
                        "response_image_path": {"type": "string"},
                        "suggested_integration": {"type": "string"},
                    },
                    "required": ["capability_type", "provider_name"],
                    "additionalProperties": True,
                },
            }
            data = self.llm_service.generate_json(
                prompt=prompt,
                max_tokens=1500,
                json_schema=schema,
            )
            if not isinstance(data, list):
                return []
            specs = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                try:
                    spec = ExternalModelSpec(
                        capability_type=str(item.get("capability_type", "")),
                        provider_name=str(item.get("provider_name", "")),
                        docs_url=item.get("docs_url"),
                        api_docs_summary=item.get("api_docs_summary"),
                        base_url_hint=item.get("base_url_hint"),
                        auth_type=str(item.get("auth_type", "api_key")),
                        request_body_example=item.get("request_body_example"),
                        response_image_path=item.get("response_image_path"),
                        suggested_integration=item.get("suggested_integration"),
                    )
                    specs.append(spec)
                except Exception as ex:
                    logger.debug("Skip invalid external spec: %s", ex)
            logger.info("ModelIntegrationPlanningAgent: produced %d external model spec(s)", len(specs))
            return specs
        except Exception as e:
            logger.warning("Model integration planning failed: %s", e)
            return []
