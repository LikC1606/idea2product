"""Test API with direct .env reading."""

import os
from pathlib import Path

# Read .env directly
env_file = Path(__file__).parent.parent / ".env"
env_vars = {}
with open(env_file) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, val = line.split("=", 1)
            env_vars[key] = val

API_KEY = env_vars.get("OPENAI_API_KEY", "")
BASE_URL = env_vars.get("OPENAI_BASE_URL", "")
MODEL = env_vars.get("OPENAI_MODEL", "gpt-4o")

print(f"Key: {API_KEY[:15]}...")
print(f"Base URL: {BASE_URL}")
print(f"Model: {MODEL}")

# Test API
from openai import OpenAI

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

try:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "Say 'Hello' in 3 words"}],
        max_tokens=50
    )
    print(f"\nOK: {response.choices[0].message.content}")
except Exception as e:
    print(f"\nERROR: {e}")
