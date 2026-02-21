from flask import Flask
from app import create_app
from app.database import DATABASE_URL, engine, SessionLocal, Base, metadata
from sqlalchemy.orm import sessionmaker
from app.models.problem import Problem
from app.models.user import User

# Create and configure the Flask app instance
app = create_app()

# Initialize the database
def init_db():
    Base.metadata.create_all(bind=engine)

# Define a route for testing the app
@app.route('/health', methods=['GET'])
def health_check():
    return {"status": "ok"}

# Run the application
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)