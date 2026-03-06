"""Project API Blueprint.

Endpoints:
  POST   /api/projects              - create project (legacy or chat-first)
  GET    /api/projects              - list projects
  GET    /api/projects/<id>         - project details
  GET    /api/projects/<id>/status  - generation status
  GET    /api/projects/<id>/events  - SSE stream of status updates
  POST   /api/projects/<id>/chat    - send message & get reply (no auto-generation)
  GET    /api/projects/<id>/chat    - get chat history
  POST   /api/projects/<id>/generate - explicitly trigger generation
  GET    /api/projects/<id>/files   - list generated files
  GET    /api/projects/<id>/file/<path> - get file content
  GET    /api/projects/<id>/preview-url - get live preview URL
  GET    /api/projects/<id>/visual-report - get visual verification results
  DELETE /api/projects/<id>         - delete project

  POST   /api/projects/analyze      - analyze requirement (legacy)
  POST   /api/projects/clarify      - generate clarification questions (legacy)
  POST   /api/projects/finalize     - finalize requirement (legacy)
"""

import json
import re
import time
from flask import Blueprint, Response, jsonify, request

from config.settings import get_settings
from src.services.llm_service import LLMService
from src.agents.stage1_requirements.interaction_agent import InteractionAgent
from src.web.services import chat_service
from src.web.services.preview_service import preview_service
from src.utils.logger import get_logger

logger = get_logger(__name__)

bp = Blueprint("projects", __name__, url_prefix="/api/projects")

# In-memory cache for clarification options to reduce repeated LLM calls.
# Keyed by (project_id, assistant_question). TTL is short (UI convenience only).
_CLARIFY_CACHE: dict = {}
_CLARIFY_CACHE_TTL_SECONDS = 300

# project_id format: proj_<date>_<time>_<hex> (e.g. proj_20250103_123456_abc123)
_PROJECT_ID_RE = re.compile(r"^proj_[a-zA-Z0-9_-]+$")


def _validate_project_id(project_id: str) -> bool:
    """Reject path traversal and invalid format. Returns True if valid."""
    if not project_id:
        return False
    if ".." in project_id or "/" in project_id or "\\" in project_id:
        return False
    return bool(_PROJECT_ID_RE.match(project_id))


def _get_task_service():
    """Lazy import to avoid circular dependency."""
    from src.web.services.task_service import TaskService
    if not hasattr(_get_task_service, "_instance"):
        _get_task_service._instance = TaskService(get_settings())
    return _get_task_service._instance


# ======================================================================
# Clarification helpers (shared by chat + UI chips)
# ======================================================================

def _extract_latest_assistant_text(messages) -> str:
    last_assistant = ""
    for m in reversed(messages or []):
        if m.get("role") == "assistant":
            last_assistant = (m.get("content") or "").strip()
            if last_assistant:
                break
    return last_assistant


def _extract_latest_user_text(messages) -> str:
    last_user = ""
    for m in reversed(messages or []):
        if m.get("role") == "user":
            last_user = (m.get("content") or "").strip()
            if last_user:
                break
    return last_user


def _extract_question_sentence(text: str) -> str:
    """Extract the last question sentence from assistant text (best-effort)."""
    text = (text or "").strip()
    if not text:
        return ""
    assistant_question = text
    for sep in ["?", "？"]:
        if sep in text:
            idx = text.rfind(sep)
            assistant_question = text[: idx + 1].strip()
            break
    return assistant_question


def _is_question(text: str) -> bool:
    t = (text or "").strip()
    return bool(t) and (t.endswith("?") or t.endswith("？"))


