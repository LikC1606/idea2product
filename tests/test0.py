"""Test API connectivity."""

from src.services.llm_service import LLMService
from config.settings import get_settings


def main():
    print("Testing API connectivity...")
    print("=" * 50)

    settings = get_settings()
    print(f"API Key: {settings.openai_api_key[:10]}...")
    print(f"Base URL: {settings.openai_base_url}")
    print(f"Model: {settings.openai_model}")

    llm = LLMService(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        vlm_model=settings.openai_vlm_model,
        max_tokens=settings.max_tokens,
        temperature=settings.temperature,
        base_url=settings.openai_base_url,
    )

    print("\nSending test request...")
    try:
        response = llm.generate("Say 'Hello, API is working!' in 10 words or less.")
        print(f"\n[OK] Response: {response}")
    except Exception as e:
        print(f"\n[ERROR] {e}")


if __name__ == "__main__":
    main()
