"""Interactive test for Stage 1 - Requirements Gathering with dialogue (automated)."""

import sys
from io import StringIO
from config.settings import get_settings
from src.services.llm_service import LLMService
from src.agents.stage1_requirements.interaction_agent import InteractionAgent


def test_interactive_with_mock_input():
    """Test interactive mode with mocked user input."""
    print("=" * 60)
    print("Testing Stage 1 Interactive Mode")
    print("=" * 60)

    requirement = "Build a todo list app with add, delete, and complete functionality"

    # Initialize
    settings = get_settings()
    llm_service = LLMService(settings)
    agent = InteractionAgent(llm_service)

    # Generate questions first
    print("\n[1] Generating clarification questions...")
    questions = agent.generate_clarification_questions(requirement)
    print(f"Generated {len(questions)} questions:")
    for q in questions:
        print(f"  [{q.category}] {q.question}")

    # Simulate user answers
    print("\n[2] Simulating user answers...")
    mock_answers = {
        questions[0].question: "Add, delete, and mark items as complete",
        questions[1].question: "Store in localStorage for now",
        questions[2].question: "Anyone who needs to organize tasks",
    }

    clarifications = {}
    for q in questions:
        if q.question in mock_answers:
            answer = mock_answers[q.question]
            q.answer = answer
            clarifications[q.question] = answer
            print(f"  Q: {q.question}")
            print(f"  A: {answer}")

    # Generate final requirements
    print("\n[3] Generating final requirements...")
    final_req = agent._generate_final_requirements(requirement, questions, clarifications)

    # Show results
    print("\n" + "=" * 60)
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
    print("Test completed successfully!")
    print("=" * 60)

    # Assertions
    assert final_req.title is not None
    assert len(final_req.features) > 0
    print("\n[OK] All assertions passed!")


if __name__ == "__main__":
    test_interactive_with_mock_input()
