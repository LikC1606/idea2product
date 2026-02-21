# 笔记应用 (Notes API)

工业级 Flask REST API 项目结构。

## 项目结构

```
test_website/
├── app/
│   ├── __init__.py      # 应用工厂
│   ├── models/
│   │   ├── __init__.py
│   │   └── note.py      # 笔记模型
│   └── routes/
│       ├── __init__.py
│       └── notes.py    # 笔记API路由
├── templates/
│   └── index.html       # 前端页面
├── config.py            # 配置文件
├── app.py               # 入口文件
├── requirements.txt     # 依赖
├── .env                 # 环境变量
└── .gitignore          # Git忽略文件
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境

复制环境变量文件（可选）：

```bash
cp .env.example .env
```

### 3. 启动服务

开发模式：

```bash
python app.py
```

或使用 flask 命令：

```bash
flask run
```

### 4. 访问应用

- 前端：http://localhost:5000
- 健康检查：http://localhost:5000/health

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/notes | 获取所有笔记 |
| POST | /api/notes | 创建笔记 |
| GET | /api/notes/:id | 获取单个笔记 |
| PUT | /api/notes/:id | 更新笔记 |
| DELETE | /api/notes/:id | 删除笔记 |

## 生产环境部署

使用 Gunicorn：

```bash
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

或使用 Docker（需要创建 Dockerfile）：
