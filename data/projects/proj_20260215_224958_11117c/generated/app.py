from flask import Flask, render_template
from app.notes import notes_blueprint
from app.database import db

def create_app():
    app = Flask(__name__)
    app.secret_key = "your_secret_key_here"

    # Register blueprints
    app.register_blueprint(notes_blueprint)

    # Initialize database
    with app.app_context():
        db.create_all()

    # Home route
    @app.route('/')
    def home():
        return render_template('index.html')

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)