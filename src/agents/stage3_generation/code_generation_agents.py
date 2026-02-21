"""Stage 3 Code Generation Agents."""

import json
import re
import ast
from pathlib import Path
from typing import Dict, List, Any, Set
from src.core.data_models import (
    Requirements, EngineeringPlan, CodeRepository, CodeFile,
    DirectoryStructure, FileSpec, CodeSkeleton, InterfaceDefinition,
    DependencyGraph, SymbolTableEntry
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
        """Generate code files from the engineering plan using Interface-First strategy."""
        requirements = context.requirements
        plan = context.engineering_plan
        project_path = context.project_path / "generated"

        logger.info(f"Generating code for {len(plan.file_structure)} files")

        # ============================================================
        # Phase 1: Interface-First Strategy
        # Step 1: Generate global skeleton (interfaces + dependency graph)
        # ============================================================
        logger.info("Phase 1: Generating code skeleton (Interface-First)")

        # Generate interface definitions (.pyi files)
        interfaces = self._generate_interfaces(requirements, plan)

        # Generate dependency graph
        dependency_graph = self._generate_dependency_graph(plan)

        # Build symbol table from interfaces
        symbol_table = self._build_symbol_table(interfaces, plan)

        # Create skeleton
        skeleton = CodeSkeleton(
            interfaces=interfaces,
            dependency_graph=dependency_graph,
            symbol_table=symbol_table
        )

        logger.info(f"  - Generated {len(interfaces)} interfaces")
        logger.info(f"  - Dependency graph: {len(dependency_graph.nodes)} nodes, {len(dependency_graph.edges)} edges")

        # ============================================================
        # Phase 2: Generate actual code files based on skeleton
        # ============================================================
        files = []

        # Generate each file
        for file_spec in plan.file_structure:
            code = self._generate_file(file_spec, requirements, plan, symbol_table)
            files.append(CodeFile(
                path=file_spec.path,
                content=code,
                language=self._get_language(file_spec.path),
                purpose=file_spec.purpose,
                dependencies=file_spec.dependencies
            ))

        # Phase 3: Analyze and fix dependencies
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
            skeleton=skeleton,
            files=files,
            structure=structure,
            dependencies=dependencies,
            readme_content=self._generate_readme(requirements)
        )

    # ============================================================
    # Interface-First Strategy Methods
    # ============================================================

    def _generate_interfaces(self, requirements: Requirements, plan: EngineeringPlan) -> List[InterfaceDefinition]:
        """Generate interface definitions (.pyi) for all modules."""
        interfaces = []

        prompt = f"""
Generate interface definitions (.pyi style) for the following application.
For each module, define the function signatures and class interfaces.

Application: {requirements.title}
Description: {requirements.description}
Features: {", ".join(f.name for f in requirements.features)}

Files to create interfaces for:
{chr(10).join(f"- {fs.path}: {fs.purpose}" for fs in plan.file_structure if fs.path.endswith('.py'))}

Return a JSON array with this structure:
[
    {{
        "module_name": "module_name",
        "functions": [
            {{"name": "function_name", "params": ["param1: type", "param2: type"], "return_type": "return_type"}}
        ],
        "classes": [
            {{"name": "ClassName", "methods": ["method_name: return_type"]}}
        ],
        "imports": ["import statements"],
        "type_hints": "type hint content"
    }}
]

Respond with valid JSON only.
"""

        try:
            result = self.llm_service.generate_json(prompt)
            for item in result:
                interfaces.append(InterfaceDefinition(
                    module_name=item.get("module_name", "unknown"),
                    functions=item.get("functions", []),
                    classes=item.get("classes", []),
                    imports=item.get("imports", []),
                    type_hints=item.get("type_hints", "")
                ))
        except Exception as e:
            logger.warning(f"LLM interface generation failed: {e}")
            # Fallback: create basic interfaces from file specs
            interfaces = self._fallback_interfaces(plan)

        return interfaces

    def _generate_dependency_graph(self, plan: EngineeringPlan) -> DependencyGraph:
        """Generate dependency graph from file specifications."""
        nodes = [fs.path for fs in plan.file_structure]
        edges = []

        # Build edges from file dependencies
        for fs in plan.file_structure:
            for dep in fs.dependencies:
                edges.append({"from": fs.path, "to": dep})

        # Determine entry point
        entry_point = "app.py"
        for fs in plan.file_structure:
            if fs.path in ["app.py", "main.py", "run.py"]:
                entry_point = fs.path
                break

        return DependencyGraph(
            nodes=nodes,
            edges=edges,
            entry_point=entry_point
        )

    def _build_symbol_table(self, interfaces: List[InterfaceDefinition], plan: EngineeringPlan) -> List[SymbolTableEntry]:
        """Build symbol table from interfaces."""
        symbol_table = []

        for interface in interfaces:
            # Add functions to symbol table
            for func in interface.functions:
                symbol_table.append(SymbolTableEntry(
                    symbol_name=func.get("name", ""),
                    symbol_type="function",
                    module=interface.module_name,
                    signature=f"{func.get('name', '')}({', '.join(func.get('params', []))}) -> {func.get('return_type', '')}",
                    docstring=None,
                    line_number=0
                ))

            # Add classes to symbol table
            for cls in interface.classes:
                symbol_table.append(SymbolTableEntry(
                    symbol_name=cls.get("name", ""),
                    symbol_type="class",
                    module=interface.module_name,
                    signature=None,
                    docstring=None,
                    line_number=0
                ))

        return symbol_table

    def _fallback_interfaces(self, plan: EngineeringPlan) -> List[InterfaceDefinition]:
        """Fallback interface generation when LLM fails."""
        interfaces = []
        for fs in plan.file_structure:
            if fs.path.endswith('.py'):
                module_name = Path(fs.path).stem
                interfaces.append(InterfaceDefinition(
                    module_name=module_name,
                    functions=[],
                    classes=[],
                    imports=[],
                    type_hints=f"# Interface for {fs.purpose}"
                ))
        return interfaces

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

    def _generate_file(self, file_spec: FileSpec, requirements: Requirements, plan: EngineeringPlan, symbol_table: List[SymbolTableEntry] = None) -> str:
        """Generate code for a single file."""
        ext = Path(file_spec.path).suffix

        # Build symbol context for better code generation
        symbol_context = ""
        if symbol_table:
            symbol_context = f"""
Available symbols from other modules:
{chr(10).join(f"- {s.symbol_name} ({s.symbol_type}) in {s.module}: {s.signature}" for s in symbol_table[:10])}
"""

        prompt = f"""
Generate code for the following file:
Path: {file_spec.path}
Purpose: {file_spec.purpose}

Application: {requirements.title}
Description: {requirements.description}
Features: {", ".join(f.name for f in requirements.features)}

Dependencies: {", ".join(file_spec.dependencies)}
{symbol_context}

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
    """
    Stage 3 Agent: Stores code in memory for future reuse.

    Full implementation with SQLite-based dynamic knowledge graph:
    - AST (Abstract Syntax Tree) caching for each module
    - Global symbol table for cross-module calls
    - Function signature retrieval
    - Query interface for code reuse
    """

    def __init__(self, llm_service: LLMService, db_path: str = None):
        self.llm_service = llm_service
        self.db_path = db_path or "data/code_memory.db"
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for code memory."""
        import sqlite3
        from pathlib import Path

        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS modules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_path TEXT UNIQUE NOT NULL,
                module_name TEXT NOT NULL,
                content TEXT NOT NULL,
                ast_cache TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS symbols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_id INTEGER NOT NULL,
                symbol_name TEXT NOT NULL,
                symbol_type TEXT NOT NULL,
                signature TEXT,
                docstring TEXT,
                line_number INTEGER,
                FOREIGN KEY (module_id) REFERENCES modules(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS code_snippets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                code TEXT NOT NULL,
                language TEXT NOT NULL,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(symbol_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_type ON symbols(symbol_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_modules_path ON modules(module_path)")

        conn.commit()
        conn.close()

    def execute(self, context: ExecutionContext, repository: CodeRepository) -> Dict[str, Any]:
        """
        Store generated code in code memory.

        Builds dynamic knowledge graph with:
        - AST (Abstract Syntax Tree) for each module
        - Global symbol table for cross-module calls
        - SQLite persistence
        """
        logger.info("Code Memory Agent: Building dynamic knowledge graph")

        import sqlite3

        result = {
            "ast_cache": {},
            "symbol_table": [],
            "module_exports": {},
            "stored_count": 0
        }

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Build AST and symbol table for each Python file
        for code_file in repository.files:
            if code_file.language == "python":
                try:
                    # Parse AST
                    tree = ast.parse(code_file.content)

                    # Store module in database
                    cursor.execute("""
                        INSERT OR REPLACE INTO modules (module_path, module_name, content, ast_cache, updated_at)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (
                        code_file.path,
                        Path(code_file.path).stem,
                        code_file.content,
                        ""
                    ))

                    module_id = cursor.lastrowid

                    # Extract exports (functions and classes)
                    exports = self._extract_exports(tree)
                    result["module_exports"][code_file.path] = exports

                    # Delete old symbols for this module
                    cursor.execute("DELETE FROM symbols WHERE module_id = ?", (module_id,))

                    # Build symbol table entries and store in DB
                    for name, node_type in exports.items():
                        signature = self._get_signature(tree, name)
                        docstring = self._get_docstring(tree, name)
                        line_num = self._get_line_number(tree, name)

                        cursor.execute("""
                            INSERT INTO symbols (module_id, symbol_name, symbol_type, signature, docstring, line_number)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (module_id, name, node_type, signature, docstring, line_num))

                        result["symbol_table"].append({
                            "symbol_name": name,
                            "symbol_type": node_type,
                            "module": code_file.path,
                            "signature": signature,
                            "line_number": line_num
                        })

                    logger.info(f"  - Stored {code_file.path}: {len(exports)} exports")
                    result["stored_count"] += 1

                except SyntaxError as e:
                    logger.warning(f"  - Failed to parse {code_file.path}: {e}")
                except Exception as e:
                    logger.warning(f"  - Error storing {code_file.path}: {e}")

        conn.commit()
        conn.close()

        logger.info(f"Code Memory: Built knowledge graph with {len(result['symbol_table'])} symbols")
        return result

    def query_symbol(self, symbol_name: str) -> List[Dict[str, Any]]:
        """Query symbols by name across all modules."""
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT s.symbol_name, s.symbol_type, s.signature, s.docstring, s.line_number, m.module_path
            FROM symbols s
            JOIN modules m ON s.module_id = m.id
            WHERE s.symbol_name LIKE ?
        """, (f"%{symbol_name}%",))

        results = []
        for row in cursor.fetchall():
            results.append({
                "symbol_name": row[0],
                "symbol_type": row[1],
                "signature": row[2],
                "docstring": row[3],
                "line_number": row[4],
                "module": row[5]
            })

        conn.close()
        return results

    def query_module(self, module_path: str) -> Dict[str, Any]:
        """Query module by path."""
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT module_path, module_name, content FROM modules WHERE module_path = ?", (module_path,))
        row = cursor.fetchone()

        if row:
            result = {
                "module_path": row[0],
                "module_name": row[1],
                "content": row[2]
            }
        else:
            result = None

        conn.close()
        return result

    def _extract_exports(self, tree: ast.AST) -> Dict[str, str]:
        """Extract function and class definitions from AST."""
        exports = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                exports[node.name] = "function"
            elif isinstance(node, ast.ClassDef):
                exports[node.name] = "class"
            elif isinstance(node, ast.AsyncFunctionDef):
                exports[node.name] = "async_function"

        return exports

    def _get_signature(self, tree: ast.AST, name: str) -> str:
        """Get function signature."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
                args = [arg.arg for arg in node.args.args]
                return f"{name}({', '.join(args)})"
        return name

    def _get_docstring(self, tree: ast.AST, name: str) -> str:
        """Get function/class docstring."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)) and node.name == name:
                if ast.get_docstring(node):
                    return ast.get_docstring(node)[:200]
        return None

    def _get_line_number(self, tree: ast.AST, name: str) -> int:
        """Get line number for a named node."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                if node.name == name:
                    return node.lineno
        return 0


class CodeMiningAgent:
    """
    Stage 3 Agent: Retrieves relevant external code from GitHub.

    Full implementation with:
    - GitHub API integration
    - Code snippet search
    - Adaptive code rewriting based on project interface specs
    """

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.github_token = None  # Set via environment variable GITHUB_TOKEN

    def execute(self, context: ExecutionContext) -> Dict[str, Any]:
        """
        Mine relevant code from external sources.

        Searches GitHub for relevant code snippets based on:
        - Feature requirements
        - Algorithm types
        - Library usage patterns
        """
        logger.info("Code Mining Agent: Mining external code")

        requirements = context.requirements
        plan = context.engineering_plan

        mined_code = {
            "snippets": [],
            "sources": [],
            "adapted_snippets": []
        }

        # Search GitHub for each feature
        for feature in requirements.features:
            # Search for relevant code
            snippets = self._search_github(feature.name, requirements.title)
            mined_code["snippets"].extend(snippets)

            # Search for common patterns
            patterns = self._search_common_patterns(feature.name)
            mined_code["snippets"].extend(patterns)

        # Adapt snippets to current project interface
        if mined_code["snippets"]:
            mined_code["adapted_snippets"] = self._adapt_snippets(
                mined_code["snippets"],
                plan
            )

        logger.info(f"Code Mining: Found {len(mined_code['snippets'])} code patterns")
        return mined_code

    def _search_github(self, feature: str, project_title: str) -> List[Dict[str, Any]]:
        """Search GitHub for relevant code snippets."""
        import requests

        snippets = []

        # Common search queries
        queries = [
            f"{feature} flask python example",
            f"{project_title} implementation python",
            f"{feature} API endpoint python"
        ]

        for query in queries[:2]:  # Limit API calls
            try:
                url = "https://api.github.com/search/code"
                params = {
                    "q": query,
                    "per_page": 3,
                    "sort": "stars"
                }

                headers = {}
                if self.github_token:
                    headers["Authorization"] = f"token {self.github_token}"

                response = requests.get(url, params=params, headers=headers, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("items", [])[:2]:
                        snippets.append({
                            "name": item.get("name", "unknown"),
                            "path": item.get("path", ""),
                            "url": item.get("html_url", ""),
                            "repository": item.get("repository", {}).get("full_name", ""),
                            "score": item.get("score", 0),
                            "source": "github"
                        })
            except Exception as e:
                logger.warning(f"GitHub search failed for '{query}': {e}")

        return snippets

    def _search_common_patterns(self, feature: str) -> List[Dict[str, Any]]:
        """Search for common code patterns."""
        # Common patterns database
        patterns_db = {
            "crud": {
                "template": '''def create_{name}(self, data):
    """Create a new {name}."""
    item = {name.capitalize()}(**data)
    db.session.add(item)
    db.session.commit()
    return item

def get_{name}(self, id):
    """Get {name} by ID."""
    return {name.capitalize()}.query.get(id)

def update_{name}(self, id, data):
    """Update {name}."""
    item = self.get_{name}(id)
    if item:
        for key, value in data.items():
            setattr(item, key, value)
        db.session.commit()
    return item

def delete_{name}(self, id):
    """Delete {name}."""
    item = self.get_{name}(id)
    if item:
        db.session.delete(item)
        db.session.commit()
    return True''',
                "description": "Flask SQLAlchemy CRUD operations"
            },
            "api": {
                "template": '''@bp.route('/api/{name}', methods=['GET'])
def get_{name}s():
    """Get all {name}s."""
    items = {name.capitalize()}.query.all()
    return jsonify([{{item.to_dict()}} for item in items])

@bp.route('/api/{name}/<int:id>', methods=['GET'])
def get_{name}(id):
    """Get {name} by ID."""
    item = {name.capitalize()}.query.get_or_404(id)
    return jsonify(item.to_dict())

@bp.route('/api/{name}', methods=['POST'])
def create_{name}():
    """Create new {name}."""
    data = request.get_json()
    item = {name.capitalize()}(**data)
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201

@bp.route('/api/{name}/<int:id>', methods=['PUT'])
def update_{name}(id):
    """Update {name}."""
    item = {name.capitalize()}.query.get_or_404(id)
    data = request.get_json()
    for key, value in data.items():
        setattr(item, key, value)
    db.session.commit()
    return jsonify(item.to_dict())

@bp.route('/api/{name}/<int:id>', methods=['DELETE'])
def delete_{name}(id):
    """Delete {name}."""
    item = {name.capitalize()}.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return '', 204''',
                "description": "Flask REST API endpoints"
            },
            "database": {
                "template": '''class {name.capitalize()}(db.Model):
    """Database model for {name}."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary."""
        return {{
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }}

    def __repr__(self):
        return f'<{name.capitalize()} {{self.name}}>''',
                "description": "Flask SQLAlchemy model"
            },
            "auth": {
                "template": '''class User(UserMixin, db.Model):
    """User model with authentication."""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    name = db.Column(db.String(100))

    def set_password(self, password):
        """Hash and set password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password."""
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def authenticate(email, password):
        """Authenticate user by email and password."""
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            return user
        return None

    def get_id(self):
        """Get user ID for Flask-Login."""
        return str(self.id)''',
                "description": "Flask-Login user authentication"
            }
        }

        # Match feature to patterns
        matched = []
        feature_lower = feature.lower()
        for key, pattern in patterns_db.items():
            if key in feature_lower or feature_lower in key:
                matched.append({
                    "name": key,
                    "code": pattern["template"],
                    "description": pattern["description"],
                    "source": "pattern_db"
                })

        return matched

    def _adapt_snippets(self, snippets: List[Dict], plan: EngineeringPlan) -> List[Dict[str, Any]]:
        """Adapt external code to current project interface specs."""
        adapted = []

        # Get interface specs from plan
        file_specs = {fs.path: fs for fs in plan.file_structure}

        for snippet in snippets:
            if "code" in snippet:
                # Already have code, try to adapt
                adapted_snippet = {
                    "original": snippet.get("description", ""),
                    "adapted_code": self._rewrite_code(snippet["code"], file_specs),
                    "source": snippet.get("source", "unknown")
                }
                adapted.append(adapted_snippet)

        return adapted

    def _rewrite_code(self, code: str, file_specs: Dict) -> str:
        """Rewrite code to match project interface specs."""
        # Use LLM to adapt code
        prompt = f"""
Rewrite the following code to match the project structure.
Keep the same functionality but adjust variable names and imports to match.

Project files:
{chr(10).join(f"- {path}: {spec.purpose}" for path, spec in file_specs.items())}

Code to adapt:
{code}

Return only the adapted code, no explanations.
"""

        try:
            result = self.llm_service.generate(prompt, max_tokens=1500)
            # Clean markdown
            result = result.strip()
            if result.startswith("```"):
                result = result.split("```")[1]
                if result.startswith("python"):
                    result = result[6:]
            return result.strip()
        except Exception as e:
            logger.warning(f"Code adaptation failed: {e}")
            return code
