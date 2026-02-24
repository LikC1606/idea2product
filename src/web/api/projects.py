"""Project API Blueprint.

Endpoints:
  POST   /api/projects              - create project (legacy or chat-first)
  GET    /api/projects              - list projects
  GET    /api/projects/<id>         - project details
  GET    /api/projects/<id>/status  - generation status
  GET    /api/projects/<id>/events  - SSE stream of status updates
  POST   /api/projects/<id>/chat    - send message & get reply (auto-triggers generation)
  GET    /api/projects/<id>/chat    - get chat history
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
import time
from flask import Blueprint, Response, jsonify, request

from config.settings import Settings
from src.services.llm_service import LLMService
from src.agents.stage1_requirements.interaction_agent import InteractionAgent
from src.web.services import chat_service
from src.web.services.preview_service import preview_service

bp = Blueprint("projects", __name__, url_prefix="/api/projects")


def _get_task_service():
    """Lazy import to avoid circular dependency."""
    from src.web.services.task_service import TaskService
    if not hasattr(_get_task_service, "_instance"):
        _get_task_service._instance = TaskService(Settings())
    return _get_task_service._instance


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
    data = request.get_json(silent=True) or {}
    ts = _get_task_service()

    if data.get("start_chat"):
        project_id = ts.create_chat_project()
        return jsonify({"project_id": project_id, "status": "idle"}), 201

    requirement = data.get("requirement", "")
    if not requirement:
        return jsonify({"error": "requirement or start_chat is required"}), 400

    interactive = data.get("interactive", False)
    clarifications = data.get("clarifications", {})
    project_id = ts.create_project(requirement, interactive=interactive, clarifications=clarifications)
    return jsonify({"project_id": project_id, "status": "pending"}), 201


@bp.route("/<project_id>/chat", methods=["POST"])
def post_chat(project_id):
    """Send a user message, get an assistant reply, auto-trigger generation.

    Body: {"message": "I want a todo app with ..."}
    Returns: {"reply": "...", "project_id": "..."}
    """
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "message is required"}), 400

    settings = Settings()

    chat_service.append_message(settings, project_id, "user", message)

    messages = chat_service.get_messages(settings, project_id)

    try:
        llm_service = LLMService.from_settings(settings)
        agent = InteractionAgent(llm_service)
        reply = agent.reply_in_chat(messages)
    except Exception as e:
        reply = f"收到你的需求，正在后台生成中。({e})"

    chat_service.append_message(settings, project_id, "assistant", reply)

    ts = _get_task_service()
    ts.enqueue_generation(project_id)

    return jsonify({"reply": reply, "project_id": project_id})


@bp.route("/<project_id>/chat", methods=["GET"])
def get_chat(project_id):
    """Get chat history for a project."""
    settings = Settings()
    messages = chat_service.get_messages(settings, project_id)
    return jsonify({"messages": messages})


# ======================================================================
# Status & files
# ======================================================================

@bp.route("", methods=["GET"])
def list_projects():
    return jsonify({"projects": _get_task_service().list_projects()})


@bp.route("/<project_id>", methods=["GET"])
def get_project(project_id):
    project = _get_task_service().get_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    return jsonify(project)


@bp.route("/<project_id>/status", methods=["GET"])
def get_project_status(project_id):
    status = _get_task_service().get_status(project_id)
    if not status:
        return jsonify({"error": "Project not found"}), 404
    return jsonify(status)


@bp.route("/<project_id>/files", methods=["GET"])
def list_project_files(project_id):
    files = _get_task_service().list_files(project_id)
    if files is None:
        return jsonify({"error": "Project not found"}), 404
    return jsonify({"files": files})


@bp.route("/<project_id>/file/<path:file_path>", methods=["GET"])
def get_project_file(project_id, file_path):
    content = _get_task_service().get_file(project_id, file_path)
    if content is None:
        return jsonify({"error": "File not found"}), 404
    return jsonify(content)


@bp.route("/<project_id>/preview-url", methods=["GET"])
def get_preview_url(project_id):
    """Return the live preview URL (if preview is running)."""
    url = preview_service.get_preview_url(project_id)
    if not url:
        return jsonify({"preview_url": None, "running": False})
    return jsonify({"preview_url": url, "running": True})


@bp.route("/<project_id>", methods=["DELETE"])
def delete_project(project_id):
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
    settings = Settings()
    context_path = settings.projects_dir / project_id / "artifacts" / "context.json"
    if not context_path.exists():
        return jsonify({"error": "No context found"}), 404

    try:
        data = json.loads(context_path.read_text(encoding="utf-8"))
    except Exception:
        return jsonify({"error": "Failed to read context"}), 500

    visual = data.get("visual_verification")
    if not visual:
        return jsonify({"available": False, "message": "Visual verification not run or not available"})

    return jsonify({"available": True, "visual_verification": visual})


# ======================================================================
# Legacy analysis endpoints (kept for backward compat)
# ======================================================================

@bp.route("/analyze", methods=["POST"])
def analyze_requirement():
    data = request.get_json(silent=True) or {}
    requirement = data.get("requirement", "")
    if not requirement:
        return jsonify({"error": "requirement is required"}), 400
    try:
        settings = Settings()
        llm_service = LLMService.from_settings(settings)
        agent = InteractionAgent(llm_service)
        analysis = agent.analyze_requirement(requirement)
        return jsonify(analysis)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/clarify", methods=["POST"])
def clarify_requirement():
    data = request.get_json(silent=True) or {}
    requirement = data.get("requirement", "")
    if not requirement:
        return jsonify({"error": "requirement is required"}), 400
    try:
        settings = Settings()
        llm_service = LLMService.from_settings(settings)
        agent = InteractionAgent(llm_service)
        questions = agent.generate_clarification_questions(requirement)
        return jsonify({
            "questions": [
                {"id": q.id, "category": q.category, "question": q.question}
                for q in questions
            ]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/finalize", methods=["POST"])
def finalize_requirement():
    data = request.get_json(silent=True) or {}
    requirement = data.get("requirement", "")
    clarifications = data.get("clarifications", {})
    if not requirement:
        return jsonify({"error": "requirement is required"}), 400
    try:
        settings = Settings()
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
        return jsonify({"error": str(e)}), 500
