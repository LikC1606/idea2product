from app.database import db
from sqlalchemy import Column, Integer, String

class User(db.Model):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    created_at = Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def __repr__(self):
        return f'<User {self.username}>'

    def save(self):
        """Save the current user instance to the database."""
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_by_id(user_id):
        """Fetch a user by their ID."""
        return User.query.filter_by(id=user_id).first()

    @staticmethod
    def get_by_username(username):
        """Fetch a user by their username."""
        return User.query.filter_by(username=username).first()

    @staticmethod
    def get_all_users():
        """Fetch all users."""
        return User.query.all()