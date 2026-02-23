"""Preview Service - Manages running previews of generated applications.

Starts a subprocess (e.g. `python app.py`) in the project's generated/ directory,
bound to a dynamically allocated port. Provides the preview URL for iframe embedding.
"""

import os
import sys
import signal
import socket
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

from config.settings import Settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

_PORT_RANGE_START = 18000
_PORT_RANGE_END = 18200


def _find_free_port(start: int = _PORT_RANGE_START, end: int = _PORT_RANGE_END) -> int:
    for port in range(start, end):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"No free port in range {start}-{end}")


class PreviewService:
    """Manages preview subprocesses for generated projects."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._previews: Dict[str, Dict] = {}
        self._lock = threading.Lock()

    def start_preview(self, project_id: str) -> Optional[str]:
        """Start or restart the preview for a project. Returns the preview URL."""
        self.stop_preview(project_id)

        gen_dir = self.settings.projects_dir / project_id / "generated"
        if not gen_dir.exists():
            logger.warning(f"No generated/ dir for {project_id}")
            return None

        entry = self._detect_entry_point(gen_dir)
        if not entry:
            logger.warning(f"No entry point found in {gen_dir}")
            return None

        port = _find_free_port()
        env = os.environ.copy()
        env["PORT"] = str(port)
        env["FLASK_RUN_PORT"] = str(port)
        env["FLASK_APP"] = entry

        cmd = [sys.executable, entry]

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(gen_dir),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
            )
        except Exception as e:
            logger.error(f"Failed to start preview for {project_id}: {e}")
            return None

        url = f"http://127.0.0.1:{port}"

        with self._lock:
            self._previews[project_id] = {
                "process": proc,
                "port": port,
                "url": url,
                "entry": entry,
                "started_at": time.time(),
            }

        logger.info(f"Preview started for {project_id} on {url} (pid={proc.pid})")
        return url

    def stop_preview(self, project_id: str):
        """Stop the preview subprocess for a project."""
        with self._lock:
            info = self._previews.pop(project_id, None)
        if not info:
            return

        proc = info["process"]
        try:
            if sys.platform == "win32":
                proc.terminate()
            else:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except (OSError, ProcessLookupError):
            pass

        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

        logger.info(f"Preview stopped for {project_id} (port={info['port']})")

    def get_preview_url(self, project_id: str) -> Optional[str]:
        """Get the preview URL if the preview is running."""
        with self._lock:
            info = self._previews.get(project_id)
        if not info:
            return None

        proc = info["process"]
        if proc.poll() is not None:
            with self._lock:
                self._previews.pop(project_id, None)
            return None

        return info["url"]

    def stop_all(self):
        """Stop all running previews."""
        with self._lock:
            ids = list(self._previews.keys())
        for pid in ids:
            self.stop_preview(pid)

    @staticmethod
    def _detect_entry_point(gen_dir: Path) -> Optional[str]:
        """Detect the entry point script in the generated directory."""
        candidates = ["app.py", "main.py", "server.py", "run.py", "manage.py"]
        for name in candidates:
            if (gen_dir / name).exists():
                return name

        for f in gen_dir.glob("*.py"):
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                if "flask" in content.lower() and ("app.run" in content or "Flask(" in content):
                    return f.name
            except Exception:
                continue
        return None


preview_service = PreviewService(Settings())
