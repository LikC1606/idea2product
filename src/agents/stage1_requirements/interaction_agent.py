"""Interaction Agent for Stage 1 - Requirements Gathering."""

import json
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from src.core.data_models import Requirements, Feature
from src.core.context import ExecutionContext
from src.services.llm_service import LLMService
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ClarificationQuestion:
    """A clarification question to ask the user."""
    id: str
    category: str  # "functional", "technical", "data", "users", "ui"
    question: str
    answer: Optional[str] = None

    def ask(self) -> str:
        """Print the question and get user answer."""
        print(f"\n[{self.category.upper()}] {self.question}")
        answer = input("> ").strip()
        self.answer = answer
        return answer


class InteractionAgent:
    """
    Stage 1 Agent: Interaction Agent

    Clarifies user requirements through simple parsing.
    For MVP, this agent extracts features from the user's requirement string.
    """

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def execute(self, context: ExecutionContext) -> Requirements:
        """
        Execute Stage 1: Requirements gathering.

        Args:
            context: Execution context with user_requirement

        Returns:
            Structured Requirements object
        """
        user_requirement = context.user_requirement
        logger.info(f"Processing requirement: {user_requirement}")

        # Use LLM to extract features from requirement
        prompt = f"""
Analyze the following user requirement and extract the key features.
Return a JSON object with the following structure:
{{
    "title": "A short title for the application",
    "description": "A brief description of what the application does",
    "features": [
        {{
            "id": "f1",
            "name": "Feature name",
            "description": "Detailed feature description",
            "priority": 1-5
        }}
    ],
    "constraints": ["any technical constraints mentioned"],
    "target_users": "Who is this for",
    "data_requirements": "Any data storage needs mentioned"
}}

User Requirement:
{user_requirement}

Respond with valid JSON only.
"""

        try:
            result = self.llm_service.generate_json(prompt)

            # Convert to Requirements model
            features = []
            for i, f in enumerate(result.get("features", []), 1):
                features.append(Feature(
                    id=f.get("id", f"f{i}"),
                    name=f["name"],
                    description=f["description"],
                    priority=f.get("priority", 3)
                ))

            requirements = Requirements(
                title=result.get("title", "Generated Application"),
                description=result.get("description", user_requirement),
                features=features,
                constraints=result.get("constraints", []),
                target_users=result.get("target_users"),
                data_requirements=result.get("data_requirements")
            )

            logger.info(f"Extracted {len(features)} features from requirement")
            return requirements

        except Exception as e:
            logger.warning(f"LLM extraction failed, using fallback: {e}")
            # Fallback: create basic requirements from user string
            return self._fallback_parse(user_requirement)

    def _fallback_parse(self, requirement: str) -> Requirements:
        """Fallback parsing when LLM is not available."""
        # Simple keyword-based feature extraction
        features = []

        keywords = {
            "add": "Add new items",
            "create": "Create new items",
            "delete": "Delete items",
            "remove": "Remove items",
            "edit": "Edit existing items",
            "update": "Update items",
            "view": "View items",
            "list": "List all items",
            "search": "Search functionality",
            "filter": "Filter items",
            "sort": "Sort items",
            "login": "User authentication",
            "register": "User registration",
            "save": "Save data",
            "load": "Load data",
            "export": "Export data",
            "import": "Import data",
        }

        requirement_lower = requirement.lower()
        feature_id = 1
        for key, desc in keywords.items():
            if key in requirement_lower:
                features.append(Feature(
                    id=f"f{feature_id}",
                    name=desc,
                    description=f"Allow users to {desc.lower()}",
                    priority=1
                ))
                feature_id += 1

        if not features:
            features.append(Feature(
                id="f1",
                name="Basic Functionality",
                description="Core application functionality",
                priority=1
            ))

        return Requirements(
            title="Generated Application",
            description=requirement,
            features=features,
            constraints=[],
            target_users=None,
            data_requirements=None
        )

    # =========================================================================
    # Interactive Dialogue Methods
    # =========================================================================

    def generate_clarification_questions(self, requirement: str) -> List[ClarificationQuestion]:
        """
        Generate clarification questions based on the user requirement.

        Args:
            requirement: The initial user requirement

        Returns:
            List of ClarificationQuestion objects
        """
        prompt = f"""
You are a requirements analyst helping clarify user needs. Analyze the following
requirement and generate clarification questions to better understand the user's needs.

Generate 3-6 questions that cover these aspects:
1. FUNCTIONAL: What exactly should the feature do? Any specific behaviors?
2. DATA: How should data be stored? What fields are needed?
3. USERS: Who are the target users? Any authentication needs?
4. UI: Any specific UI preferences or layouts?
5. TECHNICAL: Any specific tech stack or deployment requirements?

Return a JSON array of questions, each with:
{{
    "id": "q1", "category": "functional|data|users|ui|technical",
    "question": "The question text"
}}

User Requirement:
{requirement}

Respond with a valid JSON array only.
"""
        try:
            result = self.llm_service.generate_json(prompt)
            questions = []

            # Handle both list and dict responses
            items = result if isinstance(result, list) else result.get("questions", [])

            for i, q in enumerate(items, 1):
                questions.append(ClarificationQuestion(
                    id=q.get("id", f"q{i}"),
                    category=q.get("category", "functional"),
                    question=q.get("question", q.get("text", ""))
                ))

            logger.info(f"Generated {len(questions)} clarification questions")
            return questions

        except Exception as e:
            logger.warning(f"Failed to generate questions with LLM: {e}")
            return self._default_questions(requirement)

    def _default_questions(self, requirement: str) -> List[ClarificationQuestion]:
        """Fallback default questions when LLM is not available."""
        return [
            ClarificationQuestion(
                id="q1",
                category="functional",
                question="What are the core features you need?"
            ),
            ClarificationQuestion(
                id="q2",
                category="data",
                question="How should data be stored (local file, database, cloud)?"
            ),
            ClarificationQuestion(
                id="q3",
                category="users",
                question="Do users need to log in?"
            ),
        ]

    def run_interactive(self, requirement: str) -> Requirements:
        """
        Run interactive dialogue to gather requirements.

        This method:
        1. Analyzes the initial requirement
        2. Generates clarification questions
        3. Asks user each question interactively
        4. Generates final Requirements based on answers

        Args:
            requirement: Initial user requirement string

        Returns:
            Final structured Requirements object
        """
        print("\n" + "=" * 60)
        print("STAGE 1: Requirements Gathering (Interactive Mode)")
        print("=" * 60)
        print(f"\nYour initial requirement: {requirement}\n")

        # Step 1: Generate clarification questions
        questions = self.generate_clarification_questions(requirement)

        print(f"\nI have {len(questions)} questions to clarify your requirements.")
        print("Type your answer after each question (or press Enter to skip).\n")

        # Step 2: Ask each question interactively
        clarifications = {}
        for q in questions:
            answer = q.ask()
            if answer:
                clarifications[q.question] = answer

        # Step 3: Generate final requirements with all info
        final_requirements = self._generate_final_requirements(
            requirement, questions, clarifications
        )

        # Step 4: Show summary
        print("\n" + "=" * 60)
        print("REQUIREMENTS SUMMARY")
        print("=" * 60)
        print(f"Title: {final_requirements.title}")
        print(f"Description: {final_requirements.description}")
        print(f"\nFeatures ({len(final_requirements.features)}):")
        for f in final_requirements.features:
            print(f"  [{f.priority}] {f.name}: {f.description}")
        if final_requirements.constraints:
            print(f"Constraints: {', '.join(final_requirements.constraints)}")
        if final_requirements.target_users:
            print(f"Target Users: {final_requirements.target_users}")
        if final_requirements.data_requirements:
            print(f"Data Requirements: {final_requirements.data_requirements}")

        print("\n" + "=" * 60)

        return final_requirements

    def _generate_final_requirements(
        self,
        requirement: str,
        questions: List[ClarificationQuestion],
        clarifications: Dict[str, str]
    ) -> Requirements:
        """
        Generate final Requirements object using LLM with collected clarifications.
        """
        # Build context from clarifications
        clarification_text = ""
        for q, a in clarifications.items():
            clarification_text += f"\nQ: {q}\nA: {a}\n"

        prompt = f"""
You are a requirements analyst. Based on the initial requirement and user's
clarifications, create a structured requirements specification.

Initial Requirement:
{requirement}

User Clarifications:
{clarification_text}

Generate a JSON object with:
{{
    "title": "A short catchy title for the application",
    "description": "2-3 sentence description of what the app does",
    "features": [
        {{
            "id": "f1",
            "name": "Feature name (action-oriented)",
            "description": "Detailed feature description",
            "priority": 1-5 (1 = must have)
        }}
    ],
    "constraints": ["any technical constraints"],
    "target_users": "Who is this for",
    "data_requirements": "Data storage needs"
}}

Respond with valid JSON only.
"""
        try:
            result = self.llm_service.generate_json(prompt)

            features = []
            for i, f in enumerate(result.get("features", []), 1):
                features.append(Feature(
                    id=f.get("id", f"f{i}"),
                    name=f.get("name", f"Feature {i}"),
                    description=f.get("description", ""),
                    priority=f.get("priority", 3)
                ))

            requirements = Requirements(
                title=result.get("title", "Generated Application"),
                description=result.get("description", requirement),
                features=features,
                constraints=result.get("constraints", []),
                target_users=result.get("target_users"),
                data_requirements=result.get("data_requirements"),
                user_clarifications=clarifications
            )

            return requirements

        except Exception as e:
            logger.warning(f"LLM final generation failed: {e}")
            # Fallback: create requirements from clarifications directly
            return self._fallback_from_clarifications(requirement, clarifications)

    def _fallback_from_clarifications(
        self,
        requirement: str,
        clarifications: Dict[str, str]
    ) -> Requirements:
        """Create Requirements from clarifications without LLM."""
        features = []

        # Try to extract features from clarifications
        for i, (q, a) in enumerate(clarifications.items(), 1):
            if any(kw in q.lower() for kw in ["feature", "function", "do"]):
                features.append(Feature(
                    id=f"f{i}",
                    name=a.split(',')[0].strip() if ',' in a else a.strip()[:50],
                    description=a,
                    priority=1
                ))

        if not features:
            features.append(Feature(
                id="f1",
                name="Core Functionality",
                description="Application core functionality based on requirements",
                priority=1
            ))

        return Requirements(
            title="Generated Application",
            description=requirement,
            features=features,
            constraints=[],
            target_users=clarifications.get("Who are the target users?"),
            data_requirements=clarifications.get("How should data be stored?"),
            user_clarifications=clarifications
        )
