"""Interaction Agent for Stage 1 - Requirements Gathering."""

from typing import Dict, Any
from src.core.data_models import Requirements, Feature
from src.core.context import ExecutionContext
from src.services.llm_service import LLMService
from src.utils.logger import get_logger

logger = get_logger(__name__)


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