def _get_or_build_clarification_payload(
    *,
    settings,
    project_id: str,
    assistant_question: str,
    recent_messages,
    requirement_hint: str,
    raise_on_error: bool = False,
):
    """Return payload: {"questions":[...]} or None.

    - Chat should pass raise_on_error=False so clarification never blocks reply.
    - The legacy endpoint may pass raise_on_error=True to surface failures.
    """
    assistant_question = (assistant_question or "").strip()
    if not assistant_question or not _is_question(assistant_question):
        return None

    # Cache hit: avoid repeated LLM calls for the same question.
    cache_key = (project_id, assistant_question)
    now = time.time()
    cached = _CLARIFY_CACHE.get(cache_key)
    if cached:
        ts, payload = cached
        if (now - ts) <= _CLARIFY_CACHE_TTL_SECONDS:
            return payload
        _CLARIFY_CACHE.pop(cache_key, None)

    try:
        base = LLMService.from_settings(settings)
        # Force a fast model for UI clarification chips to improve success rate.
        fast_model_id = getattr(settings, "fast_model_for_code_gen", None) or base.model
        base_fast = base.with_model(fast_model_id)
        llm_service = LLMService(
            api_key=base_fast.api_key,
            model=base_fast.model,
            vlm_model=base_fast.vlm_model,
            max_tokens=base_fast.max_tokens,
            temperature=0.2,
            max_retries=1,
            base_url=base_fast.base_url,
            timeout=min(int(getattr(base_fast, "timeout", 120) or 120), 20),
        )
        agent = InteractionAgent(llm_service)
        t0 = time.time()
        q = agent.generate_options_for_question(
            assistant_question=assistant_question,
            recent_messages=recent_messages,
            requirement_hint=requirement_hint,
            question_id="q1",
            category="functional",
            allow_multiple=False,
            allow_other=True,
            max_tokens=256,
            temperature=0.2,
        )
        dt = time.time() - t0
        logger.info(
            "Clarification options generated",
            extra={
                "project_id": project_id,
                "model": getattr(llm_service, "model", ""),
                "base_url": getattr(llm_service, "base_url", ""),
                "elapsed_ms": int(dt * 1000),
                "question_len": len(assistant_question or ""),
                "options_count": len(getattr(q, "options", []) or []),
            },
        )
        payload = {
            "questions": [
                {
                    "id": q.id,
                    "category": q.category,
                    "question": q.question,
                    "need_options": bool(getattr(q, "need_options", True)),
                    "options": [{"id": opt.id, "label": opt.label} for opt in (q.options or [])],
                    "allow_multiple": bool(q.allow_multiple),
                    "allow_other": bool(q.allow_other),
                }
            ]
        }
        _CLARIFY_CACHE[cache_key] = (now, payload)
        return payload
    except Exception as e:
        if raise_on_error:
            raise
        logger.warning(f"Clarification option generation failed for {project_id}: {e}")
        return None


# ======================================================================
# Chat-based workflow
# ======================================================================

@bp.route("", methods=["POST"])
def create_project():
    """Create a new project.

    Body options:
      {"start_chat": true}              → chat-first (no requirement)
      {"requirement": "Build a ..."}    → legacy one-shot generation
    """
    try:
        data = request.get_json(silent=False) or {}
    except Exception:
        return jsonify({"error": "Invalid JSON in request body"}), 400
    ts = _get_task_service()

    if data.get("start_chat"):
        project_id = ts.create_chat_project()
        return jsonify({"project_id": project_id, "status": "idle"}), 201

    requirement = (data.get("requirement") or "").strip()
    if not requirement:
        return jsonify({"error": "requirement or start_chat is required"}), 400

    interactive = data.get("interactive", False)
    clarifications = data.get("clarifications", {})
    product_type = data.get("product_type") or None
    model_id = data.get("model_id") or None
    project_id = ts.create_project(
        requirement,
        interactive=interactive,
        clarifications=clarifications,
        product_type=product_type,
        model_id=model_id,
    )
    return jsonify({"project_id": project_id, "status": "pending"}), 201


@bp.route("/<project_id>/chat", methods=["POST"])
def post_chat(project_id):
    """Send a user message and get an assistant reply. Does NOT trigger generation.

    Generation is triggered explicitly via POST /api/projects/<id>/generate.
    Body: {"message": "I want a todo app with ..."}
    Returns: {"reply": "...", "project_id": "..."}
    """
    if not _validate_project_id(project_id):
        return jsonify({"error": "Invalid project id"}), 400
    try:
        data = request.get_json(silent=False) or {}
    except Exception:
        return jsonify({"error": "Invalid JSON in request body"}), 400
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "message is required"}), 400

    settings = get_settings()

    chat_service.append_message(settings, project_id, "user", message)

    messages = chat_service.get_messages(settings, project_id)

    clarification = None
    try:
        llm_service = LLMService.from_settings(settings)
        agent = InteractionAgent(llm_service)
        t0 = time.time()
        reply = agent.reply_in_chat(messages)
        dt = time.time() - t0
        logger.info(
            "Chat reply generated",
            extra={
                "project_id": project_id,
                "model": getattr(llm_service, "model", ""),
                "base_url": getattr(llm_service, "base_url", ""),
                "elapsed_ms": int(dt * 1000),
            },
        )
    except Exception as e:
        logger.warning(f"Chat reply failed for {project_id}: {e}")
        reply = "已收到你的需求。你可以继续补充说明，或点击 Generate 开始生成。"

    chat_service.append_message(settings, project_id, "assistant", reply)

    try:
        assistant_question = _extract_question_sentence(reply)
        clarification = _get_or_build_clarification_payload(
            settings=settings,
            project_id=project_id,
            assistant_question=assistant_question,
            recent_messages=messages[-12:],
            requirement_hint=_extract_latest_user_text(messages),
        )
    except Exception:
        clarification = None

    return jsonify({"reply": reply, "project_id": project_id, "clarification": clarification})


