from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object('deployment.config.DeploymentConfig')

    db.init_app(app)

    from app.models.note import Note
    with app.app_context():
        db.create_all()

    from app.routes import notes_blueprint
    app.register_blueprint(notes_blueprint)

    return app
```

```python