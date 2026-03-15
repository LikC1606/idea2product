"""Main orchestrator for the Idea2Product system."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable, Optional
from datetime import datetime
import threading

from config.settings import Settings, get_primary_llm_config
from src.services.llm_service import LLMService
from src.services.model_registry import ModelRegistry
from src.services.model_selector import ModelSelector
from src.utils.logger import setup_logger, get_logger, set_correlation, clear_correlation
from src.utils.prompt_loader import PromptLoader
from src.utils.file_utils import ensure_dir, write_json, read_json_safe

from .context import ExecutionContext
from .data_models import (
    Requirements,
    EngineeringPlan,
    CodeRepository,
    ValidatedProject,
    ValidationStatus,
    BDDTestCase,
    FileSpec,
    ValidationRun,
    ProductType,
    DirectoryStructure,
    TestResult,
)
from .adapters import engineering_plan_from_stage2
from .exceptions import StageExecutionError

# Import agents
from src.agents.stage1_requirements.interaction_agent import InteractionAgent
from src.agents.stage2_planning.planning_agents import (
    FlowSimulationAgent,
    TaskDivisionAgent,
    AlgorithmAnalysisAgent,
    SchemePlanningAgent,
    ModelIntegrationPlanningAgent,
)
from src.services.hf_model_service import HfModelService
from src.agents.stage3_generation.code_generation_agents import (
    CodeGenerationAgent,
    CodeMemoryAgent,
    CodeMiningAgent,
)
from src.agents.stage4_validation.validation_agents import (
    FullCycleTestingAgent,
    FineTuningAgent,
    VisualVerificationAgent,
    create_validated_project,
)


class Orchestrator:
    """
    Main orchestrator that coordinates all agents through the 4 stages.

    The orchestrator manages the complete workflow:
    1. Stage 1: Requirements gathering via Interaction Agent
    2. Stage 2: Planning via Task Division, Algorithm Analysis, and Scheme Planning agents
    3. Stage 3: Code Generation via Code Generation, Code Memory, and Code Mining agents (Interface-First strategy)
    4. Stage 4: Validation via Full-cycle Testing (BDD + Visual Verification) and Fine-tuning agents
    """

    def __init__(self, settings: Settings):
        """
        Initialize the orchestrator.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.llm_service = LLMService.from_settings(settings)
        self.prompt_loader = PromptLoader(settings.prompts_dir)

        # Model discovery & selection
        self.model_registry = ModelRegistry.load(settings.models_registry_path)
        _, _, primary_model, primary_vlm_model = get_primary_llm_config(settings)
        self.model_selector = ModelSelector(
            registry=self.model_registry,
            default_model=primary_model,
            default_vlm_model=primary_vlm_model,
        )

        # Set up logging
        self.logger = setup_logger(
            "orchestrator",
            log_level=settings.log_level,
        )
        self._stage_state_locks: dict[str, threading.Lock] = {}

    def _apply_random_seed(self) -> None:
        """Apply random seed for reproducibility if configured."""
        seed = getattr(self.settings, "random_seed", None)
        if seed is not None:
            import random

            random.seed(seed)
            try:
                import numpy as np

                np.random.seed(seed)
            except ImportError:
                pass

    def run(
        self,
        user_requirement: str,
        interactive: bool = False,
        product_type: Optional[str] = None,
        model_id: Optional[str] = None,
    ) -> ValidatedProject:
        """
        Run the complete workflow from requirement to validated project.

        Args:
            user_requirement: User's natural language requirement
            interactive: If True, run Stage 1 in interactive mode (ask clarification questions)
            product_type: Optional output type (web, pdf, video, audio, app) for plan and model routing
            model_id: Optional user-selected model id; overrides registry routing when set

        Returns:
            ValidatedProject with working code

        Raises:
            Exception: If any stage fails critically
        """
        self.logger.info("=" * 60)
        self.logger.info(f"Starting Idea2Product workflow (interactive={interactive})")
        self.logger.info("=" * 60)

        self._apply_random_seed()

        # Stage 1 input contract: user_requirement must be non-empty
        if not (user_requirement or "").strip():
            raise ValueError("user_requirement cannot be empty")

        # Create execution context
        context = ExecutionContext(
            user_requirement=user_requirement,
            product_type=product_type,
            model_id=model_id,
        )
        set_correlation(project_id=context.project_id)
        self.logger.info(f"Project ID: {context.project_id}")

        # Create project directory
        project_path = self.settings.projects_dir / context.project_id
        ensure_dir(project_path)
        context.project_path = project_path

        # Create subdirectories
        logs_dir = project_path / "logs"
        artifacts_dir = project_path / "artifacts"
        generated_dir = project_path / "generated"
        ensure_dir(logs_dir)
        ensure_dir(artifacts_dir)
        ensure_dir(generated_dir)

        # Set up project-specific logging
        project_logger = setup_logger(
            f"project.{context.project_id}",
            log_level=self.settings.log_level,
            log_file=logs_dir / "orchestrator.log",
        )

        try:
            # Execute Stage 1: Requirements
            self.logger.info("\n" + "=" * 60)
            self.logger.info("STAGE 1: Requirements Gathering")
            self.logger.info("=" * 60)
            context.update_stage(1)
            try:
                requirements = self.execute_stage_1(context, interactive=interactive)
            except Exception as e:
                self._save_artifact(artifacts_dir, "context.json", context.to_dict())
                err = StageExecutionError(f"Stage 1 failed: {e}", stage=1, partial_context=context)
                raise err from e
            context.requirements = requirements
            self._save_artifact(artifacts_dir, "01_requirements.json", requirements.model_dump(mode="json"))

            # Execute Stage 2: Planning
            self.logger.info("\n" + "=" * 60)
            self.logger.info("STAGE 2: Technical Planning")
            self.logger.info("=" * 60)
            context.update_stage(2)
            try:
                engineering_plan = self.execute_stage_2(context)
            except Exception as e:
                context.add_error(f"Stage 2 failed: {e}")
                self._save_artifact(artifacts_dir, "context.json", {**context.to_dict(), "partial_failure": True, "failed_stage": 2})
                err = StageExecutionError(f"Stage 2 failed: {e}", stage=2, partial_context=context)
                raise err from e
            context.engineering_plan = engineering_plan
            context.tasks = engineering_plan.tasks
            context.algorithms = engineering_plan.algorithms
            self._save_artifact(artifacts_dir, "02_engineering_plan.json", engineering_plan.model_dump(mode="json"))

            # Execute Stage 3: Code Generation
            self.logger.info("\n" + "=" * 60)
            self.logger.info("STAGE 3: Code Generation")
            self.logger.info("=" * 60)
            context.update_stage(3)
            try:
                code_repository = self.execute_stage_3(context)
            except Exception as e:
                context.add_error(f"Stage 3 failed: {e}")
                self._save_artifact(artifacts_dir, "context.json", {**context.to_dict(), "partial_failure": True, "failed_stage": 3})
                err = StageExecutionError(f"Stage 3 failed: {e}", stage=3, partial_context=context)
                raise err from e
            context.code_repository = code_repository
            self._save_artifact(artifacts_dir, "03_code_repository.json", code_repository.model_dump(mode="json"))

            # Stage 4: Validation & Testing
            self.logger.info("\n" + "=" * 60)
            self.logger.info("STAGE 4: Validation & Testing")
            self.logger.info("=" * 60)
            context.update_stage(4)
            try:
                validated_project = self.execute_stage_4(context)
            except Exception as e:
                context.add_error(f"Stage 4 failed: {e}")
                self._save_artifact(artifacts_dir, "context.json", {**context.to_dict(), "partial_failure": True, "failed_stage": 4})
                err = StageExecutionError(f"Stage 4 failed: {e}", stage=4, partial_context=context)
                raise err from e

            # Save final context
            self._save_artifact(artifacts_dir, "context.json", context.to_dict())

            self.logger.info("\n" + "=" * 60)
            self.logger.info("[OK] Workflow completed successfully!")
            self.logger.info("=" * 60)
            self.logger.info(f"Project location: {project_path}")
            self.logger.info(f"Generated code: {generated_dir}")

            return validated_project

        except Exception as e:
            self.logger.error(f"Workflow failed: {e}", exc_info=True)
            context.add_error(str(e))
            to_save = context.to_dict()
            if context.current_stage >= 2:
                to_save["partial_failure"] = True
                to_save["failed_stage"] = context.current_stage
            self._save_artifact(artifacts_dir, "context.json", to_save)
            raise
        finally:
            clear_correlation()

    def _llm_for_stage(
        self,
        stage: int,
        requires_vision: bool = False,
        use_fast: bool = False,
        context: Optional[ExecutionContext] = None,
    ) -> LLMService:
        """Return an LLMService configured for a pipeline stage. use_fast=True prefers fallback model when enabled.
        When context.model_id is set, uses that model; otherwise uses product_type for routing when context is provided.
        """
        prefer_fast = use_fast and getattr(self.settings, "use_fast_model_for_light_stages", True)
        if context and context.model_id:
            entry = self.model_selector.select_by_id(context.model_id)
        else:
            product_type = None
            if context:
                product_type = context.product_type
                if product_type is None and context.requirements and getattr(context.requirements, "product_type", None):
                    pt = context.requirements.product_type
                    product_type = pt.value if hasattr(pt, "value") else str(pt)
            entry = self.model_selector.select(
                stage=stage,
                requires_vision=requires_vision,
                prefer_fast=prefer_fast,
                product_type=product_type,
            )
        if entry.id == self.llm_service.model and (entry.base_url is None or entry.base_url == self.llm_service.base_url):
            return self.llm_service
        return self.llm_service.with_model(
            model_id=entry.id,
            base_url=entry.base_url,
            max_tokens=entry.max_tokens or None,
            provider=getattr(entry, "provider", None),
        )

    def execute_stage_1(self, context: ExecutionContext, interactive: bool = False) -> Requirements:
        """
        Execute Stage 1: Requirements gathering via InteractionAgent.

        Args:
            context: Execution context
            interactive: If True, ask clarification questions interactively

        Returns:
            Structured requirements
        """
        self.logger.info("[Stage1][InteractionAgent] Requirements gathering")

        llm = self._llm_for_stage(1, use_fast=True, context=context)
        self.logger.info(f"[Stage1][InteractionAgent] Using model: {llm.model}")
        agent = InteractionAgent(llm)

        if interactive:
            # Run interactive mode with clarification questions
            requirements = agent.run_interactive(context.user_requirement)
        else:
            # Run non-interactive mode
            requirements = agent.execute(context)

        self.logger.info(
            f"[Stage1][InteractionAgent] Completed, extracted {len(requirements.features)} features"
        )
        return requirements

    def execute_stage_2(self, context: ExecutionContext) -> EngineeringPlan:
        """
        Execute Stage 2: Technical planning. For web/app uses FlowSimulation, TaskDivision, AlgorithmAnalysis, SchemePlanning.
        For pdf/video/audio uses product-type-specific planning agents and fills latex_specs/video_specs/audio_specs.
        """
        requirements = context.requirements
        if requirements is None:
            raise ValueError("Stage 2 requires non-empty requirements in context (Stage2Input contract)")

        product_type = context.product_type
        if product_type is None and getattr(requirements, "product_type", None):
            pt = requirements.product_type
            product_type = pt.value if hasattr(pt, "value") else str(pt)
        product_type = (product_type or "web").lower()

        if product_type in ("pdf", "video", "audio"):
            self.logger.info(f"[Stage2] Product type '{product_type}': using non-web planning path")
            return self._execute_stage_2_non_web(context, product_type)

        self.logger.info("[Stage2] FlowSimulation → TaskDivision → AlgorithmAnalysis → SchemePlanning")

        llm_primary = self._llm_for_stage(2, context=context)
        llm_fast = self._llm_for_stage(2, use_fast=True, context=context)
        self.logger.info(
            f"[Stage2] Models: primary={llm_primary.model}, fast={llm_fast.model} (for flow/algo)"
        )

        # Flow Simulation Agent (Stage 2 Agent 0) - use fast model
        flow_agent = FlowSimulationAgent(llm_fast)
        flow_simulation = flow_agent.execute(requirements)
        self.logger.info("[Stage2][FlowSimulationAgent] Flow simulation completed")

        # Task Division Agent - use primary (complex JSON structure)
        task_agent = TaskDivisionAgent(llm_primary)
        tasks = task_agent.execute(requirements, flow_simulation)
        self.logger.info(f"[Stage2][TaskDivisionAgent] Created {len(tasks)} tasks")

        # Algorithm Analysis Agent (optional HF model search)
        hf_service = None
        if getattr(self.settings, "enable_hf_model_search", True):
            try:
                hf_service = HfModelService(
                    token=getattr(self.settings, "hf_token", None),
                    search_limit=getattr(self.settings, "hf_search_limit", 5),
                    use_cache=getattr(self.settings, "enable_hf_cache", False),
                )
            except Exception as e:
                self.logger.warning(f"HF model service init failed, continuing without: {e}")
        algo_agent = AlgorithmAnalysisAgent(
            llm_fast,
            hf_model_service=hf_service,
            hf_search_limit=getattr(self.settings, "hf_search_limit", 5),
            hf_check_inference=getattr(self.settings, "hf_check_inference", True),
        )
        algorithms = algo_agent.execute(tasks, flow_simulation=flow_simulation)
        self.logger.info(f"[Stage2][AlgorithmAnalysisAgent] Analyzed {len(algorithms)} algorithms")

        # Scheme Planning Agent - use primary (critical for code gen)
        scheme_agent = SchemePlanningAgent(llm_primary)
        file_structure, interface_specs, api_specs, pyi_stubs = scheme_agent.execute(
            requirements, tasks, flow_simulation, algorithms=algorithms
        )

        self.logger.info(
            f"[Stage2][SchemePlanningAgent] Planned {len(file_structure)} files with {len(interface_specs)} interface specs"
        )

        # BDD test-driven: synthesize BDD test cases from requirements + api_specs
        bdd_test_cases = self._synthesize_bdd_tests(requirements, api_specs, llm=llm_primary)
        self.logger.info(
            f"[Stage2][BDD] Synthesized {len(bdd_test_cases)} BDD test cases (test-driven)"
        )

        # Optional: external model/API discovery via web search (Stage 2 model selection)
        external_model_specs = []
        if getattr(self.settings, "enable_stage2_web_search", False):
            try:
                from src.services.web_search_service import get_web_search_provider
                web_provider = get_web_search_provider(self.settings)
                if web_provider:
                    model_agent = ModelIntegrationPlanningAgent(llm_fast, web_search_provider=web_provider)
                    external_model_specs = model_agent.execute(
                        requirements, tasks, flow_simulation=flow_simulation, settings=self.settings
                    )
                    if external_model_specs:
                        self.logger.info(
                            f"[Stage2][ModelIntegrationPlanningAgent] External model specs: {len(external_model_specs)}"
                        )
            except Exception as e:
                self.logger.warning(f"Model integration planning skipped: {e}")

        # Create engineering plan via adapter (handles pyi_stubs fallback, file_structure fallback)
        plan = engineering_plan_from_stage2(
            tasks=tasks,
            algorithms=algorithms,
            file_structure=file_structure,
            interface_specs=interface_specs,
            api_specs=api_specs,
            pyi_stubs=pyi_stubs,
            requirements=requirements,
            bdd_test_cases=bdd_test_cases,
            external_model_specs=external_model_specs if external_model_specs else None,
            default_file_structure_fn=self._default_file_structure,
        )

        self.logger.info("[Stage2] Complete: EngineeringPlan created")
        return plan

    def _execute_stage_2_non_web(self, context: ExecutionContext, product_type: str) -> EngineeringPlan:
        """Stage 2 for pdf/video/audio: use product-type-specific planning agents and return plan with type-specific specs."""
        requirements = context.requirements
        if requirements is None:
            raise ValueError("Stage 2 requires requirements in context")

        llm = self._llm_for_stage(2, context=context)
        self.logger.info(f"[Stage2][NonWeb] Product type={product_type}, model={llm.model}")

        # Dispatch to type-specific planning agent (implemented in stage2 agents)
        try:
            from src.agents.stage2_planning.media_planning_agents import (
                plan_pdf,
                plan_video,
                plan_audio,
            )
        except ImportError:
            # Fallback: minimal plan with placeholder specs until agents are implemented
            self.logger.info("[Stage2][NonWeb] Media planning agents not found, using minimal plan")
            return self._minimal_plan_for_media(requirements, product_type)

        if product_type == "pdf":
            latex_specs = plan_pdf(requirements, llm)
            return self._minimal_plan_for_media(requirements, product_type, latex_specs=latex_specs)
        if product_type == "video":
            video_specs = plan_video(requirements, llm)
            return self._minimal_plan_for_media(requirements, product_type, video_specs=video_specs)
        if product_type == "audio":
            audio_specs = plan_audio(requirements, llm)
            return self._minimal_plan_for_media(requirements, product_type, audio_specs=audio_specs)
        return self._minimal_plan_for_media(requirements, product_type)

    def _minimal_plan_for_media(
        self,
        requirements: Requirements,
        product_type: str,
        latex_specs: Optional[dict] = None,
        video_specs: Optional[dict] = None,
        audio_specs: Optional[dict] = None,
    ) -> EngineeringPlan:
        """Build a minimal EngineeringPlan for pdf/video/audio (no code gen; Stage 3/4 may be no-op or export-only)."""
        pt_enum = getattr(ProductType, product_type.upper(), ProductType.WEB)
        return EngineeringPlan(
            tasks=[],
            algorithms={},
            file_structure=[],
            interface_specs=[],
            dependencies=[],
            architecture_notes=f"{product_type} product: {requirements.title}. {requirements.description or ''}",
            api_specs={},
            pyi_stubs={},
            bdd_test_cases=[],
            product_type=pt_enum,
            latex_specs=latex_specs,
            video_specs=video_specs,
            audio_specs=audio_specs,
        )

    def _default_file_structure(self, tasks: list) -> list:
        """Default file structure when SchemePlanningAgent returns empty. Avoids Stage 3 failure."""
        task_ids = [t.id for t in tasks] if tasks else []
        return [
            FileSpec(path="app/__init__.py", purpose="Flask app factory", dependencies=[], layer="assembly", related_tasks=task_ids),
            FileSpec(path="app/models/__init__.py", purpose="Models package", dependencies=["app/__init__.py"], layer="base", related_tasks=task_ids),
            FileSpec(path="app/routes/__init__.py", purpose="Routes package", dependencies=["app/__init__.py"], layer="assembly", related_tasks=task_ids),
            FileSpec(path="templates/index.html", purpose="Home page", dependencies=[], layer=None, related_tasks=task_ids),
        ]

    def _synthesize_bdd_tests(self, requirements: Requirements, api_specs: dict, llm: LLMService = None) -> list:
        """Synthesize BDD test cases from requirements + API specs using LLM (test-driven)."""
        import json as _json

        features_text = "\n".join(
            f"- {f.name}: {f.description}" for f in requirements.features[:10]
        )
        api_text = _json.dumps(api_specs, indent=2, ensure_ascii=False)[:2000] if api_specs else "None"

        try:
            prompt = self.prompt_loader.format(
                "bdd_synthesis",
                title=requirements.title,
                description=requirements.description or "",
                features=features_text,
                api_specs=api_text,
            )
        except Exception:
            prompt = (
                f"Generate BDD test cases as a JSON array for: {requirements.title}\n"
                f"Features: {features_text}\nAPI specs: {api_text}\n"
                "Return JSON array with test_id, feature, scenario, given, when, then, test_code."
            )

        _llm = llm or self.llm_service
        try:
            schema = {
                "name": "bdd_cases",
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "test_id": {"type": "string"},
                        "feature": {"type": "string"},
                        "scenario": {"type": "string"},
                        "given": {"type": "string"},
                        "when": {"type": "string"},
                        "then": {"type": "string"},
                        "test_code": {"type": "string"},
                    },
                    "required": ["feature", "scenario", "given", "when", "then"],
                    "additionalProperties": True,
                },
            }
            resp = _llm.generate_json(prompt, max_tokens=4000, json_schema=schema)
            cases_data = resp if isinstance(resp, list) else []
        except Exception as e:
            self.logger.warning(f"BDD synthesis LLM call failed, using rule-based fallback: {e}")
            cases_data = []

        bdd_tests = []
        for c in cases_data[:15]:
            try:
                bdd_tests.append(BDDTestCase(
                    test_id=c.get("test_id", f"test_{len(bdd_tests)+1}"),
                    feature=c.get("feature", ""),
                    scenario=c.get("scenario", ""),
                    given=c.get("given", ""),
                    when=c.get("when", ""),
                    then=c.get("then", ""),
                    test_code=c.get("test_code", ""),
                    status="pending",
                ))
            except Exception as ex:
                self.logger.debug("Could not parse BDD test case: %s", ex)
                continue

        if not bdd_tests:
            for i, feature in enumerate(requirements.features[:5], 1):
                bdd_tests.append(BDDTestCase(
                    test_id=f"test_{i}",
                    feature=feature.name,
                    scenario=f"User can {feature.name.lower()}",
                    given="The application is running",
                    when=f"User performs {feature.name.lower()}",
                    then="The application responds correctly",
                    test_code=f"def test_{feature.name.lower().replace(' ', '_')}():\n    pass",
                    status="pending",
                ))

        return bdd_tests

    def execute_stage_3(self, context: ExecutionContext) -> CodeRepository:
        """
        Execute Stage 3: Code generation (CodeMemoryAgent, CodeMiningAgent, CodeGenerationAgent).

        Args:
            context: Execution context with engineering plan

        Returns:
            Complete code repository
        """
        self.logger.info("[Stage3] Code Generation (with CodeMemoryAgent + CodeMiningAgent support)")

        # Stage3Input pre-check
        if context.requirements is None:
            raise ValueError("Stage 3 requires requirements in context (Stage3Input contract)")
        if context.engineering_plan is None:
            raise ValueError("Stage 3 requires an EngineeringPlan in context (Stage3Input contract)")

        plan = context.engineering_plan
        pt = getattr(plan, "product_type", None)
        if pt in (ProductType.PDF, ProductType.VIDEO, ProductType.AUDIO):
            self.logger.info(f"[Stage3] Non-web product type {pt}: skipping code gen, returning minimal repository")
            return CodeRepository(
                skeleton=None,
                files=[],
                structure=DirectoryStructure(root="generated", directories=[], entry_point=""),
                dependencies=[],
                readme_content=f"# {context.requirements.title}\n\nNon-web artifact (plan has {plan.latex_specs or plan.video_specs or plan.audio_specs}).",
            )
        if not plan.file_structure:
            raise ValueError("Stage 3 requires a non-empty file_structure in EngineeringPlan")

        llm = self._llm_for_stage(3, context=context)
        self.logger.info(f"[Stage3] Using model: {llm.model}")

        # Phase 1 & 2: Memory pre_execute and Mining execute (parallel when enabled)
        memory_agent = CodeMemoryAgent(llm, settings=self.settings)
        mining_agent = CodeMiningAgent(llm, settings=self.settings)
        if getattr(self.settings, "enable_parallel_stage3_prefetch", True):
            with ThreadPoolExecutor(max_workers=2) as pool:
                f_mem = pool.submit(memory_agent.pre_execute, context)
                f_min = pool.submit(mining_agent.execute, context)
                memory_context = {}
                mining_by_task = {}
                try:
                    memory_context = f_mem.result()
                except Exception as ex:
                    self.logger.warning("[Stage3][CodeMemoryAgent] Prefetch failed, degrade to empty context: %s", ex)
                try:
                    mining_by_task = f_min.result()
                except Exception as ex:
                    self.logger.warning("[Stage3][CodeMiningAgent] Prefetch failed, degrade to empty context: %s", ex)
            self.logger.info(
                "[Stage3][CodeMemoryAgent+CodeMiningAgent] Prefetch done (parallel)"
            )
        else:
            memory_context = memory_agent.pre_execute(context)
            mining_by_task = mining_agent.execute(context)

        context.memory_context = memory_context
        context.mining_by_task = mining_by_task

        # Optional: generate hero/placeholder images and write to generated/static/images/
        if getattr(self.settings, "enable_image_generation", False):
            from src.services.asset_generation import run_asset_generation
            run_asset_generation(context, self.settings)

        # Phase 3: CodeGenerationAgent - generate code with mining/memory context, incremental snippet save
        code_agent = CodeGenerationAgent(llm, settings=self.settings)
        repository = code_agent.execute(
            context,
            mining_by_task=mining_by_task,
            memory_context=memory_context,
        )

        self.logger.info(
            f"[Stage3][CodeGenerationAgent] Complete, generated {len(repository.files)} files"
        )

        # Phase 4: CodeMemoryAgent.execute - final persist of snippets to memory
        memory_agent.execute(context, repository)

        return repository

    def execute_stage_4(self, context: ExecutionContext) -> ValidatedProject:
        """
        Execute Stage 4: Validation and testing with iterative FineTuning loop.

        Args:
            context: Execution context with code repository

        Returns:
            Validated and tested project
        """
        self.logger.info("[Stage4] Validation & iterative FineTuning loop (FullCycleTesting ↔ FineTuning)")

        # Stage4Input pre-check
        if context.requirements is None:
            raise ValueError("Stage 4 requires requirements in context (Stage4Input contract)")
        if context.engineering_plan is None:
            raise ValueError("Stage 4 requires engineering_plan in context (Stage4Input contract)")
        if context.code_repository is None:
            raise ValueError("Stage 4 requires code_repository in context (Stage4Input contract)")

        plan = context.engineering_plan
        pt = getattr(plan, "product_type", None)
        if pt in (ProductType.PDF, ProductType.VIDEO, ProductType.AUDIO) and not context.code_repository.files:
            self.logger.info(f"[Stage4] Non-web product type {pt} with no code files: skipping validation, returning minimal ValidatedProject")
            test_result = TestResult(logic_passed=True, errors=[], execution_time=0.0)
            return create_validated_project(
                context.code_repository,
                test_result,
                context.requirements,
                fix_attempts=0,
            )

        llm = self._llm_for_stage(4, context=context)
        self.logger.info(f"[Stage4] Using model: {llm.model}")

        # Full-cycle Testing Agent - saves files and generates tests
        testing_agent = FullCycleTestingAgent(llm)
        self.logger.info("[Stage4][FullCycleTestingAgent] Running full-cycle tests")
        test_result = testing_agent.execute(context)
        context.test_results = test_result
        self.logger.info(
            f"[Stage4][FullCycleTestingAgent] Initial test: {len(test_result.errors)} errors, "
            f"logic_passed={test_result.logic_passed}"
        )

        # Frontend API Testing with LangChain Agent (if basic tests pass on logic)
        from src.agents.stage4_validation.validation_agents import FrontendTestingAgent

        def _run_frontend_tests(current_result):
            if not current_result.logic_passed:
                return current_result
            self.logger.info("[Stage4][FrontendTestingAgent] Running frontend API testing...")
            frontend_agent = FrontendTestingAgent(llm)
            frontend_errors = frontend_agent.execute(context.project_path / "generated")
            if frontend_errors:
                current_result.errors.extend(frontend_errors)
                current_result.logic_passed = False
                self.logger.info(
                    f"[Stage4][FrontendTestingAgent] Found {len(frontend_errors)} API-related errors"
                )
            else:
                self.logger.info("[Stage4][FrontendTestingAgent] Frontend API testing passed")
            return current_result

        test_result = _run_frontend_tests(test_result)

        # Visual Verification Agent (runs BEFORE FineTuning so FineTuning can use visual_feedback)
        def _run_visual_verification(current_result):
            if not getattr(self.settings, "enable_visual_verification", False):
                self.logger.info(
                    "[Stage4][VisualVerificationAgent] Disabled by settings; skipping UI analysis"
                )
                return current_result

            vlm_llm = self._llm_for_stage(4, requires_vision=True, context=context)
            self.logger.info(f"[Stage4][VisualVerificationAgent] Using VLM model: {vlm_llm.model}")
            visual_agent = VisualVerificationAgent(vlm_llm)
            visual_result = visual_agent.execute(context)
            current_result.visual_feedback = {
                "alignment_score": visual_result.get("alignment_score", 0.0),
                "missing_elements": visual_result.get("missing_elements", []),
                "issues": visual_result.get("issues", []),
                "layout_feedback": visual_result.get("layout_feedback", ""),
            }
            from src.core.data_models import VisualVerificationResult

            try:
                current_result.visual_verification = VisualVerificationResult(
                    screenshot_path=visual_result.get("screenshots", [""])[0] if visual_result.get("screenshots") else "",
                    requirement_text=context.requirements.title if context.requirements else "",
                    alignment_score=visual_result.get("alignment_score", 0.0),
                    layout_feedback=visual_result.get("layout_feedback", ""),
                    missing_elements=visual_result.get("missing_elements", []),
                    issues=visual_result.get("issues", []),
                    passed=visual_result.get("passed", False),
                )
            except Exception as ex:
                self.logger.debug("Could not create visual result: %s", ex)
            self.logger.info(
                f"[Stage4][VisualVerificationAgent] alignment_score={visual_result.get('alignment_score', 0.0)}"
            )
            return current_result

        test_result = _run_visual_verification(test_result)

        # Iterative FineTuning loop: Testing → (optional Frontend/Visual) → FineTuning, up to max_stage4_rounds
        max_rounds = getattr(self.settings, "max_stage4_rounds", 1)
        quality_threshold = getattr(self.settings, "stage4_quality_threshold", 0.7)
        max_fix_attempts = max(1, getattr(self.settings, "max_fix_attempts", 2))
        fix_rounds = 0

        fine_tuning_agent = FineTuningAgent(llm)

        for round_idx in range(max_rounds):
            # Success condition: logic passed, no errors, and visual alignment above threshold (if present)
            visual_fb = getattr(test_result, "visual_feedback", None)
            alignment_score = (
                visual_fb.get("alignment_score", 1.0) if visual_fb else 1.0
            )
            if (
                test_result.logic_passed
                and not test_result.errors
                and alignment_score >= quality_threshold
            ):
                self.logger.info(
                    f"[Stage4][FineTuningLoop] Converged at round {round_idx} "
                    f"(errors=0, logic_passed=True, alignment_score={alignment_score:.2f})"
                )
                break

            need_logic_fix = (test_result.errors or test_result.warnings) and not test_result.logic_passed
            need_visual_fix = visual_fb and alignment_score < quality_threshold

            if not (need_logic_fix or need_visual_fix):
                self.logger.info(
                    f"[Stage4][FineTuningLoop] No further fixes suggested at round {round_idx}; stopping loop"
                )
                break

            if fix_rounds >= max_fix_attempts:
                self.logger.info(
                    f"[Stage4][FineTuningLoop] Reached max_fix_attempts={max_fix_attempts}; stopping loop"
                )
                break

            self.logger.info(
                f"[Stage4][FineTuningAgent] Round {round_idx + 1}/{max_rounds} "
                f"(errors={len(test_result.errors)}, logic_passed={test_result.logic_passed}, "
                f"alignment_score={alignment_score:.2f})"
            )

            repository, fixed = fine_tuning_agent.execute(context, test_result)
            if not fixed:
                self.logger.info(
                    "[Stage4][FineTuningAgent] No code changes applied; stopping loop"
                )
                break

            fix_rounds += 1
            context.code_repository = repository

            # Re-run full-cycle tests after fixes
            test_result = testing_agent.execute(context)
            context.test_results = test_result
            self.logger.info(
                f"[Stage4][FineTuningAgent] After round {fix_rounds}: "
                f"{len(test_result.errors)} errors, logic_passed={test_result.logic_passed}"
            )

            # Re-run frontend and visual checks with updated code
            test_result = _run_frontend_tests(test_result)
            test_result = _run_visual_verification(test_result)

        # Create validated project (use context.repository in case FineTuning updated it)
        repository = context.code_repository
        validated_project = create_validated_project(
            repository=repository,
            test_result=test_result,
            requirements=context.requirements,
            fix_attempts=fix_rounds,
        )

        self.logger.info(f"Stage 4 complete: Deployable={validated_project.is_deployable}")
        # Record validation run for dashboards / UX (best-effort, non-critical)
        try:
            self._record_validation_run(context, test_result)
        except Exception as ex:
            self.logger.debug("Failed to record validation run: %s", ex)
        return validated_project

    def _save_artifact(self, artifacts_dir: Path, filename: str, data: dict) -> None:
        """
        Save intermediate artifact to file.

        Args:
            artifacts_dir: Directory for artifacts
            filename: Filename
            data: Data to save
        """
        filepath = artifacts_dir / filename
        write_json(filepath, data)
        self.logger.debug(f"Saved artifact: {filename}")

    def _checkpoint_path(self, artifacts_dir: Path) -> Path:
        return artifacts_dir / "stage_state.json"

    def _requirements_signature(self, requirements: Requirements) -> str:
        payload = {
            "title": requirements.title,
            "description": requirements.description,
            "features": [f"{f.id}:{f.name}:{f.description}" for f in requirements.features],
            "constraints": requirements.constraints,
            "product_type": str(getattr(requirements, "product_type", "") or ""),
        }
        import json as _json
        import hashlib as _hashlib
        raw = _json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return _hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _execution_signature(
        self,
        requirements: Requirements,
        product_type: Optional[str],
        model_id: Optional[str],
    ) -> str:
        payload = {
            "requirements_signature": self._requirements_signature(requirements),
            "product_type": str(product_type or ""),
            "model_id": str(model_id or ""),
            "flags": {
                "enable_parallel_stage3_prefetch": bool(getattr(self.settings, "enable_parallel_stage3_prefetch", True)),
                "enable_stage3_syntax_check": bool(getattr(self.settings, "enable_stage3_syntax_check", True)),
                "enable_visual_verification": bool(getattr(self.settings, "enable_visual_verification", False)),
            },
        }
        import json as _json
        import hashlib as _hashlib
        raw = _json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return _hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _stage_state_lock(self, artifacts_dir: Path) -> threading.Lock:
        key = str(artifacts_dir.resolve())
        if key not in self._stage_state_locks:
            self._stage_state_locks[key] = threading.Lock()
        return self._stage_state_locks[key]

    def _load_stage_state(self, artifacts_dir: Path) -> dict:
        return read_json_safe(self._checkpoint_path(artifacts_dir), default={}) or {}

    def _save_stage_state(self, artifacts_dir: Path, state: dict) -> None:
        path = self._checkpoint_path(artifacts_dir)
        tmp = path.with_suffix(path.suffix + ".tmp")
        write_json(tmp, state)
        tmp.replace(path)

    def _mark_stage_state(
        self,
        artifacts_dir: Path,
        stage: int,
        status: str,
        run_id: str,
        execution_signature: str,
        artifact: str = "",
        error: str = "",
    ) -> dict:
        with self._stage_state_lock(artifacts_dir):
            state = self._load_stage_state(artifacts_dir)
            stages = state.setdefault("stages", {})
            prev = stages.get(str(stage), {})
            attempts = int(prev.get("attempts", 0)) + (1 if status == "started" else 0)
            row = {
                "status": status,
                "run_id": run_id,
                "execution_signature": execution_signature,
                "attempts": attempts if status == "started" else int(prev.get("attempts", attempts)),
                "updated_at": datetime.now().isoformat(),
                "artifact": artifact or prev.get("artifact", ""),
                "error": error or "",
            }
            stages[str(stage)] = row
            state["updated_at"] = datetime.now().isoformat()
            self._save_stage_state(artifacts_dir, state)
            return state

    def _record_validation_run(self, context: ExecutionContext, test_result) -> None:
        """Append a ValidationRun entry under artifacts/validation_runs.json for this project."""
        if context.project_path is None:
            return
        artifacts_dir = context.project_path / "artifacts"
        try:
            import json as _json

            artifacts_dir.mkdir(parents=True, exist_ok=True)
            runs_path = artifacts_dir / "validation_runs.json"
            existing = []
            if runs_path.exists():
                try:
                    existing = _json.loads(runs_path.read_text(encoding="utf-8")) or []
                    if not isinstance(existing, list):
                        existing = []
                except Exception:
                    existing = []
            now = datetime.now()
            run_id = f"run_{now.strftime('%Y%m%d_%H%M%S')}"
            status = "passed" if getattr(test_result, "passed", False) else "failed"
            errors = len(getattr(test_result, "errors", []) or [])
            warnings = len(getattr(test_result, "warnings", []) or [])
            metrics = {
                "errors": errors,
                "warnings": warnings,
                "logic_passed": getattr(test_result, "logic_passed", False),
                "visual_passed": bool(
                    getattr(getattr(test_result, "visual_verification", None), "passed", False)
                ),
            }
            summary = f"{'Passed' if status == 'passed' else 'Failed'}: {errors} errors, {warnings} warnings."
            run = ValidationRun(
                run_id=run_id,
                project_id=context.project_id,
                stage="full_cycle",
                status=status,
                started_at=now,
                finished_at=now,
                metrics=metrics,
                summary=summary,
            )
            existing.append(run.model_dump(mode="json"))
            write_json(runs_path, existing)
            self.logger.debug("Recorded validation run %s for project %s", run_id, context.project_id)
        except Exception as ex:
            self.logger.debug("Could not record validation run for %s: %s", context.project_id, ex)

    def run_from_stage_2(
        self,
        project_id: str,
        requirements: Requirements,
        progress_callback: Optional[Callable[[int, str], None]] = None,
        product_type: Optional[str] = None,
        model_id: Optional[str] = None,
    ) -> ValidatedProject:
        """
        Run Stage 2 through 4 for an existing project with given requirements.
        Used for incremental updates: merge new requirements then re-plan and re-generate.
        product_type and model_id optionally override context for plan and model selection.
        """
        self._apply_random_seed()

        def _report(progress: int, stage: str) -> None:
            if progress_callback:
                try:
                    progress_callback(progress, stage)
                except Exception as ex:
                    self.logger.debug("Progress callback failed: %s", ex)

        set_correlation(project_id=project_id)
        project_path = self.settings.projects_dir / project_id
        ensure_dir(project_path)
        logs_dir = project_path / "logs"
        artifacts_dir = project_path / "artifacts"
        ensure_dir(logs_dir)
        ensure_dir(artifacts_dir)

        context = ExecutionContext(
            user_requirement=requirements.description or requirements.title or "App",
            product_type=product_type,
            model_id=model_id,
        )
        context.project_id = project_id
        context.project_path = project_path
        context.requirements = requirements
        context.update_stage(1)
        exec_sig = self._execution_signature(requirements, product_type=product_type, model_id=model_id)
        context.execution_signature = exec_sig

        try:
            self._save_artifact(artifacts_dir, "01_requirements.json", requirements.model_dump(mode="json"))

            stage_state = self._load_stage_state(artifacts_dir)
            stage2_state = (stage_state.get("stages", {}) or {}).get("2", {})
            can_resume_stage2 = (
                stage2_state.get("status") == "succeeded"
                and stage2_state.get("execution_signature") == exec_sig
                and (artifacts_dir / "02_engineering_plan.json").exists()
            )
            if can_resume_stage2:
                try:
                    self.logger.info("run_from_stage_2: resuming from cached Stage 2 result for %s", project_id)
                    engineering_plan = EngineeringPlan.model_validate(
                        read_json_safe(artifacts_dir / "02_engineering_plan.json", default={}) or {}
                    )
                    context.resume_from_stage = 3
                except Exception as ex:
                    self.logger.warning("Stage 2 checkpoint invalid for %s, recomputing: %s", project_id, ex)
                    can_resume_stage2 = False
            if not can_resume_stage2:
                _report(25, "Stage 2: Planning (FlowSimulation + TaskDivision + AlgorithmAnalysis + SchemePlanning)")
                context.update_stage(2)
                self._mark_stage_state(
                    artifacts_dir, stage=2, status="started", run_id=context.run_id, execution_signature=exec_sig
                )
                try:
                    engineering_plan = self.execute_stage_2(context)
                except Exception as e:
                    context.add_error(f"Stage 2 failed: {e}")
                    self._mark_stage_state(
                        artifacts_dir,
                        stage=2,
                        status="failed",
                        run_id=context.run_id,
                        execution_signature=exec_sig,
                        error=str(e),
                    )
                    self._save_artifact(
                        artifacts_dir,
                        "context.json",
                        {**context.to_dict(), "partial_failure": True, "failed_stage": 2},
                    )
                    self.logger.error("run_from_stage_2 Stage 2 failed for %s: %s", project_id, e, exc_info=True)
                    raise StageExecutionError(f"Stage 2 failed: {e}", stage=2, partial_context=context) from e
                self._save_artifact(artifacts_dir, "02_engineering_plan.json", engineering_plan.model_dump(mode="json"))
                self._mark_stage_state(
                    artifacts_dir,
                    stage=2,
                    status="succeeded",
                    run_id=context.run_id,
                    execution_signature=exec_sig,
                    artifact="02_engineering_plan.json",
                )
            context.engineering_plan = engineering_plan
            context.tasks = engineering_plan.tasks
            context.algorithms = engineering_plan.algorithms

            if getattr(self.settings, "enable_plan_completeness_check", True):
                try:
                    from src.utils.plan_validator import validate_plan_completeness
                    _ok, _warnings = validate_plan_completeness(engineering_plan)
                    for _w in _warnings:
                        self.logger.warning("[plan_validator] %s", _w)
                except Exception as _ex:
                    self.logger.debug("Plan completeness check failed: %s", _ex)

            stage_state = self._load_stage_state(artifacts_dir)
            stage3_state = (stage_state.get("stages", {}) or {}).get("3", {})
            can_resume_stage3 = (
                stage3_state.get("status") == "succeeded"
                and stage3_state.get("execution_signature") == exec_sig
                and (artifacts_dir / "03_code_repository.json").exists()
            )
            if can_resume_stage3:
                try:
                    self.logger.info("run_from_stage_2: resuming from cached Stage 3 result for %s", project_id)
                    code_repository = CodeRepository.model_validate(
                        read_json_safe(artifacts_dir / "03_code_repository.json", default={}) or {}
                    )
                    context.resume_from_stage = 4
                except Exception as ex:
                    self.logger.warning("Stage 3 checkpoint invalid for %s, regenerating: %s", project_id, ex)
                    can_resume_stage3 = False
            if not can_resume_stage3:
                _report(50, "Stage 3: Code Generation (CodeMemoryAgent + CodeMiningAgent + CodeGenerationAgent)")
                context.update_stage(3)
                self._mark_stage_state(
                    artifacts_dir, stage=3, status="started", run_id=context.run_id, execution_signature=exec_sig
                )
                try:
                    code_repository = self.execute_stage_3(context)
                except Exception as e:
                    context.add_error(f"Stage 3 failed: {e}")
                    self._mark_stage_state(
                        artifacts_dir,
                        stage=3,
                        status="failed",
                        run_id=context.run_id,
                        execution_signature=exec_sig,
                        error=str(e),
                    )
                    self._save_artifact(
                        artifacts_dir,
                        "context.json",
                        {**context.to_dict(), "partial_failure": True, "failed_stage": 3},
                    )
                    self.logger.error("run_from_stage_2 Stage 3 failed for %s: %s", project_id, e, exc_info=True)
                    raise StageExecutionError(f"Stage 3 failed: {e}", stage=3, partial_context=context) from e
                self._save_artifact(artifacts_dir, "03_code_repository.json", code_repository.model_dump(mode="json"))
                self._mark_stage_state(
                    artifacts_dir,
                    stage=3,
                    status="succeeded",
                    run_id=context.run_id,
                    execution_signature=exec_sig,
                    artifact="03_code_repository.json",
                )
            context.code_repository = code_repository

            _report(75, "Stage 4: Validation & Testing (FullCycleTestingAgent ↔ FineTuningAgent loop)")
            context.update_stage(4)
            self._mark_stage_state(
                artifacts_dir, stage=4, status="started", run_id=context.run_id, execution_signature=exec_sig
            )
            try:
                validated_project = self.execute_stage_4(context)
            except Exception as e:
                context.add_error(f"Stage 4 failed: {e}")
                self._mark_stage_state(
                    artifacts_dir,
                    stage=4,
                    status="failed",
                    run_id=context.run_id,
                    execution_signature=exec_sig,
                    error=str(e),
                )
                self._save_artifact(
                    artifacts_dir,
                    "context.json",
                    {**context.to_dict(), "partial_failure": True, "failed_stage": 4},
                )
                self.logger.error("run_from_stage_2 Stage 4 failed for %s: %s", project_id, e, exc_info=True)
                raise StageExecutionError(f"Stage 4 failed: {e}", stage=4, partial_context=context) from e
            self._mark_stage_state(
                artifacts_dir,
                stage=4,
                status="succeeded",
                run_id=context.run_id,
                execution_signature=exec_sig,
                artifact="context.json",
            )
            self._save_artifact(artifacts_dir, "context.json", context.to_dict())

            self.logger.info("run_from_stage_2 complete for %s", project_id)
            return validated_project

        except StageExecutionError:
            raise
        except Exception as e:
            self.logger.error("run_from_stage_2 failed for %s: %s", project_id, e, exc_info=True)
            context.add_error(str(e))
            to_save = context.to_dict()
            if context.current_stage >= 2:
                to_save["partial_failure"] = True
                to_save["failed_stage"] = min(context.current_stage, 4)
            self._save_artifact(artifacts_dir, "context.json", to_save)
            raise
        finally:
            clear_correlation()

    def run_first_time(self, project_id: str, requirements: Requirements) -> ValidatedProject:
        """
        First-time generate for a project: run from Stage 2 with given requirements
        (Stage 1 output already provided as requirements). Same as run_from_stage_2.
        """
        return self.run_from_stage_2(project_id, requirements)
