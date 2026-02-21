"""Stage 3 Code Generation Agents."""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Set
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

        # Phase 2: Analyze and fix dependencies
        files = self._resolve_dependencies(files, requirements, plan)

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

    def _resolve_dependencies(self, files: List[CodeFile], requirements: Requirements, plan: EngineeringPlan) -> List[CodeFile]:
        """Analyze dependencies and generate missing files or fix imports."""
        logger.info("Resolving dependencies between files...")

        # Build a map of existing files
        file_map = {f.path: f for f in files}

        # Check if app/__init__.py is needed
        has_app_routes = any('app/routes' in f.path for f in files)
        has_app_main = any(f.path.endswith('/main.py') for f in files)
        if (has_app_routes or has_app_main) and 'app/__init__.py' not in file_map:
            # Generate app/__init__.py
            init_stub = self._generate_init_stub('app/__init__.py')
            files.append(init_stub)
            file_map['app/__init__.py'] = init_stub
            logger.info("Generated missing stub: app/__init__.py")

        # Find all imports and references in each file
        missing_refs = self._find_missing_references(files)

        logger.info(f"Found {len(missing_refs)} missing references")

        # Generate missing files
        for ref_path, ref_type in missing_refs:
            if ref_path in file_map:
                continue  # Already exists

            # Try to generate a stub for the missing file
            stub = self._generate_missing_stub(ref_path, ref_type, requirements, plan)
            if stub:
                files.append(stub)
                file_map[ref_path] = stub
                logger.info(f"Generated missing stub: {ref_path}")

        # Fix import mismatches within existing files
        files = self._fix_import_mismatches(files)

        return files

    # Python standard library modules to skip
    STDLIB_MODULES = {
        'datetime', 'os', 'sys', 'json', 're', 'time', 'datetime', 'collections',
        'urllib', 'http', 'email', 'html', 'xml', 'csv', 'io', 'logging',
        'configparser', 'pathlib', 'typing', 'copy', 'pickle', 'shelve',
        'sqlite3', 'threading', 'multiprocessing', 'asyncio', 'concurrent',
        'functools', 'itertools', 'operator', 'abc', 'dataclasses', 'enum',
        'warnings', 'abc', 'ast', 'gc', 'inspect', 'traceback', 'types',
        'unittest', 'doctest', 'pdb', 'profile', 'timeit', 'random', 'math',
        'statistics', 'decimal', 'fractions', 'numbers', 'cmath', 'array',
        'heapq', 'bisect', 'graphlib', 'uuid', 'hashlib', 'hmac', 'secrets',
        'ssl', 'socket', 'select', 'signal', 'mmap', 'pty', 'tty', 'termios',
        'textwrap', 'string', 'struct', 'codecs', 'unicodedata', 'locale',
        'gettext', 'argparse', 'optparse', 'getopt', 'logging', 'getpass',
        'getuser', 'curses', 'platform', 'errno', 'ctypes', 'weakref',
        'types', 'copy', 'pprint', 'textwrap', 'unittest', 'doctest'
    }

    def _find_missing_references(self, files: List[CodeFile]) -> List[tuple]:
        """Find references to files that don't exist in the file list."""
        missing = []
        existing_paths = {f.path for f in files}

        # Also add variations (e.g., app/models vs app/models.py)
        path_variations = set()
        for p in existing_paths:
            path_variations.add(p)
            # Add without extension
            if p.endswith('.py'):
                path_variations.add(p[:-3])
            # Add with .py extension
            path_variations.add(p + '.py')

        for file in files:
            if file.language != 'python':
                continue

            content = file.content

            # Find from X import Y patterns
            from_imports = re.findall(r'from\s+([\w.]+)\s+import', content)
            for imp in from_imports:
                # Convert module path to file path
                if imp.startswith('app.'):
                    file_path = imp.replace('.', '/') + '.py'
                elif imp.startswith('config.'):
                    file_path = imp.replace('.', '/') + '.py'
                elif imp == 'config':
                    file_path = 'config/__init__.py'
                else:
                    file_path = imp + '.py'

                if file_path not in path_variations and file_path not in existing_paths:
                    missing.append((file_path, 'module'))

            # Find import X patterns (local imports)
            local_imports = re.findall(r'^import\s+([\w.]+)', content, re.MULTILINE)
            for imp in local_imports:
                if imp.startswith('app.'):
                    file_path = imp.replace('.', '/') + '.py'
                    if file_path not in path_variations and file_path not in existing_paths:
                        missing.append((file_path, 'module'))

        return missing

    def _generate_missing_stub(self, ref_path: str, ref_type: str, requirements: Requirements, plan: EngineeringPlan) -> CodeFile:
        """Generate a stub file for a missing reference."""
        logger.info(f"Generating stub for missing: {ref_path}")

        # Extract module name from path
        module_name = ref_path.replace('/', '.').replace('\\', '.').replace('.py', '').split('.')[-1]

        # Skip standard library modules - they don't need stubs
        if module_name.lower() in self.STDLIB_MODULES:
            logger.info(f"Skipping stdlib module: {ref_path}")
            return None

        # Also skip third-party packages that are typically available
        skip_modules = {'flask', 'sqlalchemy', 'werkzeug', 'requests', 'openai', 'pydantic', 'jinja'}
        if module_name.lower() in skip_modules:
            logger.info(f"Skipping third-party module: {ref_path}")
            return None

        # Determine what kind of stub to generate based on path
        if 'config' in ref_path.lower():
            return self._generate_config_stub(ref_path, requirements)
        elif 'models' in ref_path.lower():
            return self._generate_model_stub(ref_path, requirements)
        elif 'controllers' in ref_path.lower():
            return self._generate_controller_stub(ref_path, requirements)
        elif 'services' in ref_path.lower():
            return self._generate_service_stub(ref_path, requirements)
        elif ref_path.endswith('__init__.py'):
            return self._generate_init_stub(ref_path)
        else:
            # Generic stub - but only for app-related modules
            if 'app.' in ref_path or ref_path.startswith('app/'):
                return CodeFile(
                    path=ref_path,
                    content=f'# Auto-generated stub for {ref_path}\n',
                    language='python',
                    purpose=f'Stub for {ref_path}',
                    dependencies=[]
                )
            else:
                # Skip non-app modules
                return None

    def _generate_config_stub(self, ref_path: str, requirements: Requirements) -> CodeFile:
        """Generate a config stub."""
        content = f'''"""Configuration for {requirements.title}."""

import os
from pathlib import Path

# Database path
BASE_DIR = Path(__file__).parent.parent
DATABASE_PATH = str(BASE_DIR / "app.db")

class Config:
    """Application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{DATABASE_PATH}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
'''
        return CodeFile(
            path=ref_path,
            content=content,
            language='python',
            purpose='Application configuration',
            dependencies=[]
        )

    def _generate_model_stub(self, ref_path: str, requirements: Requirements) -> CodeFile:
        """Generate a models stub."""
        content = f'''"""Database models for {requirements.title}."""

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ProductContent(Base):
    __tablename__ = 'product_content'

    id = Column(Integer, primary_key=True)
    image_url = Column(String(500))
    needs_description = Column(Text)
    product_title = Column(String(255))
    selling_points = Column(Text)  # JSON string

    def __repr__(self):
        return f"<ProductContent {self.product_title}>"

# Export Base for other modules
__all__ = ['Base', 'ProductContent']
'''
        return CodeFile(
            path=ref_path,
            content=content,
            purpose='Database models',
            language='python',
            dependencies=[]
        )

    def _generate_controller_stub(self, ref_path: str, requirements: Requirements) -> CodeFile:
        """Generate a controller stub."""
        content = f'''"""Controllers for {requirements.title}."""

from flask import Blueprint, request, jsonify

controllers = Blueprint('controllers', __name__)

@controllers.route('/api/process', methods=['POST'])
def process_request():
    """Process user request."""
    data = request.get_json()
    return jsonify({{
        'status': 'success',
        'message': 'Request processed'
    }})

def generate_product_content(image_path=None, description=None):
    """Generate product content based on description."""
    # Placeholder implementation
    return {{
        'title': 'Generated Title',
        'selling_points': ['Point 1', 'Point 2', 'Point 3']
    }}

__all__ = ['controllers', 'generate_product_content']
'''
        return CodeFile(
            path=ref_path,
            content=content,
            purpose='Business logic controllers',
            language='python',
            dependencies=[]
        )

    def _generate_service_stub(self, ref_path: str, requirements: Requirements) -> CodeFile:
        """Generate a service stub."""
        content = f'''"""Services for {requirements.title}."""

class ContentGenerator:
    """Service for generating content."""

    def __init__(self):
        pass

    def generate(self, image=None, description=None):
        """Generate content based on input."""
        return {
            'title': 'Sample Product Title',
            'selling_points': [
                'High quality',
                'Durable material',
                'Affordable price'
            ]
        }

    def validate_image(self, image_path):
        """Validate uploaded image."""
        return True

__all__ = ['ContentGenerator']
'''
        return CodeFile(
            path=ref_path,
            content=content,
            purpose='Service layer',
            language='python',
            dependencies=[]
        )

    def _generate_init_stub(self, ref_path: str) -> CodeFile:
        """Generate __init__.py stub."""
        # Special handling for app/__init__.py - export the Flask app
        if ref_path == 'app/__init__.py' or ref_path == 'app/__init__.py':
            content = '''"""App package."""

from flask import Flask

app = Flask(__name__)

# Import routes to register them
from app import routes
app.register_blueprint(routes.routes)

__all__ = ['app']
'''
        else:
            pkg_name = ref_path.replace('/__init__.py', '').replace('__init__.py', '')
            content = f'''"""Package: {pkg_name}"""

__all__ = []
'''
        return CodeFile(
            path=ref_path,
            content=content,
            purpose='Package init',
            language='python',
            dependencies=[]
        )

    def _fix_import_mismatches(self, files: List[CodeFile]) -> List[CodeFile]:
        """Fix function/class name mismatches in imports."""
        # Build a map of what functions/classes exist in each file
        exports = {}
        for f in files:
            if f.language != 'python':
                continue
            exports[f.path] = self._extract_exports(f.content)

        # Fix imports in each file
        fixed_files = []
        for f in files:
            if f.language != 'python':
                fixed_files.append(f)
                continue

            content = f.content
            original = content

            # Check if routes needs init_routes
            if 'routes.py' in f.path and 'init_routes' in content:
                # Add init_routes function if missing
                if 'def init_routes' not in content:
                    # Insert init_routes before the Blueprint definition
                    lines = content.split('\n')
                    new_lines = []
                    for i, line in enumerate(lines):
                        new_lines.append(line)
                        if "routes = Blueprint" in line:
                            new_lines.insert(i, '''def init_routes(app):
    """Initialize all routes on the app."""
    app.register_blueprint(routes)

''')
                    content = '\n'.join(new_lines)

            # Fix controllers import if it references non-existent function
            if 'controllers' in f.path:
                # Make sure generate_product_content exists
                # Function is called but not defined here - that's OK if imported

                # Make sure we have a valid function that can be imported
                if 'from app.controllers import generate_product_content' in content:
                    # Check if controllers.py has this function
                    controllers_file = None
                    for cf in files:
                        if 'controllers.py' in cf.path:
                            controllers_file = cf
                            break

                    if controllers_file and 'def generate_product_content' not in controllers_file.content:
                        # Add the function to controllers
                        controllers_content = controllers_file.content
                        if 'def generate_product_content' not in controllers_content:
                            # Add at the end
                            controllers_content += '''

def generate_product_content(image_path=None, description=None):
    """Generate product content."""
    return {
        'title': 'Generated Product',
        'selling_points': ['Point 1', 'Point 2', 'Point 3']
    }
'''
                        # Update the controllers file
                        idx = next(i for i, cf in enumerate(files) if cf.path == controllers_file.path)
                        files[idx] = CodeFile(
                            path=controllers_file.path,
                            content=controllers_content,
                            language=controllers_file.language,
                            purpose=controllers_file.purpose,
                            dependencies=controllers_file.dependencies
                        )

            fixed_files.append(f)

        return fixed_files

    def _extract_exports(self, content: str) -> Set[str]:
        """Extract function and class definitions from Python code."""
        exports = set()

        # Find def and class definitions
        funcs = re.findall(r'^def\s+(\w+)', content, re.MULTILINE)
        classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)

        exports.update(funcs)
        exports.update(classes)

        return exports

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
                # Clean up markdown code block markers
                result = self._clean_code(result)
                return result
            else:
                return self._template_file(file_spec.path, requirements)
        except Exception as e:
            logger.warning(f"LLM code generation failed for {file_spec.path}: {e}")
            return self._template_file(file_spec.path, requirements)

    def _clean_code(self, code: str) -> str:
        """Clean up markdown code block markers from generated code."""
        # Remove markdown code block markers (``` or ```python etc.)
        lines = code.split('\n')
        cleaned_lines = []
        for line in lines:
            # Skip lines that are only ``` or ```python etc.
            stripped = line.strip()
            if stripped.startswith('```'):
                continue
            cleaned_lines.append(line)

        # Also check for any remaining ``` at end of file
        result = '\n'.join(cleaned_lines)
        # Remove any trailing ```
        if result.rstrip().endswith('`'):
            # Check if it ends with ```
            result = result.rstrip()
            if result.endswith('```'):
                result = result[:-3].rstrip()
            elif result.endswith('``'):
                result = result[:-2].rstrip()
            elif result.endswith('`'):
                result = result[:-1].rstrip()

        return result

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
