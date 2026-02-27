#!/usr/bin/env python3
"""List all Flask routes - run from project root."""
import sys
sys.path.insert(0, ".")
from src.web.app import app

print("Registered routes:")
for rule in sorted(app.url_map.iter_rules(), key=lambda r: str(r)):
    if "api" in str(rule):
        print(f"  {rule.rule} -> {rule.endpoint} [{', '.join(rule.methods - {'HEAD', 'OPTIONS'})}]")
