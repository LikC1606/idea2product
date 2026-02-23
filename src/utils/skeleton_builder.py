"""Build CodeSkeleton from pyi_stubs (Interface-First strategy)."""

import re
from pathlib import Path
from typing import Dict, List, Any

from src.core.data_models import (
    CodeSkeleton,
    InterfaceDefinition,
    DependencyGraph,
    SymbolTableEntry,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


def build_skeleton_from_pyi_stubs(
    pyi_stubs: Dict[str, str],
    file_structure: List[Any],
    entry_point: str = "app.py",
) -> CodeSkeleton:
    """
    Build a minimal CodeSkeleton from Stage 2 pyi_stubs and file_structure.

    Parses .pyi stub content to extract function/class signatures and builds
    a dependency graph from file_structure.
    """
    interfaces: List[InterfaceDefinition] = []
    symbol_table: List[SymbolTableEntry] = []
    nodes: List[str] = []
    edges: List[Dict[str, str]] = []

    for file_path, stub_content in (pyi_stubs or {}).items():
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
