from app.factory import create_app
from app.extensions import migrate
from app.database import db

app = create_app()

# Initialize database migration
migrate.init_app(app, db)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)