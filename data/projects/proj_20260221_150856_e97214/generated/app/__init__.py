"""
Flask 应用工厂
框架代码，不包含具体业务逻辑
"""
import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from app_config import DevelopmentConfig

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
        app.config.from_object(DevelopmentConfig)

    # 初始化扩展
    db.init_app(app)

    # CORS 支持
    CORS(app)

    # ==== 在这里注册业务蓝图 ====
    from app.routes.blog_routes import blog_bp
    app.register_blueprint(blog_bp, url_prefix='/api/blogs')
    # ==============================

    # 首页路由
    @app.route('/')
    def index():
        return render_template('index.html')

    # 博客列表页面路由
    @app.route('/blogs')
    def blog_list():
        return render_template('blog_list.html')

    # 健康检查
    @app.route('/health')
    def health():
        return {'status': 'ok'}

    # 博客详情页面路由
    @app.route('/blogs/<int:id>')
    def blog_detail(id):
        return render_template('blog_detail.html', blog=Blog.query.get_or_404(id))

    # 博客创建页面路由
    @app.route('/blogs/new')
    def blog_create():
        return render_template('blog_create.html')

    # 博客编辑页面路由
    @app.route('/blogs/<int:id>/edit')
    def blog_edit(id):
        return render_template('blog_edit.html', blog=Blog.query.get_or_404(id))

    # 创建数据库表
    with app.app_context():
        db.create_all()

    return app
