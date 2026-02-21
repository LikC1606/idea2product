from flask import Flask
from app.database import init_db
from app.controllers.problem_controller import problem_bp
from app.controllers.user_controller import user_bp
from app.controllers.solution_controller import solution_bp
from app.routes import routes_bp

def create_app():
    app = Flask(
        __name__,
        template_folder='../templates',
        static_folder='../static',
        static_url_path='/static'
    )

    # Initialize database
    init_db()

    # Register Blueprints
    app.register_blueprint(problem_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(solution_bp)
    app.register_blueprint(routes_bp)

    # Home route
    @app.route('/')
    def home():
        return app.send_static_file('index.html')

    return app