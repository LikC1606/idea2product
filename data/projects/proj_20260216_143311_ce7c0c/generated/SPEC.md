# Flask 基础框架模板
# 此文件定义了标准的 Flask 项目结构
# AI 可以读取此文件作为参考，生成符合框架规范的代码

## 文件结构

flask_base/
├── app/
│   ├── __init__.py      # 应用工厂 - 在这里注册蓝图
│   ├── models/
│   │   └── __init__.py  # 模型包
│   └── routes/
│       └── __init__.py  # 路由包
├── templates/
│   └── index.html       # 主页模板
├── config.py            # 多环境配置
├── app.py               # 入口文件
├── requirements.txt     # 依赖
└── .env                # 环境变量

## 关键接口规范

### 1. 模型规范 (app/models/__init__.py)
```python
from app import db

class ModelName(db.Model):
    __tablename__ = 'table_name'

    id = db.Column(db.Integer, primary_key=True)
    # 其他字段...

    def to_dict(self):
        return {
            'id': self.id,
            # 其他字段...
        }
```

### 2. 路由规范 (app/routes/xxx.py)
```python
from flask import Blueprint, request, jsonify
from app import db
from app.models.xxx import ModelName

xxx_bp = Blueprint('xxx', __name__)

@xxx_bp.route('/xxx', methods=['GET'])
def get_xxx():
    items = ModelName.query.all()
    return jsonify([item.to_dict() for item in items])

@xxx_bp.route('/xxx', methods=['POST'])
def create_xxx():
    data = request.get_json()
    item = ModelName(字段=data['字段'])
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201
```

### 3. 注册蓝图规范 (app/__init__.py)
```python
# 导入蓝图
from app.routes.xxx import xxx_bp

# 注册蓝图
app.register_blueprint(xxx_bp, url_prefix='/api')
```

### 4. 前端模板规范 (templates/xxx.html)
```html
<!DOCTYPE html>
<html>
<head>
    <title>Title</title>
    <script>
        const API_BASE = '/api';
        // 使用 fetch 调用 API
    </script>
</head>
<body>
    <!-- 页面内容 -->
</body>
</html>
```

## 常见修改文件

1. **app/__init__.py** - 注册新蓝图
2. **app/models/__init__.py** - 添加新模型导入
3. **app/routes/__init__.py** - 添加新路由导入
4. **app/routes/xxx.py** - 新建路由文件
5. **app/models/xxx.py** - 新建模型文件
6. **templates/xxx.html** - 新建前端页面
7. **config.py** - 添加配置项（可选）
8. **requirements.txt** - 添加依赖（可选）
