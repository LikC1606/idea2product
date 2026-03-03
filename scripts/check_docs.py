#!/usr/bin/env python3
"""Lightweight doc consistency check.

Validates that agents listed in docs/refs/AGENTS_REF.md exist in src/agents/.
Run from project root: python scripts/check_docs.py
"""

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AGENTS_REF = PROJECT_ROOT / "docs" / "refs" / "AGENTS_REF.md"
AGENTS_DIR = PROJECT_ROOT / "src" / "agents"


def extract_agents_from_ref(path: Path) -> set[str]:
    """Extract Agent class names from AGENTS_REF.md table rows."""
    text = path.read_text(encoding="utf-8")
    # Match table rows like "| InteractionAgent | ..." or "| CodeGenerationAgent | ..."
    pattern = r"^\|\s+(\w+Agent)\s+\|"
    found = set()
    for m in re.finditer(pattern, text, re.MULTILINE):
        found.add(m.group(1))
    return found


def find_agent_classes_in_code(dir_path: Path) -> set[str]:
    """Find class XAgent definitions in Python files under dir_path."""
    found = set()
    for py in dir_path.rglob("*.py"):
        content = py.read_text(encoding="utf-8")
        for m in re.finditer(r"class\s+(\w+Agent)\s*[:\(]", content):
            found.add(m.group(1))
    return found


def main() -> int:
    if not AGENTS_REF.exists():
        print(f"AGENTS_REF not found: {AGENTS_REF}", file=sys.stderr)
        return 1
    if not AGENTS_DIR.exists():
        print(f"Agents dir not found: {AGENTS_DIR}", file=sys.stderr)
        return 1

    ref_agents = extract_agents_from_ref(AGENTS_REF)
    code_agents = find_agent_classes_in_code(AGENTS_DIR)

    missing = ref_agents - code_agents
    if missing:
        print(f"AGENTS_REF lists agents not found in code: {sorted(missing)}", file=sys.stderr)
        return 1

    print("check_docs: AGENTS_REF matches src/agents (ok)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
