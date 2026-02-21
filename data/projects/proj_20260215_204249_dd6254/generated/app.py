from flask import Flask
from app import controllers
from app.database import init_db, engine
from app.routes import assembly_bp

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static', static_url_path='/static')

    # Initialize the database
    init_db(engine)

    # Register blueprints
    app.register_blueprint(controllers.problem_controller.problem_bp)
    app.register_blueprint(controllers.user_controller.user_bp)
    app.register_blueprint(controllers.solution_controller.solution_bp)
    app.register_blueprint(assembly_bp)

    # Home route
    @app.route('/')
    def home():
        return app.send_static_file('index.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)