"""Interaction Agent for Stage 1 - Requirements Gathering."""

import json
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from src.core.data_models import Requirements, Feature
from src.core.context import ExecutionContext
from src.services.llm_service import LLMService
from src.utils.logger import get_logger
from src.core.response_schemas import ExtractedRequirements, RequirementAnalysis, validate_response
from .requirement_analysis_prompt import get_requirement_analysis_prompt

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
            validated = validate_response(result, ExtractedRequirements)

            features = []
            for i, f in enumerate(validated.features, 1):
                features.append(Feature(
                    id=f.get("id", f"f{i}"),
                    name=f["name"],
                    description=f["description"],
                    priority=f.get("priority", 3)
                ))

            requirements = Requirements(
                title=validated.title,
                description=validated.description or user_requirement,
                features=features,
                constraints=validated.constraints,
                target_users=validated.target_users,
                data_requirements=validated.data_requirements,
            )

            logger.info(f"Extracted {len(features)} features from requirement")
            return requirements

        except Exception as e:
            logger.warning(f"LLM extraction failed, using fallback: {e}")
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
    # Requirement Analysis Method (New)
    # =========================================================================

    def analyze_requirement(self, requirement: str) -> dict:
        """
        分析需求，判断是否需要继续提问，并提供改进建议。

        Args:
            requirement: 用户的需求描述

        Returns:
            分析结果字典：
            - needs_clarification: 是否需要继续提问
            - questions: 需要澄清的问题列表
            - improvements: 改进建议列表
        """
        logger.info("Analyzing requirement...")

        prompt = get_requirement_analysis_prompt(requirement)

        try:
            result = self.llm_service.generate_json(prompt)
            needs = result.get("needs_clarification", False)
            logger.info(f"Analysis complete. Needs clarification: {needs}")
            return result

        except Exception as e:
            logger.warning(f"Requirement analysis failed: {e}")
            fallback_qs = self._default_questions(requirement)
            return {
                "needs_clarification": True,
                "questions": [
                    {"question": q.question, "reason": "LLM unavailable; keyword-based fallback"}
                    for q in fallback_qs
                ],
                "improvements": []
            }

    # =========================================================================
    # Interactive Dialogue Methods
    # =========================================================================

    def generate_clarification_questions(
        self,
        requirement: str,
        analysis_result: Optional[dict] = None,
    ) -> List[ClarificationQuestion]:
        """
        Generate clarification questions tailored to the specific requirement.

        Args:
            requirement: The initial user requirement
            analysis_result: Optional output from analyze_requirement(); when
                provided, its identified gaps are injected into the prompt so
                the generated questions stay focused on those gaps.

        Returns:
            List of ClarificationQuestion objects
        """
        # Build an optional "gaps" section from a prior analysis
        gaps_section = ""
        if analysis_result:
            gap_reasons = [
                q.get("reason", "")
                for q in analysis_result.get("questions", [])
                if q.get("reason")
            ]
            if gap_reasons:
                gaps_section = (
                    "\n## Identified gaps from prior analysis (focus on these)\n"
                    + "\n".join(f"- {r}" for r in gap_reasons[:6])
                    + "\n"
                )

        prompt = f"""You are a requirements analyst. Based on the user requirement below,
generate 3-6 clarification questions that are **specific to this requirement**.

## Rules
- Every question MUST address a concrete gap, ambiguity, or missing detail in
  THIS requirement. Do NOT ask generic questions that could apply to any app.
- You may optionally assign a category (functional / data / users / ui / technical)
  but only when the question genuinely belongs to that category. Do NOT force one
  question per category.
- The question language should match the user's requirement language.

## Good / bad examples

Requirement: "Build a todo app with add and delete"
  GOOD: "Should tasks have a due date or priority level?"
  GOOD: "Do you need to group tasks by category or tag?"
  BAD:  "Who are the target users?" (too generic)
  BAD:  "How should data be stored?" (implementation detail, not a requirement gap)

Requirement: "Build a blog with comments"
  GOOD: "Should comments support nested replies or only top-level?"
  GOOD: "Can multiple authors publish posts, or is it single-author?"
  BAD:  "What are the core features?" (already stated: blog + comments)

Requirement: "Build a calculator with add, subtract, multiply, divide"
  GOOD: "Should it support parentheses and operator precedence?"
  GOOD: "Do you need a calculation history panel?"
  BAD:  "What interaction method?" (obvious for a calculator)
{gaps_section}
## User Requirement

{requirement}

## Output

Return a JSON array (no markdown fences):
[
  {{"id": "q1", "category": "functional", "question": "..."}},
  ...
]
"""
        try:
            result = self.llm_service.generate_json(prompt)
            questions = []

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
        """Keyword-based fallback questions when LLM is not available.

        Instead of returning the same 3 generic questions for every requirement,
        this method detects the application type from the requirement text and
        returns questions relevant to that type.
        """
        req_lower = requirement.lower()

        _DOMAIN_QUESTIONS: Dict[str, List[str]] = {
            "todo": [
                "Should tasks have a due date or priority level?",
                "Do you need to organize tasks by category or tag?",
                "Should completed tasks be archived or permanently deleted?",
            ],
            "blog": [
                "Should comments support nested replies?",
                "Can multiple authors publish posts, or single-author only?",
                "Do you need rich-text editing or Markdown for posts?",
            ],
            "calculator": [
                "Should it support parentheses and operator precedence?",
                "Do you need a calculation history panel?",
                "Should it handle scientific operations (sin, cos, log)?",
            ],
            "weather": [
                "Should it show a multi-day forecast or current weather only?",
                "Should the user search by city name or use their GPS location?",
                "Do you need weather alerts or notifications?",
            ],
            "chat": [
                "Should it support group conversations or 1-on-1 only?",
                "Do you need message history persistence?",
                "Should it support file/image sharing?",
            ],
            "note": [
                "Should notes support rich formatting (bold, lists, images)?",
                "Do you need folders or tags to organize notes?",
                "Should notes sync across devices?",
            ],
            "shop": [
                "Should there be a shopping cart and checkout flow?",
                "Do you need product categories and search/filtering?",
                "Should it support user reviews and ratings?",
            ],
        }

        _DOMAIN_KEYWORDS: Dict[str, List[str]] = {
            "todo": ["todo", "task", "待办", "任务"],
            "blog": ["blog", "post", "article", "博客", "文章"],
            "calculator": ["calculator", "calculate", "计算器", "计算"],
            "weather": ["weather", "forecast", "天气", "预报"],
            "chat": ["chat", "message", "聊天", "消息", "即时通讯"],
            "note": ["note", "notebook", "笔记", "记事"],
            "shop": ["shop", "store", "ecommerce", "商城", "商店", "购物"],
        }

        for domain, keywords in _DOMAIN_KEYWORDS.items():
            if any(kw in req_lower for kw in keywords):
                return [
                    ClarificationQuestion(id=f"q{i+1}", category="functional", question=q)
                    for i, q in enumerate(_DOMAIN_QUESTIONS[domain])
                ]

        return [
            ClarificationQuestion(
                id="q1",
                category="functional",
                question=f"What specific behaviors should the app have beyond '{requirement[:60]}'?",
            ),
            ClarificationQuestion(
                id="q2",
                category="functional",
                question="Are there any features you consider must-have vs nice-to-have?",
            ),
        ]

    def run_interactive(self, requirement: str) -> Requirements:
        """
        Run interactive dialogue to gather requirements.

        This method:
        1. Analyzes the initial requirement with LLM
        2. Determines if clarification is needed
        3. If needed, asks improvement questions
        4. Generates final Requirements based on all info

        Args:
            requirement: Initial user requirement string

        Returns:
            Final structured Requirements object
        """
        print("\n" + "=" * 60)
        print("STAGE 1: Requirements Gathering (Interactive Mode)")
        print("=" * 60)
        print(f"\nYour initial requirement: {requirement}\n")

        # Step 1: Analyze requirement with LLM
        print("Analyzing your requirement...")
        analysis = self.analyze_requirement(requirement)

        # Step 2: Show analysis result to user (simplified)
        needs_clarification = analysis.get("needs_clarification", False)

        if needs_clarification:
            print("\n[需要进一步澄清]")

            # Show improvement suggestions
            improvements = analysis.get("improvements", [])
            if improvements:
                print("\n改进建议:")
                for imp in improvements[:3]:
                    priority = imp.get("priority", "medium")
                    symbol = {"high": "●", "medium": "○", "low": "◌"}.get(priority, "○")
                    print(f"  {symbol} {imp.get('content', '')}")
        else:
            print("\n[需求已足够完善]")

        print("-" * 60)

        # Step 3: Generate clarification questions based on analysis
        questions_from_analysis = analysis.get("questions", [])
        if questions_from_analysis:
            questions = []
            for i, q in enumerate(questions_from_analysis, 1):
                questions.append(ClarificationQuestion(
                    id=f"q{i}",
                    category="functional",
                    question=q.get("question", "")
                ))
            logger.info(f"Using {len(questions)} questions from analysis")
        else:
            questions = self.generate_clarification_questions(
                requirement, analysis_result=analysis
            )

        print(f"\n需要澄清 {len(questions)} 个问题:")
        print("输入回答后按回车 (直接回车跳过)\n")

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

    # =========================================================================
    # Build-style: chat reply, conversation -> requirements, merge requirements
    # =========================================================================

    def reply_in_chat(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate an assistant reply given conversation history (no pipeline).
        Used for ChatGPT-style continuous dialogue.
        """
        if not messages:
            return "请描述你想要的应用或功能，我会根据你的描述在后台生成产品。你可以随时补充需求，我会在已有基础上改进。"
        system = """You are a friendly requirements analyst. The user is describing an app they want to build.
Have a natural conversation to clarify their needs. When you have enough information, you can suggest they're ready;
the system will automatically generate the app in the background. Keep replies concise. Use the same language as the user."""
        conv = "\n".join(
            f"{'User' if m.get('role') == 'user' else 'Assistant'}: {m.get('content', '')}"
            for m in messages[-20:]
        )
        prompt = f"Conversation so far:\n{conv}\n\nRespond as the assistant (one message only):"
        try:
            return self.llm_service.generate(prompt, system=system)
        except Exception as e:
            logger.warning(f"reply_in_chat failed: {e}")
            return "已收到。我会根据当前对话在后台生成或更新应用，你可以在右侧查看代码和预览。"

    def conversation_to_requirements(self, messages: List[Dict[str, str]]) -> Requirements:
        """
        Turn full conversation history into a single Requirements object (for first-time generate).
        """
        conv = "\n".join(
            f"{m.get('role', 'user').upper()}: {m.get('content', '')}"
            for m in messages
        )
        prompt = f"""Based on this conversation about an app, output a single JSON object for the application requirements.
Conversation:
{conv}

Output JSON only:
{{
    "title": "Short app title",
    "description": "2-3 sentence description",
    "features": [{{"id": "f1", "name": "...", "description": "...", "priority": 1}}],
    "constraints": [],
    "target_users": "...",
    "data_requirements": "..."
}}
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
            return Requirements(
                title=result.get("title", "Generated Application"),
                description=result.get("description", ""),
                features=features,
                constraints=result.get("constraints", []),
                target_users=result.get("target_users"),
                data_requirements=result.get("data_requirements")
            )
        except Exception as e:
            logger.warning(f"conversation_to_requirements failed: {e}")
            last_user = next((m.get("content", "") for m in reversed(messages) if m.get("role") == "user"), "")
            return self._fallback_parse(last_user or "Web application")

    def merge_requirements(
        self,
        existing: Requirements,
        new_message: str,
        recent_messages: Optional[List[Dict[str, str]]] = None,
    ) -> Requirements:
        """
        Merge new user request into existing Requirements (for incremental generate).
        """
        existing_json = existing.model_dump(mode="json")
        existing_str = json.dumps(existing_json, indent=2, ensure_ascii=False)[:2500]
        extra = ""
        if recent_messages:
            extra = "\nRecent messages:\n" + "\n".join(
                f"{m.get('role')}: {m.get('content', '')}" for m in recent_messages[-5:]
            )
        prompt = f"""Existing requirements (JSON):
{existing_str}

New user request: {new_message}
{extra}

Output the UPDATED requirements as a single JSON object (same structure: title, description, features, constraints, target_users, data_requirements).
Incorporate the new request into features or description. Do not remove existing features unless the user explicitly asks to remove something.
Respond with valid JSON only."""
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
            return Requirements(
                title=result.get("title", existing.title),
                description=result.get("description", existing.description),
                features=features,
                constraints=result.get("constraints", existing.constraints),
                target_users=result.get("target_users") or existing.target_users,
                data_requirements=result.get("data_requirements") or existing.data_requirements
            )
        except Exception as e:
            logger.warning(f"merge_requirements failed: {e}")
            return existing
