"""Main orchestrator for the Idea2Product system."""

from pathlib import Path
from typing import Callable, Optional
from datetime import datetime

from config.settings import Settings
from src.services.llm_service import LLMService
from src.services.model_registry import ModelRegistry
from src.services.model_selector import ModelSelector
from src.utils.logger import setup_logger, get_logger, set_correlation, clear_correlation
from src.utils.prompt_loader import PromptLoader
from src.utils.file_utils import ensure_dir, write_json

from .context import ExecutionContext
from .data_models import (
    Requirements,
    EngineeringPlan,
    CodeRepository,
    ValidatedProject,
    ValidationStatus,
    BDDTestCase,
)

# Import agents
from src.agents.stage1_requirements.interaction_agent import InteractionAgent
from src.agents.stage2_planning.planning_agents import (
    FlowSimulationAgent,
    TaskDivisionAgent,
    AlgorithmAnalysisAgent,
    SchemePlanningAgent,
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
        self.model_selector = ModelSelector(
            registry=self.model_registry,
            default_model=getattr(settings, "openai_model", "gpt-4o"),
            default_vlm_model=getattr(settings, "openai_vlm_model", "gpt-4o"),
        )

        # Set up logging
        self.logger = setup_logger(
            "orchestrator",
            log_level=settings.log_level,
        )

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

    def run(self, user_requirement: str, interactive: bool = False) -> ValidatedProject:
        """
        Run the complete workflow from requirement to validated project.

        Args:
            user_requirement: User's natural language requirement
            interactive: If True, run Stage 1 in interactive mode (ask clarification questions)

        Returns:
            ValidatedProject with working code

        Raises:
            Exception: If any stage fails critically
        """
        self.logger.info("=" * 60)
        self.logger.info(f"Starting Idea2Product workflow (interactive={interactive})")
        self.logger.info("=" * 60)

        self._apply_random_seed()

        # Create execution context
        context = ExecutionContext(user_requirement=user_requirement)
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
                raise
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
                raise
            context.engineering_plan = engineering_plan
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
                raise
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
                raise

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
            self._save_artifact(artifacts_dir, "context.json", context.to_dict())
            raise
        finally:
            clear_correlation()

    def _llm_for_stage(self, stage: int, requires_vision: bool = False, use_fast: bool = False) -> LLMService:
        """Return an LLMService configured for a pipeline stage. use_fast=True prefers gpt-4o-mini when enabled."""
        prefer_fast = use_fast and getattr(self.settings, "use_fast_model_for_light_stages", True)
        entry = self.model_selector.select(stage=stage, requires_vision=requires_vision, prefer_fast=prefer_fast)
        if entry.id == self.llm_service.model and (entry.base_url is None or entry.base_url == self.llm_service.base_url):
            return self.llm_service
        return self.llm_service.with_model(
            model_id=entry.id,
            base_url=entry.base_url,
            max_tokens=entry.max_tokens or None,
        )

    def execute_stage_1(self, context: ExecutionContext, interactive: bool = False) -> Requirements:
        """
        Execute Stage 1: Requirements gathering.

        Args:
            context: Execution context
            interactive: If True, ask clarification questions interactively

        Returns:
            Structured requirements
        """
        self.logger.info("Stage 1: Interaction Agent")

        llm = self._llm_for_stage(1, use_fast=True)
        self.logger.info(f"  - Model: {llm.model}")
        agent = InteractionAgent(llm)

        if interactive:
            # Run interactive mode with clarification questions
            requirements = agent.run_interactive(context.user_requirement)
        else:
            # Run non-interactive mode
            requirements = agent.execute(context)

        self.logger.info(f"Stage 1 complete: {len(requirements.features)} features extracted")
        return requirements

    def execute_stage_2(self, context: ExecutionContext) -> EngineeringPlan:
        """
        Execute Stage 2: Technical planning.

        Args:
            context: Execution context with requirements

        Returns:
            Complete engineering plan
        """
        self.logger.info("Stage 2: Task Division → Algorithm Analysis → Scheme Planning")

        # Basic precondition check
        requirements = context.requirements
        if requirements is None:
            raise ValueError("Stage 2 requires non-empty requirements in context")

        llm_primary = self._llm_for_stage(2)
        llm_fast = self._llm_for_stage(2, use_fast=True)
        self.logger.info(f"  - Model: {llm_primary.model} (fast for flow/algo: {llm_fast.model})")

        # Flow Simulation Agent (Stage 2 Agent 0) - use fast model
        flow_agent = FlowSimulationAgent(llm_fast)
        flow_simulation = flow_agent.execute(requirements)
        self.logger.info("  - Flow simulation completed")

        # Task Division Agent - use primary (complex JSON structure)
        task_agent = TaskDivisionAgent(llm_primary)
        tasks = task_agent.execute(requirements, flow_simulation)
        self.logger.info(f"  - Created {len(tasks)} tasks")

        # Algorithm Analysis Agent (optional HF model search)
        hf_service = None
        if getattr(self.settings, "enable_hf_model_search", False):
            try:
                hf_service = HfModelService(
                    token=getattr(self.settings, "hf_token", None),
                    search_limit=getattr(self.settings, "hf_search_limit", 5),
                )
            except Exception as e:
                self.logger.warning(f"HF model service init failed, continuing without: {e}")
        algo_agent = AlgorithmAnalysisAgent(
            llm_fast,
            hf_model_service=hf_service,
            hf_search_limit=getattr(self.settings, "hf_search_limit", 5),
        )
        algorithms = algo_agent.execute(tasks)
        self.logger.info(f"  - Analyzed {len(algorithms)} algorithms")

        # Scheme Planning Agent - use primary (critical for code gen)
        scheme_agent = SchemePlanningAgent(llm_primary)
        file_structure, interface_specs, api_specs, pyi_stubs = scheme_agent.execute(
            requirements, tasks, flow_simulation
        )

        if not file_structure:
            self.logger.error(
                "SchemePlanningAgent returned empty file_structure; "
                "Stage 3 will have nothing to generate. Check LLM connectivity and prompt."
            )

        self.logger.info(
            f"  - Planned {len(file_structure)} files with {len(interface_specs)} interface specs"
        )

        # Extract dependencies from algorithm analysis (always include flask as base)
        dependencies: set[str] = {"flask"}
        for alg in algorithms.values():
            for lib in alg.libraries:
                if not lib:
                    continue
                lib_normalized = lib.strip()
                # Filter out obvious non-package or built-in names
                if lib_normalized.lower() in {"dict", "list", "str", "int", "standard"}:
                    continue
                dependencies.add(lib_normalized)

        # BDD test-driven: synthesize BDD test cases from requirements + api_specs
        bdd_test_cases = self._synthesize_bdd_tests(requirements, api_specs, llm=llm_primary)
        self.logger.info(f"  - Synthesized {len(bdd_test_cases)} BDD test cases (test-driven)")

        # Create engineering plan
        plan = EngineeringPlan(
            tasks=tasks,
            algorithms=algorithms,
            file_structure=file_structure,
            interface_specs=interface_specs,
            dependencies=sorted(dependencies),
            architecture_notes=f"Web application: {requirements.title}",
            api_specs=api_specs,
            pyi_stubs=pyi_stubs,
            bdd_test_cases=bdd_test_cases,
        )

        self.logger.info("Stage 2 complete: Engineering plan created")
        return plan

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
            raw = _llm.generate(prompt, max_tokens=4000)
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0]
            cases_data = _json.loads(raw)
            if not isinstance(cases_data, list):
                cases_data = []
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
            except Exception:
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
        Execute Stage 3: Code generation.

        Args:
            context: Execution context with engineering plan

        Returns:
            Complete code repository
        """
        self.logger.info("Stage 3: Code Generation (with Memory and Mining support)")

        # Basic precondition checks
        if context.engineering_plan is None:
            raise ValueError("Stage 3 requires an EngineeringPlan in context")
        if not context.engineering_plan.file_structure:
            raise ValueError("Stage 3 requires a non-empty file_structure in EngineeringPlan")

        llm = self._llm_for_stage(3)
        self.logger.info(f"  - Model: {llm.model}")

        # Code Generation Agent (with optional memory/mining via settings)
        code_agent = CodeGenerationAgent(llm, settings=self.settings)
        repository = code_agent.execute(context)

        self.logger.info(f"Stage 3 complete: Generated {len(repository.files)} files")

        # Code Memory Agent: save snippets when ENABLE_CODE_MEMORY
        memory_agent = CodeMemoryAgent(llm, settings=self.settings)
        memory_agent.execute(context, repository)

        # Code Mining Agent: runs per-task in CodeGenerationAgent; this logs status
        mining_agent = CodeMiningAgent(llm, settings=self.settings)
        mining_agent.execute(context)

        return repository

    def execute_stage_4(self, context: ExecutionContext) -> ValidatedProject:
        """
        Execute Stage 4: Validation and testing with code fix agent.

        Args:
            context: Execution context with code repository

        Returns:
            Validated and tested project
        """
        self.logger.info("Stage 4: Code Fix with LangChain Agent")

        llm = self._llm_for_stage(4)
        self.logger.info(f"  - Model: {llm.model}")

        # Full-cycle Testing Agent - saves files and generates tests
        testing_agent = FullCycleTestingAgent(llm)
        test_result = testing_agent.execute(context)

        self.logger.info(f"  - Initial test: {len(test_result.errors)} errors")

        # Use CodeFixAgent to fix code (replaces run_and_fix_loop)
        from src.agents.stage4_validation.validation_agents import CodeFixAgent

        code_fix_agent = CodeFixAgent(llm)
        generated_path = context.project_path / "generated"

        try:
            code_fix_agent.execute(generated_path)
        except Exception as e:
            self.logger.warning(f"CodeFixAgent failed ({e}), falling back to run_and_fix_loop")
            context.code_repository = testing_agent.run_and_fix_loop(
                context.project_path,
                context.code_repository,
                context.requirements,
                getattr(context.engineering_plan, "api_specs", None),
                max_iterations=5,
            )
            # Re-save fixed files to disk
            testing_agent._save_files(generated_path, context.code_repository)

        # Re-run tests to confirm
        test_result = testing_agent.execute(context)
        self.logger.info(f"  - Final test: {len(test_result.errors)} errors, logic_passed={test_result.logic_passed}")

        # Frontend API Testing with LangChain Agent (if basic tests pass)
        from src.agents.stage4_validation.validation_agents import FrontendTestingAgent
        if test_result.logic_passed:
            self.logger.info("  - Running frontend API testing...")
            frontend_agent = FrontendTestingAgent(llm)
            frontend_errors = frontend_agent.execute(context.project_path / "generated", port=5555)
            if frontend_errors:
                test_result.errors.extend(frontend_errors)
                test_result.logic_passed = False
                self.logger.info(f"  - Frontend API testing found {len(frontend_errors)} errors")
            else:
                self.logger.info("  - Frontend API testing passed!")

        # Optional: if still errors/warnings, try FineTuningAgent (syntax/import/entry-point fixes on repository)
        if (test_result.errors or test_result.warnings) and not test_result.logic_passed:
            fine_tuning_agent = FineTuningAgent(llm)
            repository, fixed = fine_tuning_agent.execute(context, test_result)
            if fixed:
                context.code_repository = repository
                repository = context.code_repository
                test_result = testing_agent.execute(context)
                self.logger.info(f"  - After FineTuning: {len(test_result.errors)} errors, logic_passed={test_result.logic_passed}")

        # Visual Verification Agent (optional, controlled by settings flag)
        # Uses a vision-capable model when available
        if getattr(self.settings, "enable_visual_verification", False):
            vlm_llm = self._llm_for_stage(4, requires_vision=True)
            self.logger.info(f"  - VLM Model: {vlm_llm.model}")
            visual_agent = VisualVerificationAgent(vlm_llm)
            visual_result = visual_agent.execute(context)
            # Store visual feedback into test_result for downstream use (P4/P5)
            test_result.visual_feedback = {
                "alignment_score": visual_result.get("alignment_score", 0.0),
                "missing_elements": visual_result.get("missing_elements", []),
                "issues": visual_result.get("issues", []),
                "layout_feedback": visual_result.get("layout_feedback", ""),
            }
            from src.core.data_models import VisualVerificationResult
            try:
                test_result.visual_verification = VisualVerificationResult(
                    screenshot_path=visual_result.get("screenshots", [""])[0] if visual_result.get("screenshots") else "",
                    requirement_text=context.requirements.title if context.requirements else "",
                    alignment_score=visual_result.get("alignment_score", 0.0),
                    layout_feedback=visual_result.get("layout_feedback", ""),
                    missing_elements=visual_result.get("missing_elements", []),
                    issues=visual_result.get("issues", []),
                    passed=visual_result.get("passed", False),
                )
            except Exception:
                pass
            self.logger.info(f"  - Visual alignment_score={visual_result.get('alignment_score', 0.0)}")
        else:
            self.logger.info("Visual verification disabled by settings; skipping UI analysis")

        # Create validated project (use context.repository in case FineTuning updated it)
        repository = context.code_repository
        validated_project = create_validated_project(
            repository=repository,
            test_result=test_result,
            requirements=context.requirements
        )

        self.logger.info(f"Stage 4 complete: Deployable={validated_project.is_deployable}")
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

    def run_from_stage_2(
        self,
        project_id: str,
        requirements: Requirements,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> ValidatedProject:
        """
        Run Stage 2 through 4 for an existing project with given requirements.
        Used for incremental updates: merge new requirements then re-plan and re-generate.
        Creates/uses project_path = projects_dir / project_id and writes all artifacts there.
        If progress_callback(progress_pct, stage_name) is provided, it is called at each stage start.
        """
        self._apply_random_seed()

        def _report(progress: int, stage: str) -> None:
            if progress_callback:
                try:
                    progress_callback(progress, stage)
                except Exception:
                    pass

        set_correlation(project_id=project_id)
        project_path = self.settings.projects_dir / project_id
        ensure_dir(project_path)
        logs_dir = project_path / "logs"
        artifacts_dir = project_path / "artifacts"
        ensure_dir(logs_dir)
        ensure_dir(artifacts_dir)

        context = ExecutionContext(user_requirement=requirements.description or requirements.title or "App")
        context.project_id = project_id
        context.project_path = project_path
        context.requirements = requirements
        context.update_stage(1)

        try:
            self._save_artifact(artifacts_dir, "01_requirements.json", requirements.model_dump(mode="json"))

            _report(25, "Stage 2: Planning")
            context.update_stage(2)
            engineering_plan = self.execute_stage_2(context)
            context.engineering_plan = engineering_plan
            self._save_artifact(artifacts_dir, "02_engineering_plan.json", engineering_plan.model_dump(mode="json"))

            _report(50, "Stage 3: Code Generation")
            context.update_stage(3)
            code_repository = self.execute_stage_3(context)
            context.code_repository = code_repository
            self._save_artifact(artifacts_dir, "03_code_repository.json", code_repository.model_dump(mode="json"))

            _report(75, "Stage 4: Validation & Testing")
            context.update_stage(4)
            validated_project = self.execute_stage_4(context)
            self._save_artifact(artifacts_dir, "context.json", context.to_dict())

            self.logger.info(f"run_from_stage_2 complete for {project_id}")
            return validated_project

        except Exception as e:
            self.logger.error(f"run_from_stage_2 failed for {project_id}: {e}", exc_info=True)
            context.add_error(str(e))
            self._save_artifact(artifacts_dir, "context.json", context.to_dict())
            raise
        finally:
            clear_correlation()

    def run_first_time(self, project_id: str, requirements: Requirements) -> ValidatedProject:
        """
        First-time generate for a project: run from Stage 2 with given requirements
        (Stage 1 output already provided as requirements). Same as run_from_stage_2.
        """
        return self.run_from_stage_2(project_id, requirements)
