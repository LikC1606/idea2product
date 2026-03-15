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

# Lightweight startup config checks (warnings only; do not block server start)
try:
    from config.settings import load_settings_lenient, validate_startup_config_log_warnings
    from src.utils.env_check import run_startup_env_check
    _startup_settings = load_settings_lenient()
    validate_startup_config_log_warnings(_startup_settings)
    run_startup_env_check(_startup_settings)
except Exception:
    pass


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


@app.route("/api/options/models", methods=["GET"])
def get_options_models():
    """Return available LLM models from registry for user selection (product_type, model override)."""
    try:
        from config.settings import get_settings
        from src.services.model_registry import ModelRegistry

        settings = get_settings()
        registry = ModelRegistry.load(settings.models_registry_path)
        models = [
            {
                "id": m.id,
                "provider": m.provider,
                "capabilities": m.capabilities,
                "roles": m.roles,
                "cost_tier": m.cost_tier,
                "max_tokens": m.max_tokens,
            }
            for m in registry.models
        ]
        return jsonify({"models": models})
    except Exception as e:
        return jsonify({"error": str(e), "models": []}), 500


@app.route("/api/health")
def health_check():
    """Health check: verifies service is up and critical resources are available.
    Query: check_llm=1 to run LLM reachability check (only if HEALTH_CHECK_LLM=true)."""
    try:
        from config.settings import get_settings
        from src.utils.env_check import run_env_checks
        settings = get_settings()
        check_llm = request.args.get("check_llm") in ("1", "true", "yes")
        result = run_env_checks(settings, check_llm=check_llm)
        checks = result.get("checks", {})
        healthy = result.get("ok", False)
        status_code = 200 if healthy else 503
        payload = {
            "status": "healthy" if healthy else "degraded",
            "service": "idea2product-api",
            "checks": checks,
        }
        if result.get("warnings"):
            payload["warnings"] = result["warnings"]
        return jsonify(payload), status_code
    except Exception as e:
        from src.utils.logger import get_logger
        get_logger(__name__).exception("Health check failed")
        return jsonify({
            "status": "degraded",
            "service": "idea2product-api",
            "checks": {"config": False},
            "error": str(e),
        }), 503


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
    """Return JSON for 500 errors. Log full exception; expose details only when configured.
    When the exception is StageExecutionError, always include error_code and failed_stage
    so the frontend can show 'Stage N failed' without exposing full details."""
    from src.utils.logger import get_logger
    get_logger(__name__).exception("Unhandled exception")
    msg = "Internal server error"
    payload = {"error": msg}
    if request.path.startswith("/api/"):
        try:
            from config.settings import get_settings
            from src.core.exceptions import StageExecutionError as SEE
            exc = e
            while exc:
                if isinstance(exc, SEE):
                    payload["error_code"] = f"STAGE_{getattr(exc, 'stage', 0)}_FAILED"
                    payload["failed_stage"] = getattr(exc, "stage", None)
                    if get_settings().expose_error_details:
                        payload["error"] = str(exc) if exc else msg
                    break
                exc = getattr(exc, "__cause__", None)
            if not payload.get("error_code") and get_settings().expose_error_details:
                payload["error"] = str(e) if e else msg
        except Exception:
            pass
        return jsonify(payload), 500
    return jsonify(payload), 500


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
