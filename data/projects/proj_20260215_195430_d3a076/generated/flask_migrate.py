from app.extensions import migrate
from app.database import db
from app.factory import create_app

app = create_app()
migrate.init_app(app, db)