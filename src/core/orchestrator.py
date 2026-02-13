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
        self.llm_service = LLMService(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            vlm_model=settings.openai_vlm_model,
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
        )
        self.prompt_loader = PromptLoader(settings.prompts_dir)

        # Set up logging
        self.logger = setup_logger(
            "orchestrator",
            log_level=settings.log_level,
        )

    def run(self, user_requirement: str) -> ValidatedProject:
        """
        Run the complete workflow from requirement to validated project.

        Args:
            user_requirement: User's natural language requirement

        Returns:
            ValidatedProject with working code

        Raises:
            Exception: If any stage fails critically
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting Idea2Product workflow")
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
            requirements = self.execute_stage_1(context)
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

            # Execute Stage 4: Validation
            self.logger.info("\n" + "=" * 60)
            self.logger.info("STAGE 4: Validation & Testing")
            self.logger.info("=" * 60)
            context.update_stage(4)
            validated_project = self.execute_stage_4(context)
            context.validated_project = validated_project
            self._save_artifact(artifacts_dir, "04_validated_project.json", validated_project.model_dump(mode="json"))

            # Save final context
            self._save_artifact(artifacts_dir, "context.json", context.to_dict())

            self.logger.info("\n" + "=" * 60)
            self.logger.info("✓ Workflow completed successfully!")
            self.logger.info("=" * 60)
            self.logger.info(f"Project location: {project_path}")
            self.logger.info(f"Generated code: {generated_dir}")

            return validated_project

        except Exception as e:
            self.logger.error(f"Workflow failed: {e}", exc_info=True)
            context.add_error(str(e))
            self._save_artifact(artifacts_dir, "context.json", context.to_dict())
            raise

    def execute_stage_1(self, context: ExecutionContext) -> Requirements:
        """
        Execute Stage 1: Requirements gathering.

        Args:
            context: Execution context

        Returns:
            Structured requirements

        Raises:
            NotImplementedError: Stage 1 agents not yet implemented
        """
        self.logger.info("Stage 1: Interaction Agent")
        # TODO: Implement Interaction Agent
        raise NotImplementedError("Stage 1: Interaction Agent not yet implemented")

    def execute_stage_2(self, context: ExecutionContext) -> EngineeringPlan:
        """
        Execute Stage 2: Technical planning.

        Args:
            context: Execution context with requirements

        Returns:
            Complete engineering plan

        Raises:
            NotImplementedError: Stage 2 agents not yet implemented
        """
        self.logger.info("Stage 2: Task Division → Algorithm Analysis → Scheme Planning")
        # TODO: Implement Stage 2 agents
        raise NotImplementedError("Stage 2: Planning agents not yet implemented")

    def execute_stage_3(self, context: ExecutionContext) -> CodeRepository:
        """
        Execute Stage 3: Code generation.

        Args:
            context: Execution context with engineering plan

        Returns:
            Complete code repository

        Raises:
            NotImplementedError: Stage 3 agents not yet implemented
        """
        self.logger.info("Stage 3: Code Generation (with Memory and Mining support)")
        # TODO: Implement Stage 3 agents
        raise NotImplementedError("Stage 3: Code generation agents not yet implemented")

    def execute_stage_4(self, context: ExecutionContext) -> ValidatedProject:
        """
        Execute Stage 4: Validation and testing.

        Args:
            context: Execution context with code repository

        Returns:
            Validated and tested project

        Raises:
            NotImplementedError: Stage 4 agents not yet implemented
        """
        self.logger.info("Stage 4: Black-box Testing → Fine-tuning (if needed)")
        # TODO: Implement Stage 4 agents
        raise NotImplementedError("Stage 4: Validation agents not yet implemented")

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
