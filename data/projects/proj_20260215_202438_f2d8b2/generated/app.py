from flask import Flask, render_template
from app.database import db
from app.routes import register_blueprints

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    register_blueprints(app)

    @app.route('/')
    def index():
        return render_template('index.html')

    return app