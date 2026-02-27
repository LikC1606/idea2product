"""File system utilities."""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Union


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path

    Returns:
        Path object
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_file(path: Union[str, Path], content: str) -> None:
    """
    Write content to a file.

    Args:
        path: File path
        content: Content to write
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_file(path: Union[str, Path]) -> str:
    """
    Read content from a file.

    Args:
        path: File path

    Returns:
        File content
    """
    path = Path(path)
    return path.read_text(encoding="utf-8")


def write_json(path: Union[str, Path], data: Dict[str, Any], atomic: bool = True) -> None:
    """
    Write data to a JSON file.

    Args:
        path: File path
        data: Data to write
        atomic: If True (default), write to temp file then rename to avoid corruption on partial write
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, indent=2, ensure_ascii=False)
    if atomic:
        suffix = path.suffix or ".json"
        fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=".tmp_", suffix=suffix)
        tmp = Path(tmp_path)
        try:
            with open(fd, "w", encoding="utf-8") as f:
                f.write(content)
            tmp.replace(path)
        except Exception:
            tmp.unlink(missing_ok=True)
            raise
    else:
        path.write_text(content, encoding="utf-8")


def read_json(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Read data from a JSON file.

    Args:
        path: File path

    Returns:
        Parsed JSON data

    Raises:
        FileNotFoundError: If file does not exist
        json.JSONDecodeError: If file content is not valid JSON
    """
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8"))


def read_json_safe(
    path: Union[str, Path],
    default: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Read data from a JSON file, returning default on missing or invalid file.

    Args:
        path: File path
        default: Value to return on file not found or JSON parse error (default: None)

    Returns:
        Parsed JSON data or default
    """
    path = Path(path)
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default
