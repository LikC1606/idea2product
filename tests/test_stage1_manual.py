"""Interactive test for Stage 1 - Requirements Gathering (manual input)."""

from config.settings import get_settings
from src.services.llm_service import LLMService
from src.agents.stage1_requirements.interaction_agent import InteractionAgent


def main():
    """Run interactive Stage 1 requirements gathering with manual input."""
    print("=" * 60)
    print("Idea2Product - Stage 1 Interactive Test")
    print("=" * 60)

    # Get initial requirement from user
    print("\n[Step 1] Enter your project requirement:")
    print("(e.g., Build a todo list app with add, delete, and complete functionality)")
    requirement = input("> ").strip()

    if not requirement:
        print("Using default requirement...")
        requirement = "Build a todo list app with add, delete, and complete functionality"

    print(f"\nRequirement: {requirement}")

    # Initialize
    settings = get_settings()
    llm_service = LLMService(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model=settings.openai_model,
        vlm_model=settings.openai_vlm_model,
        max_tokens=settings.max_tokens,
        temperature=settings.temperature,
    )
    agent = InteractionAgent(llm_service)

    # Generate questions
    print("\n[Step 2] Generating clarification questions...")
    questions = agent.generate_clarification_questions(requirement)
    print(f"\nGenerated {len(questions)} questions:\n")

    # Ask each question interactively
    clarifications = {}
    for i, q in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] [{q.category.upper()}] {q.question}")
        answer = input("> ").strip()
        if answer:
            clarifications[q.question] = answer
            q.answer = answer
        print()

    # Generate final requirements
    print("[Step 3] Generating final requirements...\n")
    final_req = agent._generate_final_requirements(requirement, questions, clarifications)

    # Show results
    print("=" * 60)
    print("FINAL REQUIREMENTS")
    print("=" * 60)
    print(f"Title: {final_req.title}")
    print(f"Description: {final_req.description}")
    print(f"\nFeatures ({len(final_req.features)}):")
    for f in final_req.features:
        print(f"  [{f.priority}] {f.name}")
        print(f"      {f.description}")
    if final_req.constraints:
        print(f"Constraints: {final_req.constraints}")
    if final_req.target_users:
        print(f"Target Users: {final_req.target_users}")
    if final_req.data_requirements:
        print(f"Data Requirements: {final_req.data_requirements}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
