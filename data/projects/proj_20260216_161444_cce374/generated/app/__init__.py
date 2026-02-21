from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import get_config

db = SQLAlchemy()

# 在 db 定义后才能导入使用 db 的模块
from app.routes.notes import notes_bp

def create_app():
    app = Flask(__name__)

    # 加载配置
    config_class = get_config()
    app.config.from_object(config_class)

    db.init_app(app)
    CORS(app)

    app.register_blueprint(notes_bp, url_prefix='/api')

    @app.route('/')
    def index():
        return app.send_static_file('index.html')

    return app