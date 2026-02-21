from flask import Flask
from .routes import app as routes_app

def create_app():
    app = Flask(__name__)
    app.register_blueprint(routes_app)
    return app
```

```python