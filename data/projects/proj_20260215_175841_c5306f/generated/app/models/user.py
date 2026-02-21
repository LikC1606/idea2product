from app.database import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        # This method would typically hash the password
        # Placeholder for password hashing logic
        self.password_hash = password

    def check_password(self, password):
        # This method would typically verify the hashed password
        # Placeholder for password verification logic
        return self.password_hash == password