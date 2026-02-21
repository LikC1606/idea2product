from app.database import db

class User:
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

    def to_dict(self):
        """
        Converts the User instance into a dictionary representation.
        """
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email
        }