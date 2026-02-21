"""App package."""

from flask import Flask

app = Flask(__name__)

# Import routes to register them
from app import routes
app.register_blueprint(routes.routes)

__all__ = ['app']
