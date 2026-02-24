"""Web Backend - Flask Application."""

import os
import atexit
from pathlib import Path
from flask import Flask, jsonify, render_template
from flask_cors import CORS

PROJECT_ROOT = Path(__file__).parent.parent.parent

from config.settings import Settings

app = Flask(__name__, template_folder=str(PROJECT_ROOT / "templates"))
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")

CORS(app)

from src.web.api import projects
app.register_blueprint(projects.bp)


@app.route("/api/health")
def health_check():
    return jsonify({"status": "healthy", "service": "idea2product-api"})


@app.route("/")
def index():
    return render_template("index.html")


def create_app():
    return app


def run_server(host="127.0.0.1", port=8080, debug=False):
    app.run(host=host, port=port, debug=debug, use_reloader=False)


def _cleanup():
    """Stop all preview subprocesses on exit."""
    try:
        from src.web.services.preview_service import preview_service
        preview_service.stop_all()
    except Exception:
        pass


atexit.register(_cleanup)

if __name__ == "__main__":
    run_server(debug=False)
