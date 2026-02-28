"""Chat session storage per project. Persists messages to artifacts/chat.json."""

from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from filelock import FileLock, Timeout

from config.settings import Settings
from src.utils.file_utils import ensure_dir, read_json_safe, write_json
from src.utils.logger import get_logger

logger = get_logger(__name__)


CHAT_FILENAME = "chat.json"


def _chat_path(projects_dir: Path, project_id: str) -> Path:
    return projects_dir / project_id / "artifacts" / CHAT_FILENAME


def get_messages(settings: Settings, project_id: str) -> List[Dict[str, str]]:
    """
    Load chat messages for a project. Returns empty list if no chat file exists.
    Uses file lock for safe concurrent read during append.
    """
    path = _chat_path(settings.projects_dir, project_id)
    if not path.exists():
        return []
    try:
        with FileLock(str(path) + ".lock", timeout=10):
            data = read_json_safe(path, default={})
            return data.get("messages", []) if isinstance(data, dict) else []
    except Timeout:
        logger.warning(f"Chat file lock timeout for project {project_id}, returning empty messages")
        return []


def append_message(
    settings: Settings,
    project_id: str,
    role: str,
    content: str,
) -> None:
    """
    Append a message and persist. Creates project dir and artifacts dir if needed.
    Uses file lock to prevent concurrent write corruption.
    """
    projects_dir = settings.projects_dir
    project_dir = projects_dir / project_id
    artifacts_dir = project_dir / "artifacts"
    ensure_dir(artifacts_dir)
    path = artifacts_dir / CHAT_FILENAME

    try:
        with FileLock(str(path) + ".lock", timeout=10):
            messages = []
            data = read_json_safe(path, default={})
            if isinstance(data, dict):
                messages = list(data.get("messages", []))
            messages.append({"role": role, "content": content})
            write_json(path, {"messages": messages, "updated_at": datetime.now().isoformat()})
    except Timeout:
        logger.warning(f"Chat file lock timeout for project {project_id}, cannot append message")
        raise RuntimeError("Chat storage is temporarily busy, please retry") from None
