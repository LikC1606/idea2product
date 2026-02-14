"""Test Stage 1 - InteractionAgent (Requirements Gathering)."""

from config.settings import get_settings
from src.services.llm_service import LLMService
from src.agents.stage1_requirements.interaction_agent import InteractionAgent
from src.core.context import ExecutionContext


def test_interaction_agent_with_llm():
    """Test InteractionAgent with LLM (requires OPENAI_API_KEY)."""
    settings = get_settings()
    llm_service = LLMService(settings)
    agent = InteractionAgent(llm_service)

    context = ExecutionContext(
        project_id="test_001",
        user_requirement="Build a todo list app with add, delete, and complete functionality"
    )

    requirements = agent.execute(context)

    print(f"\n=== Stage 1 Results ===")
    print(f"Title: {requirements.title}")
    print(f"Description: {requirements.description}")
    print(f"Features ({len(requirements.features)}):")
    for f in requirements.features:
        print(f"  - {f.name}: {f.description}")
    print(f"Constraints: {requirements.constraints}")
    print(f"Target Users: {requirements.target_users}")
    print(f"Data Requirements: {requirements.data_requirements}")

    # Basic assertions
    assert requirements.title is not None
    assert len(requirements.features) > 0


def test_interaction_agent_fallback():
    """Test InteractionAgent fallback parsing (no LLM required)."""
    # Create a mock LLM service that raises exception
    class MockLLMService:
        def generate_json(self, prompt):
            raise Exception("LLM not available")

    agent = InteractionAgent(MockLLMService())

    context = ExecutionContext(
        project_id="test_002",
        user_requirement="Build a todo list app with add, delete, and complete functionality"
    )

    requirements = agent.execute(context)

    print(f"\n=== Fallback Results ===")
    print(f"Title: {requirements.title}")
    print(f"Description: {requirements.description}")
    print(f"Features ({len(requirements.features)}):")
    for f in requirements.features:
        print(f"  - {f.name}: {f.description}")

    # Fallback should still extract features
    assert requirements.title is not None


if __name__ == "__main__":
    # Run fallback test first (no API key needed)
    print("Running fallback test...")
    test_interaction_agent_fallback()

    # Run LLM test (requires OPENAI_API_KEY)
    print("\nRunning LLM test...")
    test_interaction_agent_with_llm()
