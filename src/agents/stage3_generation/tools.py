"""Tools system using LangChain."""
from contextvars import ContextVar
from typing import Any, Dict, List, Optional
from pathlib import Path
import sys

from langchain_core.tools import tool

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Context vars for per-invocation state (supports parallel/multi-project)
_ctx_project_path: ContextVar[Optional[Path]] = ContextVar("project_path", default=None)
_ctx_code_memory_service: ContextVar[Optional[Any]] = ContextVar(
    "code_memory_service", default=None
)
_ctx_project_id: ContextVar[Optional[str]] = ContextVar("project_id", default=None)
_ctx_cross_project_memory: ContextVar[bool] = ContextVar(
    "cross_project_memory", default=False
)


def set_code_memory_service(service):
    """Set code memory service for snippet search (when ENABLE_CODE_MEMORY)."""
    _ctx_code_memory_service.set(service)


def set_project_path(path: Path):
    """设置项目路径。"""
    _ctx_project_path.set(path)


def set_project_id(project_id: Optional[str]):
    """设置当前 project_id，供 get_module_signatures / search_snippets 使用。"""
    _ctx_project_id.set(project_id)


def set_cross_project_memory(enabled: bool):
    """设置是否允许跨项目 snippet 检索。"""
    _ctx_cross_project_memory.set(enabled)


@tool
def list_files() -> str:
    """列出项目中的所有文件。"""
    project_path = _ctx_project_path.get()
    if not project_path:
        return "Error: project_path not set"

    files = []
    # 只列出文本文件
    text_extensions = [".py", ".html", ".txt", ".md", ".json", ".env", ".yml", ".yaml"]
    for f in project_path.rglob("*"):
        if f.is_file() and f.suffix in text_extensions:
            rel_path = f.relative_to(project_path)
            files.append(str(rel_path))

    return "\n".join(files)[:2000]


@tool
def read_file(file_path: str) -> str:
    """读取项目中的文件内容。

    Args:
        file_path: 文件路径（如 app/models/note.py）
    """
    project_path = _ctx_project_path.get()
    if not project_path:
        return "Error: project_path not set"

    full_path = project_path / file_path
    if not full_path.exists():
        return f"Error: File not found: {file_path}"

    try:
        # 只读取文本文件
        if full_path.suffix in [".py", ".html", ".txt", ".md", ".json", ".env"]:
            content = full_path.read_text(encoding="utf-8")
            return content[:5000]
        else:
            return f"Skipped: {file_path} is not a text file"
    except UnicodeDecodeError:
        return f"Error: Binary file, cannot read: {file_path}"
    except Exception as e:
        return f"Error reading file: {e}"


@tool
def write_file(file_path: str, content: str) -> str:
    """创建或覆盖文件。

    Args:
        file_path: 文件路径（如 app/models/note.py）
        content: 文件内容
    """
    project_path = _ctx_project_path.get()
    if not project_path:
        return "Error: project_path not set"

    full_path = project_path / file_path
    full_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        full_path.write_text(content, encoding="utf-8")
        return f"Success: File written: {file_path}"
    except Exception as e:
        return f"Error writing file: {e}"


@tool
def modify_file(file_path: str, old_content: str, new_content: str) -> str:
    """修改文件的部分内容，替换 old_content 为 new_content。

    Args:
        file_path: 文件路径
        old_content: 要替换的旧内容
        new_content: 新的内容
    """
    project_path = _ctx_project_path.get()
    if not project_path:
        return "Error: project_path not set"

    full_path = project_path / file_path
    if not full_path.exists():
        return f"Error: File not found: {file_path}"

    try:
        content = full_path.read_text(encoding="utf-8")
        if old_content not in content:
            return f"Error: Content to replace not found in file"

        new_file_content = content.replace(old_content, new_content)
        full_path.write_text(new_file_content, encoding="utf-8")
        return f"Success: File modified: {file_path}"
    except Exception as e:
        return f"Error modifying file: {e}"


@tool
def validate_syntax(file_path: str) -> str:
    """Validate Python syntax of a file. Call this after creating or modifying .py files.

    Args:
        file_path: Path to the Python file (e.g. app/models/note.py)
    """
    project_path = _ctx_project_path.get()
    if not project_path:
        return "Error: project_path not set"

    full_path = project_path / file_path
    if not full_path.exists():
        return f"Error: File not found: {file_path}"

    if full_path.suffix != ".py":
        return f"Skipped: {file_path} is not a Python file"

    try:
        import ast as _ast

        source = full_path.read_text(encoding="utf-8")
        _ast.parse(source)
        return "OK"
    except SyntaxError as e:
        return f"Error: Line {e.lineno}: {e.msg}"
    except Exception as e:
        return f"Error: {e}"


