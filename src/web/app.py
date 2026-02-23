"""Web Backend - Flask Application."""

import os
import threading
from pathlib import Path
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

from config.settings import Settings
from src.web.services.task_service import TaskService

# Initialize Flask app
app = Flask(__name__, template_folder=str(PROJECT_ROOT / 'templates'))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Enable CORS
CORS(app)

# Initialize services
settings = Settings()
task_service = TaskService(settings)

# Import and register blueprints
from src.web.api import projects
app.register_blueprint(projects.bp)

# Health check endpoint
@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'idea2product-api'
    })

# Root endpoint - serve HTML
@app.route('/')
def index():
    """Root endpoint - serve the frontend."""
    return render_template('index.html')


def create_app():
    """Application factory."""
    return app


def run_server(host='0.0.0.0', port=5000, debug=False):
    """Run the Flask server."""
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_server(debug=False)
