from app.database import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp(), nullable=False)

    # Relationships
    problems = db.relationship('Problem', backref='user', lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"

    def save(self):
        """Save the instance to the database."""
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_by_id(user_id):
        """Retrieve a user by their ID."""
        return User.query.get(user_id)

    @staticmethod
    def get_by_username(username):
        """Retrieve a user by their username."""
        return User.query.filter_by(username=username).first()

    @staticmethod
    def get_by_email(email):
        """Retrieve a user by their email."""
        return User.query.filter_by(email=email).first()