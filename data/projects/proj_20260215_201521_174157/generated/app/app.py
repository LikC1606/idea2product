from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize the Flask app
app = Flask(__name__)

# Configuration for SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy and Migrate
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Import and register blueprints
from app.controllers.problem_controller import problem_bp
from app.controllers.user_controller import user_bp

app.register_blueprint(problem_bp)
app.register_blueprint(user_bp)

# Application entry point
if __name__ == '__main__':
    app.run(debug=True)