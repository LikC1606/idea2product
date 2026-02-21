"""测试 LLM 原始输出"""
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

IMPORTANT: For each task, provide DETAILED implementation specifications including:
1. Specific function/method signatures (e.g., "def add_note(content: str) -> Note")
2. API endpoints with HTTP methods (e.g., "POST /notes - create new note")
3. Data structures/classes to implement (e.g., "class Note: id, content, created_at")

Example output format:
[
    {
        "id": "T1",
        "name": "Frontend UI",
        "description": "Create HTML page with form. Form submits to /notes via POST. Display saved notes below form.",
        "type": "frontend",
        "implementation_specs": {
            "api_endpoints": [],
            "functions": [],
            "classes": []
        },
        "dependencies": [],
        "priority": 5,
        "complexity": "low"
    },
    {
        "id": "T2",
        "name": "Backend API",
        "description": "Implement API: POST /notes - receives {content: str}, returns {id, content, created_at}. GET /notes - returns list of all notes.",
        "type": "backend",
        "implementation_specs": {
            "api_endpoints": [
                {"path": "/notes", "method": "POST", "request": "{content: str}", "response": "{id, content, created_at}"},
                {"path": "/notes", "method": "GET", "response": "[{id, content, created_at}]"}
            ],
            "functions": ["def save_note(content: str) -> Note", "def get_notes() -> List[Note]"],
            "classes": []
        },
        "dependencies": ["T3"],
        "priority": 4,
        "complexity": "medium"
    }
]

Task types:
- frontend: UI, templates, static files
- backend: routes, controllers, API endpoints
- database: models, schema, migrations
- testing: test files (optional)
- deployment: deployment config (optional)

Respond with valid JSON array only.
"""

result = llm.generate_json(prompt)
import json
print(json.dumps(result, indent=2))
