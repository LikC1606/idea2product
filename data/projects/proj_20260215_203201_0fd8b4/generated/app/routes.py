from flask import Flask
from app.controllers.problem_controller import problem_bp
from app.controllers.user_controller import user_bp
from app.controllers.solution_controller import solution_bp
from app.database import init_db

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static', static_url_path='/static')

    # Register Blueprints
    app.register_blueprint(problem_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(solution_bp)

    # Initialize database
    init_db()

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)