"""Minimal code stubs for CodeGenerationAgent fallback when agent.invoke fails.

When the LLM agent throws, we generate placeholder files to avoid complete failure.
Real fixes depend on Stage 4 CodeFixAgent.
"""

from pathlib import Path
from typing import List, Optional


def generate_fallback_stub(
    task,
    plan,
    project_path: Path,
    task_relevant_paths: List[str],
) -> bool:
    """Generate minimal stub files for a failed task. Returns True if any file was written."""
    written = False
    task_type = getattr(task.type, "value", str(task.type)) if hasattr(task, "type") else ""

    for rel_path in task_relevant_paths or []:
        if not rel_path or "__pycache__" in rel_path:
            continue
        dest = project_path / rel_path
        if dest.exists():
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)

        if rel_path.endswith(".py"):
            content = _stub_python(rel_path, task_type)
        elif rel_path.endswith(".html"):
            content = _stub_html(rel_path, task_type)
        else:
            continue

        if content:
            try:
                dest.write_text(content, encoding="utf-8")
                written = True
            except OSError:
                pass
    return written


def _stub_python(rel_path: str, task_type: str) -> Optional[str]:
    """Generate minimal Python stub."""
    p = rel_path.replace("\\", "/")
    if "models/" in p:
        name = Path(p).stem
        class_name = "".join(w.capitalize() for w in name.split("_")) or "Model"
        return f'''"""Model stub - fallback placeholder."""
from app import db


class {class_name}(db.Model):
    __tablename__ = "{name}"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
'''
    if "routes/" in p:
        bp_name = Path(p).stem
        return f'''"""Routes stub - fallback placeholder."""
from flask import Blueprint

{bp_name}_bp = Blueprint("{bp_name}", __name__)


@{bp_name}_bp.route("/")
def index():
    return {{"message": "stub"}}, 200
'''
    if "config" in p:
        return '''"""Config stub - fallback placeholder."""
def get_config():
    return {"DEBUG": True}
'''
    return None


def _stub_html(rel_path: str, task_type: str) -> Optional[str]:
    """Generate minimal HTML stub."""
    return '''<!DOCTYPE html>
<html>
<head><title>Stub</title><link rel="stylesheet" href="/static/css/base.css"></head>
<body><p>Placeholder - implementation pending.</p></body>
</html>'''
