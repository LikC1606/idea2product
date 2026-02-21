# Flask Base Framework Template
# This file defines the standard Flask project structure
# AI can read this file as reference to generate code that follows framework conventions

## File Structure

flask_base/
├── app/
│   ├── __init__.py      # App factory - register blueprints here
│   ├── models/
│   │   └── __init__.py  # Models package
│   └── routes/
│       └── __init__.py  # Routes package
├── templates/
│   └── index.html       # Frontend template
├── static/
│   └── static files (CSS, JS, images)
├── config.py            # Multi-environment config
├── app.py               # Entry point
├── requirements.txt     # Dependencies
└── .env                # Environment variables

## Key Interface Specifications

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

## Common Modification Files

1. **app/__init__.py** - Register new blueprints AND add frontend routes
2. **app/models/__init__.py** - Add new model imports
3. **app/routes/__init__.py** - Add new route imports
4. **app/routes/xxx.py** - Create new route file
5. **app/models/xxx.py** - Create new model file
6. **templates/xxx.html** - Create new frontend page
7. **config.py** - Add configuration (optional)
8. **requirements.txt** - Add dependencies (optional)

## Frontend Routing

For a complete web application, you need both:
- **API routes**: `/api/xxx` - Handle data operations (JSON)
- **Frontend routes**: `/` or `/xxx` - Serve HTML pages

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