@tool
def run_app() -> str:
    """运行应用并检查是否有错误。"""
    project_path = _ctx_project_path.get()
    if not project_path:
        return "Error: project_path not set"

    sys.path.insert(0, str(project_path))

    try:
        from app import create_app

        app = create_app()
        return "Success: App imported and created successfully"
    except Exception as e:
        return f"Error: {str(e)[:500]}"
    finally:
        if project_path and str(project_path) in sys.path:
            sys.path.remove(str(project_path))


@tool
def search_similar_snippet(query: str) -> str:
    """Search code memory for similar implementations. Use when implementing CRUD, auth, or common patterns.

    Args:
        query: Search terms, e.g. 'flask crud api', 'sqlalchemy model', 'blueprint route'
    """
    code_memory_service = _ctx_code_memory_service.get()
    project_id = _ctx_project_id.get()
    cross_project_memory = _ctx_cross_project_memory.get()
    if not code_memory_service:
        return "Code memory is disabled. Implement from scratch."
    try:
        snippets = code_memory_service.search_snippets(
            query, limit=3, project_id=project_id, cross_project=cross_project_memory
        )
        if not snippets:
            return "No similar snippets found in memory."
        out = []
        for s in snippets:
            out.append(f"=== {s.function_name} ===\n{s.code[:800]}\n")
        return "\n".join(out)[:3000]
    except Exception as e:
        return f"Search failed: {e}"


@tool
def get_module_signatures(module_name: str) -> str:
    """Get interface signatures (functions, classes) for a module from the symbol table.
    Use this to discover available functions/classes in other modules before calling them.

    Args:
        module_name: Module name, e.g. 'app.models.user' or 'app.routes.auth'
    """
    code_memory_service = _ctx_code_memory_service.get()
    project_path = _ctx_project_path.get()
    project_id = _ctx_project_id.get()
    if code_memory_service:
        try:
            symbols = code_memory_service.get_symbols_by_module(
                module_name, project_id=project_id or "current"
            )
            if symbols:
                lines = [f"# Signatures for {module_name}"]
                for s in symbols:
                    sig = s.signature or s.symbol_name
                    lines.append(f"  {s.symbol_type}: {sig}")
                return "\n".join(lines)
        except Exception as e:
            logger.debug(f"Symbol table lookup failed: {e}")

    if not project_path:
        return f"No signatures available for {module_name}"

    mod_path = module_name.replace(".", "/") + ".py"
    full_path = project_path / mod_path
    if not full_path.exists():
        return f"Module {module_name} not found"

    try:
        import ast as _ast

        source = full_path.read_text(encoding="utf-8")
        tree = _ast.parse(source)
        sigs = []
        for node in _ast.iter_child_nodes(tree):
            if isinstance(node, _ast.FunctionDef):
                args = ", ".join(a.arg for a in node.args.args)
                ret = ""
                if node.returns:
                    ret = f" -> {_ast.unparse(node.returns)}"
                sigs.append(f"def {node.name}({args}){ret}")
            elif isinstance(node, _ast.ClassDef):
                bases = (
                    ", ".join(_ast.unparse(b) for b in node.bases) if node.bases else ""
                )
                sigs.append(f"class {node.name}({bases})")
                for item in node.body:
                    if isinstance(item, _ast.FunctionDef):
                        args = ", ".join(a.arg for a in item.args.args)
                        sigs.append(f"  def {item.name}({args})")
        return (
            "\n".join(sigs)[:3000]
            if sigs
            else f"No public signatures found in {module_name}"
        )
    except Exception as e:
        return f"Could not parse {module_name}: {e}"


def get_tools(
    project_path: Path,
    code_memory_service=None,
    project_id: Optional[str] = None,
    cross_project_memory: bool = False,
) -> List:
    """获取所有工具实例。"""
    _ctx_project_path.set(project_path)
    _ctx_code_memory_service.set(code_memory_service)
    _ctx_project_id.set(project_id)
    _ctx_cross_project_memory.set(cross_project_memory)

    tools = [
        list_files,
        read_file,
        write_file,
        modify_file,
        validate_syntax,
        run_app,
        get_module_signatures,
    ]
    if code_memory_service:
        tools.append(search_similar_snippet)
    return tools
