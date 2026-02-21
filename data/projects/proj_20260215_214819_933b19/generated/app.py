from flask import Flask
from app.database import db
from app.routes import register_routes

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static', static_url_path='/static')

    # Configurations
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
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
        return render_template('index.html')

    return app

if __name__ == "__main__":
    app = create_app()
    print(114514)
    app.run(debug=True)