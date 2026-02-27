#!/usr/bin/env python3
"""Test generate using Flask test client - bypasses network."""
import sys
sys.path.insert(0, ".")
from src.web.app import app

# Create project via test client
with app.test_client() as c:
    r = c.post("/api/projects", json={"start_chat": True})
    print("Create status:", r.status_code, "Content-Type:", r.content_type)
    d = r.get_json()
    pid = d["project_id"]
    print("Project:", pid)

    # POST generate
    r2 = c.post(f"/api/projects/{pid}/generate", json={})
    print("Generate status:", r2.status_code, "Content-Type:", r2.content_type)
    print("Generate body:", r2.data[:300] if r2.data else "empty")
