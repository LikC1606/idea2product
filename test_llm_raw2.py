"""测试 LLM raw output"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import get_settings
from src.core.data_models import Requirements, Feature

settings = get_settings()
from src.services.llm_service import LLMService
llm = LLMService(settings.openai_api_key, base_url=settings.openai_base_url)

requirements = Requirements(
    title="A simple note-taking app",
    description="One page where I can enter text and save it",
    features=[
        Feature(id="F1", name="Create note", description="Enter text in a text area"),
        Feature(id="F2", name="Save note", description="Save the entered text")
    ]
)

prompt = """
Based on the following requirements, divide them into 3-5 COARSE-GRAINED tasks.

Requirements:
Title: A simple note-taking app
Description: One page where I can enter text and save it
Features: Create note, Save note

IMPORTANT: For EACH task, provide the SAME API specification. All tasks should know about the full API.

Example output format:
[
    {
        "id": "T1",
        "name": "Frontend UI",
        "description": "Create HTML page with form to submit to backend. Display notes fetched from API.",
        "type": "frontend",
        "api_specs": {
            "endpoints": [
                {"path": "/notes", "method": "POST", "request": "{content: str}", "response": "{id, content, created_at}"},
                {"path": "/notes", "method": "GET", "response": "[{id, content, created_at}]"}
            ]
        },
        "dependencies": [],
        "priority": 5,
        "complexity": "low"
    },
    {
        "id": "T2",
        "name": "Backend API",
        "description": "Implement API endpoints that match the frontend needs.",
        "type": "backend",
        "api_specs": {
            "endpoints": [
                {"path": "/notes", "method": "POST", "request": "{content: str}", "response": "{id, content, created_at}"},
                {"path": "/notes", "method": "GET", "response": "[{id, content, created_at}]"}
            ]
        },
        "dependencies": ["T3"],
        "priority": 4,
        "complexity": "medium"
    },
    {
        "id": "T3",
        "name": "Database Models",
        "description": "Define Note model matching the API response structure.",
        "type": "database",
        "api_specs": {
            "endpoints": [
                {"path": "/notes", "method": "POST", "request": "{content: str}", "response": "{id, content, created_at}"},
                {"path": "/notes", "method": "GET", "response": "[{id, content, created_at}]"}
            ]
        },
        "dependencies": [],
        "priority": 4,
        "complexity": "low"
    }
]

Task types:
- frontend: UI, templates, static files - MUST include api_specs
- backend: routes, controllers - MUST include api_specs
- database: models, schema - MUST include api_specs
- testing: test files (optional)
- deployment: deployment config (optional)

IMPORTANT:
- ALL tasks should have the SAME api_specs/endpoints definition
- This ensures frontend and backend use consistent API

Respond with valid JSON array only.
"""

result = llm.generate_json(prompt)
import json
print(json.dumps(result, indent=2))
