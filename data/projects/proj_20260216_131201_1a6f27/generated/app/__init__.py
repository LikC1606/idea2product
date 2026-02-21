from flask import Flask
from app.database import init_db, SessionLocal
from app.routes import routes

def create_app():
    app = Flask(__name__)
    app.register_blueprint(routes)
    init_db()
    return app