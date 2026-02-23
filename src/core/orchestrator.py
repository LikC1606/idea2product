"""Main orchestrator for the Idea2Product system."""

from pathlib import Path
from typing import Optional
from datetime import datetime

from config.settings import Settings
from src.services.llm_service import LLMService
from src.utils.logger import setup_logger, get_logger
from src.utils.prompt_loader import PromptLoader
from src.utils.file_utils import ensure_dir, write_json

from .context import ExecutionContext
from .data_models import (
    Requirements,
    EngineeringPlan,
    CodeRepository,
    ValidatedProject,
    ValidationStatus,
)

# Import agents
from src.agents.stage1_requirements.interaction_agent import InteractionAgent
from src.agents.stage2_planning.planning_agents import (
    FlowSimulationAgent,
    TaskDivisionAgent,
    AlgorithmAnalysisAgent,
    SchemePlanningAgent,
)
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

        # Set up logging
        self.logger = setup_logger(
            "orchestrator",
            log_level=settings.log_level,
        )

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

        # Create execution context
        context = ExecutionContext(user_requirement=user_requirement)
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
            requirements = self.execute_stage_1(context, interactive=interactive)
            context.requirements = requirements
            self._save_artifact(artifacts_dir, "01_requirements.json", requirements.model_dump(mode="json"))

            # Execute Stage 2: Planning
            self.logger.info("\n" + "=" * 60)
            self.logger.info("STAGE 2: Technical Planning")
            self.logger.info("=" * 60)
            context.update_stage(2)
            engineering_plan = self.execute_stage_2(context)
            context.engineering_plan = engineering_plan
            self._save_artifact(artifacts_dir, "02_engineering_plan.json", engineering_plan.model_dump(mode="json"))

            # Execute Stage 3: Code Generation
            self.logger.info("\n" + "=" * 60)
            self.logger.info("STAGE 3: Code Generation")
            self.logger.info("=" * 60)
            context.update_stage(3)
            code_repository = self.execute_stage_3(context)
            context.code_repository = code_repository
            self._save_artifact(artifacts_dir, "03_code_repository.json", code_repository.model_dump(mode="json"))

            # Stage 4: Validation & Testing
            self.logger.info("\n" + "=" * 60)
            self.logger.info("STAGE 4: Validation & Testing")
            self.logger.info("=" * 60)
            context.update_stage(4)
            validated_project = self.execute_stage_4(context)

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

        # Use Interaction Agent to parse requirements
        agent = InteractionAgent(self.llm_service)

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

        # Flow Simulation Agent (Stage 2 Agent 0)
        flow_agent = FlowSimulationAgent(self.llm_service)
        flow_simulation = flow_agent.execute(requirements)
        self.logger.info("  - Flow simulation completed")

        # Task Division Agent
        task_agent = TaskDivisionAgent(self.llm_service)
        tasks = task_agent.execute(requirements, flow_simulation)
        self.logger.info(f"  - Created {len(tasks)} tasks")

        # Algorithm Analysis Agent
        algo_agent = AlgorithmAnalysisAgent(self.llm_service)
        algorithms = algo_agent.execute(tasks)
        self.logger.info(f"  - Analyzed {len(algorithms)} algorithms")

        # Scheme Planning Agent
        scheme_agent = SchemePlanningAgent(self.llm_service)
        file_structure, interface_specs, api_specs, pyi_stubs = scheme_agent.execute(
            requirements, tasks, flow_simulation
        )

        if not file_structure:
            self.logger.warning("SchemePlanningAgent returned empty file_structure")

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

        # Create engineering plan
        plan = EngineeringPlan(
            tasks=tasks,
            algorithms=algorithms,
            file_structure=file_structure,
            interface_specs=interface_specs,
            dependencies=sorted(dependencies),
            architecture_notes=f"Web application: {requirements.title}",
            api_specs=api_specs,
            pyi_stubs=pyi_stubs
        )

        self.logger.info("Stage 2 complete: Engineering plan created")
        return plan

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

        # Code Generation Agent (with optional memory/mining via settings)
        code_agent = CodeGenerationAgent(self.llm_service, settings=self.settings)
        repository = code_agent.execute(context)

        self.logger.info(f"Stage 3 complete: Generated {len(repository.files)} files")

        # Code Memory Agent: save snippets when ENABLE_CODE_MEMORY
        memory_agent = CodeMemoryAgent(self.llm_service, settings=self.settings)
        memory_agent.execute(context, repository)

        # Code Mining Agent: runs per-task in CodeGenerationAgent; this logs status
        mining_agent = CodeMiningAgent(self.llm_service, settings=self.settings)
        mining_agent.execute(context)

        return repository

    def execute_stage_4(self, context: ExecutionContext) -> ValidatedProject:
        """
        Execute Stage 4: Validation and testing with run-fix loop.

        Args:
            context: Execution context with code repository

        Returns:
            Validated and tested project
        """
        self.logger.info("Stage 4: Run-Fix Loop (run code → fix errors → repeat)")

        # Full-cycle Testing Agent - saves files and generates tests
        testing_agent = FullCycleTestingAgent(self.llm_service)
        test_result = testing_agent.execute(context)

        self.logger.info(f"  - Initial test: {len(test_result.errors)} errors")

        # 运行-修复循环 (最多5次)
        validation_agent = FullCycleTestingAgent(self.llm_service)

        # 获取接口规范（如果有）
        interface_specs = []
        if hasattr(context, 'engineering_plan') and context.engineering_plan:
            interface_specs = context.engineering_plan.interface_specs

        # 运行-修复循环
        repository = validation_agent.run_and_fix_loop(
            project_path=context.project_path,
            repository=context.code_repository,
            requirements=context.requirements,
            interface_specs=interface_specs,
            max_iterations=5
        )

        # 更新 context 中的 repository
        context.code_repository = repository

        # 重新运行测试确认
        test_result = testing_agent.execute(context)
        self.logger.info(f"  - Final test: {len(test_result.errors)} errors, logic_passed={test_result.logic_passed}")

        # Optional: if still errors/warnings, try FineTuningAgent (syntax/import/entry-point fixes on repository)
        if (test_result.errors or test_result.warnings) and not test_result.logic_passed:
            fine_tuning_agent = FineTuningAgent(self.llm_service)
            repository, fixed = fine_tuning_agent.execute(context, test_result)
            if fixed:
                context.code_repository = repository
                repository = context.code_repository
                test_result = testing_agent.execute(context)
                self.logger.info(f"  - After FineTuning: {len(test_result.errors)} errors, logic_passed={test_result.logic_passed}")

        # Visual Verification Agent (optional, controlled by settings flag)
        if getattr(self.settings, "enable_visual_verification", False):
            visual_agent = VisualVerificationAgent(self.llm_service)
            visual_agent.execute(context)
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

    def run_from_stage_2(self, project_id: str, requirements: Requirements) -> ValidatedProject:
        """
        Run Stage 2 through 4 for an existing project with given requirements.
        Used for incremental updates: merge new requirements then re-plan and re-generate.
        Creates/uses project_path = projects_dir / project_id and writes all artifacts there.
        """
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

        self._save_artifact(artifacts_dir, "01_requirements.json", requirements.model_dump(mode="json"))

        context.update_stage(2)
        engineering_plan = self.execute_stage_2(context)
        context.engineering_plan = engineering_plan
        self._save_artifact(artifacts_dir, "02_engineering_plan.json", engineering_plan.model_dump(mode="json"))

        context.update_stage(3)
        code_repository = self.execute_stage_3(context)
        context.code_repository = code_repository
        self._save_artifact(artifacts_dir, "03_code_repository.json", code_repository.model_dump(mode="json"))

        context.update_stage(4)
        validated_project = self.execute_stage_4(context)
        self._save_artifact(artifacts_dir, "context.json", context.to_dict())

        self.logger.info(f"run_from_stage_2 complete for {project_id}")
        return validated_project

    def run_first_time(self, project_id: str, requirements: Requirements) -> ValidatedProject:
        """
        First-time generate for a project: run from Stage 2 with given requirements
        (Stage 1 output already provided as requirements). Same as run_from_stage_2.
        """
        return self.run_from_stage_2(project_id, requirements)
