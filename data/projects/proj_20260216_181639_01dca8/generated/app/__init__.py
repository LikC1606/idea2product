from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from config import get_config

# Extensions

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')

    config_class = get_config()
    app.config.from_object(config_class)

    db.init_app(app)

    # Register blueprints
    from app.routes.notes import notes_bp
    app.register_blueprint(notes_bp, url_prefix='/api')

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/notes')
    def notes():
        return render_template('notes.html')

    return app