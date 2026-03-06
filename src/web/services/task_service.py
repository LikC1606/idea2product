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
from src.core.exceptions import LLMServiceError
from src.utils.file_utils import read_json, read_json_safe, write_json
from src.utils.logger import get_logger

logger = get_logger(__name__)

class BinaryFileError(Exception):
    """Raised when attempting to preview a binary or non-text file."""


def _is_transient_error(exc: BaseException) -> bool:
    """True if the exception is typically transient (network/LLM timeout, 5xx)."""
    if isinstance(exc, (LLMServiceError, TimeoutError)):
        return True
    try:
        from openai import APITimeoutError, APIConnectionError, APIError, RateLimitError
        if isinstance(exc, (APITimeoutError, APIConnectionError, APIError, RateLimitError)):
            return True
    except ImportError:
        pass
    return False

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
        """Write current task dict to disk for crash recovery. May raise on I/O error."""
        with self._lock:
            task = self.tasks.get(project_id)
        if not task:
            return
        serializable = {k: v for k, v in task.items() if k != "result" or v is None or isinstance(v, dict)}
        path = self._status_path(project_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        write_json(path, serializable)

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
                data = read_json_safe(status_file)
                if not data:
                    continue
                pid = data.get("project_id", proj_dir.name)
                if data.get("status") == "processing":
                    data["status"] = "failed"
                    data["error"] = "Server restarted while generation was in progress"
                    data["current_stage"] = "Interrupted"
                with self._lock:
                    self.tasks.setdefault(pid, data)
            except Exception as ex:
                logger.debug("Could not restore persisted task %s: %s", pid, ex)

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
        self,
        requirement: str,
        interactive: bool = False,
        clarifications: Dict[str, str] = None,
        product_type: str = None,
        model_id: str = None,
    ) -> str:
        project_id = self.create_chat_project()
        with self._lock:
            self.tasks[project_id]["requirement"] = requirement
            if product_type is not None:
                self.tasks[project_id]["product_type"] = product_type
            if model_id is not None:
                self.tasks[project_id]["model_id"] = model_id
        self._enqueue_legacy(
            project_id, requirement, interactive, clarifications or {}, product_type, model_id
        )
        return project_id

    def _enqueue_legacy(
        self,
        project_id: str,
        requirement: str,
        interactive: bool,
        clarifications: Dict[str, str],
        product_type: str = None,
        model_id: str = None,
    ):
        thread = threading.Thread(
            target=self._run_legacy,
            args=(project_id, requirement, interactive, clarifications, product_type, model_id),
            daemon=True,
        )
        thread.start()

    def _run_legacy(
        self,
        project_id: str,
        requirement: str,
        interactive: bool,
        clarifications: Dict[str, str],
        product_type: str = None,
        model_id: str = None,
    ):
        from src.core.orchestrator import Orchestrator

        proj_lock = self._get_project_lock(project_id)
        with proj_lock:
            try:
                self._update(project_id, status="processing", progress=5, stage="Stage 1: Analyzing requirements")
                orchestrator = Orchestrator(self.settings)
                result = orchestrator.run(
                    requirement,
                    interactive=False,
                    product_type=product_type,
                    model_id=model_id,
                )
                self._complete(project_id, result)
            except Exception as e:
                self._fail(project_id, e)

    # ------------------------------------------------------------------
    # Chat-based generation (auto-triggered after each message)
    # ------------------------------------------------------------------

    def enqueue_generation(
        self,
        project_id: str,
        product_type: str = None,
        model_id: str = None,
    ):
        """Enqueue a generation task for a project.

        Optionally pass product_type and model_id for this run (stored and passed to orchestrator).
        If a generation is already running for this project, mark that a
        re-generation is needed so it runs again with the latest conversation
        once the current one finishes.
        """
        with self._lock:
            self.tasks.setdefault(project_id, {})
            if product_type is not None:
                self.tasks[project_id]["product_type"] = product_type
            if model_id is not None:
                self.tasks[project_id]["model_id"] = model_id

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
        retry_on_transient = getattr(self.settings, "task_generation_retry_on_transient", False)
        last_exception = None

        for attempt in range(2):
            if attempt > 0:
                logger.warning("Retrying generation for %s after transient error", project_id)
            try:
                messages = get_messages(self.settings, project_id)
                if not messages:
                    return

                self._update(project_id, status="processing", progress=5, stage="Preparing requirements")

                llm_service = LLMService.from_settings(self.settings)
                agent = InteractionAgent(llm_service)
                orchestrator = Orchestrator(self.settings)

                req_path = self.settings.projects_dir / project_id / "artifacts" / "01_requirements.json"
                existing_data = read_json_safe(req_path)
                is_incremental = existing_data is not None

                if is_incremental:
                    self._update(project_id, progress=10, stage="Merging requirements")
                    try:
                        from src.core.data_models import Requirements
                        existing_req = Requirements(**existing_data)
                    except Exception as e:
                        logger.warning("Invalid requirements.json for %s, falling back to first-time: %s", project_id, e)
                        is_incremental = False

                if is_incremental:
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
                    self.tasks.setdefault(project_id, {})
                    self.tasks[project_id]["requirement"] = (
                        requirements.description or requirements.title or ""
                    )
                    run_product_type = self.tasks[project_id].get("product_type")
                    run_model_id = self.tasks[project_id].get("model_id")

                if run_product_type and not getattr(requirements, "product_type", None):
                    from src.core.data_models import ProductType
                    try:
                        requirements.product_type = ProductType(run_product_type)
                    except (ValueError, TypeError):
                        pass

                def _on_progress(progress: int, stage: str) -> None:
                    self._update(project_id, progress=progress, stage=stage)

                self._update(project_id, progress=20, stage="Stage 2: Planning")
                result = orchestrator.run_from_stage_2(
                    project_id,
                    requirements,
                    progress_callback=_on_progress,
                    product_type=run_product_type,
                    model_id=run_model_id,
                )

                elapsed = round(time.time() - start_time, 1)
                logger.info("Generation completed for %s in %ss", project_id, elapsed)
                self._complete(project_id, result)

                self._try_start_preview(project_id)
                return

            except Exception as e:
                last_exception = e
                if attempt == 0 and retry_on_transient and _is_transient_error(e):
                    logger.warning("Transient error for %s (will retry once): %s", project_id, e)
                    continue
                self._fail(project_id, e)
                return

        if last_exception is not None:
            self._fail(project_id, last_exception)

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
        try:
            self._persist_task(project_id)
        except Exception as e:
            logger.warning("Failed to persist task status for %s: %s", project_id, e)

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
        try:
            self._persist_task(project_id)
        except Exception as e:
            logger.warning("Failed to persist task status for %s: %s", project_id, e)

    def _fail(self, project_id: str, error: Exception):
        msg = str(error)
        logger.error("Generation failed for %s: %s", project_id, msg)
        logger.debug("%s", traceback.format_exc())
        with self._lock:
            task = self.tasks.setdefault(project_id, {})
            task["status"] = "failed"
            task["error"] = msg
            task["current_stage"] = f"Error: {msg[:80]}"
        try:
            self._persist_task(project_id)
        except Exception:
            logger.exception("Failed to persist task status after failure for %s", project_id)
            # Do not re-raise so the original failure reason is not masked

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
                project = dict(task)
            else:
                project = self._load_project(project_id)
        if not project:
            return None
        project.update(self._timeline_for_project(project_id))
        return project

    def list_projects(self) -> List[Dict[str, Any]]:
        projects = []
        seen = set()

        with self._lock:
            for pid, task in self.tasks.items():
                seen.add(pid)
                base = {
                    "project_id": pid,
                    "requirement": task.get("requirement", ""),
                    "status": task.get("status", "unknown"),
                    "created_at": task.get("created_at", ""),
                }
                base.update(self._timeline_for_project(pid))
                projects.append(base)

        data_dir = self.settings.projects_dir
        if data_dir.exists():
            for proj_dir in sorted(data_dir.iterdir(), reverse=True):
                if proj_dir.is_dir() and proj_dir.name not in seen:
                    project = self._load_project(proj_dir.name)
                    if project:
                        base = {
                            "project_id": proj_dir.name,
                            "requirement": project.get("requirement", ""),
                            "status": project.get("status", "completed"),
                            "created_at": project.get("created_at", ""),
                        }
                        base.update(self._timeline_for_project(proj_dir.name))
                        projects.append(base)
        return projects

    def list_files(self, project_id: str) -> Optional[List[Dict[str, str]]]:
        """List files from the generated/ directory, falling back to artifacts."""
        gen_dir = self.settings.projects_dir / project_id / "generated"
        if gen_dir.exists():
            files = []
            skip_suffixes = {
                ".pyc", ".pyo", ".pyd",
                ".db", ".sqlite", ".sqlite3",
                ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico",
                ".pdf",
                ".zip", ".tar", ".gz", ".7z",
                ".mp4", ".webm", ".mp3", ".wav",
            }
            for f in sorted(gen_dir.rglob("*")):
                if f.is_file():
                    if "__pycache__" in f.parts:
                        continue
                    if f.suffix.lower() in skip_suffixes:
                        continue
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
            except Exception as ex:
                logger.debug("Could not load artifacts for list_files: %s", ex)
        return []

    def get_file(self, project_id: str, file_path: str) -> Optional[Dict[str, str]]:
        full = self.settings.projects_dir / project_id / "generated" / file_path
        if not full.exists():
            return None
        if "__pycache__" in full.parts:
            raise BinaryFileError("该文件来自 __pycache__，无法预览。")
        binary_suffixes = {
            ".pyc", ".pyo", ".pyd",
            ".db", ".sqlite", ".sqlite3",
            ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico",
            ".pdf",
            ".zip", ".tar", ".gz", ".7z",
            ".mp4", ".webm", ".mp3", ".wav",
        }
        if Path(file_path).suffix.lower() in binary_suffixes:
            raise BinaryFileError("该文件为二进制或资源文件，无法在代码视图中预览。")
        try:
            content = full.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raise BinaryFileError("该文件不是 UTF-8 文本（可能为二进制），无法预览。")
        except Exception:
            return None
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
            except Exception as ex:
                logger.debug("Could not read status file: %s", ex)

        req_file = artifacts / "01_requirements.json"
        chat_file = artifacts / "chat.json"
        desc = ""
        if req_file.exists():
            try:
                data = json.loads(req_file.read_text(encoding="utf-8"))
                desc = data.get("description", "")
            except Exception as ex:
                logger.debug("Could not read requirements for fallback: %s", ex)
        if not desc and chat_file.exists():
            try:
                data = json.loads(chat_file.read_text(encoding="utf-8"))
                msgs = data.get("messages", [])
                for m in msgs:
                    if m.get("role") == "user":
                        desc = m.get("content", "")[:100]
                        break
            except Exception as ex:
                logger.debug("Could not read chat for fallback: %s", ex)
        return {
            "project_id": project_id,
            "requirement": desc,
            "status": "completed",
            "created_at": "",
            "result": {"is_deployable": True, "files_count": 0, "test_passed": True},
        }

    def get_plan(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Return persisted EngineeringPlan JSON for a project, if available."""
        artifacts = self.settings.projects_dir / project_id / "artifacts"
        plan_path = artifacts / "02_engineering_plan.json"
        if not plan_path.exists():
            return None
        try:
            return json.loads(plan_path.read_text(encoding="utf-8"))
        except Exception as ex:
            logger.debug("Could not read engineering plan for %s: %s", project_id, ex)
            return None

    def update_plan(self, project_id: str, patch: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Patch persisted EngineeringPlan (currently supports safe task field updates)."""
        artifacts = self.settings.projects_dir / project_id / "artifacts"
        plan_path = artifacts / "02_engineering_plan.json"
        if not plan_path.exists():
            return None
        try:
            data = json.loads(plan_path.read_text(encoding="utf-8"))
        except Exception as ex:
            logger.debug("Could not read engineering plan for patch %s: %s", project_id, ex)
            return None

        tasks_patch = patch.get("tasks") or []
        if tasks_patch:
            # Index existing tasks by id
            tasks = data.get("tasks") or []
            index = {t.get("id"): t for t in tasks if isinstance(t, dict) and t.get("id")}
            allowed_keys = {"name", "description", "priority", "estimated_complexity"}
            for tp in tasks_patch:
                if not isinstance(tp, dict):
                    continue
                tid = tp.get("id")
                if not tid or tid not in index:
                    continue
                target = index[tid]
                for key, value in tp.items():
                    if key == "id":
                        continue
                    # allow title as alias for name
                    if key == "title":
                        key = "name"
                    if key in allowed_keys:
                        target[key] = value

        # Validate via data model to avoid breaking changes
        try:
            from src.core.data_models import EngineeringPlan

            plan_obj = EngineeringPlan.model_validate(data)
            data = plan_obj.model_dump(mode="json")
        except Exception as ex:
            logger.debug("EngineeringPlan validation failed during update for %s: %s", project_id, ex)
            return None

        try:
            plan_path.parent.mkdir(parents=True, exist_ok=True)
            write_json(plan_path, data)
        except Exception as ex:
            logger.warning("Failed to persist updated engineering plan for %s: %s", project_id, ex)
            return None
        return data

    def _timeline_for_project(self, project_id: str) -> Dict[str, str]:
        """Derive simple timeline metadata from artifacts (ISO8601 strings or '')."""
        artifacts = self.settings.projects_dir / project_id / "artifacts"
        timeline: Dict[str, str] = {
            "planning_completed_at": "",
            "generation_completed_at": "",
            "validation_last_run_at": "",
        }
        try:
            plan_file = artifacts / "02_engineering_plan.json"
            if plan_file.exists():
                ts = datetime.fromtimestamp(plan_file.stat().st_mtime).isoformat()
                timeline["planning_completed_at"] = ts
            repo_file = artifacts / "03_code_repository.json"
            if repo_file.exists():
                ts = datetime.fromtimestamp(repo_file.stat().st_mtime).isoformat()
                timeline["generation_completed_at"] = ts
            runs_file = artifacts / "validation_runs.json"
            if runs_file.exists():
                data = read_json_safe(runs_file) or []
                if isinstance(data, list) and data:
                    last = sorted(
                        data,
                        key=lambda r: r.get("finished_at") or r.get("started_at") or "",
                        reverse=True,
                    )[0]
                    finished = last.get("finished_at") or last.get("started_at")
                    if finished:
                        timeline["validation_last_run_at"] = finished
        except Exception as ex:
            logger.debug("Could not build timeline for %s: %s", project_id, ex)
        return timeline

    @staticmethod
    def _guess_language(ext: str) -> str:
        return {
            ".py": "python", ".html": "html", ".css": "css", ".js": "javascript",
            ".json": "json", ".md": "markdown", ".txt": "text", ".yml": "yaml",
            ".yaml": "yaml", ".toml": "toml", ".cfg": "ini", ".ini": "ini",
            ".sh": "bash", ".bat": "batch", ".sql": "sql",
        }.get(ext.lower(), "text")
