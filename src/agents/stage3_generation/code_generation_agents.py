"""Stage 3 Code Generation Agents."""

import json
from pathlib import Path
from typing import Dict, List, Any
from src.core.data_models import (
    Requirements, EngineeringPlan, CodeRepository, CodeFile,
    DirectoryStructure, FileSpec
)
from src.core.context import ExecutionContext
from src.services.llm_service import LLMService
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CodeGenerationAgent:
    """Stage 3 Agent: Generates code based on engineering plan."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def execute(self, context: ExecutionContext) -> CodeRepository:
        """Generate code files from the engineering plan."""
        requirements = context.requirements
        plan = context.engineering_plan
        project_path = context.project_path / "generated"

        logger.info(f"Generating code for {len(plan.file_structure)} files")

        files = []

        # Generate each file
        for file_spec in plan.file_structure:
            code = self._generate_file(file_spec, requirements, plan)
            files.append(CodeFile(
                path=file_spec.path,
                content=code,
                language=self._get_language(file_spec.path),
                purpose=file_spec.purpose,
                dependencies=file_spec.dependencies
            ))

        # Create directory structure
        directories = list(set(
            str(Path(f.path).parent) for f in files
            if Path(f.path).parent != Path(".")
        ))

        structure = DirectoryStructure(
            root="generated",
            directories=directories,
            entry_point=self._find_entry_point(files)
        )

        # Extract dependencies
        dependencies = self._extract_dependencies(plan, files)

        logger.info(f"Generated {len(files)} files")
        return CodeRepository(
            files=files,
            structure=structure,
            dependencies=dependencies,
            readme_content=self._generate_readme(requirements)
        )

    def _generate_file(self, file_spec: FileSpec, requirements: Requirements, plan: EngineeringPlan) -> str:
        """Generate code for a single file."""
        ext = Path(file_spec.path).suffix

        prompt = f"""
Generate code for the following file:
Path: {file_spec.path}
Purpose: {file_spec.purpose}

Application: {requirements.title}
Description: {requirements.description}
Features: {", ".join(f.name for f in requirements.features)}

Dependencies: {", ".join(file_spec.dependencies)}

Return the code content only, no explanations.
"""

        try:
            # For Python files, use LLM
            if ext in ['.py', '.html', '.css', '.js']:
                result = self.llm_service.generate(prompt, max_tokens=2000)
                return result
            else:
                return self._template_file(file_spec.path, requirements)
        except Exception as e:
            logger.warning(f"LLM code generation failed for {file_spec.path}: {e}")
            return self._template_file(file_spec.path, requirements)

    def _template_file(self, path: str, requirements: Requirements) -> str:
        """Get template code for a file."""
        ext = Path(path).suffix
        name = Path(path).stem

        templates = {
            '.py': f'''"""Generated module: {name}"""

from flask import Flask, jsonify, request

app = Flask(__name__)

# {requirements.title}
# {requirements.description}

@app.route('/')
def index():
    return jsonify({{
        'app': '{requirements.title}',
        'features': {json.dumps([f.name for f in requirements.features])}
    }})

if __name__ == '__main__':
    app.run(debug=True)
''',
            '.html': f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{requirements.title}</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="container">
        <h1>{requirements.title}</h1>
        <p>{requirements.description}</p>
        <ul class="features">
            {"".join(f"<li>{f.name}</li>" for f in requirements.features[:5])}
        </ul>
    </div>
    <script src="/static/script.js"></script>
</body>
</html>
''',
            '.css': f'''/* {requirements.title} Styles */

body {{
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background: #f5f5f5;
}}

.container {{
    max-width: 800px;
    margin: 0 auto;
    background: white;
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}}

h1 {{
    color: #333;
}}

.features {{
    list-style: none;
    padding: 0;
}}

.features li {{
    padding: 10px;
    margin: 5px 0;
    background: #f9f9f9;
    border-left: 3px solid #007bff;
}}
''',
            '.js': f'''// {requirements.title} - Client Script

// Features: {", ".join(f.name for f in requirements.features)}

document.addEventListener('DOMContentLoaded', () => {{
    console.log('App loaded');

    // Initialize features
    const features = {json.dumps([f.name for f in requirements.features])};
    console.log('Available features:', features);
}});
''',
            '.json': json.dumps({
                "name": requirements.title.lower().replace(" ", "-"),
                "version": "1.0.0",
                "description": requirements.description
            }, indent=2),
            '.txt': f'''{requirements.title}
{"=" * len(requirements.title)}

{requirements.description}

Features:
{chr(10).join(f"- {f.name}: {f.description}" for f in requirements.features)}
'''
        }

        return templates.get(ext, f"# Generated file: {path}")

    def _get_language(self, path: str) -> str:
        """Determine language from file extension."""
        ext = Path(path).suffix.lower()
        lang_map = {
            '.py': 'python',
            '.html': 'html',
            '.css': 'css',
            '.js': 'javascript',
            '.json': 'json',
            '.txt': 'text',
            '.md': 'markdown'
        }
        return lang_map.get(ext, 'text')

    def _find_entry_point(self, files: List[CodeFile]) -> str:
        """Find the main entry point file."""
        for f in files:
            if f.path == 'app.py':
                return f.path
            if f.path.endswith('app.py'):
                return f.path
        return files[0].path if files else "app.py"

    def _extract_dependencies(self, plan: EngineeringPlan, files: List[CodeFile]) -> List[str]:
        """Extract Python dependencies from the plan."""
        deps = set(['flask'])

        for alg in plan.algorithms.values():
            for lib in alg.libraries:
                if lib not in ['dict', 'list', 'str', 'int']:
                    deps.add(lib)

        return sorted(deps)

    def _generate_readme(self, requirements: Requirements) -> str:
        """Generate README content."""
        return f"""# {requirements.title}

{requirements.description}

## Features

{chr(10).join(f"- {f.name}: {f.description}" for f in requirements.features)}

## Setup

```bash
pip install -r requirements.txt
python app.py
```

## Usage

Open http://localhost:5000 in your browser.
"""


class CodeMemoryAgent:
    """Stage 3 Agent: Stores code in memory for future reuse."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def execute(self, context: ExecutionContext, repository: CodeRepository) -> None:
        """Store generated code in code memory."""
        logger.info("Code Memory Agent: Storing code for future reuse")
        # For MVP, this is a no-op - code memory can be implemented later
        pass


class CodeMiningAgent:
    """Stage 3 Agent: Retrieves relevant external code."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def execute(self, context: ExecutionContext) -> Dict[str, Any]:
        """Mine relevant code from external sources."""
        logger.info("Code Mining Agent: Mining external code")
        # For MVP, this is a no-op - code mining can be implemented later
        return {}
