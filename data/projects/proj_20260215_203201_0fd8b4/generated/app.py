from flask import Flask
from app.routes import create_app
from app.controllers.problem_controller import problem_bp
from app.controllers.user_controller import user_bp
from app.controllers.solution_controller import solution_bp
from app.database import init_db

# Initialize Flask application
app = create_app()

# Register blueprints
app.register_blueprint(problem_bp)
app.register_blueprint(user_bp)
app.register_blueprint(solution_bp)

# Initialize the database
with app.app_context():
    init_db()

# Run the application
if __name__ == "__main__":
    app.run(debug=True)