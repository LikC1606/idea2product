"""
Flask 应用工厂
框架代码，不包含具体业务逻辑
"""
import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import fetch_config

db = SQLAlchemy()

# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_app(config_name=None):
    """应用工厂函数"""
    # 设置模板路径
    template_dir = os.path.join(BASE_DIR, 'templates')
    app = Flask(__name__, template_folder=template_dir)

    # 加载配置
    if config_name:
        app.config.from_object(config_name)
    else:
        app.config.from_object(fetch_config())

    # 初始化扩展
    db.init_app(app)

    # CORS 支持
    CORS(app)

    # ==== 在这里注册业务蓝图 ====
    # from app.routes.xxx import xxx_bp
    # app.register_blueprint(xxx_bp, url_prefix='/api')
    # ==============================

    from app.routes.blogs import blogs_bp
    app.register_blueprint(blogs_bp, url_prefix='/api')

    # 首页路由
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/blogs')
    def blogs():
        return render_template('blog.html')

    # 健康检查
    @app.route('/health')
    def health():
        return {'status': 'ok'}

    # 创建数据库表
    with app.app_context():
        db.create_all()

    return app
