from flask import Flask
from app.database import db
from app.routes import problem_blueprint, user_blueprint, solution_blueprint

def create_app():
    app = Flask(__name__)
    
    # Configuration can be added here
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize database
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(problem_blueprint, url_prefix='/problems')
    app.register_blueprint(user_blueprint, url_prefix='/users')
    app.register_blueprint(solution_blueprint, url_prefix='/solutions')

    return app