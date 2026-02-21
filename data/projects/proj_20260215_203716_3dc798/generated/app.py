from flask import Flask
from app.routes import routes_bp
from app.controllers.problem_controller import problem_bp
from app.controllers.user_controller import user_bp
from app.controllers.solution_controller import solution_bp
from app.database import init_db

def create_app():
    # Initialize the Flask app
    app = Flask(
        __name__, 
        template_folder='../templates', 
        static_folder='../static', 
        static_url_path='/static'
    )

    # Configure database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///acm_platform.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    init_db()

    # Register blueprints
    app.register_blueprint(routes_bp)
    app.register_blueprint(problem_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(solution_bp)

    # Home route
    @app.route('/')
    def home():
        return app.send_static_file('index.html')

    return app

# Run the app
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)