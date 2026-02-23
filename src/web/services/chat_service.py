"""Chat session storage per project. Persists messages to artifacts/chat.json."""

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from config.settings import Settings
from src.utils.file_utils import ensure_dir, read_json, write_json


CHAT_FILENAME = "chat.json"


def _chat_path(projects_dir: Path, project_id: str) -> Path:
    return projects_dir / project_id / "artifacts" / CHAT_FILENAME


def get_messages(settings: Settings, project_id: str) -> List[Dict[str, str]]:
    """
    Load chat messages for a project. Returns empty list if no chat file exists.
    """
    path = _chat_path(settings.projects_dir, project_id)
    if not path.exists():
        return []
    try:
        data = read_json(path)
        return data.get("messages", [])
    except Exception:
        return []


def append_message(
    settings: Settings,
    project_id: str,
    role: str,
    content: str,
) -> None:
    """
    Append a message and persist. Creates project dir and artifacts dir if needed.
    """
    projects_dir = settings.projects_dir
    project_dir = projects_dir / project_id
    artifacts_dir = project_dir / "artifacts"
    ensure_dir(artifacts_dir)
    path = artifacts_dir / CHAT_FILENAME

    messages = get_messages(settings, project_id)
    messages.append({"role": role, "content": content})
    data = {"messages": messages, "updated_at": datetime.now().isoformat()}
    write_json(path, data)
