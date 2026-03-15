"""Preview Service - Manages running previews of generated applications.

Starts a subprocess (e.g. `python app.py`) in the project's generated/ directory,
bound to a dynamically allocated port. Provides the preview URL for iframe embedding.

Features:
- Child stderr captured to logs/<project_id>/preview.log
- Health check: waits for the app to accept TCP connections before returning URL
- Idle timeout: reaps processes that have been running longer than MAX_PREVIEW_LIFETIME
"""

import json
import os
import sys
import signal
import socket
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, Optional, Any

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
        self._last_error: Dict[str, str] = {}
        self._status: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._reaper_started = False

    def start_preview(self, project_id: str) -> Optional[str]:
        """Start or restart the preview for a project. Returns the preview URL."""
        self._set_status(project_id, "starting")
        self.stop_preview(project_id)
        self._ensure_reaper()

        gen_dir = self.settings.projects_dir / project_id / "generated"
        if not gen_dir.exists():
            self._set_error(project_id, "No generated/ directory found")
            self._set_status(project_id, "error")
            logger.warning(f"No generated/ dir for {project_id}")
            return None

        entry = self._detect_entry_point(gen_dir)
        if not entry:
            self._set_error(project_id, "No entry point (app.py / main.py) found in generated code")
            self._set_status(project_id, "error")
            logger.warning(f"No entry point found in {gen_dir}")
            return None

        self._set_status(project_id, "installing")
        ok, install_err = self._install_requirements(gen_dir)
        if not ok:
            msg = f"Dependency install failed: {install_err or 'pip install returned non-zero'}"
            self._set_error(project_id, msg)
            self._set_status(project_id, "error")
            logger.warning("Preview %s: %s", project_id, msg)
            return None
        self._set_status(project_id, "starting")

        port = _find_free_port()
        env = os.environ.copy()
        env["PORT"] = str(port)
        env["FLASK_RUN_PORT"] = str(port)
        env["FLASK_APP"] = entry
        # Force non-debug / non-reloader behavior for stability. Even if generated
        # code uses app.run(...), many templates respect these env flags.
        env.setdefault("FLASK_ENV", "production")
        env["FLASK_DEBUG"] = "0"
        env["FLASK_RUN_RELOAD"] = "0"
        env["DEBUG"] = "0"
        env["WERKZEUG_DEBUG_PIN"] = "off"
        env["PYTHONUNBUFFERED"] = "1"
        existing_pypath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = str(gen_dir) + (os.pathsep + existing_pypath if existing_pypath else "")

        log_dir = self.settings.projects_dir / project_id / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        stderr_log = log_dir / "preview.log"

        cmd = [sys.executable, entry]

        stderr_fh = None
        try:
            stderr_fh = open(stderr_log, "a", encoding="utf-8")
            proc = subprocess.Popen(
                cmd,
                cwd=str(gen_dir),
                env=env,
                stdout=stderr_fh,
                stderr=stderr_fh,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
            )
        except Exception as e:
            if stderr_fh is not None:
                try:
                    stderr_fh.close()
                except OSError:
                    pass
            self._set_error(project_id, f"Failed to start process: {e}")
            self._set_status(project_id, "error")
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
                err_snippet = self._read_last_error_from_log(stderr_log)
                self._set_error(
                    project_id,
                    f"Process exited immediately (code={proc.returncode}). {err_snippet}"
                )
                logger.warning(
                    f"Preview process for {project_id} exited immediately "
                    f"(code={proc.returncode}). Check {stderr_log}"
                )
                self._set_status(project_id, "error")
                self._cleanup_entry(project_id)
                return None
            self._set_status(project_id, "warming")
            logger.info(
                f"Preview for {project_id} on {url} did not pass health check "
                f"within {_HEALTH_CHECK_TIMEOUT}s; returning URL anyway"
            )

        self._clear_error(project_id)
        self._set_status(project_id, "running")
        full_url = self._append_default_route(project_id, url)
        logger.info(f"Preview started for {project_id} on {full_url} (pid={proc.pid}, healthy={healthy})")
        return full_url

    def _get_default_preview_path(self, project_id: str) -> Optional[str]:
        """Read 02_engineering_plan.json and return main frontend route (list page over forms)."""
        plan_path = self.settings.projects_dir / project_id / "artifacts" / "02_engineering_plan.json"
        if not plan_path.exists():
            return None
        try:
            data = json.loads(plan_path.read_text(encoding="utf-8"))
            routes = (data.get("api_specs") or {}).get("frontend_routes") or {}
            candidates = []
            for path, _ in routes.items():
                if path and path != "/" and "<" not in path:
                    p = path.rstrip("/") or path
                    # Prefer list routes (e.g. /tasks) over form routes (e.g. /tasks/new)
                    is_form = "/new" in p or "/create" in p or "/edit" in p
                    candidates.append((p, is_form))
            # Prefer non-form routes, then by path length (shorter = likely main list)
            if candidates:
                best = min(candidates, key=lambda x: (x[1], len(x[0])))
                return best[0]
        except Exception as ex:
            logger.debug("Could not detect default route: %s", ex)
        return None

    def _append_default_route(self, project_id: str, base_url: str) -> str:
        """Append default main route to preview URL when available."""
        path = self._get_default_preview_path(project_id)
        if path:
            return base_url.rstrip("/") + path
        return base_url

    def get_preview_error(self, project_id: str) -> Optional[str]:
        """Return the last error message for this project's preview, or None."""
        with self._lock:
            return self._last_error.get(project_id)

    def _set_error(self, project_id: str, message: str):
        with self._lock:
            self._last_error[project_id] = message

    def _clear_error(self, project_id: str):
        with self._lock:
            self._last_error.pop(project_id, None)

    @staticmethod
    def _read_last_error_from_log(log_path: Path, max_chars: int = 200) -> str:
        """Read the last few lines from the preview log to surface the error."""
        try:
            text = log_path.read_text(encoding="utf-8", errors="replace")
            tail = text.strip()[-max_chars:] if text.strip() else ""
            return tail
        except Exception as ex:
            logger.debug("Could not read preview log: %s", ex)
            return ""

    def stop_preview(self, project_id: str):
        """Stop the preview subprocess for a project."""
        with self._lock:
            info = self._previews.pop(project_id, None)
        if not info:
            return
        self._terminate(info)
        self._set_status(project_id, "stopped")
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
            self._set_status(project_id, "stopped")
            return None

        return self._append_default_route(project_id, info["url"])

    def ensure_preview_started(self, project_id: str) -> Dict[str, Any]:
        """
        Ensure preview is running or being started asynchronously.
        Returns status payload for API responses.
        """
        url = self.get_preview_url(project_id)
        if url:
            return self.get_preview_status(project_id)

        with self._lock:
            current = (self._status.get(project_id) or {}).get("state")
            if current in {"starting", "installing"}:
                return self.get_preview_status(project_id)
            self._status[project_id] = {"state": "starting", "updated_at": time.time()}

        t = threading.Thread(
            target=self._start_preview_async_worker,
            args=(project_id,),
            daemon=True,
        )
        t.start()
        return self.get_preview_status(project_id)

    def _start_preview_async_worker(self, project_id: str) -> None:
        try:
            url = self.start_preview(project_id)
            if not url and self.get_preview_error(project_id):
                self._set_status(project_id, "error")
        except Exception as ex:
            self._set_error(project_id, f"Preview start failed: {ex}")
            self._set_status(project_id, "error")
            logger.warning("Async preview start failed for %s: %s", project_id, ex)

    def get_preview_status(self, project_id: str) -> Dict[str, Any]:
        url = self.get_preview_url(project_id)
        with self._lock:
            state = (self._status.get(project_id) or {}).get("state") or ("running" if url else "idle")
        err = self.get_preview_error(project_id)
        return {
            "preview_url": url,
            "running": bool(url),
            "state": state,
            "starting": state == "starting",
            "installing": state == "installing",
            "warming": state == "warming",
            "preview_error": err,
        }

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
        except (OSError, ProcessLookupError) as ex:
            logger.debug("Terminate signal failed: %s", ex)
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
            except OSError as ex:
                logger.debug("Close stderr failed: %s", ex)

    def _install_requirements(self, gen_dir: Path) -> tuple[bool, Optional[str]]:
        """Install pip packages from the generated project's requirements.txt.
        Returns (True, None) on success, (False, error_message) on failure."""
        req_file = gen_dir / "requirements.txt"
        if not req_file.exists():
            return True, None
        try:
            logger.info("Installing dependencies from %s", req_file)
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-q", "-r", str(req_file)],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                snippet = (result.stderr or result.stdout or "")[:300]
                logger.warning("pip install returned %s: %s", result.returncode, snippet)
                return False, snippet.strip() or f"pip exited with code {result.returncode}"
            logger.info("Dependencies installed successfully")
            return True, None
        except subprocess.TimeoutExpired as e:
            logger.warning("Failed to install dependencies: timeout %s", e)
            return False, "pip install timed out"
        except Exception as e:
            logger.warning("Failed to install dependencies: %s", e)
            return False, str(e)

    def _set_status(self, project_id: str, state: str) -> None:
        with self._lock:
            self._status[project_id] = {
                "state": state,
                "updated_at": time.time(),
            }

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
            except Exception as ex:
                logger.debug("Could not check file for Flask app: %s", ex)
                continue
        return None


_preview_service: Optional[PreviewService] = None


def _get_preview_service() -> PreviewService:
    global _preview_service
    if _preview_service is None:
        from config.settings import get_settings
        _preview_service = PreviewService(get_settings())
    return _preview_service


class _PreviewServiceProxy:
    """Lazy proxy so `preview_service` can be imported at module load
    without requiring Settings / .env to be available."""

    def __getattr__(self, name):
        return getattr(_get_preview_service(), name)


preview_service: PreviewService = _PreviewServiceProxy()  # type: ignore[assignment]
