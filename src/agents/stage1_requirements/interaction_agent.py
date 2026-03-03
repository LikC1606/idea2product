"""Interaction Agent for Stage 1 - Requirements Gathering."""

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Iterator

from src.core.data_models import Requirements, Feature
from src.core.context import ExecutionContext
from src.services.llm_service import LLMService
from src.utils.logger import get_logger
from src.utils.prompt_loader import PromptLoader
from pydantic import ValidationError
from src.core.response_schemas import ExtractedRequirements, RequirementAnalysis, validate_response

logger = get_logger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parents[3] / "config" / "prompts"
_prompt_loader = PromptLoader(_PROMPTS_DIR)


@dataclass
class ClarificationOption:
    """An answer option for a clarification question."""

    id: str
    label: str


@dataclass
class ClarificationQuestion:
    """A clarification question to ask the user (optionally with choices)."""

    id: str
    category: str  # "functional", "technical", "data", "users", "ui"
    question: str
    options: List[ClarificationOption] = field(default_factory=list)
    allow_multiple: bool = False
    allow_other: bool = True
    answer: Optional[str] = None

    def ask(self) -> str:
        """Print the question (with options when available) and get user answer."""
        print(f"\n[{self.category.upper()}] {self.question}")

        # If no structured options, fall back to free-text question
        if not self.options:
            answer = input("> ").strip()
            self.answer = answer
            return answer

        # Render options as numbered list
        for idx, opt in enumerate(self.options, 1):
            print(f"  {idx}) {opt.label}")
        if self.allow_other:
            print("  0) 其他 / 自定义（直接输入你的想法）")

        raw = input("> ").strip()
        if not raw:
            self.answer = ""
            return ""

        selected_labels: List[str] = []
        free_text: Optional[str] = None

        def _label_for_index(i: int) -> Optional[str]:
            if 1 <= i <= len(self.options):
                return self.options[i - 1].label
            return None

        # 多选：逗号或空格分隔的数字
        if self.allow_multiple and any(sep in raw for sep in [",", " ", "，"]):
            parts = [p.strip() for p in raw.replace("，", ",").split(",") if p.strip()]
            for p in parts:
                if p.isdigit():
                    idx = int(p)
                    if idx == 0 and self.allow_other:
                        continue
                    label = _label_for_index(idx)
                    if label:
                        selected_labels.append(label)
                else:
                    # 非纯数字视为额外自由输入
                    free_text = (free_text or "") + (" " if free_text else "") + p
        elif raw.isdigit():
            idx = int(raw)
            if idx == 0 and self.allow_other:
                # 用户将通过后续输入给出自定义答案
                print("请输入你的自定义答案：")
                free_text = input("> ").strip()
            else:
                label = _label_for_index(idx)
                if label:
                    selected_labels.append(label)
                else:
                    # 非法编号，退化为自由文本
                    free_text = raw
        else:
            # 直接文本回答
            free_text = raw

        combined_parts: List[str] = []
        if selected_labels:
            combined_parts.append(", ".join(selected_labels))
        if free_text:
            combined_parts.append(free_text)

        answer = " | ".join(combined_parts) if combined_parts else ""
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

        prompt = _prompt_loader.format(
            "interaction_extract",
            user_requirement=user_requirement,
        )

        try:
            result = self.llm_service.generate_json(prompt)
            if not isinstance(result, dict):
                return self._fallback_parse(user_requirement)
            validated = validate_response(result, ExtractedRequirements)

            features = []
            for i, f in enumerate(validated.features, 1):
                features.append(Feature(
                    id=f.get("id", f"f{i}"),
                    name=f["name"],
                    description=f["description"],
                    priority=f.get("priority", 3)
                ))

            dm = getattr(validated, "design_mode", None)
            if dm in (None, "", "null") or dm not in ("modern", "minimal", "dashboard"):
                dm = None

            requirements = Requirements(
                title=validated.title,
                description=validated.description or user_requirement,
                features=features,
                constraints=validated.constraints,
                target_users=validated.target_users,
                data_requirements=validated.data_requirements,
                design_mode=dm,
            )

            logger.info(f"Extracted {len(features)} features from requirement")
            return requirements

        except ValidationError as e:
            logger.warning(f"Requirements schema mismatch: {e.errors()}, using fallback")
            return self._fallback_parse(user_requirement)
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

        prompt = _prompt_loader.format("requirement_analysis", requirement=requirement)

        try:
            result = self.llm_service.generate_json(prompt)
            if not isinstance(result, dict):
                raise ValueError("Expected dict")
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

        prompt = _prompt_loader.format(
            "interaction_clarification_questions",
            requirement=requirement,
            gaps_section=gaps_section,
        )
        try:
            result = self.llm_service.generate_json(prompt)
            questions: List[ClarificationQuestion] = []
            if isinstance(result, list):
                items = result
            elif isinstance(result, dict):
                items = result.get("questions", [])
            else:
                items = []

            for i, q in enumerate(items, 1):
                if not isinstance(q, dict):
                    continue
                # Parse options (if provided)
                raw_options = q.get("options") or []
                options: List[ClarificationOption] = []
                if isinstance(raw_options, list):
                    for j, opt in enumerate(raw_options, 1):
                        if isinstance(opt, str):
                            options.append(
                                ClarificationOption(id=f"opt{j}", label=opt)
                            )
                        elif isinstance(opt, dict):
                            label = opt.get("label") or opt.get("text") or ""
                            if not label:
                                continue
                            options.append(
                                ClarificationOption(
                                    id=opt.get("id", f"opt{j}"),
                                    label=label,
                                )
                            )

                questions.append(
                    ClarificationQuestion(
                        id=q.get("id", f"q{i}"),
                        category=q.get("category", "functional"),
                        question=q.get("question", q.get("text", "")),
                        options=options,
                        allow_multiple=bool(q.get("allow_multiple", False)),
                        allow_other=bool(q.get("allow_other", True)),
                    )
                )

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

        prompt = _prompt_loader.format(
            "interaction_final_requirements",
            requirement=requirement,
            clarification_text=clarification_text or "(none)",
        )
        try:
            result = self.llm_service.generate_json(prompt)
            if not isinstance(result, dict):
                return self._fallback_from_clarifications(requirement, clarifications)
            features = []
            for i, f in enumerate(result.get("features", []), 1):
                if not isinstance(f, dict):
                    continue
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
                a_safe = a if a is not None else ""
                features.append(Feature(
                    id=f"f{i}",
                    name=a_safe.split(',')[0].strip() if ',' in a_safe else a_safe.strip()[:50],
                    description=a_safe,
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
        Generate an assistant reply given conversation history.
        Does NOT produce Requirements - only returns reply text for dialogue.
        Used for ChatGPT-style continuous chat (Web/API).
        """
        if not messages:
            return "请描述你想要的应用或功能，我会根据你的描述在后台生成产品。你可以随时补充需求，我会在已有基础上改进。"
        system = _prompt_loader.load("interaction_chat_system")
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

    def reply_in_chat_stream(self, messages: List[Dict[str, str]]) -> Iterator[str]:
        """
        Stream an assistant reply given conversation history.
        Does NOT produce Requirements - yields reply text chunks only.
        Used for SSE streaming in Web/API.
        """
        if not messages:
            yield "请描述你想要的应用或功能，我会根据你的描述在后台生成产品。你可以随时补充需求，我会在已有基础上改进。"
            return
        system = _prompt_loader.load("interaction_chat_system")
        # Build OpenAI-format messages (only user/assistant for context)
        openai_messages = [{"role": "system", "content": system}]
        for m in messages[-20:]:
            role = m.get("role", "user")
            if role not in ("user", "assistant"):
                continue
            openai_messages.append({"role": role, "content": m.get("content", "") or ""})
        try:
            for chunk in self.llm_service.stream_messages(openai_messages):
                yield chunk
        except Exception as e:
            logger.warning(f"reply_in_chat_stream failed: {e}")
            yield "已收到。我会根据当前对话在后台生成或更新应用，你可以在右侧查看代码和预览。"

    def _dict_to_requirements(
        self,
        result: dict,
        fallback: Optional[Requirements] = None,
    ) -> Requirements:
        """Shared parsing: dict from LLM -> Requirements. Used by conversation_to_requirements and merge_requirements."""
        features = []
        for i, f in enumerate(result.get("features", []), 1):
            if not isinstance(f, dict):
                continue
            features.append(Feature(
                id=f.get("id", f"f{i}"),
                name=f.get("name", f"Feature {i}"),
                description=f.get("description", ""),
                priority=f.get("priority", 3),
            ))
        dm = result.get("design_mode")
        if dm and dm not in ("modern", "minimal", "dashboard"):
            dm = fallback.design_mode if fallback else None
        return Requirements(
            title=result.get("title", fallback.title if fallback else "Generated Application"),
            description=result.get("description", fallback.description if fallback else ""),
            features=features,
            constraints=result.get("constraints", fallback.constraints if fallback else []),
            target_users=result.get("target_users") or (fallback.target_users if fallback else None),
            data_requirements=result.get("data_requirements") or (fallback.data_requirements if fallback else None),
            design_mode=dm or (fallback.design_mode if fallback else None),
        )

    def conversation_to_requirements(self, messages: List[Dict[str, str]]) -> Requirements:
        """
        Turn full conversation history into a single Requirements object (first-time generate).
        Core entry for Web flow when starting fresh.
        """
        conv = "\n".join(
            f"{m.get('role', 'user').upper()}: {m.get('content', '')}"
            for m in messages
        )
        prompt = _prompt_loader.format("interaction_conversation", conv=conv)
        try:
            result = self.llm_service.generate_json(prompt)
            if not isinstance(result, dict):
                raise ValueError("Expected dict")
            return self._dict_to_requirements(result)
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
        Merge new user request into existing Requirements (incremental generate).
        Uses same parsing logic as conversation_to_requirements via _dict_to_requirements.
        """
        existing_json = existing.model_dump(mode="json")
        existing_str = json.dumps(existing_json, indent=2, ensure_ascii=False)[:2500]
        extra = ""
        if recent_messages:
            extra = "\nRecent messages:\n" + "\n".join(
                f"{m.get('role')}: {m.get('content', '')}" for m in recent_messages[-5:]
            )
        prompt = _prompt_loader.format(
            "interaction_merge",
            existing_str=existing_str,
            new_message=new_message,
            extra=extra,
        )
        try:
            result = self.llm_service.generate_json(prompt)
            if not isinstance(result, dict):
                return existing
            return self._dict_to_requirements(result, fallback=existing)
        except Exception as e:
            logger.warning(f"merge_requirements failed: {e}")
            return existing
