"""Build CodeSkeleton from pyi_stubs (Interface-First strategy)."""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional

from src.core.data_models import (
    CodeSkeleton,
    InterfaceDefinition,
    DependencyGraph,
    SymbolTableEntry,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


def generate_minimal_pyi_from_interface_specs(
    interface_specs: List[Any],
    file_structure: List[Any],
) -> Dict[str, str]:
    """
    Generate minimal .pyi stub content when SchemePlanningAgent returns empty pyi_stubs.

    Uses interface_specs (exports) and file_structure to build placeholder stubs
    so CodeGenerationAgent has non-empty Interface-First constraints.
    """
    stubs: Dict[str, str] = {}
    seen_paths: set = set()

    # Build from interface_specs (has exports with type, name, params, returns)
    for spec in interface_specs or []:
        file_path = getattr(spec, "file_path", None) or (spec if isinstance(spec, str) else "")
        if not file_path or not file_path.endswith(".py"):
            continue
        file_path = file_path.replace("\\", "/")
        if file_path in seen_paths:
            continue
        seen_paths.add(file_path)

        lines = ['"""Minimal stub generated from interface_specs."""', ""]
        exports = getattr(spec, "exports", []) or []

        for exp in exports:
            exp_type = getattr(exp, "type", "function")
            name = getattr(exp, "name", "")
            if not name:
                continue
            if exp_type == "class":
                extends = getattr(exp, "extends", None) or ""
                base = f"({extends})" if extends else ""
                lines.append(f"class {name}{base}:")
                lines.append("    ...")
                lines.append("")
            else:
                params = getattr(exp, "params", []) or []
                returns = getattr(exp, "returns", "Any") or "Any"
                params_str = ", ".join(params) if params else ""
                lines.append(f"def {name}({params_str}) -> {returns}:")
                lines.append("    ...")
                lines.append("")

        if len(lines) > 2:  # More than just docstring
            stubs[file_path] = "\n".join(lines)

    # Fallback: from file_structure when interface_specs yielded nothing
    for spec in file_structure or []:
        path = getattr(spec, "path", None) or (spec if isinstance(spec, str) else "")
        if not path or not path.endswith(".py"):
            continue
        path = path.replace("\\", "/")
        if path in seen_paths:
            continue

        layer = getattr(spec, "layer", None) or ""
        purpose = getattr(spec, "purpose", "") or ""

        if "app/__init__" in path or path == "app/__init__.py":
            stubs[path] = '''"""App factory."""
from flask import Flask

def create_app() -> Flask:
    ...
'''
        elif "app/models" in path or "/models/" in path:
            mod_name = Path(path).stem
            class_name = "".join(w.capitalize() for w in mod_name.split("_")) or "Model"
            stubs[path] = f'''"""Model module."""
from flask_sqlalchemy import SQLAlchemy

class {class_name}:
    ...
'''
        elif "routes" in path or "route" in path:
            stubs[path] = '''"""Routes blueprint."""
from flask import Blueprint

def get_bp() -> Blueprint:
    ...
'''
        else:
            stubs[path] = f'"""{purpose or "Module"}."""\n\n...\n'

        seen_paths.add(path)

    return stubs


def build_skeleton_from_pyi_stubs(
    pyi_stubs: Dict[str, str],
    file_structure: List[Any],
    entry_point: str = "app.py",
    interface_specs: Optional[List[Any]] = None,
) -> CodeSkeleton:
    """
    Build a minimal CodeSkeleton from Stage 2 pyi_stubs and file_structure.

    Parses .pyi stub content to extract function/class signatures and builds
    a dependency graph from file_structure.

    When pyi_stubs is empty, generates minimal stubs from interface_specs
    and file_structure (fallback for when SchemePlanningAgent returns no pyi_stubs).
    """
    interfaces: List[InterfaceDefinition] = []
    symbol_table: List[SymbolTableEntry] = []
    nodes: List[str] = []
    edges: List[Dict[str, str]] = []

    # Fallback: generate minimal pyi_stubs when empty
    effective_pyi = dict(pyi_stubs or {})
    if not effective_pyi and (interface_specs or file_structure):
        effective_pyi = generate_minimal_pyi_from_interface_specs(
            interface_specs or [],
            file_structure or [],
        )
        if effective_pyi:
            logger.info(
                "pyi_stubs was empty; generated %d minimal stubs from interface_specs/file_structure",
                len(effective_pyi),
            )

    for file_path, stub_content in effective_pyi.items():
        if not file_path.endswith(".py") and not file_path.endswith(".pyi"):
            continue
        if not stub_content or not isinstance(stub_content, str):
            continue

        module_name = file_path.replace("/", ".").replace("\\", ".").replace(".py", "").replace(".pyi", "")
        nodes.append(file_path)

        functions = _parse_functions_from_stub(stub_content)
        classes = _parse_classes_from_stub(stub_content)
        imports = _parse_imports_from_stub(stub_content)

        for fn in functions:
            symbol_table.append(
                SymbolTableEntry(
                    symbol_name=fn.get("name", ""),
                    symbol_type="function",
                    module=module_name,
                    signature=fn.get("signature"),
                    docstring=None,
                    line_number=0,
                )
            )
        for cls in classes:
            symbol_table.append(
                SymbolTableEntry(
                    symbol_name=cls.get("name", ""),
                    symbol_type="class",
                    module=module_name,
                    signature=None,
                    docstring=None,
                    line_number=0,
                )
            )

        interfaces.append(
            InterfaceDefinition(
                module_name=module_name,
                functions=functions,
                classes=classes,
                imports=imports,
                type_hints=stub_content[:2000],
            )
        )

    # Build dependency edges from file_structure
    for spec in file_structure or []:
        path = getattr(spec, "path", None) or (spec if isinstance(spec, str) else "")
        if not path:
            continue
        deps = getattr(spec, "dependencies", []) or []
        for dep in deps:
            if dep and dep not in nodes:
                nodes.append(dep)
            if path and dep:
                edges.append({"from": path, "to": dep})

    if not nodes:
        nodes = ["app.py"]
    if not any(e.get("from") == entry_point or e.get("to") == entry_point for e in edges):
        # Ensure entry_point is in graph
        if entry_point not in nodes:
            nodes.insert(0, entry_point)

    dep_graph = DependencyGraph(
        nodes=nodes,
        edges=edges,
        entry_point=entry_point,
    )

    return CodeSkeleton(
        interfaces=interfaces,
        dependency_graph=dep_graph,
        symbol_table=symbol_table,
    )


def _parse_functions_from_stub(content: str) -> List[Dict[str, Any]]:
    """Extract function signatures from .pyi-style content."""
    functions = []
    # Match: def name(...) -> ...:  or def name(...):
    pattern = re.compile(r"def\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*([^:]+))?\s*:", re.MULTILINE)
    for m in pattern.finditer(content):
        name = m.group(1)
        params_str = m.group(2)
        returns = m.group(3).strip() if m.group(3) else "Any"
        params = [p.strip().split(":")[0].strip() for p in params_str.split(",") if p.strip()]
        functions.append({
            "name": name,
            "params": params,
            "return_type": returns,
            "signature": m.group(0),
        })
    return functions


def _parse_classes_from_stub(content: str) -> List[Dict[str, Any]]:
    """Extract class definitions from .pyi-style content."""
    classes = []
    # Match: class Name(...): or class Name:
    pattern = re.compile(r"class\s+(\w+)\s*(?:\(([^)]*)\))?\s*:", re.MULTILINE)
    for m in pattern.finditer(content):
        name = m.group(1)
        bases = m.group(2).strip() if m.group(2) else ""
        classes.append({
            "name": name,
            "bases": [b.strip() for b in bases.split(",") if b.strip()],
            "methods": [],
        })
    return classes


def _parse_imports_from_stub(content: str) -> List[str]:
    """Extract import statements from content."""
    imports = []
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("import ") or line.startswith("from "):
            imports.append(line)
    return imports[:20]  # Limit to avoid huge context
