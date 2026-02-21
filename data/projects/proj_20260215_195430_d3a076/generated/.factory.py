from flask import Flask, render_template
from app.database import db
from app.blueprints.problem import problem_bp
from app.blueprints.user import user_bp
from app.blueprints.auth import auth_bp
from app.errors import handle_404
from app.extensions import migrate
from app.config import Config

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(problem_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)

    app.register_error_handler(404, handle_404)

    @app.route('/')
    def index():
        return render_template('index.html')

    return app