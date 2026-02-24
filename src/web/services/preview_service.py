"""Preview Service - Manages running previews of generated applications.

Starts a subprocess (e.g. `python app.py`) in the project's generated/ directory,
bound to a dynamically allocated port. Provides the preview URL for iframe embedding.

Features:
- Child stderr captured to logs/<project_id>/preview.log
- Health check: waits for the app to accept TCP connections before returning URL
- Idle timeout: reaps processes that have been running longer than MAX_PREVIEW_LIFETIME
"""

import os
import sys
import signal
import socket
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, Optional

from config.settings import Settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

_PORT_RANGE_START = 18000
_PORT_RANGE_END = 18200
_MAX_PREVIEW_LIFETIME = 3600  # seconds (1 hour)
_HEALTH_CHECK_TIMEOUT = 8  # seconds to wait for app to start listening


def _find_free_port(start: int = _PORT_RANGE_START, end: int = _PORT_RANGE_END) -> int:
    for port in range(start, end):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"No free port in range {start}-{end}")


def _wait_for_port(port: int, timeout: float = _HEALTH_CHECK_TIMEOUT) -> bool:
    """Block until 127.0.0.1:port accepts a TCP connection, or timeout."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return True
        except (OSError, ConnectionRefusedError):
            time.sleep(0.3)
    return False


class PreviewService:
    """Manages preview subprocesses for generated projects."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._previews: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        self._reaper_started = False

    def start_preview(self, project_id: str) -> Optional[str]:
        """Start or restart the preview for a project. Returns the preview URL."""
        self.stop_preview(project_id)
        self._ensure_reaper()

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

        log_dir = self.settings.projects_dir / project_id / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        stderr_log = log_dir / "preview.log"

        cmd = [sys.executable, entry]

        try:
            stderr_fh = open(stderr_log, "a", encoding="utf-8")
            proc = subprocess.Popen(
                cmd,
                cwd=str(gen_dir),
                env=env,
                stdout=subprocess.PIPE,
                stderr=stderr_fh,
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
                "stderr_fh": stderr_fh,
            }

        healthy = _wait_for_port(port)
        if not healthy:
            if proc.poll() is not None:
                logger.warning(
                    f"Preview process for {project_id} exited immediately "
                    f"(code={proc.returncode}). Check {stderr_log}"
                )
                self._cleanup_entry(project_id)
                return None
            logger.info(
                f"Preview for {project_id} on {url} did not pass health check "
                f"within {_HEALTH_CHECK_TIMEOUT}s; returning URL anyway"
            )

        logger.info(f"Preview started for {project_id} on {url} (pid={proc.pid}, healthy={healthy})")
        return url

    def stop_preview(self, project_id: str):
        """Stop the preview subprocess for a project."""
        with self._lock:
            info = self._previews.pop(project_id, None)
        if not info:
            return
        self._terminate(info)
        logger.info(f"Preview stopped for {project_id} (port={info['port']})")

    def get_preview_url(self, project_id: str) -> Optional[str]:
        """Get the preview URL if the preview is running."""
        with self._lock:
            info = self._previews.get(project_id)
        if not info:
            return None

        proc = info["process"]
        if proc.poll() is not None:
            self._cleanup_entry(project_id)
            return None

        return info["url"]

    def stop_all(self):
        """Stop all running previews."""
        with self._lock:
            ids = list(self._previews.keys())
        for pid in ids:
            self.stop_preview(pid)

    # ------------------------------------------------------------------
    # Idle reaper
    # ------------------------------------------------------------------

    def _ensure_reaper(self):
        if self._reaper_started:
            return
        self._reaper_started = True
        t = threading.Thread(target=self._reaper_loop, daemon=True)
        t.start()

    def _reaper_loop(self):
        """Periodically kill preview processes that exceed the max lifetime."""
        while True:
            time.sleep(60)
            now = time.time()
            to_reap = []
            with self._lock:
                for pid, info in self._previews.items():
                    age = now - info["started_at"]
                    if age > _MAX_PREVIEW_LIFETIME:
                        to_reap.append(pid)
                    elif info["process"].poll() is not None:
                        to_reap.append(pid)
            for pid in to_reap:
                logger.info(f"Reaping idle/dead preview for {pid}")
                self.stop_preview(pid)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _cleanup_entry(self, project_id: str):
        with self._lock:
            info = self._previews.pop(project_id, None)
        if info:
            self._close_stderr(info)

    @staticmethod
    def _terminate(info: Dict):
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
        PreviewService._close_stderr(info)

    @staticmethod
    def _close_stderr(info: Dict):
        fh = info.get("stderr_fh")
        if fh:
            try:
                fh.close()
            except Exception:
                pass

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


_preview_service: Optional[PreviewService] = None


def _get_preview_service() -> PreviewService:
    global _preview_service
    if _preview_service is None:
        _preview_service = PreviewService(Settings())
    return _preview_service


class _PreviewServiceProxy:
    """Lazy proxy so `preview_service` can be imported at module load
    without requiring Settings / .env to be available."""

    def __getattr__(self, name):
        return getattr(_get_preview_service(), name)


preview_service: PreviewService = _PreviewServiceProxy()  # type: ignore[assignment]
