# Flask Base Framework Template
# This file defines the standard Flask project structure
# AI can read this file as reference to generate code that follows framework conventions

## File Structure

flask_base/
├── app/
│   ├── __init__.py      # App factory - register blueprints here
│   ├── models/
│   │   └── __init__.py  # Models package
│   ├── routes/
│   │   └── __init__.py  # Routes package
│   ├── static/          # Static files served by Flask
│   │   └── uploads/     # Uploaded files (images, attachments)
│   │       └── .gitkeep
│   └── utils/           # Utility functions
├── templates/
│   └── index.html       # Frontend template
├── config.py            # Multi-environment config
├── app.py               # Entry point
├── requirements.txt     # Dependencies
└── .env                # Environment variables

## Static Files

Flask automatically serves static files from `app/static/`. All CSS, JS, images, and uploaded files should be stored here.

- **CSS/JS/Images**: Store in `app/static/` subdirectories (e.g., `app/static/css/`, `app/static/images/`)
- **Uploaded files**: Store in `app/static/uploads/` - Flask serves these at `/static/uploads/<filename>`
- **URL format**: Use `/static/<path>` in HTML templates to reference static files

Example for image upload:
```python
UPLOAD_FOLDER = 'app/static/uploads'

def save_image(image):
    # Save to app/static/uploads/
    filename = secure_filename(image.filename)
    image.save(os.path.join(UPLOAD_FOLDER, filename))
    # Return URL path: /static/uploads/<filename>
    return '/static/uploads/' + filename
```

## Key Interface Specifications Example

**Note**: The package name "app" is the ONLY valid name. Do NOT use myapp, application, or any variant.

### 1. Model Specification (app/models/__init__.py)
```python
from app import db

class ModelName(db.Model):
    __tablename__ = 'table_name'

    id = db.Column(db.Integer, primary_key=True)
    # Other fields...

    def to_dict(self):
        return {
            'id': self.id,
            # Other fields...
        }
```

### 2. Route Specification (app/routes/xxx.py)
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
    item = ModelName(field=data['field'])
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201
```

### 3. Blueprint Registration Specification (app/__init__.py)
```python
# Import blueprints
from app.routes.xxx import xxx_bp

# Register blueprints
app.register_blueprint(xxx_bp, url_prefix='/api')
```

### 4. Frontend Template Specification (templates/xxx.html)
```html
<!DOCTYPE html>
<html>
<head>
    <title>Title</title>
    <script>
        const API_BASE = '/api';
        // Use fetch to call API
    </script>
</head>
<body>
    <!-- Page content -->
</body>
</html>
```

### 5. Frontend Route Specification (app/__init__.py)
```python
# Frontend route - serves the main HTML page
@app.route('/')
def index():
    return render_template('index.html')

# Or for single-page applications:
@app.route('/<path:catch_all>')
def spa(catch_all):
    return render_template('index.html')
```

## Commercial-Grade Auth Pattern

When the app has user login/authentication, follow these rules:

1. **app/__init__.py** must:
   - Import and register auth blueprint: `from app.routes.auth import auth_bp` and `app.register_blueprint(auth_bp, url_prefix='/api/auth')`
   - Add page routes: `@app.route('/login')` → `render_template('login.html')`, `@app.route('/register')` → `render_template('register.html')`
   - Redirect unauthenticated users from main app routes to `/login`

2. **login.html** must contain a link to `/register` (e.g. "没有账号？去注册")
3. **register.html** must contain a link to `/login` (e.g. "已有账号？去登录")
4. **Blueprint routes** use relative paths: `@auth_bp.route('/login')` not `@auth_bp.route('/api/auth/login')` when url_prefix is `/api/auth`

## Common Modification Files

1. **app/__init__.py** - Register new blueprints AND add frontend routes
2. **app/models/__init__.py** - Add new model imports
3. **app/routes/__init__.py** - Add new route imports
4. **app/routes/xxx.py** - Create new route file
5. **app/models/xxx.py** - Create new model file
6. **templates/xxx.html** - Create new frontend page
7. **app/static/uploads/** - Uploaded files directory
8. **config.py** - Add configuration (optional)
9. **requirements.txt** - Add dependencies (optional)

## Frontend Routing

For a complete web application, you need both:
- **API routes**: `/api/xxx` - Handle data operations (JSON)
- **Frontend routes**: `/` or `/xxx` - Serve HTML pages

**Auth apps**: When the app has login, frontend_routes must include `/login` and `/register` in addition to the main app route.

Example frontend route setup:
```python
from flask import Flask, render_template

app = Flask(__name__)

# Serve main page
@app.route('/')
def index():
    return render_template('index.html')

# Serve specific pages
@app.route('/notes')
def notes_page():
    return render_template('notes.html')

# SPA mode - catch all routes
@app.route('/<path:catch_all>')
def spa(catch_all):
    return render_template('index.html')
```
