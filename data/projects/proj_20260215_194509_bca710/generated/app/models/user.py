# Path: app/models/user.py
# Purpose: User model for the ACM Problem-Solving Platform
# Layer: base

from app.database import db

class User:
    def __init__(self, username: str, email: str, password: str):
        self.username = username
        self.email = email
        self.password = password

    def to_dict(self):
        """Convert User object to dictionary representation."""
        return {
            'username': self.username,
            'email': self.email,
            'password': self.password
        }