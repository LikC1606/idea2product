"""Web Backend - Flask Application."""

import os
import atexit
from pathlib import Path
from flask import Flask, jsonify, render_template, send_from_directory, request
from flask_cors import CORS
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge

PROJECT_ROOT = Path(__file__).parent.parent.parent


FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"

_MAX_JSON_BODY_BYTES = 64 * 1024  # 64KB for chat / create project bodies

app = Flask(__name__, template_folder=str(PROJECT_ROOT / "templates"))
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")

CORS(app)

from src.web.api import projects
app.register_blueprint(projects.bp)


@app.before_request
def check_request_size():
    """Reject oversized JSON bodies for API POST endpoints."""
    if request.method != "POST" or not request.path.startswith("/api/"):
        return
    cl = request.content_length
    if cl is not None and cl > _MAX_JSON_BODY_BYTES:
        raise RequestEntityTooLarge(f"Request body too large (max {_MAX_JSON_BODY_BYTES} bytes)")


@app.errorhandler(BadRequest)
def handle_bad_request(e):
    """Return JSON for invalid request body (e.g. malformed JSON)."""
    if request.path.startswith("/api/"):
        msg = str(e.description) if e.description else "Invalid request"
        if "JSON" in msg or "json" in str(e).lower():
            return jsonify({"error": "Invalid JSON in request body"}), 400
        return jsonify({"error": msg}), 400
    return e


@app.errorhandler(RequestEntityTooLarge)
def handle_request_too_large(e):
    """Return JSON for oversized request body."""
    if request.path.startswith("/api/"):
        return jsonify({"error": "Request body too large"}), 413
    return e


@app.errorhandler(422)
def handle_validation_error(e):
    """Return JSON for Pydantic/validation errors (422 Unprocessable Entity)."""
    if request.path.startswith("/api/"):
        return jsonify({"error": "Validation error", "details": str(e)}), 422
    return e


@app.route("/api/projects/<project_id>/generate", methods=["POST"])
def trigger_generate_app(project_id):
    """Generate endpoint - at app level to ensure routing works."""
    from src.web.api.projects import _get_task_service
    from src.web.services import chat_service
    from config.settings import get_settings

    ts = _get_task_service()
    project = ts.get_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    messages = chat_service.get_messages(get_settings(), project_id)
    user_messages = [m for m in messages if m.get("role") == "user"]
    if not user_messages:
        return jsonify({"error": "No messages yet. Send a message first, then click Generate."}), 400

    ts.enqueue_generation(project_id)
    return jsonify({"status": "queued", "project_id": project_id})


@app.route("/api/health")
def health_check():
    """Health check: verifies service is up and critical resources are available."""
    checks = {"config": True, "projects_dir_writable": True}
    try:
        from config.settings import get_settings
        settings = get_settings()
        try:
            settings.projects_dir.mkdir(parents=True, exist_ok=True)
            test_file = settings.projects_dir / ".health_write_test"
            test_file.touch()
            test_file.unlink()
        except OSError:
            checks["projects_dir_writable"] = False
    except Exception:
        checks["config"] = False

    healthy = checks["config"] and checks["projects_dir_writable"]
    status_code = 200 if healthy else 503
    return jsonify({
        "status": "healthy" if healthy else "degraded",
        "service": "idea2product-api",
        "checks": checks,
    }), status_code


@app.route("/")
def index():
    if FRONTEND_DIST.exists() and (FRONTEND_DIST / "index.html").exists():
        return send_from_directory(FRONTEND_DIST, "index.html")
    return render_template("index.html")


@app.route("/assets/<path:path>")
def frontend_assets(path):
    """Serve Vite-built frontend assets from frontend/dist/assets."""
    if FRONTEND_DIST.exists():
        assets_dir = FRONTEND_DIST / "assets"
        if assets_dir.exists():
            return send_from_directory(assets_dir, path)
    return "", 404


@app.errorhandler(404)
def handle_404(e):
    """Return JSON for API 404 instead of HTML."""
    if request.path.startswith("/api/"):
        return jsonify({"error": "Not found"}), 404
    if FRONTEND_DIST.exists() and (FRONTEND_DIST / "index.html").exists():
        return send_from_directory(FRONTEND_DIST, "index.html")
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def handle_500(e):
    """Return JSON for 500 errors so frontend gets valid JSON instead of HTML."""
    return jsonify({"error": "Internal server error"}), 500


@app.errorhandler(405)
def handle_405(e):
    """Return JSON for 405 Method Not Allowed instead of HTML."""
    if request.path.startswith("/api/"):
        return jsonify({"error": "Method not allowed"}), 405
    raise e


def create_app():
    return app


def run_server(host=None, port=None, debug=False):
    host = host or os.environ.get("HOST", "0.0.0.0")
    port = port or int(os.environ.get("PORT", "8080"))
    app.run(host=host, port=port, debug=debug, use_reloader=False)


def _cleanup():
    """Stop all preview subprocesses on exit."""
    try:
        from src.web.services.preview_service import preview_service
        preview_service.stop_all()
    except Exception as ex:
        import logging
        logging.getLogger(__name__).debug("Cleanup stop_all failed: %s", ex)


atexit.register(_cleanup)

if __name__ == "__main__":
    run_server(debug=False)
