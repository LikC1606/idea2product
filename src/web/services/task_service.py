"""Task Service - Background task management with per-project serialization.

Supports two generation modes:
  1. First-time: conversation_to_requirements -> run_first_time (Stage 2-4)
  2. Incremental: merge_requirements -> run_from_stage_2 (Stage 2-4)

Same project_id tasks are serialized: if a new generation is requested while one
is running, the latest request is queued and executed after the current one finishes.

Task metadata is persisted to artifacts/task_status.json so the server can
reconstruct state after a restart.
"""

import json
import threading
import traceback
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from config.settings import Settings
from src.utils.file_utils import read_json, write_json
from src.utils.logger import get_logger

logger = get_logger(__name__)

_TASK_STATUS_FILE = "task_status.json"


class TaskService:
    """Background task management with per-project serialization."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._project_locks: Dict[str, threading.Lock] = {}
        self._pending_regenerate: Dict[str, bool] = {}
        self._restore_persisted_tasks()

    def _get_project_lock(self, project_id: str) -> threading.Lock:
        with self._lock:
            if project_id not in self._project_locks:
                self._project_locks[project_id] = threading.Lock()
            return self._project_locks[project_id]

    # ------------------------------------------------------------------
    # Task persistence
    # ------------------------------------------------------------------

    def _status_path(self, project_id: str) -> Path:
        return self.settings.projects_dir / project_id / "artifacts" / _TASK_STATUS_FILE

    def _persist_task(self, project_id: str):
        """Write current task dict to disk for crash recovery."""
        with self._lock:
            task = self.tasks.get(project_id)
        if not task:
            return
        serializable = {k: v for k, v in task.items() if k != "result" or v is None or isinstance(v, dict)}
        try:
            path = self._status_path(project_id)
            path.parent.mkdir(parents=True, exist_ok=True)
            write_json(path, serializable)
        except Exception:
            pass

    def _restore_persisted_tasks(self):
        """On startup, scan projects_dir and reload last-known task status."""
        projects_dir = self.settings.projects_dir
        if not projects_dir.exists():
            return
        for proj_dir in projects_dir.iterdir():
            if not proj_dir.is_dir():
                continue
            status_file = proj_dir / "artifacts" / _TASK_STATUS_FILE
            if not status_file.exists():
                continue
            try:
                data = read_json(status_file)
                pid = data.get("project_id", proj_dir.name)
                if data.get("status") == "processing":
                    data["status"] = "failed"
                    data["error"] = "Server restarted while generation was in progress"
                    data["current_stage"] = "Interrupted"
                with self._lock:
                    self.tasks.setdefault(pid, data)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Project creation (chat-first: no requirement needed upfront)
    # ------------------------------------------------------------------

    def create_chat_project(self) -> str:
        """Create a project for chat-based workflow. Returns project_id."""
        import uuid
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        short = uuid.uuid4().hex[:6]
        project_id = f"proj_{ts}_{short}"

        project_dir = self.settings.projects_dir / project_id
        artifacts_dir = project_dir / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "generated").mkdir(exist_ok=True)
        (project_dir / "logs").mkdir(exist_ok=True)

        task_data = {
            "project_id": project_id,
            "requirement": "",
            "status": "idle",
            "progress": 0,
            "current_stage": "",
            "created_at": datetime.now().isoformat(),
            "result": None,
            "error": None,
        }
        with self._lock:
            self.tasks[project_id] = task_data
        self._persist_task(project_id)

        logger.info(f"Created chat project {project_id}")
        return project_id

    # ------------------------------------------------------------------
    # Legacy: create project with requirement (non-chat mode)
    # ------------------------------------------------------------------

    def create_project(
        self, requirement: str, interactive: bool = False, clarifications: Dict[str, str] = None
    ) -> str:
        project_id = self.create_chat_project()
        with self._lock:
            self.tasks[project_id]["requirement"] = requirement
        self._enqueue_legacy(project_id, requirement, interactive, clarifications or {})
        return project_id

    def _enqueue_legacy(
        self, project_id: str, requirement: str, interactive: bool, clarifications: Dict[str, str]
    ):
        thread = threading.Thread(
            target=self._run_legacy, args=(project_id, requirement, interactive, clarifications), daemon=True
        )
        thread.start()

    def _run_legacy(
        self, project_id: str, requirement: str, interactive: bool, clarifications: Dict[str, str]
    ):
        from src.core.orchestrator import Orchestrator

        proj_lock = self._get_project_lock(project_id)
        with proj_lock:
            try:
                self._update(project_id, status="processing", progress=5, stage="Stage 1: Analyzing requirements")
                orchestrator = Orchestrator(self.settings)
                result = orchestrator.run(requirement, interactive=False)
                self._complete(project_id, result)
            except Exception as e:
                self._fail(project_id, e)

    # ------------------------------------------------------------------
    # Chat-based generation (auto-triggered after each message)
    # ------------------------------------------------------------------

    def enqueue_generation(self, project_id: str):
        """Enqueue a generation task for a project.

        If a generation is already running for this project, mark that a
        re-generation is needed so it runs again with the latest conversation
        once the current one finishes.
        """
        proj_lock = self._get_project_lock(project_id)
        acquired = proj_lock.acquire(blocking=False)
        if not acquired:
            with self._lock:
                self._pending_regenerate[project_id] = True
            logger.info(f"Generation already running for {project_id}; queued re-run")
            return

        thread = threading.Thread(
            target=self._run_generation, args=(project_id, proj_lock), daemon=True
        )
        thread.start()

    def _run_generation(self, project_id: str, proj_lock: threading.Lock):
        """Run generation holding the project lock. Re-runs if pending."""
        try:
            self._do_generate(project_id)
        finally:
            proj_lock.release()

        with self._lock:
            should_rerun = self._pending_regenerate.pop(project_id, False)
        if should_rerun:
            self.enqueue_generation(project_id)

    def _do_generate(self, project_id: str):
        from src.core.orchestrator import Orchestrator
        from src.agents.stage1_requirements.interaction_agent import InteractionAgent
        from src.services.llm_service import LLMService
        from src.web.services.chat_service import get_messages

        start_time = time.time()

        try:
            messages = get_messages(self.settings, project_id)
            if not messages:
                return

            self._update(project_id, status="processing", progress=5, stage="Preparing requirements")

            llm_service = LLMService.from_settings(self.settings)
            agent = InteractionAgent(llm_service)
            orchestrator = Orchestrator(self.settings)

            req_path = self.settings.projects_dir / project_id / "artifacts" / "01_requirements.json"
            is_incremental = req_path.exists()

            if is_incremental:
                self._update(project_id, progress=10, stage="Merging requirements")
                existing_data = read_json(req_path)
                from src.core.data_models import Requirements
                existing_req = Requirements(**existing_data)
                last_user_msg = ""
                for m in reversed(messages):
                    if m.get("role") == "user":
                        last_user_msg = m.get("content", "")
                        break
                requirements = agent.merge_requirements(existing_req, last_user_msg, messages[-5:])
            else:
                self._update(project_id, progress=10, stage="Analyzing conversation")
                requirements = agent.conversation_to_requirements(messages)

            with self._lock:
                self.tasks.setdefault(project_id, {})["requirement"] = (
                    requirements.description or requirements.title or ""
                )

            def _on_progress(progress: int, stage: str) -> None:
                self._update(project_id, progress=progress, stage=stage)

            self._update(project_id, progress=20, stage="Stage 2: Planning")
            result = orchestrator.run_from_stage_2(
                project_id, requirements, progress_callback=_on_progress
            )

            elapsed = round(time.time() - start_time, 1)
            logger.info(f"Generation completed for {project_id} in {elapsed}s")
            self._complete(project_id, result)

            self._try_start_preview(project_id)

        except Exception as e:
            self._fail(project_id, e)

    def _try_start_preview(self, project_id: str):
        """Try to start/restart preview after generation completes."""
        try:
            from src.web.services.preview_service import preview_service
            preview_service.start_preview(project_id)
        except Exception as e:
            logger.warning(f"Preview start failed for {project_id}: {e}")

    # ------------------------------------------------------------------
    # Status helpers
    # ------------------------------------------------------------------

    def _update(self, project_id: str, status: str = None, progress: int = None, stage: str = None):
        with self._lock:
            task = self.tasks.setdefault(project_id, {})
            if status:
                task["status"] = status
            if progress is not None:
                task["progress"] = progress
            if stage:
                task["current_stage"] = stage
        self._persist_task(project_id)

    def _complete(self, project_id: str, result):
        with self._lock:
            task = self.tasks.setdefault(project_id, {})
            task["status"] = "completed"
            task["progress"] = 100
            task["current_stage"] = "Completed"
            task["error"] = None
            if result is not None:
                task["result"] = {
                    "is_deployable": getattr(result, "is_deployable", True),
                    "files_count": len(result.repository.files) if hasattr(result, "repository") else 0,
                    "test_passed": (
                        result.test_results.logic_passed if hasattr(result, "test_results") and result.test_results else False
                    ),
                }
            else:
                task["result"] = {"is_deployable": True, "files_count": 0, "test_passed": False}
        self._persist_task(project_id)

    def _fail(self, project_id: str, error: Exception):
        msg = str(error)
        logger.error(f"Generation failed for {project_id}: {msg}")
        logger.debug(traceback.format_exc())
        with self._lock:
            task = self.tasks.setdefault(project_id, {})
            task["status"] = "failed"
            task["error"] = msg
            task["current_stage"] = f"Error: {msg[:80]}"
        self._persist_task(project_id)

    # ------------------------------------------------------------------
    # Query methods
    # ------------------------------------------------------------------

    def get_status(self, project_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            task = self.tasks.get(project_id)

        if not task:
            if (self.settings.projects_dir / project_id).exists():
                return {
                    "project_id": project_id,
                    "status": "idle",
                    "progress": 0,
                    "current_stage": "",
                    "error": None,
                }
            return None

        return {
            "project_id": project_id,
            "status": task.get("status", "idle"),
            "progress": task.get("progress", 0),
            "current_stage": task.get("current_stage", ""),
            "error": task.get("error"),
        }

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            task = self.tasks.get(project_id)
            if task:
                return dict(task)
        return self._load_project(project_id)

    def list_projects(self) -> List[Dict[str, Any]]:
        projects = []
        seen = set()

        with self._lock:
            for pid, task in self.tasks.items():
                seen.add(pid)
                projects.append({
                    "project_id": pid,
                    "requirement": task.get("requirement", ""),
                    "status": task.get("status", "unknown"),
                    "created_at": task.get("created_at", ""),
                })

        data_dir = self.settings.projects_dir
        if data_dir.exists():
            for proj_dir in sorted(data_dir.iterdir(), reverse=True):
                if proj_dir.is_dir() and proj_dir.name not in seen:
                    project = self._load_project(proj_dir.name)
                    if project:
                        projects.append({
                            "project_id": proj_dir.name,
                            "requirement": project.get("requirement", ""),
                            "status": project.get("status", "completed"),
                            "created_at": project.get("created_at", ""),
                        })
        return projects

    def list_files(self, project_id: str) -> Optional[List[Dict[str, str]]]:
        """List files from the generated/ directory, falling back to artifacts."""
        gen_dir = self.settings.projects_dir / project_id / "generated"
        if gen_dir.exists():
            files = []
            for f in sorted(gen_dir.rglob("*")):
                if f.is_file():
                    rel = f.relative_to(gen_dir).as_posix()
                    files.append({"path": rel, "language": self._guess_language(f.suffix)})
            if files:
                return files

        art_path = self.settings.projects_dir / project_id / "artifacts" / "03_code_repository.json"
        if art_path.exists():
            try:
                data = json.loads(art_path.read_text(encoding="utf-8"))
                return [
                    {"path": f["path"], "language": f.get("language", "text")}
                    for f in data.get("files", [])
                ]
            except Exception:
                pass
        return []

    def get_file(self, project_id: str, file_path: str) -> Optional[Dict[str, str]]:
        full = self.settings.projects_dir / project_id / "generated" / file_path
        if not full.exists():
            return None
        try:
            content = full.read_text(encoding="utf-8")
        except Exception:
            content = full.read_text(encoding="utf-8", errors="replace")
        return {
            "path": file_path,
            "content": content,
            "language": self._guess_language(Path(file_path).suffix),
        }

    def delete_project(self, project_id: str) -> bool:
        with self._lock:
            self.tasks.pop(project_id, None)

        project_path = self.settings.projects_dir / project_id
        if project_path.exists():
            import shutil
            shutil.rmtree(project_path, ignore_errors=True)
            return True
        return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        artifacts = self.settings.projects_dir / project_id / "artifacts"
        if not artifacts.exists():
            return None

        status_file = artifacts / _TASK_STATUS_FILE
        if status_file.exists():
            try:
                return read_json(status_file)
            except Exception:
                pass

        req_file = artifacts / "01_requirements.json"
        chat_file = artifacts / "chat.json"
        desc = ""
        if req_file.exists():
            try:
                data = json.loads(req_file.read_text(encoding="utf-8"))
                desc = data.get("description", "")
            except Exception:
                pass
        if not desc and chat_file.exists():
            try:
                data = json.loads(chat_file.read_text(encoding="utf-8"))
                msgs = data.get("messages", [])
                for m in msgs:
                    if m.get("role") == "user":
                        desc = m.get("content", "")[:100]
                        break
            except Exception:
                pass
        return {
            "project_id": project_id,
            "requirement": desc,
            "status": "completed",
            "created_at": "",
            "result": {"is_deployable": True, "files_count": 0, "test_passed": True},
        }

    @staticmethod
    def _guess_language(ext: str) -> str:
        return {
            ".py": "python", ".html": "html", ".css": "css", ".js": "javascript",
            ".json": "json", ".md": "markdown", ".txt": "text", ".yml": "yaml",
            ".yaml": "yaml", ".toml": "toml", ".cfg": "ini", ".ini": "ini",
            ".sh": "bash", ".bat": "batch", ".sql": "sql",
        }.get(ext.lower(), "text")
