from flask import Flask
from app.database import db
from app.routes import assembly_bp
from app.controllers.problem_controller import problem_bp
from app.controllers.user_controller import user_bp
from app.controllers.solution_controller import solution_bp

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static', static_url_path='/static')

    # Configurations
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'  # Change to your database URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize database
    db.init_app(app)
    with app.app_context():
        db.create_all()

    # Register blueprints
    app.register_blueprint(assembly_bp)
    app.register_blueprint(problem_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(solution_bp)

    # Home route
    @app.route('/')
    def home():
        return "Welcome to the Simple Note-Taking App!"  # Replace with a proper render_template for index.html

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)