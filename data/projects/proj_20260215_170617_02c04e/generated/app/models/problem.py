from app.database import db

class Problem(db.Model):
    __tablename__ = 'problems'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    solutions = db.relationship('Solution', backref='problem', lazy=True)

    def __init__(self, title, description, difficulty):
        self.title = title
        self.description = description
        self.difficulty = difficulty

    def save(self):
        """Save the problem to the database."""
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """Delete the problem from the database."""
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def get_all():
        """Retrieve all problems."""
        return Problem.query.all()

    @staticmethod
    def get_by_id(problem_id):
        """Retrieve a problem by its ID."""
        return Problem.query.get(problem_id)

    @staticmethod
    def get_by_difficulty(difficulty):
        """Retrieve problems filtered by difficulty."""
        return Problem.query.filter_by(difficulty=difficulty).all()