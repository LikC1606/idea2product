"""File system utilities."""

import json
from pathlib import Path
from typing import Any, Dict, Union


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


def write_json(path: Union[str, Path], data: Dict[str, Any]) -> None:
    """
    Write data to a JSON file.

    Args:
        path: File path
        data: Data to write
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def read_json(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Read data from a JSON file.

    Args:
        path: File path

    Returns:
        Parsed JSON data
    """
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8"))
