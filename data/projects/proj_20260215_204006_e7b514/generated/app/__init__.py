from flask import Flask, render_template
from app.database import init_db
from app.routes import register_routes
from app.controllers.problem_controller import problem_bp
from app.controllers.user_controller import user_bp
from app.controllers.solution_controller import solution_bp

def create_app():
    # Initialize Flask app
    app = Flask(
        __name__, 
        template_folder='../templates', 
        static_folder='../static', 
        static_url_path='/static'
    )

    # Initialize the database
    init_db()

    # Register blueprints
    app.register_blueprint(problem_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(solution_bp)
    
    # Register additional routes
    register_routes(app)

    # Home route
    @app.route('/')
    def home():
        return render_template('index.html')

    return app