#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup check script - ASCII only for Windows compatibility"""

import sys
from pathlib import Path

print("=" * 60)
print("Idea2Product Setup Check")
print("=" * 60)

# 1. Python version
print("\n[Python Version]")
print(f"  Python {sys.version.split()[0]}")
if sys.version_info >= (3, 9):
    print("  [OK] Python 3.9+")
else:
    print("  [FAIL] Need Python 3.9+")

# 2. Dependencies
print("\n[Dependencies]")
try:
    import pydantic
    print(f"  [OK] pydantic {pydantic.__version__}")
except ImportError:
    print("  [FAIL] pydantic not installed")
    print("         Run: pip install -r requirements.txt")

try:
    import openai
    print(f"  [OK] openai {openai.__version__}")
except ImportError:
    print("  [FAIL] openai not installed")
    print("         Run: pip install -r requirements.txt")

# 3. Project structure
print("\n[Project Structure]")
project_root = Path(__file__).parent
key_files = [
    "config/settings.py",
    "src/core/orchestrator.py",
    "src/services/llm_service.py",
]
for file_path in key_files:
    if (project_root / file_path).exists():
        print(f"  [OK] {file_path}")
    else:
        print(f"  [FAIL] {file_path} missing")

# 4. Environment config
print("\n[Environment Config]")
env_file = project_root / ".env"
if env_file.exists():
    print("  [OK] .env file exists")
    if "OPENAI_API_KEY=sk-" in env_file.read_text():
        print("  [WARNING] OPENAI_API_KEY needs configuration")
else:
    print("  [FAIL] .env file missing")
    print("         Run: cp .env.example .env")

# 5. Module loading
print("\n[Module Loading]")
try:
    from config.settings import Settings
    print("  [OK] Can import Settings")
except Exception as e:
    print(f"  [FAIL] Cannot import Settings: {e}")

try:
    from src.core.data_models import Requirements
    print("  [OK] Can import data models")
except Exception as e:
    print(f"  [FAIL] Cannot import data models: {e}")

print("\n" + "=" * 60)
print("Next Steps:")
print("=" * 60)
print("1. Install dependencies:")
print("   pip install -r requirements.txt")
print("")
print("2. Configure environment:")
print("   cp .env.example .env")
print("   # Edit .env and add your OPENAI_API_KEY")
print("")
print("3. Test CLI:")
print("   python -m src.cli list")
print("")
print("Note: Agents are not implemented yet, so 'create'")
print("      command will fail with NotImplementedError")
print("=" * 60)
