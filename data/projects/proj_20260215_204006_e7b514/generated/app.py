from flask import Flask
from app.database import init_db
from app.controllers.problem_controller import problem_bp
from app.controllers.user_controller import user_bp
from app.controllers.solution_controller import solution_bp
from app.routes import register_routes
from app.__init__ import create_app

# Initialize Flask app
app = create_app()

# Register blueprints for controllers
app.register_blueprint(problem_bp)
app.register_blueprint(user_bp)
app.register_blueprint(solution_bp)

# Initialize database
with app.app_context():
    init_db()

# Register additional routes
register_routes(app)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)