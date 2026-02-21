from flask import Flask
from app.database import db
from app.routes import register_routes

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static', static_url_path='/static')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///note_taking_app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize database
    db.init_app(app)
    with app.app_context():
        db.create_all()

    # Register routes
    register_routes(app)

    # Home route
    @app.route('/')
    def home():
        return app.send_static_file('index.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)