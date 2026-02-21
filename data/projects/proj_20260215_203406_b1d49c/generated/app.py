from flask import Flask
from app.controllers.problem_controller import problem_bp
from app.controllers.user_controller import user_bp
from app.controllers.solution_controller import solution_bp
from app.routes import app as main_routes
from app import create_app

def register_blueprints(app):
    app.register_blueprint(problem_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(solution_bp)
    app.register_blueprint(main_routes)

def main():
    app = create_app()
    register_blueprints(app)
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    main()