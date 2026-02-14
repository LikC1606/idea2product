"""Test API connectivity - run with: python -c "import sys; sys.path.insert(0, '.'); exec(open('tests/test_api.py').read())" """

from src.services.llm_service import LLMService
from config.settings import get_settings

settings = get_settings()
print(f"Base URL: {settings.openai_base_url}")
print(f"Model: {settings.openai_model}")

llm = LLMService(
    api_key=settings.openai_api_key,
    model=settings.openai_model,
    base_url=settings.openai_base_url,
)

try:
    response = llm.generate("Say 'Hello' in 5 words")
    print(f"OK: {response}")
except Exception as e:
    print(f"ERROR: {e}")
