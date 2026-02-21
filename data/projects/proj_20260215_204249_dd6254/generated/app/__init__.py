from flask import Flask, render_template
from .routes import register_routes
from .database import init_db, engine

def create_app():
    # Initialize Flask app
    app = Flask(__name__, template_folder='../templates', static_folder='../static', static_url_path='/static')

    # Configure database
    init_db(engine)

    # Register routes
    register_routes(app)

    # Define home route
    @app.route('/')
    def home():
        return render_template('index.html')

    return app