@bp.route("/<project_id>/chat/stream", methods=["POST"])
def post_chat_stream(project_id):
    """Stream assistant reply via SSE. Body: {"message": "..."}. Appends user msg first, then streams AI reply."""
    if not _validate_project_id(project_id):
        return jsonify({"error": "Invalid project id"}), 400
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "message is required"}), 400

    settings = get_settings()
    chat_service.append_message(settings, project_id, "user", message)
    messages = chat_service.get_messages(settings, project_id)

    def generate_and_persist():
        buffer = []
        try:
            llm_service = LLMService.from_settings(settings)
            agent = InteractionAgent(llm_service)
            t0 = time.time()
            for chunk in agent.reply_in_chat_stream(messages):
                buffer.append(chunk)
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            full_reply = "".join(buffer)
            chat_service.append_message(settings, project_id, "assistant", full_reply)
            clarification = None
            try:
                assistant_question = _extract_question_sentence(full_reply)
                clarification = _get_or_build_clarification_payload(
                    settings=settings,
                    project_id=project_id,
                    assistant_question=assistant_question,
                    recent_messages=messages[-12:],
                    requirement_hint=_extract_latest_user_text(messages),
                )
            except Exception:
                clarification = None
            dt = time.time() - t0
            logger.info(
                "Chat stream completed",
                extra={
                    "project_id": project_id,
                    "model": getattr(llm_service, "model", ""),
                    "base_url": getattr(llm_service, "base_url", ""),
                    "elapsed_ms": int(dt * 1000),
                    "reply_len": len(full_reply),
                },
            )
        except Exception as e:
            logger.warning(f"Chat stream failed for {project_id}: {e}")
            fallback = "已收到你的需求。你可以继续补充说明，或点击 Generate 开始生成。"
            yield f"data: {json.dumps({'chunk': fallback})}\n\n"
            chat_service.append_message(settings, project_id, "assistant", fallback)
            clarification = None
        yield f"data: {json.dumps({'done': True, 'clarification': clarification})}\n\n"

    return Response(
        generate_and_persist(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


@bp.route("/<project_id>/chat", methods=["GET"])
def get_chat(project_id):
    """Get chat history for a project."""
    if not _validate_project_id(project_id):
        return jsonify({"error": "Invalid project id"}), 400
    settings = get_settings()
    messages = chat_service.get_messages(settings, project_id)
    return jsonify({"messages": messages})


@bp.route("/<project_id>/generate", methods=["POST"])
def trigger_generate(project_id):
    """Explicitly trigger generation for a project. Body may include product_type, model_id."""
    if not _validate_project_id(project_id):
        return jsonify({"error": "Invalid project id"}), 400
    ts = _get_task_service()
    project = ts.get_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    settings = get_settings()
    messages = chat_service.get_messages(settings, project_id)
    user_messages = [m for m in messages if m.get("role") == "user"]
    if not user_messages:
        return jsonify({"error": "No messages yet. Send a message first, then click Generate."}), 400

    data = request.get_json(silent=True) or {}
    product_type = data.get("product_type") or None
    model_id = data.get("model_id") or None
    ts.enqueue_generation(project_id, product_type=product_type, model_id=model_id)
    return jsonify(
        {
            "status": "queued",
            "project_id": project_id,
            "product_type": product_type,
            "model_id": model_id,
        }
    )


# ======================================================================
# Status & files
# ======================================================================

@bp.route("", methods=["GET"])
def list_projects():
    return jsonify({"projects": _get_task_service().list_projects()})


@bp.route("/<project_id>", methods=["GET"])
def get_project(project_id):
    if not _validate_project_id(project_id):
        return jsonify({"error": "Invalid project id"}), 400
    project = _get_task_service().get_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    return jsonify(project)


@bp.route("/<project_id>/status", methods=["GET"])
def get_project_status(project_id):
    if not _validate_project_id(project_id):
        return jsonify({"error": "Invalid project id"}), 400
    status = _get_task_service().get_status(project_id)
    if not status:
        return jsonify({"error": "Project not found"}), 404
    return jsonify(status)


@bp.route("/<project_id>/files", methods=["GET"])
def list_project_files(project_id):
    if not _validate_project_id(project_id):
        return jsonify({"error": "Invalid project id"}), 400
    files = _get_task_service().list_files(project_id)
    if files is None:
        return jsonify({"error": "Project not found"}), 404
    return jsonify({"files": files})


@bp.route("/<project_id>/file/<path:file_path>", methods=["GET"])
def get_project_file(project_id, file_path):
    if not _validate_project_id(project_id):
        return jsonify({"error": "Invalid project id"}), 400
    try:
        content = _get_task_service().get_file(project_id, file_path)
    except Exception as e:
        # Binary / unreadable files should not render as garbled text in the UI
        from src.web.services.task_service import BinaryFileError
        if isinstance(e, BinaryFileError):
            return jsonify({"error": str(e)}), 415
        raise
    if content is None:
        return jsonify({"error": "File not found"}), 404
    return jsonify(content)


@bp.route("/<project_id>/preview-url", methods=["GET"])
def get_preview_url(project_id):
    """Return the live preview URL (if preview is running)."""
    if not _validate_project_id(project_id):
        return jsonify({"error": "Invalid project id"}), 400
    url = preview_service.get_preview_url(project_id)
    if not url:
        # Check if project is completed and auto-start preview
        task_service = _get_task_service()
        project = task_service.get_project(project_id)
        if project and project.get("status") == "completed":
            # Auto-start preview for completed projects
            url = preview_service.start_preview(project_id)

        error = preview_service.get_preview_error(project_id)
        return jsonify({"preview_url": url, "running": bool(url), "preview_error": error})
    return jsonify({"preview_url": url, "running": True})


@bp.route("/<project_id>/clarification-questions", methods=["GET"])
def get_clarification_questions(project_id):
    """Generate structured clarification options for the latest assistant question.

    Returns: {"questions": [{id, category, question, options:[{id,label}], allow_multiple, allow_other}]}
    """
    if not _validate_project_id(project_id):
        return jsonify({"error": "Invalid project id"}), 400
    settings = get_settings()
    messages = chat_service.get_messages(settings, project_id)
    if not messages:
        return jsonify({"questions": []})

    last_assistant = _extract_latest_assistant_text(messages)
    if not last_assistant:
        return jsonify({"questions": []})

    assistant_question = _extract_question_sentence(last_assistant)
    last_user = _extract_latest_user_text(messages)

    try:
        payload = _get_or_build_clarification_payload(
            settings=settings,
            project_id=project_id,
            assistant_question=assistant_question,
            recent_messages=messages[-12:],
            requirement_hint=last_user,
            raise_on_error=True,
        )
        if not payload:
            return jsonify({"questions": []})
        return jsonify(payload)
    except Exception as e:
        logger.exception(e)
        # Per product decision: this endpoint is LLM-backed; on failure, surface error to UI.
        return jsonify({"error": str(e) or "Failed to generate clarification options"}), 500


@bp.route("/<project_id>", methods=["DELETE"])
def delete_project(project_id):
    if not _validate_project_id(project_id):
        return jsonify({"error": "Invalid project id"}), 400
    preview_service.stop_preview(project_id)
    success = _get_task_service().delete_project(project_id)
    if not success:
        return jsonify({"error": "Project not found"}), 404
    return jsonify({"message": "Project deleted"})


# ======================================================================
# SSE - Server-Sent Events for real-time status updates
# ======================================================================

@bp.route("/<project_id>/events", methods=["GET"])
def stream_status(project_id):
    """SSE endpoint: streams status updates until completed or failed.

    Usage (JS): new EventSource('/api/projects/<id>/events')
    Each event is JSON: {"status": "...", "progress": N, "current_stage": "...", "error": ...}
    """
    if not _validate_project_id(project_id):
        return jsonify({"error": "Invalid project id"}), 400
    def generate():
        ts = _get_task_service()
        prev = None
        while True:
            status = ts.get_status(project_id)
            payload = json.dumps(status or {"status": "unknown"})
            if payload != prev:
                yield f"data: {payload}\n\n"
                prev = payload
            if status and status.get("status") in ("completed", "failed"):
                break
            time.sleep(1.5)

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ======================================================================
# Visual verification report
# ======================================================================

@bp.route("/<project_id>/visual-report", methods=["GET"])
def get_visual_report(project_id):
    """Return visual verification results if available."""
    if not _validate_project_id(project_id):
        return jsonify({"error": "Invalid project id"}), 400
    settings = get_settings()
    context_path = settings.projects_dir / project_id / "artifacts" / "context.json"
    if not context_path.exists():
        return jsonify({"error": "No context found"}), 404

    try:
        data = json.loads(context_path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.exception(e)
        return jsonify({"error": "Failed to read context"}), 500

    visual = data.get("visual_verification")
    if not visual:
        return jsonify({"available": False, "message": "Visual verification not run or not available"})

    return jsonify({"available": True, "visual_verification": visual})


# ======================================================================
# Planning & validation APIs
# ======================================================================


@bp.route("/<project_id>/plan", methods=["GET"])
def get_project_plan(project_id):
    """Return persisted EngineeringPlan for a project, if available."""
    if not _validate_project_id(project_id):
        return jsonify({"error": "Invalid project id"}), 400
    ts = _get_task_service()
    plan = ts.get_plan(project_id)
    if plan is None:
        return jsonify({"error": "Plan not found for this project"}), 404
    return jsonify(plan)


@bp.route("/<project_id>/plan", methods=["PATCH"])
def patch_project_plan(project_id):
    """Patch EngineeringPlan (safe fields only, currently task-level name/description/priority/complexity)."""
    if not _validate_project_id(project_id):
        return jsonify({"error": "Invalid project id"}), 400
    try:
        data = request.get_json(silent=False) or {}
    except Exception:
        return jsonify({"error": "Invalid JSON in request body"}), 400
    ts = _get_task_service()
    project = ts.get_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    try:
        updated = ts.update_plan(project_id, data)
    except Exception as e:
        logger.exception(e)
        err_msg = str(e) if getattr(get_settings(), "expose_error_details", False) else "Internal server error"
        return jsonify({"error": err_msg}), 500
    if updated is None:
        return jsonify({"error": "Failed to update plan (no existing plan or invalid patch)"}), 400
    return jsonify(updated)


@bp.route("/<project_id>/validation-runs", methods=["GET"])
def list_validation_runs(project_id):
    """List validation runs for a project (if any)."""
    if not _validate_project_id(project_id):
        return jsonify({"error": "Invalid project id"}), 400
    ts = _get_task_service()
    project = ts.get_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    artifacts = get_settings().projects_dir / project_id / "artifacts"
    runs_file = artifacts / "validation_runs.json"
    if not runs_file.exists():
        return jsonify({"runs": []})
    try:
        data = json.loads(runs_file.read_text(encoding="utf-8")) or []
    except Exception as e:
        logger.exception(e)
        err_msg = str(e) if getattr(get_settings(), "expose_error_details", False) else "Internal server error"
        return jsonify({"error": err_msg}), 500
    if not isinstance(data, list):
        data = []
    # sort by finished_at / started_at desc
    data = sorted(
        data,
        key=lambda r: r.get("finished_at") or r.get("started_at") or "",
        reverse=True,
    )
    return jsonify({"runs": data})


@bp.route("/<project_id>/validation-runs/<run_id>", methods=["GET"])
def get_validation_run(project_id, run_id):
    """Get details for a single validation run."""
    if not _validate_project_id(project_id):
        return jsonify({"error": "Invalid project id"}), 400
    settings = get_settings()
    artifacts = settings.projects_dir / project_id / "artifacts"
    runs_file = artifacts / "validation_runs.json"
    if not runs_file.exists():
        return jsonify({"error": "No validation runs for this project"}), 404
    try:
        data = json.loads(runs_file.read_text(encoding="utf-8")) or []
    except Exception as e:
        logger.exception(e)
        err_msg = str(e) if getattr(settings, "expose_error_details", False) else "Internal server error"
        return jsonify({"error": err_msg}), 500
    if not isinstance(data, list):
        data = []
    for run in data:
        if run.get("run_id") == run_id:
            return jsonify(run)
    return jsonify({"error": "Validation run not found"}), 404


@bp.route("/<project_id>/overview", methods=["GET"])
def get_project_overview(project_id):
    """Return aggregated overview: project status, timeline, plan & latest validation summary."""
    if not _validate_project_id(project_id):
        return jsonify({"error": "Invalid project id"}), 400
    settings = get_settings()
    ts = _get_task_service()
    project = ts.get_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    artifacts = settings.projects_dir / project_id / "artifacts"

    # Plan summary (very lightweight)
    plan_summary = None
    plan_file = artifacts / "02_engineering_plan.json"
    if plan_file.exists():
        try:
            plan_data = json.loads(plan_file.read_text(encoding="utf-8"))
            tasks = plan_data.get("tasks") or []
            arch = plan_data.get("architecture_notes") or ""
            plan_summary = f"{len(tasks)} tasks planned" + (f"; {arch[:140]}" if arch else "")
        except Exception as e:
            logger.debug("Failed to build plan summary for %s: %s", project_id, e)

    # Latest validation run (if any)
    latest_run = None
    runs_file = artifacts / "validation_runs.json"
    if runs_file.exists():
        try:
            runs = json.loads(runs_file.read_text(encoding="utf-8")) or []
            if isinstance(runs, list) and runs:
                runs = sorted(
                    runs,
                    key=lambda r: r.get("finished_at") or r.get("started_at") or "",
                    reverse=True,
                )
                latest_run = runs[0]
        except Exception as e:
            logger.debug("Failed to read validation runs for overview %s: %s", project_id, e)

    overview = {
        "project": project,
        "timeline": {
            "planning_completed_at": project.get("planning_completed_at", ""),
            "generation_completed_at": project.get("generation_completed_at", ""),
            "validation_last_run_at": project.get("validation_last_run_at", ""),
        },
        "plan_summary": plan_summary,
        "latest_validation": latest_run,
    }
    return jsonify(overview)


# ======================================================================
# Legacy analysis endpoints (kept for backward compat)
# ======================================================================

@bp.route("/analyze", methods=["POST"])
def analyze_requirement():
    data = request.get_json(silent=True) or {}
    requirement = (data.get("requirement") or "").strip()
    if not requirement:
        return jsonify({"error": "requirement is required"}), 400
    try:
        settings = get_settings()
        llm_service = LLMService.from_settings(settings)
        agent = InteractionAgent(llm_service)
        analysis = agent.analyze_requirement(requirement)
        return jsonify(analysis)
    except Exception as e:
        logger.exception(e)
        err_msg = str(e) if getattr(get_settings(), "expose_error_details", False) else "Internal server error"
        return jsonify({"error": err_msg}), 500


@bp.route("/clarify", methods=["POST"])
def clarify_requirement():
    data = request.get_json(silent=True) or {}
    requirement = (data.get("requirement") or "").strip()
    if not requirement:
        return jsonify({"error": "requirement is required"}), 400
    try:
        settings = get_settings()
        llm_service = LLMService.from_settings(settings)
        agent = InteractionAgent(llm_service)
        questions = agent.generate_clarification_questions(requirement)
        return jsonify(
            {
                "questions": [
                    {
                        "id": q.id,
                        "category": q.category,
                        "question": q.question,
                        "options": [
                            {"id": opt.id, "label": opt.label}
                            for opt in (q.options or [])
                        ],
                        "allow_multiple": bool(q.allow_multiple),
                        "allow_other": bool(q.allow_other),
                    }
                    for q in questions
                ]
            }
        )
    except Exception as e:
        logger.exception(e)
        err_msg = str(e) if getattr(get_settings(), "expose_error_details", False) else "Internal server error"
        return jsonify({"error": err_msg}), 500


@bp.route("/finalize", methods=["POST"])
def finalize_requirement():
    data = request.get_json(silent=True) or {}
    requirement = (data.get("requirement") or "").strip()
    clarifications = data.get("clarifications", {})
    if not requirement:
        return jsonify({"error": "requirement is required"}), 400
    try:
        settings = get_settings()
        llm_service = LLMService.from_settings(settings)
        agent = InteractionAgent(llm_service)
        questions = [
            type("Question", (), {"id": f"q{i}", "question": q})()
            for i, q in enumerate(clarifications.keys(), 1)
        ]
        final_req = agent._generate_final_requirements(requirement, questions, clarifications)
        return jsonify({
            "title": final_req.title,
            "description": final_req.description,
            "features": [
                {"id": f.id, "name": f.name, "description": f.description, "priority": f.priority}
                for f in final_req.features
            ],
            "constraints": final_req.constraints,
            "target_users": final_req.target_users,
            "data_requirements": final_req.data_requirements,
        })
    except Exception as e:
        logger.exception(e)
        err_msg = str(e) if getattr(get_settings(), "expose_error_details", False) else "Internal server error"
        return jsonify({"error": err_msg}), 500
