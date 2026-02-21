from app.database import db

class User:
    """
    Represents a user in the ACM Problem-Solving Platform system.
    """
    def __init__(self, username, email):
        self.username = username
        self.email = email

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"