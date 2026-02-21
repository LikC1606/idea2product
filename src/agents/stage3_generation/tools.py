"""Tools system using LangChain."""
from typing import Any, Dict, List
from pathlib import Path
import sys

from langchain_core.tools import tool

from src.utils.logger import get_logger

logger = get_logger(__name__)


# 全局项目路径（由 get_tools 设置）
_project_path = None


def set_project_path(path: Path):
    """设置项目路径。"""
    global _project_path
    _project_path = path


@tool
def list_files() -> str:
    """列出项目中的所有文件。"""
    if not _project_path:
        return "Error: project_path not set"

    files = []
    # 只列出文本文件
    text_extensions = ['.py', '.html', '.txt', '.md', '.json', '.env', '.yml', '.yaml']
    for f in _project_path.rglob("*"):
        if f.is_file() and f.suffix in text_extensions:
            rel_path = f.relative_to(_project_path)
            files.append(str(rel_path))

    return "\n".join(files)[:2000]


@tool
def read_file(file_path: str) -> str:
    """读取项目中的文件内容。

    Args:
        file_path: 文件路径（如 app/models/note.py）
    """
    if not _project_path:
        return "Error: project_path not set"

    full_path = _project_path / file_path
    if not full_path.exists():
        return f"Error: File not found: {file_path}"

    try:
        # 只读取文本文件
        if full_path.suffix in ['.py', '.html', '.txt', '.md', '.json', '.env']:
            content = full_path.read_text(encoding='utf-8')
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
    if not _project_path:
        return "Error: project_path not set"

    full_path = _project_path / file_path
    full_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        full_path.write_text(content, encoding='utf-8')
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
    if not _project_path:
        return "Error: project_path not set"

    full_path = _project_path / file_path
    if not full_path.exists():
        return f"Error: File not found: {file_path}"

    try:
        content = full_path.read_text(encoding='utf-8')
        if old_content not in content:
            return f"Error: Content to replace not found in file"

        new_file_content = content.replace(old_content, new_content)
        full_path.write_text(new_file_content, encoding='utf-8')
        return f"Success: File modified: {file_path}"
    except Exception as e:
        return f"Error modifying file: {e}"


@tool
def run_app() -> str:
    """运行应用并检查是否有错误。"""
    if not _project_path:
        return "Error: project_path not set"

    sys.path.insert(0, str(_project_path))

    try:
        from app import create_app
        app = create_app()
        return "Success: App imported and created successfully"
    except Exception as e:
        return f"Error: {str(e)[:500]}"
    finally:
        if str(_project_path) in sys.path:
            sys.path.remove(str(_project_path))


def get_tools(project_path: Path):
    """获取所有工具实例。"""
    global _project_path
    _project_path = project_path

    return [
        list_files,
        read_file,
        write_file,
        modify_file,
        run_app,
    ]
